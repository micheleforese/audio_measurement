from cDAQ.plot import Plot
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import usbtmc
from cDAQ.alghorithm import LogaritmicScale
from cDAQ.config import Config
from cDAQ.console import console
from cDAQ.scpi import SCPI, Bandwidth, Switch
from cDAQ.timer import Timer, Timer_Message
from cDAQ.UsbTmc import get_device_list, print_devices_list
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

    generator: usbtmc.Instrument = list_devices[0]

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

            number_of_periods = 5

            if frequency <= 100:
                config.Fs = 1000
                config.number_of_samples = int(
                    (config.Fs / frequency) * number_of_periods
                )
            elif frequency <= 1000:
                config.Fs = 10000
                config.number_of_samples = int(
                    (config.Fs / frequency) * number_of_periods
                )
            elif frequency <= 10000:
                config.Fs = 102000
                config.number_of_samples = int(
                    (config.Fs / frequency) * number_of_periods
                )

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
                exact=(config.amplitude_pp / 2) / np.sqrt(2), approx=rms_value
            )

            table.add_row(
                "{:.5f}".format(frequency),
                "{}".format(config.number_of_samples),
                "{:.5f} ".format(round(rms_value, 5)),
                "{:.5f} ".format(round((config.amplitude_pp / 2) / np.sqrt(2), 5)),
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
        y_dBV.append(20 * np.log10(row[1] * 2 * np.sqrt(2) / config.amplitude_pp))
        x_frequency.append(row[0])

    plot = Plot()
    plot.generate_plot(
        plot_file_path,
        x_frequency,
        y_dBV,
        title="Frequency response",
        xscale="log",
        xlabel="Frequency",
        ylabel=r"$\frac{V_out}{V_int} dB$",
        ylim=[-10, 10],
    )


def test_curva():

    THIS_PATH = Path(__file__).parent

    curva(
        THIS_PATH / "basic.json",
        THIS_PATH / "basic.csv",
        THIS_PATH / "basic.png",
        debug=True,
    )
