from pathlib import Path
from time import sleep
from typing import List, Optional, Tuple, Type

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from rich.live import Live
from rich.table import Column, Table
from usbtmc import Instrument

from cDAQ.alghorithm import LogaritmicScale
from cDAQ.config import Config
from cDAQ.console import console
from cDAQ.scpi import SCPI, Bandwidth, Switch
from cDAQ.timer import Timer, Timer_Message
from cDAQ.usbtmc import UsbTmc, get_device_list, print_devices_list
from cDAQ.utility import percentage_error, rms


def curva(
    config_file_path: Path,
    measurements_file_path: Path,
    plot_file_path: Path,
    debug: bool = False,
):

    """Load JSON config"""
    config = Config(config_file_path)

    if debug:
        config.print()

    sampling_curve(
        config=config, measurements_file_path=measurements_file_path, debug=debug
    )

    plot_from_csv(
        measurements_file_path=measurements_file_path,
        plot_file_path=plot_file_path,
        y_lim_min=config.plot.y_limit[0],
        y_lim_max=config.plot.y_limit[1],
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
    f.write("{},{},{}\n".format("Frequency", "RMS Value", "dbV"))

    frequency: float = round(config.sampling.min_Hz, 5)

    table = Table(
        Column(f"Frequency [Hz]", justify="right"),
        Column(f"Number of samples", justify="right"),
        Column(f"Rms Value [V]", justify="right"),
        Column("Voltage Expected", justify="right"),
        Column(f"Relative Error", justify="right"),
        Column(f"Time [s]", justify="right"),
    )

    with Live(
        table,
        screen=False,
        console=console,
        vertical_overflow="visible",
        auto_refresh=True,
    ) as live:

        while log_scale.check():
            log_scale.next()
            # Frequency in Hz
            frequency = log_scale.get_frequency()

            # Sets the Frequency
            generator.write(SCPI.set_source_frequency(1, round(frequency, 5)))

            sleep(0.4)

            if frequency <= 100:
                config.Fs = frequency * 4
                config.number_of_samples = 400
            elif frequency <= 1000:
                config.Fs = frequency * 3
                config.number_of_samples = 400
            elif frequency <= 10000:
                config.Fs = frequency * 6
                config.number_of_samples = 400
            else:
                config.Fs = frequency * 3
                config.number_of_samples = 400

            if config.Fs > 102000:
                config.Fs = 102000

            time = Timer()
            time.start()

            # GET MEASUREMENTS
            rms_value: Optional[float] = rms(
                frequency=frequency,
                Fs=config.Fs,
                ch_input=config.nidaq.ch_input,
                max_voltage=config.nidaq.max_voltage,
                min_voltage=config.nidaq.min_voltage,
                number_of_samples=config.number_of_samples,
            )

            if rms_value:
                message: Timer_Message = time.stop()

                perc_error = percentage_error(
                    exact=(config.amplitude_pp / 2) / np.math.sqrt(2), approx=rms_value
                )

                table.add_row(
                    "{:.5f}".format(frequency),
                    "{}".format(config.number_of_samples),
                    "{:.5f} ".format(round(rms_value, 5)),
                    "{:.5f} ".format(
                        round((config.amplitude_pp / 2) / np.math.sqrt(2), 5)
                    ),
                    "[{}]{:.3f}[/]".format(
                        "cyan" if perc_error <= 0 else "red", round(perc_error, 3)
                    ),
                    "[cyan]{}[/]".format(message.elapsed_time),
                )

                # if(debug):
                #     live.console.log(
                #         "Frequency - Rms Value: {} - {}".format(round(frequency, 5), rms_value))

                """File Writing"""
                f.write(
                    "{},{},{}\n".format(
                        frequency,
                        rms_value,
                        20
                        * np.math.log10(
                            rms_value * 2 * np.math.sqrt(2) / config.amplitude_pp
                        ),
                    )
                )

    f.close()


def plot_from_csv(
    measurements_file_path: Path,
    plot_file_path: Path,
    y_lim_min: float,
    y_lim_max: float,
    debug: bool = False,
):
    if debug:
        console.print("Measurements_file_path: {}".format(measurements_file_path))

    x_frequency: List[float] = []
    y_dBV: List[float] = []

    csvfile = np.genfromtxt(measurements_file_path, delimiter=",", skip_header=1)

    measurements = pd.read_csv(measurements_file_path)
    console.print(measurements)

    for row in list(csvfile):
        y_dBV.append(row[2])
        x_frequency.append(row[0])

    fig1, ax = plt.subplots(figsize=(16, 9), dpi=200)

    ax.plot(x_frequency, y_dBV, ".-")
    ax.set_xscale("log")
    ax.set_title("Frequency response")
    ax.set_xlabel("Frequency")
    ax.set_ylabel(r"$\frac{V_out}{V_int} dB$", rotation=90)

    ax.set_ylim(y_lim_min, y_lim_max)
    ax.grid(True, linestyle="-")

    # ax.set_ylim(-1, 1)

    plt.savefig(plot_file_path)
