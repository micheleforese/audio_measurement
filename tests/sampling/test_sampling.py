from curses.ascii import FS
from pathlib import Path
from time import sleep
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import usbtmc
from cDAQ.alghorithm import LogaritmicScale
from cDAQ.config import Config
from cDAQ.console import console
from cDAQ.scpi import SCPI, Bandwidth, Switch
from cDAQ.timer import Timer, Timer_Message
from cDAQ.UsbTmc import UsbTmc, get_device_list, print_devices_list
from cDAQ.utility import percentage_error, rms
from rich.live import Live
from rich.table import Column, Table
from usbtmc import Instrument
import pandas as pd


def curva(
    config_file_path: Path,
    measurements_file_path: Path,
    plot_file_path: Path,
    debug: bool = False,
):
    """Load JSON config"""
    config = Config(config_file_path)
    config.print()

    sampling_curve(
        config=config, measurements_file_path=measurements_file_path, debug=debug
    )

    plot(
        config=config,
        measurements_file_path=measurements_file_path,
        plot_file_path=plot_file_path,
        debug=debug,
    )


def sampling_curve(
    config: Config,
    measurements_file_path: Path,
    debug: bool = False,
):
    """Asks for the 2 instruments"""
    list_devices: List[Instrument] = get_device_list()
    if debug:
        print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    """Open the Instruments interfaces"""
    # Auto Close with the destructor
    generator.open()

    """Sets the Configuration for the Voltmeter"""
    generator_configs: list = [
        SCPI.clear(),
        SCPI.reset(),
        SCPI.set_output(1, Switch.OFF),
        SCPI.set_function_voltage_ac(),
        SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
        SCPI.set_source_voltage_amplitude(1, round(config.amplitude_pp, 5)),
        SCPI.set_source_frequency(1, round(config.sampling.min_Hz, 5)),
    ]

    SCPI.exec_commands(generator, generator_configs)

    generator_ac_curves: List[str] = [
        SCPI.set_output(1, Switch.ON),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    log_scale: LogaritmicScale = LogaritmicScale(
        config.sampling.min_Hz,
        config.sampling.max_Hz,
        config.step,
        config.sampling.points_per_decade,
    )

    f = open(measurements_file_path, "w")
    frequency: float = round(config.sampling.min_Hz, 5)

    table = Table(
        Column(f"Frequency [Hz]", justify="right"),
        Column(f"Number of samples", justify="right"),
        Column(f"Rms Value [V]", justify="right"),
        Column("Voltage Expected", justify="right"),
        Column(f"Relative Error", justify="right"),
        Column(f"Time [s]", justify="right"),
    )

    with Live(table, screen=False, console=console, auto_refresh=True) as live:

        while log_scale.check():
            log_scale.next()
            # Frequency in Hz
            frequency = log_scale.get_frequency()

            # Sets the Frequency
            generator.write(SCPI.set_source_frequency(1, round(frequency, 5)))

            sleep(0.4)

            number_of_periods = 10

            samples_per_period = 10

            if frequency <= 100:
                config.number_of_samples = 10 * number_of_periods
            elif frequency <= 1000:
                config.number_of_samples = 20 * number_of_periods
            elif frequency <= 10000:
                config.number_of_samples = 30 * number_of_periods
            else:
                config.number_of_samples = 30 * number_of_periods

            config.Fs = config.number_of_samples / number_of_periods * frequency
            if config.Fs > 102000:
                config.Fs = 102000

            # live.console.log(
            #     "number_of_samples, Fs: {} - {}".format(
            #         config.number_of_samples, config.Fs
            #     )
            # )

            time = Timer()
            time.start()

            # GET MEASUREMENTS
            rms_value = rms(
                frequency=frequency,
                Fs=config.Fs,
                ch_input=config.nidaq.ch_input,
                max_voltage=config.nidaq.max_voltage,
                min_voltage=config.nidaq.min_voltage,
                number_of_samples=config.number_of_samples,
            )

            message: Timer_Message = time.stop()

            perc_error = percentage_error(
                exact=(config.amplitude_pp / 2) / np.math.sqrt(2), approx=rms_value
            )

            table.add_row(
                "{:.5f}".format(frequency),
                "{}".format(config.number_of_samples),
                "{:.5f} ".format(round(rms_value, 5)),
                "{:.5f} ".format(round((config.amplitude_pp / 2) / np.math.sqrt(2), 5)),
                "[{}]{:.3f}[/]".format(
                    "cyan" if perc_error <= 0 else "red", round(perc_error, 3)
                ),
                "[cyan]{}[/]".format(message.elapsed_time),
            )

            # if(debug):
            #     live.console.log(
            #         "Frequency - Rms Value: {} - {}".format(round(frequency, 5), rms_value))

            """File Writing"""
            f.write("{},{}\n".format(frequency, rms_value))

    f.close()


def plot(
    config: Config,
    measurements_file_path: Path,
    plot_file_path: Path,
    debug: bool = False,
):
    if debug:
        console.print("Measurements_file_path: {}".format(measurements_file_path))

    x_frequency: List[float] = []
    y_dBV: List[float] = []

    csvfile = np.genfromtxt(measurements_file_path, delimiter=",")

    measurements = pd.read_csv(measurements_file_path)
    console.print(measurements)

    for row in list(csvfile):
        y_dBV.append(
            20 * np.math.log10(row[1] * 2 * np.math.sqrt(2) / config.amplitude_pp)
        )
        x_frequency.append(row[0])

    plt.plot(x_frequency, y_dBV)
    plt.xscale("log")
    plt.title("Frequency response")
    plt.xlabel("Frequency")
    plt.ylabel(r"$\frac{V_out}{V_int} dB$", rotation=90)
    plt.ylim(-5, 5)
    plt.savefig(plot_file_path)


def test_curva():

    THIS_PATH = Path(__file__).parent

    curva(
        config_file_path=THIS_PATH / "basic.json",
        measurements_file_path=THIS_PATH / "basic.csv",
        plot_file_path=THIS_PATH / "basic.png",
        debug=True,
    )


def test_error_sampling():
    """
    Remember to set ENV variable PYTHONIOENCODING to utf8
    export PYTHONIOENCODING=utf8
    """
    THIS_PATH = Path(__file__).parent

    config: Config = Config(THIS_PATH / "basic.json")

    measurements_file_path: Path = THIS_PATH / "basic.csv"
    debug = True

    """Asks for the 2 instruments"""
    list_devices: List[Instrument] = get_device_list()
    if debug:
        print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    """Open the Instruments interfaces"""
    # Auto Close with the destructor
    generator.open()

    """Sets the Configuration for the Voltmeter"""
    generator_configs: list = [
        SCPI.clear(),
        SCPI.reset(),
        SCPI.set_output(1, Switch.OFF),
        SCPI.set_function_voltage_ac(),
        SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
        SCPI.set_source_voltage_amplitude(1, round(2, 5)),
    ]

    SCPI.exec_commands(generator, generator_configs)

    log_scale: LogaritmicScale = LogaritmicScale(
        config.sampling.min_Hz,
        config.sampling.max_Hz,
        config.step,
        config.sampling.points_per_decade,
    )

    f = open(measurements_file_path, "w")

    f.write(
        "{},{},{},{},{},{},{},{},{}\n".format(
            "Frequency [Hz]",
            "Fs [Hz]",
            "Samples",
            "Samples x period",
            "Periods",
            "Rms Value [V]",
            "Real Voltage",
            "R.E.",
            "Time [s]",
        )
    )

    table = Table(
        Column(f"Check", justify="center"),
        Column(f"Frequency [Hz]", justify="right"),
        Column(f"Fs [Hz]", justify="right"),
        Column(f"Samples", justify="right"),
        Column(f"Samples x period", justify="right"),
        Column(f"Periods", justify="right"),
        Column(f"Rms Value [V]", justify="right"),
        Column(f"Real Voltage", justify="right"),
        Column(f"R.E.", justify="right"),
        Column(f"Time [s]", justify="right"),
        title_justify="center",
    )

    generator_ac_curves: List[str] = [
        SCPI.set_source_frequency(1, round(10, 5)),
        SCPI.set_output(1, Switch.ON),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    with Live(
        table,
        screen=False,
        console=console,
        vertical_overflow="visible",
        auto_refresh=True,
    ) as live:

        frequency: List[float] = [
            10,
            50,
            100,
            500,
            1000,
            5000,
            10000,
        ]

        max_n_sample_constant: float = 1000
        max_Fs_constant = 102000

        min_n_sample_per_period_constant: float = 2
        max_n_samples_per_period_constant: float = 10

        for freq in frequency:
            generator.write(SCPI.set_source_frequency(1, round(freq, 5)))
            sleep(0.4)

            # Algorithm Constant DO NOT TOUCH
            min_Fs_constant = freq * 2

            Fs: float = min_Fs_constant
            max_Fs: float = 0

            max_Fs_relative: float = max_n_samples_per_period_constant * freq

            if max_Fs_relative > max_Fs_constant:
                max_Fs = max_Fs_constant
            else:
                max_Fs = max_Fs_relative

            # live.console.log(
            #     "Fs",
            #     np.logspace(
            #         np.math.log10(min_Fs_constant),
            #         np.math.log10(max_Fs),
            #         10,
            #     ),
            # )

            for Fs in np.logspace(
                np.math.log10(min_Fs_constant),
                np.math.log10(max_Fs),
                10,
            ):
                if Fs > max_Fs:
                    Fs = max_Fs

                # live.console.log(
                #     "n_sample",
                #     np.logspace(
                #         np.math.log10(min_n_sample_per_period_constant),
                #         np.math.log10(max_n_sample_constant),
                #         10,
                #     ),
                # )

                for n_sample in np.logspace(
                    np.math.log10(min_n_sample_per_period_constant),
                    np.math.log10(max_n_sample_constant),
                    10,
                ):
                    n_sample = int(round(n_sample))

                    if n_sample > max_n_sample_constant:
                        n_sample = max_n_sample_constant

                    n_sample_per_period = Fs / freq
                    n_periods = n_sample / n_sample_per_period

                    time = Timer()
                    time.start()

                    # GET MEASUREMENTS
                    rms_value = rms(
                        frequency=freq,
                        Fs=Fs,
                        ch_input=config.nidaq.ch_input,
                        max_voltage=config.nidaq.max_voltage,
                        min_voltage=config.nidaq.min_voltage,
                        number_of_samples=n_sample,
                    )

                    message: Timer_Message = time.stop()

                    perc_error = percentage_error(
                        exact=(config.amplitude_pp / 2) / np.math.sqrt(2),
                        approx=rms_value,
                    )

                    table.add_row(
                        ":white_heavy_check_mark-emoji:"
                        if abs(perc_error) < 1.2
                        else ":cross_mark-emoji:",
                        "{:.5f}".format(freq),
                        "{:.5f}".format(Fs),
                        "{}".format(n_sample),
                        "{:.3}".format(n_sample_per_period),
                        "{:.3f}".format(n_periods),
                        "{:.5f} ".format(round(rms_value, 5)),
                        "{:.5f} ".format(
                            round((config.amplitude_pp / 2) / np.math.sqrt(2), 5)
                        ),
                        "[{}]{:.3f}[/]".format(
                            "cyan" if perc_error <= 0 else "red", round(perc_error, 3)
                        ),
                        "[cyan]{}[/]".format(message.elapsed_time),
                    )

                    f.write(
                        "{},{},{},{},{},{},{},{},{}\n".format(
                            "{:.5f}".format(freq),
                            "{:.5f}".format(Fs),
                            "{}".format(n_sample),
                            "{:.3}".format(n_sample_per_period),
                            "{:.3f}".format(n_periods),
                            "{:.5f} ".format(round(rms_value, 5)),
                            "{:.5f} ".format(
                                round((config.amplitude_pp / 2) / np.math.sqrt(2), 5)
                            ),
                            "{:.3f}".format(round(perc_error, 3)),
                            "{}".format(message.elapsed_time),
                        )
                    )

    f.close()
