from pathlib import Path
from time import sleep
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from rich.live import Live
from rich.panel import Panel
from rich.table import Column, Table

from cDAQ.alghorithm import LogaritmicScale
from cDAQ.config import Config
from cDAQ.console import console
from cDAQ.scpi import SCPI, Bandwidth, Switch
from cDAQ.timer import Timer, Timer_Message
from cDAQ.usbtmc import UsbTmc, get_device_list, print_devices_list
from cDAQ.utility import percentage_error, rms, transfer_function
from usbtmc import Instrument


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
        SCPI.set_source_voltage_amplitude(1, round(config.rigol.amplitude_pp, 5)),
        SCPI.set_source_frequency(1, round(config.sampling.f_min, 5)),
    ]

    SCPI.exec_commands(generator, generator_configs)

    generator_ac_curves: List[str] = [
        SCPI.set_output(1, Switch.ON),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    log_scale: LogaritmicScale = LogaritmicScale(
        config.sampling.f_min,
        config.sampling.f_max,
        config.calculate_step(),
        config.sampling.points_per_decade,
    )

    f = open(measurements_file_path, "w")
    f.write("{},{},{}\n".format("Frequency", "RMS Value", "dbV"))

    frequency: float = round(config.sampling.f_min, 5)

    table = Table(
        Column(f"Frequency [Hz]", justify="right"),
        Column(f"Fs [Hz]", justify="right"),
        Column(f"Number of samples", justify="right"),
        Column(f"Rms Value [V]", justify="right"),
        Column("Voltage Expected", justify="right"),
        Column(f"Relative Error", justify="right"),
        Column(f"dB Error", justify="right"),
        Column(f"Time [s]", justify="right"),
    )

    max_dB: Optional[float] = None

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

            # sleep(0.2)

            Fs = config.nidaq.max_Fs

            if frequency < 20:
                Fs = frequency * config.sampling.n_fs
                config.sampling.number_of_samples = 90
            elif frequency <= 1000:
                Fs = frequency * config.sampling.n_fs
            elif frequency <= 10000:
                Fs = frequency * config.sampling.n_fs
            else:
                Fs = frequency * config.sampling.n_fs

            if Fs > config.nidaq.max_Fs:
                Fs = config.nidaq.max_Fs

            time = Timer()
            time.start()

            # GET MEASUREMENTS
            rms_value: Optional[float] = rms(
                frequency=frequency,
                Fs=Fs,
                ch_input=config.nidaq.ch_input,
                max_voltage=config.nidaq.max_voltage,
                min_voltage=config.nidaq.min_voltage,
                number_of_samples=config.sampling.number_of_samples,
            )

            if rms_value:
                message: Timer_Message = time.stop()

                perc_error = percentage_error(
                    exact=(config.rigol.amplitude_pp / 2) / np.math.sqrt(2),
                    approx=rms_value,
                )

                bBV: float = 20 * np.math.log10(
                    rms_value * 2 * np.math.sqrt(2) / config.rigol.amplitude_pp
                )

                transfer_func_dB = transfer_function(
                    rms_value, config.rigol.amplitude_pp / (2 * np.math.sqrt(2))
                )

                if max_dB:
                    max_dB = max(abs(max_dB), abs(transfer_func_dB))
                else:
                    max_dB = transfer_func_dB

                table.add_row(
                    "{:.5f}".format(frequency),
                    "{:.5f}".format(Fs),
                    "{}".format(config.sampling.number_of_samples),
                    "{:.5f} ".format(round(rms_value, 5)),
                    "{:.5f} ".format(
                        round((config.rigol.amplitude_pp / 2) / np.math.sqrt(2), 5)
                    ),
                    "[{}]{:.3f}[/]".format(
                        "red" if perc_error <= 0 else "green", round(perc_error, 3)
                    ),
                    "[{}]{:.2f}[/]".format(
                        "red" if bBV <= 0 else "green", transfer_func_dB
                    ),
                    "[cyan]{}[/]".format(message.elapsed_time),
                )

                """File Writing"""
                f.write(
                    "{},{},{}\n".format(
                        frequency,
                        rms_value,
                        bBV,
                    )
                )

    SCPI.exec_commands(
        generator,
        [
            SCPI.set_output(1, Switch.OFF),
        ],
    )
    console.print(Panel("max_dB: {}".format(max_dB)))

    f.close()


def plot_from_csv(
    measurements_file_path: Path,
    plot_file_path: Path,
    y_lim: Optional[Tuple[float, float]] = None,
    x_lim: Optional[Tuple[float, float]] = None,
    y_offset: float = 0,
    debug: bool = False,
):
    if debug:
        console.print("Measurements_file_path: {}".format(measurements_file_path))
        console.print("Plot_file_path: {}".format(plot_file_path))
        console.print("y_lim: {}".format(y_lim))
        console.print("x_lim: {}".format(x_lim))

    x_frequency: List[float] = []
    y_dBV: List[float] = []

    measurements = pd.read_csv(
        measurements_file_path, header=0, names=["Frequency", "RMS Value", "dbV"]
    )
    console.print(measurements)

    for i, row in measurements.iterrows():
        y_dBV.append(float(row["dbV"]) - y_offset)
        x_frequency.append(row["Frequency"])

    fig1, ax = plt.subplots(figsize=(16 * 2, 9 * 2), dpi=300)

    # plt.rcParams["font.size"] = "40"

    for label in ax.get_xticklabels():
        label.set_fontsize(40)

    for label in ax.get_yticklabels():
        label.set_fontsize(40)

    # ax.plot(x_frequency, y_dBV)
    ax.plot(x_frequency, y_dBV)
    ax.set_xscale("log")
    ax.set_title("Frequency response", fontsize=70)
    ax.set_xlabel("Frequency (Hz)", fontsize=40)
    ax.set_ylabel(r"Amplitude (dB)", fontsize=40)

    if y_lim:
        x_lim_min, x_lim_max = y_lim
        ax.set_ylim(x_lim_min, x_lim_max)
    else:
        min_y_dBV = min(y_dBV)
        max_y_dBV = max(y_dBV)
        ax.set_ylim(
            min_y_dBV - 1,
            max_y_dBV + 1,
        )

    console.print(
        Panel(
            "min dB: {}\n".format(min(y_dBV))
            + "max dB: {}\n".format(max(y_dBV))
            + "diff dB: {}".format(abs(max(y_dBV) - min(y_dBV)))
        )
    )

    # if x_lim:
    #     x_lim_min, x_lim_max = x_lim
    #     ax.set_ylim(x_lim_min, x_lim_max)
    # else:
    #     min_plot_x = min(x_frequency)
    #     max_plot_x = max(x_frequency)
    #     ax.set_ylim(
    #         min_plot_x + abs(min_plot_x) / min_plot_x,
    #         max_plot_x + abs(max_plot_x) / max_plot_x,
    #     )

    ax.grid(True, linestyle="-", which="both", color="0.8")

    plt.savefig(plot_file_path)
