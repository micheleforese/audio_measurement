from pathlib import Path
from time import sleep
from typing import List, Optional, Tuple, Type

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from rich.live import Live
from rich.panel import Panel
from rich.table import Column, Table
from usbtmc import Instrument

from cDAQ.alghorithm import LogaritmicScale
from cDAQ.config import Config
from cDAQ.console import console
from cDAQ.scpi import SCPI, Bandwidth, Switch
from cDAQ.timer import Timer, Timer_Message
from cDAQ.usbtmc import UsbTmc, get_device_list, print_devices_list
from cDAQ.utility import percentage_error, rms, transfer_function


def sampling_curve(
    config: Config,
    measurements_file_path: Path,
    amplitude_pp: Optional[float],
    nFs: float,
    spd: float,
    n_samp: int,
    debug: bool = False,
):
    # Check Config
    if amplitude_pp:
        config.rigol.amplitude_pp = amplitude_pp

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
        SCPI.set_source_voltage_amplitude(1, round(amplitude_pp, 5)),
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
        spd,
    )

    f = open(measurements_file_path, "w")
    f.write("{},{},{}\n".format("Frequency", "RMS Value", "dbV"))

    frequency: float = round(config.sampling.min_Hz, 5)

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
                Fs = frequency * nFs
                config.sampling.number_of_samples = 90
            elif frequency <= 1000:
                Fs = frequency * nFs
                config.sampling.number_of_samples = n_samp
            elif frequency <= 10000:
                Fs = frequency * nFs
                config.sampling.number_of_samples = n_samp
            else:
                Fs = frequency * nFs
                config.sampling.number_of_samples = n_samp

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
                    exact=(amplitude_pp / 2) / np.math.sqrt(2), approx=rms_value
                )

                bBV: float = 20 * np.math.log10(
                    rms_value * 2 * np.math.sqrt(2) / amplitude_pp
                )

                transfer_func_dB = transfer_function(
                    rms_value, amplitude_pp / (2 * np.math.sqrt(2))
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
                    "{:.5f} ".format(round((amplitude_pp / 2) / np.math.sqrt(2), 5)),
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

    console.print(Panel("max_dB: {}".format(max_dB)))

    f.close()


def plot_from_csv(
    measurements_file_path: Path,
    plot_file_path: Path,
    y_lim_min: Optional[float] = None,
    y_lim_max: Optional[float] = None,
    debug: bool = False,
):
    if debug:
        console.print("Measurements_file_path: {}".format(measurements_file_path))
        console.print("{}, {}".format(y_lim_min, y_lim_max))

    x_frequency: List[float] = []
    y_dBV: List[float] = []

    measurements = pd.read_csv(
        measurements_file_path, header=0, names=["Frequency", "RMS Value", "dbV"]
    )
    console.print(measurements)

    # for i, row in measurements.iterrows():
    #     y_dBV.append(row["dbV"])
    #     x_frequency.append(row["Frequency"])

    fig1, ax = plt.subplots(figsize=(16 * 2, 9 * 2), dpi=300)

    # plt.rcParams["font.size"] = "40"

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontsize(40)

    for label in ax.get_xticklabels():
        label.set_fontsize(50)

    # ax.plot(x_frequency, y_dBV)
    ax.plot(measurements.columns["Frequency"], measurements.columns["dbV"])
    ax.set_xscale("log")
    ax.set_title("Frequency response")
    ax.set_xlabel("Frequency", fontsize=50)
    ax.set_ylabel(r"$\frac{V_out}{V_int} dB$", fontsize=50)

    if y_lim_min is not None and y_lim_max is not None:
        ax.set_ylim(y_lim_min, y_lim_max)
    else:
        ax.set_ylim(min(y_dBV), max(y_dBV))

    ax.grid(True, linestyle="-")

    plt.savefig(plot_file_path)
