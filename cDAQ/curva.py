import enum
from curses.ascii import FS
from pathlib import Path
from platform import system
from re import A
from time import clock
from typing import List

import matplotlib.pyplot as plt
import nidaqmx
import nidaqmx.constants
import nidaqmx.stream_readers
import nidaqmx.stream_writers
import nidaqmx.system
import numpy as np
from nidaqmx._task_modules.channels.ai_channel import AIChannel
from nidaqmx._task_modules.channels.ao_channel import AOChannel
from nidaqmx.errors import DaqError, Error
from nidaqmx.system._collections.device_collection import DeviceCollection
from nidaqmx.system.system import System
from nidaqmx.task import Task
from nidaqmx.types import CtrFreq
from numpy.lib.function_base import average
from numpy.ma.core import shape
from numpy.matlib import log10, sqrt
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.style import StyleType
from rich.table import Column, Table
from rich.tree import Tree
from scipy.fft import fft, fftfreq, rfft
from sympy import numbered_symbols

import usbtmc
from cDAQ.alghorithm import LogaritmicScale
from cDAQ.config import Config
from cDAQ.console import console
from cDAQ.scpi import SCPI, Bandwidth, Switch
from cDAQ.timer import Timer, Timer_Message
from cDAQ.UsbTmc import get_device_list, print_devices_list
from cDAQ.utility import percentage_error, rms
from usbtmc import Instrument


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

    with Live(table, refresh_per_second=4, screen=False, console=console) as live:

        while log_scale.check():
            log_scale.next()
            # Frequency in Hz
            frequency = log_scale.get_frequency()

            # Sets the Frequency
            generator.write(SCPI.set_source_frequency(1, round(frequency, 5)))

            config.number_of_samples = 200

            if frequency <= 100:
                config.Fs = 1000
            elif frequency <= 1000:
                config.Fs = 10000
            elif frequency <= 10000:
                config.Fs = 102000

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

            # live.console.log(
            #     "Voltage espected: {}".format((config.amplitude_pp / 2) / sqrt(2))
            # )

            perc_error = percentage_error(
                exact=(config.amplitude_pp / 2) / sqrt(2), approx=rms_value
            )
            style_percentage_error = "cyan"

            if perc_error <= 0:
                style_percentage_error = "red"

            table.add_row(
                "{:.5f}".format(frequency),
                "{}".format(config.number_of_samples),
                "{:.5f} ".format(round(rms_value, 5)),
                "{:.5f} ".format(round((config.amplitude_pp / 2) / sqrt(2), 5)),
                "[{}]{:.3f}[/]".format(style_percentage_error, round(perc_error, 3)),
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

    for row in list(csvfile):
        y_dBV.append(20 * log10(row[1] * 2 * sqrt(2) / config.amplitude_pp))
        x_frequency.append(row[0])

    plt.plot(x_frequency, y_dBV)
    plt.xscale("log")
    plt.title("Frequency response graph")
    plt.xlabel("Frequency")
    plt.ylabel("Vout/Vin dB")
    # plt.yticks(np.arange(start=-10.0, stop=11.0, step=5.0))
    plt.savefig(plot_file_path)
