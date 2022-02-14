import enum
from curses.ascii import FS
from os import read
from pathlib import Path
from platform import system
from re import A
from time import clock
from typing import List

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
from rich import table
from rich.layout import Layout
from rich.panel import Panel
from rich.style import StyleType
from rich.tree import Tree
from scipy.fft import fft, fftfreq, rfft

from cDAQ.alghorithm import LogaritmicScale
from cDAQ.config import Config
from cDAQ.console import console
from cDAQ.scpi import SCPI, Switch
from cDAQ.UsbTmc import *
from cDAQ.utility import *


def curva(
    config_file_path: os.path,
    measurements_file_path: os.path,
    plot_file_path: os.path,
    debug: bool = False,
):
    """Load JSON config"""
    config = Config(config_file_path)
    config.print()

    sampling_curve(config=config,
                   measurements_file_path=measurements_file_path, debug=debug)

    plot(
        config=config,
        measurements_file_path=measurements_file_path,
        plot_file_path=plot_file_path,
        debug=debug
    )


def sampling_curve(
    config: Config,
    measurements_file_path: os.path,
    debug: bool = False,
):
    """Asks for the 2 instruments"""
    list_devices: List[Instrument] = get_device_list()
    if(debug):
        print_devices_list(list_devices)

    generator: usbtmc.Instrument = list_devices[0]

    """Open the Instruments interfaces"""
    # Auto Close with the destructor
    generator.open()

    """Sets the Configuration for the Voltmeter"""
    generator_configs: list = [
        SCPI.clear(),
        SCPI.set_output(1, Switch.OFF),
        SCPI.set_function_voltage_ac(),
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
        config.sampling.points_per_decade
    )

    period: np.float = 0.0

    delay: np.float = 0.0
    aperture: np.float = 0.0
    interval: np.float = 0.0

    delay_min: np.float = config.delay_min
    aperture_min: np.float = config.aperture_min
    interval_min: np.float = config.interval_min

    f = open(measurements_file_path, "w")
    frequency: float

    while log_scale.check():
        log_scale.next()
        # Frequency in Hz
        frequency = log_scale.get_frequency()

        # Period in seconds
        period = 1 / frequency

        # Delay in seconds
        delay = period * 6
        delay = 1

        # Aperture in seconds
        aperture = period * 0.5

        # Interval in seconds
        # Interval is 10% more than aperture
        interval = period * 0.5

        if(delay < delay_min):
            delay = delay_min

        if(aperture < aperture_min):
            aperture = aperture_min

        if(interval < interval_min):
            interval = interval_min

        aperture *= 1.2
        interval *= 5

        delay = round(delay, 4)
        aperture = round(aperture, 4)
        interval = round(interval, 4)

        # Sets the Frequency
        generator.write(SCPI.set_source_frequency(1, round(frequency, 5)))

        sleep(0.6)

        # GET MEASUREMENTS
        rms_value = rms(frequency=frequency, Fs=config.Fs,
                        ch_input=config.nidaq.ch_input,
                        max_voltage=config.nidaq.max_voltage,
                        min_voltage=config.nidaq.min_voltage,
                        number_of_samples=config.number_of_samples,
                        time_report=True)

        if(debug):
            console.log(
                "Frequency - Rms Value: {} - {}".format(round(frequency, 5), rms_value))

        """File Writing"""
        f.write("{},{}\n".format(frequency, rms_value))

    f.close()


def plot(
    config: Config,
    measurements_file_path: os.path,
    plot_file_path: os.path,
    debug: bool = False
):
    if(debug):
        console.print("Measurements_file_path: {}".format(
            measurements_file_path))

    x_frequency: List[float] = []
    y_dBV: List[float] = []

    csvfile = genfromtxt(measurements_file_path, delimiter=',')

    for row in list(csvfile):
        y_dBV.append(20 * log10(row[1] * 2*sqrt(2)/config.amplitude_pp))
        x_frequency.append(row[0])

    plt.plot(x_frequency, y_dBV)
    plt.xscale("log")
    plt.title("Frequency response graph")
    plt.xlabel("Frequency")
    plt.ylabel("Vout/Vin dB")
    # plt.yticks(np.arange(start=-10.0, stop=11.0, step=5.0))
    plt.savefig(plot_file_path)
