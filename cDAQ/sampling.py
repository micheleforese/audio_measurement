from pathlib import Path
from typing import List, Optional, Union

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import rich as rich
from scipy.interpolate import interp1d
import scipy as sp
import scipy.interpolate
from rich.live import Live
from rich.panel import Panel
from rich.table import Column, Table
from scipy.interpolate import make_interp_spline

from cDAQ.alghorithm import LogaritmicScale
from cDAQ.config import Config, Plot
from cDAQ.config.type import ModAuto, Range
from cDAQ.console import console
from cDAQ.scpi import SCPI, Bandwidth, Switch
from cDAQ.timer import Timer, Timer_Message
from cDAQ.usbtmc import UsbTmc, get_device_list, print_devices_list
from cDAQ.utility import (
    INTRERP_KIND,
    log_interp1d,
    logx_interp1d,
    percentage_error,
    rms,
    transfer_function,
)
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
        SCPI.set_source_frequency(1, round(config.sampling.f_range.min, 5)),
    ]

    SCPI.exec_commands(generator, generator_configs)

    generator_ac_curves: List[str] = [
        SCPI.set_output(1, Switch.ON),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    log_scale: LogaritmicScale = LogaritmicScale(
        config.sampling.f_range.min,
        config.sampling.f_range.max,
        config.sampling.points_per_decade,
    )

    f = open(measurements_file_path, "w")
    f.write("{},{},{}\n".format("Frequency", "RMS Value", "dbV"))

    frequency: float = round(config.sampling.f_range.min, 5)

    table = Table(
        Column("Frequency [Hz]", justify="right"),
        Column("Fs [Hz]", justify="right"),
        Column("Number of samples", justify="right"),
        Column("Rms Value [V]", justify="right"),
        Column("Voltage Expected", justify="right"),
        Column("Relative Error", justify="right"),
        Column("dB Error", justify="right"),
        Column("Time [s]", justify="right"),
    )

    max_dB: Optional[float] = None

    with Live(
        table,
        screen=False,
        console=console,
        vertical_overflow="visible",
        auto_refresh=True,
    ) as live:

        for frequency in log_scale.f_list:

            # Sets the Frequency
            generator.write(SCPI.set_source_frequency(1, round(frequency, 5)))

            # sleep(0.2)

            Fs = config.nidaq._max_Fs

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
    plot_config: Plot,
    debug: bool = False,
):
    if debug:
        console.print(Panel(plot_config.tree()))

    x_frequency: List[float] = []
    y_dBV: List[float] = []

    measurements = pd.read_csv(
        measurements_file_path, header=0, names=["Frequency", "RMS Value", "dbV"]
    )

    for i, row in measurements.iterrows():
        y_dBV.append(row["dbV"])
        x_frequency.append(row["Frequency"])

    console.print(
        Panel(
            "min dB: {}\n".format(min(y_dBV))
            + "max dB: {}\n".format(max(y_dBV))
            + "diff dB: {}".format(abs(max(y_dBV) - min(y_dBV)))
        )
    )

    if plot_config.y_offset:
        y_offset: Optional[float] = None
        if isinstance(plot_config.y_offset, float):
            y_offset = plot_config.y_offset
        elif isinstance(plot_config.y_offset, ModAuto):
            if plot_config.y_offset == ModAuto.MIN:
                y_offset = float(min(y_dBV))
            elif plot_config.y_offset == ModAuto.MAX:
                y_offset = float(max(y_dBV))
            elif plot_config.y_offset == ModAuto.NO:
                y_offset = None
            else:
                console.print('y_offset should be "max", "min" or "no".', style="error")

        if y_offset:
            for i in range(len(y_dBV)):
                y_dBV[i] = y_dBV[i] - y_offset

    fig1, ax = plt.subplots(figsize=(16 * 2, 9 * 2), dpi=300)

    x_frequency_log = [np.math.log10(x_log) for x_log in x_frequency]

    cubic_interpolation_model = interp1d(x_frequency_log, y_dBV, kind="cubic")
    # cubic_interpolation_model = logx_interp1d(x_frequency_log, y_dBV, kind=INTRERP_KIND.CUBIC)
    x_frequency_log_interpolated = np.linspace(
        min(x_frequency_log),
        max(x_frequency_log),
        int(len(x_frequency_log) * 10),
    )

    x_frequency_interpolated = [
        np.math.pow(10, x_intrp) for x_intrp in x_frequency_log_interpolated
    ]

    y_dBV_interpolated = cubic_interpolation_model(x_frequency_log_interpolated)

    ax.semilogx(
        x_frequency,
        y_dBV,
        "o",
        x_frequency_interpolated,
        y_dBV_interpolated,
        "-",
        linewidth=4,
    )
    ax.set_title("Frequency response", fontsize=50)
    ax.set_xlabel("Frequency ($Hz$)", fontsize=40)
    ax.set_ylabel(r"Amplitude ($dB$)", fontsize=40)

    ax.tick_params(axis="both", labelsize=15)
    ax.tick_params(axis="x", rotation=90)

    logLocator = ticker.LogLocator(subs=np.arange(0, 1, 0.1))
    logFormatter = ticker.LogFormatter(
        labelOnlyBase=False, minor_thresholds=(np.inf, 0.5)
    )
    # ax.xaxis.set_scientific(False)
    # X Axis - Major
    ax.xaxis.set_major_locator(logLocator)
    ax.xaxis.set_major_formatter(logFormatter)
    # X Axis - Minor
    ax.xaxis.set_minor_locator(logLocator)
    ax.xaxis.set_minor_formatter(logFormatter)
    # ax.ticklabel_format(style="plain", axis='x')

    ax.grid(True, linestyle="-", which="both", color="0.7")

    if plot_config.y_limit:
        ax.set_ylim(plot_config.y_limit.min, plot_config.y_limit.max)
    else:
        min_y_dBV = min(y_dBV_interpolated)
        max_y_dBV = max(y_dBV_interpolated)
        ax.set_ylim(
            min_y_dBV - 1,
            max_y_dBV + 1,
        )

    plt.savefig(plot_file_path)
