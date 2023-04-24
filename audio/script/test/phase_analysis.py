import time

import click
from matplotlib import ticker
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from rich.prompt import Prompt

from audio.config.type import Range
from audio.console import console
from audio.math.algorithm import LogarithmicScale
from audio.math.rms import RMS, RMSResult, VoltageSampling
from audio.usb.usbtmc import Instrument, UsbTmc
from audio.utility import trim_value
from audio.utility.interrupt import InterruptHandler
from audio.utility.scpi import SCPI, Bandwidth, Switch


@click.command()
def phase_analysis():
    freq_min: float = float(
        Prompt.ask("Frequency Min (Hz) [10]", show_default=True, default=10),
    )
    freq_max: float = float(
        Prompt.ask("Frequency Max (Hz) [200_000]", show_default=True, default=200_000),
    )
    frequency_range = Range[float](freq_min, freq_max)
    amplitude: float = float(
        Prompt.ask("Amplitude (Vpp) [1]", show_default=True, default=1.0),
    )
    points_per_decade: int = int(
        Prompt.ask("Points per decade [10]", show_default=True, default=10),
    )
    n_sample: int = int(
        Prompt.ask("Sample per point [200]", show_default=True, default=200),
    )
    Fs_multiplier: int = int(
        Prompt.ask("Fs multiplier [50]", show_default=True, default=50),
    )
    interpolation_rate: int = int(
        Prompt.ask("interpolation rate [20]", show_default=True, default=20),
    )

    with InterruptHandler() as h:
        # Asks for the 2 instruments
        list_devices: list[Instrument] = UsbTmc.search_devices()

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
            SCPI.set_source_voltage_amplitude(1, round(amplitude, 5)),
            SCPI.set_source_frequency(1, round(frequency_range.min_value, 5)),
        ]

        SCPI.exec_commands(generator, generator_configs)

        generator_ac_curves: list[str] = [
            SCPI.set_output(1, Switch.ON),
        ]

        SCPI.exec_commands(generator, generator_ac_curves)
        time.sleep(1)

        log_scale: LogarithmicScale = LogarithmicScale(
            frequency_range.min_value,
            frequency_range.max_value,
            points_per_decade,
        )

        from audio.device.cdaq import Ni9223

        nidaq = Ni9223(n_sample)

        nidaq.create_task("Test")
        channels = [
            "cDAQ9189-1CDBE0AMod5/ai1",
            "cDAQ9189-1CDBE0AMod5/ai3",
        ]
        nidaq.add_ai_channel(channels)

        phase_offset_list: list[float] = []

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
            Fs = trim_value(frequency * Fs_multiplier, max_value=1000000)
            nidaq.set_sampling_clock_timing(Fs)

            nidaq.task_start()
            voltages = nidaq.read_multi_voltages()
            nidaq.task_stop()
            voltages_sampling_0 = VoltageSampling.from_list(
                voltages[0][100:],
                frequency,
                Fs,
            )
            voltages_sampling_1 = VoltageSampling.from_list(
                voltages[1][100:],
                frequency,
                Fs,
            )

            result_0: RMSResult = RMS.rms_v2(
                voltages_sampling_0,
                interpolation_rate=interpolation_rate,
                trim=False,
            )
            result_1: RMSResult = RMS.rms_v2(
                voltages_sampling_1,
                interpolation_rate=interpolation_rate,
                trim=False,
            )

            voltages_sampling_0 = VoltageSampling.from_list(
                result_0.voltages,
                input_frequency=frequency,
                sampling_frequency=Fs * interpolation_rate,
            )
            voltages_sampling_1 = VoltageSampling.from_list(
                result_1.voltages,
                input_frequency=frequency,
                sampling_frequency=Fs * interpolation_rate,
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

        generator_ac_curves: list[str] = [
            SCPI.set_output(1, Switch.OFF),
            SCPI.set_output(2, Switch.OFF),
        ]
        SCPI.exec_commands(generator, generator_ac_curves)
        generator.close()
        nidaq.task_close()

        plot: tuple[Figure, Axes] = plt.subplots(figsize=(16 * 2, 9 * 2), dpi=600)

        fig: Figure
        axes: Axes
        fig, axes = plot

        axes.semilogx(
            log_scale.f_list,
            phase_offset_list,
            ".-",
            linewidth=2,
        )

        title = Prompt.ask("Plot Title")
        axes.set_title("LA-125-2 CH_B 0dB")
        axes.set_title("LA-125-2 CH_B 15dB")
        axes.set_title("LA-125-2 CH_B 30dB")
        axes.set_title(
            f"{title}, A: {amplitude:0.2f} Vpp",
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
            return f"{x:.0f}"

        logMinorFormat = ticker.FuncFormatter(logMinorFormatFunc)

        # X Axis - Major
        axes.xaxis.set_major_formatter(logMinorFormat)

        from audio.constant import APP_AUDIO_TEST

        directory = APP_AUDIO_TEST / "LA-125_2ch"
        directory.mkdir(exist_ok=True, parents=True)

        from datetime import datetime

        time_now = datetime.now()
        file_name = f'{time_now.strftime("%Y.%m.%d-%H:%M:%S")} {title}'

        file = directory / f"{file_name}.pdf"

        fig.savefig(file)
        console.log(f"[FILE:SAVED]: {file}")
