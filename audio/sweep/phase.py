import copy
import time
from enum import Enum, auto
from math import log10
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Type

import click
import matplotlib.ticker as ticker
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from rich.panel import Panel
from rich.prompt import Confirm, FloatPrompt, Prompt

from audio.config.sweep import SweepConfig
from audio.config.type import Range
from audio.console import console
from audio.math.algorithm import LogarithmicScale
from audio.math.rms import RMS, RMSResult, VoltageSampling
from audio.sampling import config_set_level, plot_from_csv, sampling_curve
from audio.usb.usbtmc import Instrument, UsbTmc
from audio.utility import trim_value
from audio.utility.interrupt import InterruptHandler
from audio.utility.scpi import SCPI, Bandwidth, Switch


def phase_sweep(name: str, folder_path: Path, graph_path: Path, config: SweepConfig):

    with InterruptHandler() as h:
        # Asks for the 2 instruments
        list_devices: List[Instrument] = UsbTmc.search_devices()

        generator: UsbTmc = UsbTmc(list_devices[0])

        # Open the Instruments interfaces
        # Auto Close with the destructor
        generator.open()

        # Sets the Configuration for the Voltmeter
        generator_configs: list = [
            SCPI.clear(),
            SCPI.set_output(1, Switch.OFF),
            SCPI.set_output(2, Switch.OFF),
            SCPI.set_function_voltage_ac(),
            SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
            SCPI.set_source_voltage_amplitude(
                1, round(config.rigol.amplitude_peak_to_peak, 5)
            ),
            SCPI.set_source_frequency(1, round(config.sampling.frequency_min, 5)),
        ]

        SCPI.exec_commands(generator, generator_configs)

        generator_ac_curves: List[str] = [
            SCPI.set_output(1, Switch.ON),
        ]

        SCPI.exec_commands(generator, generator_ac_curves)
        time.sleep(1)

        log_scale: LogarithmicScale = LogarithmicScale(
            config.sampling.frequency_min,
            config.sampling.frequency_max,
            config.sampling.points_per_decade,
        )

        from audio.device.cDAQ import ni9223

        nidaq = ni9223(config.sampling.number_of_samples)

        nidaq.create_task("Test")
        channels = config.nidaq.input_channels
        nidaq.add_ai_channel(channels)

        phase_offset_list: List[float] = []

        import matplotlib.pyplot as plt
        from rich.progress import track

        for frequency in track(
            log_scale.f_list,
            total=len(log_scale.f_list),
            console=console,
        ):
            generator_configs: list = [
                SCPI.set_source_frequency(1, round(frequency, 5)),
            ]

            SCPI.exec_commands(generator, generator_configs)
            Fs = trim_value(
                frequency * config.sampling.Fs_multiplier, max_value=1000000
            )
            nidaq.set_sampling_clock_timing(Fs)

            nidaq.task_start()
            voltages = nidaq.read_multi_voltages()
            nidaq.task_stop()
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

            from audio.math.phase import phase_offset_v2

            phase_offset = phase_offset_v2(voltages_sampling_0, voltages_sampling_1)
            from audio.constant import APP_TEST

            APP_TEST.mkdir(exist_ok=True, parents=True)

            if phase_offset is None:

                voltages_sampling_0.save(APP_TEST / f"{frequency:.5f}_0.csv")
                voltages_sampling_1.save(APP_TEST / f"{frequency:.5f}_1.csv")

            phase_offset_list.append(phase_offset)

            if h.interrupted:
                break

        generator_ac_curves: List[str] = [
            SCPI.set_output(1, Switch.OFF),
            SCPI.set_output(2, Switch.OFF),
        ]
        SCPI.exec_commands(generator, generator_ac_curves)
        generator.close()
        nidaq.task_close()

        plot: Tuple[Figure, Axes] = plt.subplots(figsize=(16 * 2, 9 * 2), dpi=600)

        fig: Figure
        axes: Axes
        fig, axes = plot

        axes.semilogx(
            log_scale.f_list,
            phase_offset_list,
            ".-",
            linewidth=2,
        )

        if config.plot.title is not None:
            title = config.plot.title
        else:
            title = Prompt.ask("Phase Plot Title")
            graph_path = folder_path / f"{title}.pdf"

        axes.set_title(
            f"{title}, A: {config.rigol.amplitude_peak_to_peak:0.2f} Vpp",
            fontsize=50,
            pad=50,
        )

        axes.set_xlabel(
            "Frequency ($Hz$)",
            fontsize=40,
            labelpad=20,
        )
        axes.set_ylabel(
            "Angle ($deg$)",
            fontsize=40,
            labelpad=20,
        )

        axes.tick_params(
            axis="both",
            labelsize=22,
        )
        axes.tick_params(axis="x", rotation=45)
        axes.grid(True, linestyle="-", which="both", color="0.7")

        def logMinorFormatFunc(x, pos):
            return "{:.0f}".format(x)

        logMinorFormat = ticker.FuncFormatter(logMinorFormatFunc)

        # X Axis - Major
        # axes.xaxis.set_major_locator(logLocator)
        axes.xaxis.set_major_formatter(logMinorFormat)

        folder_path.mkdir(exist_ok=True, parents=True)

        fig.savefig(graph_path)
        console.log(f"[FILE:SAVED]: '{graph_path}'")
