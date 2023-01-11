import copy
import time
from datetime import timedelta
from enum import Enum, auto
from math import log10, sqrt
from pathlib import Path
from time import sleep
from typing import Callable, Dict, List, Optional, Tuple, Type

import click
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    track,
)
from rich.prompt import Confirm, FloatPrompt, Prompt
from rich.table import Column, Table
from usbtmc import Instrument

from audio.config.plot import PlotConfig
from audio.config.sweep import SweepConfig
from audio.config.type import Range
from audio.console import console
from audio.database.db import Database
from audio.device.cDAQ import ni9223
from audio.math import dBV, percentage_error, transfer_function
from audio.math.algorithm import LogarithmicScale
from audio.math.interpolation import INTERPOLATION_KIND, logx_interpolation_model
from audio.math.pid import PID_Controller, Timed_Value
from audio.math.rms import RMS, RMSResult, VoltageSampling
from audio.math.voltage import VdBu_to_Vrms, Vpp_to_Vrms, calculate_gain_dB
from audio.model.file import File
from audio.model.insertion_gain import InsertionGain
from audio.model.sampling import VoltageSampling
from audio.model.set_level import SetLevel
from audio.model.sweep import SweepData
from audio.plot import multiplot
from audio.sampling import config_set_level, plot_from_csv, sampling_curve
from audio.usb.usbtmc import Instrument, ResourceManager, UsbTmc
from audio.utility import trim_value
from audio.utility.interrupt import InterruptHandler
from audio.utility.scpi import SCPI, Bandwidth, SCPI_v2, Switch
from audio.utility.timer import Timer, Timer_Message


class SweepAmplitudePhaseTable:
    table: Table

    def __init__(self) -> None:
        self.table = Table(
            Column(r"Frequency [Hz]", justify="right"),
            Column(r"Fs [Hz]", justify="right"),
            Column(r"Number of samples", justify="right"),
            Column(r"Input Voltage [V]", justify="right"),
            Column(r"Rms Value [V]", justify="right"),
            Column(r"Gain [dB]", justify="right"),
            Column(r"Sampling Time[s]", justify="right"),
            Column(r"Calculation Time[s]", justify="right"),
            title="[blue]Sweep.",
        )

    def add_data(
        self,
        frequency: float,
        Fs: float,
        number_of_samples: int,
        amplitude_peak_to_peak: float,
        rms: float,
        gain_dBV: float,
        sampling_time: timedelta,
        calculation_time: timedelta,
    ):
        self.table.add_row(
            "{:.2f}".format(frequency),
            "{:.2f}".format(Fs),
            "{}".format(number_of_samples),
            "{}".format(amplitude_peak_to_peak),
            "{:.5f} ".format(rms),
            "[{}]{:.2f}[/]".format("red" if gain_dBV <= 0 else "green", gain_dBV),
            "[cyan]{}[/]".format(sampling_time),
            "[cyan]{}[/]".format(calculation_time),
        )


def sweep_amplitude_phase(
    config: SweepConfig,
    sweep_home_path: Path,
    sweep_amplitude_file_graph_path: Path,
    sweep_phase_file_graph_path: Path,
):
    DEFAULT = {"delay": 0.2}

    HOME: Path = sweep_home_path
    HOME.mkdir(parents=True, exist_ok=True)

    db = Database(HOME / "database.db")

    measurements_path: Path = HOME / "sweep"
    measurements_path.mkdir(parents=True, exist_ok=True)

    # Asks for the 2 instruments
    try:
        rm = ResourceManager()
        list_devices = rm.search_resources()
        if len(list_devices) < 1:
            raise Exception("UsbTmc devices not found.")
        generator = rm.open_resource(list_devices[0])

    except Exception as e:
        console.print(f"{e}")

    sweep_amplitude_phase_table = SweepAmplitudePhaseTable()

    scpi = SCPI_v2()

    if not generator.instr.connected:
        generator.open()

    # Sets the Configuration for the Voltmeter
    generator.exec(
        [
            scpi.reset,
            SCPI.reset(),
            SCPI.clear(),
            SCPI.set_output(1, Switch.OFF),
            SCPI.set_function_voltage_ac(),
            SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
            SCPI.set_source_voltage_amplitude(
                1,
                round(
                    config.rigol.amplitude_peak_to_peak,
                    5,
                ),
            ),
            SCPI.set_source_frequency(1, round(config.sampling.frequency_min, 5)),
        ]
    )
    generator.exec(
        [
            SCPI.set_output(1, Switch.ON),
        ]
    )

    log_scale: LogarithmicScale = LogarithmicScale(
        config.sampling.frequency_min,
        config.sampling.frequency_max,
        config.sampling.points_per_decade,
    )

    frequency_list: List[float] = []
    rms_list: List[float] = []
    dBV_list: List[float] = []
    fs_list: List[float] = []
    oversampling_ratio_list: List[float] = []
    n_periods_list: List[float] = []
    n_samples_list: List[int] = []

    frequency: float = round(config.sampling.frequency_min, 5)

    max_dB: Optional[float] = None

    Fs = trim_value(
        frequency * config.sampling.Fs_multiplier,
        max_value=config.nidaq.Fs_max,
    )
    # Trim number_of_samples to MAX value
    if config.sampling.number_of_samples_max is not None:
        if config.sampling.number_of_samples > config.sampling.number_of_samples_max:

            config.sampling.number_of_samples = int(
                trim_value(
                    config.sampling.number_of_samples,
                    config.sampling.number_of_samples_max,
                )
            )
    nidaq = ni9223(
        config.sampling.number_of_samples,
        input_channel=config.nidaq.input_channels,
    )

    nidaq.create_task("Sweep Amplitude-Phase")
    nidaq.add_ai_channel(config.nidaq.input_channels)
    nidaq.set_sampling_clock_timing(Fs)

    timer = Timer()

    for frequency in track(
        log_scale.f_list,
        total=len(log_scale.f_list),
        console=console,
    ):
        timer.start()

        # Sets the Frequency
        generator.write(
            SCPI.set_source_frequency(1, round(frequency, 5)),
        )

        sleep(
            config.sampling.delay_measurements
            if config.sampling.delay_measurements is not None
            else DEFAULT.get("delay")
        )

        # Trim number_of_samples to MAX value
        Fs = trim_value(
            frequency * config.sampling.Fs_multiplier,
            max_value=config.nidaq.Fs_max,
        )

        oversampling_ratio = Fs / frequency
        n_periods = config.sampling.number_of_samples / oversampling_ratio

        frequency_list.append(frequency)
        fs_list.append(Fs)
        oversampling_ratio_list.append(oversampling_ratio)
        n_periods_list.append(n_periods)
        n_samples_list.append(config.sampling.number_of_samples)

        # BEGIN -- CSV FILE
        sweep_frequency_path = measurements_path / "{}".format(
            round(frequency, 5)
        ).replace(".", "_", 1)
        sweep_frequency_path.mkdir(parents=True, exist_ok=True)

        save_file_path = sweep_frequency_path / "sample.csv"
        # END -- CSV FILE

        # GET MEASUREMENTS

        nidaq.set_sampling_clock_timing(Fs)
        nidaq.task_start()
        timer.start()
        voltages = nidaq.read_multi_voltages()
        sampling_time = timer.stop()
        nidaq.task_stop()

        timer.start()
        voltages_sampling_0 = VoltageSampling.from_list(voltages[0], frequency, Fs)
        voltages_sampling_1 = VoltageSampling.from_list(voltages[1], frequency, Fs)

        result_0: RMSResult = RMS.rms_v2(
            voltages_sampling_0,
            interpolation_rate=config.sampling.interpolation_rate,
            trim=False,
        )
        result_1: RMSResult = RMS.rms_v2(
            voltages_sampling_1,
            interpolation_rate=config.sampling.interpolation_rate,
            trim=False,
        )
        voltages_sampling_0 = VoltageSampling.from_list(
            result_0.voltages,
            input_frequency=frequency,
            sampling_frequency=Fs * config.sampling.interpolation_rate,
        )
        voltages_sampling_1 = VoltageSampling.from_list(
            result_1.voltages,
            input_frequency=frequency,
            sampling_frequency=Fs * config.sampling.interpolation_rate,
        )

        voltages_sampling = VoltageSampling.from_list(
            voltages,
            frequency,
            Fs,
        )
        result: RMSResult = RMS.rms_v2(voltages_sampling)
        voltages_sampling.save(save_file_path)

        sampling_time = timer.stop()
        calculation_time = timer.stop()

        if result.rms:

            rms_list.append(result.rms)

            gain_bBV = calculate_gain_dB(
                Vin=Vpp_to_Vrms(config.rigol.amplitude_peak_to_peak), Vout=result.rms
            )

            if max_dB:
                max_dB = max(abs(max_dB), abs(gain_bBV))
            else:
                max_dB = gain_bBV

            sweep_amplitude_phase_table.add_data(
                frequency=frequency,
                Fs=Fs,
                amplitude_peak_to_peak=config.rigol.amplitude_peak_to_peak,
                number_of_samples=config.sampling.number_of_samples,
                rms=result.rms,
                gain_dBV=gain_bBV,
                sampling_time=sampling_time,
                calculation_time=calculation_time,
            )
            dBV_list.append(gain_bBV)

        else:
            console.print("[ERROR] - Error retrieving rms_value.", style="error")

    sampling_data = pd.DataFrame(
        list(
            zip(
                frequency_list,
                rms_list,
                dBV_list,
                fs_list,
                oversampling_ratio_list,
                n_periods_list,
                n_samples_list,
            )
        ),
        columns=[
            "frequency",
            "rms",
            "dBV",
            "fs",
            "oversampling_ratio",
            "n_periods",
            "n_samples",
        ],
    )

    sweep_data = SweepData(
        sampling_data,
        amplitude=config.rigol.amplitude_peak_to_peak,
        config=config.plot,
    )

    console.print(f"[FILE - SWEEP CSV] '{sweep_amplitude_file_graph_path}'")

    sweep_data.save(sweep_amplitude_file_graph_path)

    generator.exec(
        [
            SCPI.set_output(1, Switch.OFF),
            SCPI.clear(),
        ],
    )

    console.print(
        Panel(
            f'[bold][[blue]FILE[/blue] - [cyan]CSV[/cyan]][/bold] - "[bold green]{sweep_amplitude_file_graph_path.absolute()}[/bold green]"'
        )
    )
