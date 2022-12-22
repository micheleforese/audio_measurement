import copy
import time
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
)
from rich.prompt import Confirm, FloatPrompt, Prompt
from rich.table import Column, Table
from usbtmc import Instrument

import audio.ui.terminal as ui_t
from audio.config.plot import PlotConfig
from audio.config.sweep import SweepConfig
from audio.config.type import Range
from audio.console import console
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
from audio.procedure import (
    DataProcedure,
    Procedure,
    ProcedureAsk,
    ProcedureCheck,
    ProcedureCheckCondition,
    ProcedureDefault,
    ProcedureFile,
    ProcedureInsertionGain,
    ProcedureMultiPlot,
    ProcedurePhaseSweep,
    ProcedurePrint,
    ProcedureSerialNumber,
    ProcedureSetLevel,
    ProcedureStep,
    ProcedureSweep,
    ProcedureTask,
    ProcedureText,
)
from audio.sampling import config_set_level, plot_from_csv, sampling_curve
from audio.usb.usbtmc import Instrument, UsbTmc
from audio.utility import trim_value
from audio.utility.interrupt import InterruptHandler
from audio.utility.scpi import SCPI, Bandwidth, Switch
from audio.utility.timer import Timer, Timer_Message
from datetime import timedelta


class AmplitudeSweepTable:
    table: Table

    def __init__(self) -> None:
        self.table = Table(
            Column(r"Frequency [Hz]", justify="right"),
            Column(r"Fs [Hz]", justify="right"),
            Column("Number of samples", justify="right"),
            Column(r"Input Voltage [V]", justify="right"),
            Column(r"Rms Value [V]", justify="right"),
            Column(r"Gain [dB]", justify="right"),
            Column(r"Time [s]", justify="right"),
            Column(r"Max Voltage [V]", justify="right"),
            Column(r"Min Voltage [V]", justify="right"),
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
        time: timedelta,
        voltage_max: float,
        voltage_min: float,
    ):
        self.table.add_row(
            "{:.2f}".format(frequency),
            "{:.2f}".format(Fs),
            "{}".format(number_of_samples),
            "{}".format(amplitude_peak_to_peak),
            "{:.5f} ".format(rms),
            "[{}]{:.2f}[/]".format("red" if gain_dBV <= 0 else "green", gain_dBV),
            "[cyan]{}[/]".format(time),
            "{:.5f}".format(voltage_max),
            "{:.5f}".format(voltage_min),
        )


def amplitude_sweep(
    config: SweepConfig,
    sweep_home_path: Path,
    sweep_file_path: Path,
    debug: bool = False,
):
    DEFAULT = {"delay": 0.2}

    HOME: Path = sweep_home_path
    HOME.mkdir(parents=True, exist_ok=True)

    measurements_path: Path = HOME / "sweep"
    measurements_path.mkdir(parents=True, exist_ok=True)

    progress_list_task = Progress(
        SpinnerColumn(),
        "•",
        TextColumn(
            "[bold blue]{task.description}[/] - [bold green]{task.fields[task]}[/]",
        ),
        transient=True,
    )
    progress_sweep = Progress(
        SpinnerColumn(),
        "•",
        TextColumn(
            "[bold blue]{task.description}",
            justify="right",
        ),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        "•",
        TimeElapsedColumn(),
        "•",
        MofNCompleteColumn(),
        TextColumn(
            " - Frequency: [bold green]{task.fields[frequency]} - RMS: {task.fields[rms]}"
        ),
        console=console,
        transient=True,
    )
    progress_task = Progress(
        SpinnerColumn(),
        "•",
        TextColumn(
            "[bold blue]{task.description}",
        ),
        transient=True,
    )

    amplitude_sweep_table = AmplitudeSweepTable()

    live_group = Group(
        Panel(
            Group(
                amplitude_sweep_table.table,
                progress_list_task,
                progress_sweep,
                progress_task,
            )
        ),
    )
    live = Live(
        live_group,
        transient=True,
        console=console,
        vertical_overflow="visible",
    )
    live.start()

    task_sampling = progress_list_task.add_task(
        "Sampling", start=False, task="Retrieving Devices"
    )
    progress_list_task.start_task(task_sampling)

    # Asks for the 2 instruments
    try:
        list_devices: List[Instrument] = UsbTmc.search_devices()

        if len(list_devices) < 1:
            raise Exception("UsbTmc devices not found.")

        if debug:
            UsbTmc.print_devices_list(list_devices)

        generator: UsbTmc = UsbTmc(list_devices[0])

    except Exception as e:
        console.print(f"{e}")

    progress_list_task.update(task_sampling, task="Setting Devices")

    if not generator.instr.instrument.connected:
        generator.open()

    if config.rigol.amplitude_peak_to_peak > 12:
        generator.exec(
            [
                SCPI.set_output(1, Switch.OFF),
            ]
        )
        generator.close()
        console.print("[ERROR] - Voltage Input > 12.", style="error")
        exit()

    # Sets the Configuration for the Voltmeter
    generator.exec(
        [
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

    sleep(2)

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

    progress_list_task.update(task_sampling, task="Sweep")

    task_sweep = progress_sweep.add_task(
        "Sweep",
        start=False,
        total=len(log_scale.f_list),
        frequency="",
        rms="",
    )
    progress_sweep.start_task(task_sweep)

    Fs = trim_value(
        frequency * config.sampling.Fs_multiplier, max_value=config.nidaq.Fs_max
    )

    nidaq = ni9223(
        config.sampling.number_of_samples,
        input_channel=[config.nidaq.input_channel],
    )

    nidaq.create_task("Sampling")
    nidaq.add_ai_channel([config.nidaq.input_channel])
    nidaq.set_sampling_clock_timing(Fs)

    for frequency in log_scale.f_list:

        # Sets the Frequency
        generator.write(SCPI.set_source_frequency(1, round(frequency, 5)))

        sleep(
            config.sampling.delay_measurements
            if config.sampling.delay_measurements is not None
            else DEFAULT.get("delay")
        )

        # Trim number_of_samples to MAX value
        Fs = trim_value(
            frequency * config.sampling.Fs_multiplier, max_value=config.nidaq.Fs_max
        )

        # Trim number_of_samples to MAX value
        if config.sampling.number_of_samples_max is not None:
            if (
                config.sampling.number_of_samples
                > config.sampling.number_of_samples_max
            ):

                config.sampling.number_of_samples = int(
                    trim_value(
                        config.sampling.number_of_samples,
                        config.sampling.number_of_samples_max,
                    )
                )

        oversampling_ratio = Fs / frequency
        n_periods = config.sampling.number_of_samples / oversampling_ratio

        frequency_list.append(frequency)
        fs_list.append(Fs)
        oversampling_ratio_list.append(oversampling_ratio)
        n_periods_list.append(n_periods)
        n_samples_list.append(config.sampling.number_of_samples)

        time = Timer()
        time.start()

        sweep_frequency_path = measurements_path / "{}".format(
            round(frequency, 5)
        ).replace(".", "_", 1)
        sweep_frequency_path.mkdir(parents=True, exist_ok=True)

        save_file_path = sweep_frequency_path / "sample.csv"

        # GET MEASUREMENTS

        nidaq.set_sampling_clock_timing(Fs)
        nidaq.task_start()
        voltages = nidaq.read_single_voltages()
        nidaq.task_stop()

        voltages_sampling = VoltageSampling.from_list(
            voltages,
            frequency,
            Fs,
        )
        result: RMSResult = RMS.rms_v2(voltages_sampling)
        voltages_sampling.save(save_file_path)

        message: Timer_Message = time.stop()

        if result.rms:
            max_voltage = max(result.voltages)
            min_voltage = min(result.voltages)

            rms_list.append(result.rms)

            progress_sweep.update(
                task_sweep,
                frequency=f"{round(frequency, 5)}",
                rms="{}".format(round(result.rms, 5)),
            )

            from audio.math.voltage import calculate_gain_dB

            gain_bBV = calculate_gain_dB(
                Vin=Vpp_to_Vrms(config.rigol.amplitude_peak_to_peak), Vout=result.rms
            )
            # gain_bBV: float = dBV(
            #     V_in=Vpp_to_Vrms(config.rigol.amplitude_peak_to_peak),
            #     V_out=result.rms,
            # )

            # transfer_func_dB = transfer_function(
            #     result.rms, Vpp_to_Vrms(config.rigol.amplitude_peak_to_peak)
            # )

            if max_dB:
                max_dB = max(abs(max_dB), abs(gain_bBV))
            else:
                max_dB = gain_bBV

            amplitude_sweep_table.add_data(
                frequency=frequency,
                Fs=Fs,
                amplitude_peak_to_peak=config.rigol.amplitude_peak_to_peak,
                number_of_samples=config.sampling.number_of_samples,
                rms=result.rms,
                gain_dBV=gain_bBV,
                time=message.elapsed_time,
                voltage_max=max_voltage,
                voltage_min=min_voltage,
            )
            dBV_list.append(gain_bBV)

            progress_sweep.update(task_sweep, advance=1)

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

    console.print(f"[FILE - SWEEP CSV] '{sweep_file_path}'")

    sweep_data.save(sweep_file_path)

    progress_sweep.remove_task(task_sweep)

    progress_list_task.update(task_sampling, task="Shutting down the Channel 1")

    generator.exec(
        [
            SCPI.set_output(1, Switch.OFF),
            SCPI.clear(),
        ],
    )

    progress_list_task.remove_task(task_sampling)

    if debug:
        console.print(Panel("max_dB: {}".format(max_dB)))

    console.print(
        Panel(
            f'[bold][[blue]FILE[/blue] - [cyan]CSV[/cyan]][/bold] - "[bold green]{sweep_file_path.absolute()}[/bold green]"'
        )
    )

    live.stop()
