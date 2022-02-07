import enum
from os import read
from platform import system
from re import A
from time import clock
from typing import List, Optional
from nidaqmx._task_modules.channels.ai_channel import AIChannel
from nidaqmx._task_modules.channels.ao_channel import AOChannel
from nidaqmx.errors import DaqError, Error
from nidaqmx.task import Task
from nidaqmx.types import CtrFreq
from numpy.ma.core import shape
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.style import StyleType
from rich.tree import Tree
import nidaqmx
import nidaqmx.system
import nidaqmx.constants
import nidaqmx.stream_readers
import nidaqmx.stream_writers
import numpy as np
from cDAQ.utility import *
from usbTmc.UsbTmc import *
from usbTmc.utility import *
from pathlib import Path
from .utility import *
from scipy.fft import fft, fftfreq, rfft
from typing import List
from nidaqmx._task_modules.channels.ao_channel import AOChannel
from nidaqmx.system._collections.device_collection import DeviceCollection
from nidaqmx.system.system import System
from numpy.lib.function_base import average
from numpy.ma.core import sin, sqrt
from rich import table
from rich.console import Console
from rich import inspect, pretty
from rich.panel import Panel
from rich.table import Column, Table
import nidaqmx
import nidaqmx.system
from rich.tree import Tree
import numpy as np
import math
import time
from .timer import Timer
from .console import console


class cDAQ:
    """
    Class for Initialize the nidaqmx driver connection
    """
    system: System

    def __init__(self) -> None:

        # Get the system instance for the nidaqmx-driver
        self.system = nidaqmx.system.System.local()

    def print_driver_version(self, debug: bool = False):
        """Prints the Version for the nidaqmx driver

        Args:
            debug (bool): if true, prints the versions divided in a table
        """

        if(not debug):
            console.print(
                Panel.fit(
                    "Version: [blue]{}[/].[blue]{}[/].[blue]{}[/]".format(
                        self.system.driver_version.major_version,
                        self.system.driver_version.minor_version,
                        self.system.driver_version.update_version
                    )
                )
            )
        else:
            table = Table(
                Column(justify="left"),
                Column(justify="right"),
                title="cDAQ Driver info", show_header=False)

            # Major Version
            table.add_row("Major Version", "{}".format(
                self.system.driver_version.major_version))

            # Minor Version
            table.add_row("Minor Version", "{}".format(
                self.system.driver_version.minor_version))

            # Update Version
            table.add_row("Update Version", "{}".format(
                self.system.driver_version.update_version))
            console.print(table)

    def _list_devices(self) -> DeviceCollection:
        """Returns the Device connected to the machine

        Returns:
            DeviceCollection: Device List
        """

        return self.system.devices

    def print_list_devices(self):
        """Prints the Devices connected to the machine
        """

        table = Table(title="Device List")
        table.add_column(
            "[yellow]Name[/]",
            justify="left", style="blue", no_wrap=True
        )

        for device in self._list_devices():
            table.add_row(device.name)
        console.print(table)


def print_supported_output_types(channel: AOChannel):
    supported_types: Tree = Tree(
        "[yellow]Supported Types[/]",
    )

    for t in channel.physical_channel.ao_output_types:
        supported_types.add(
            "[green]{}[/green]: [blue]{}[/blue]".format(t.name, int(t.value)))

    console.print(Panel.fit(supported_types))


def integrate(y_values: List[float], delta) -> float:

    volume: np.float = 0.0

    for idx, y in enumerate(y_values):
        # If it's the last element then exit the loop
        if(idx + 1 == len(y_values)):
            break
        else:
            y_plus = y_values[idx + 1]

            # console.print(
            #     "Values: {} - {}".format(round(y, 5), round(y_plus, 9)))

            # if(idx % 10 == 0):
            # input()

            # Make the calculations
            if(y * y_plus < 0):
                r_rec: np.float = abs(y) * delta / 4
                l_rec: np.float = abs(y_plus) * delta / 4
                volume += r_rec + l_rec
                # console.print("Volume: {}".format(round(volume, 9)))
            else:
                r_rec: np.float = abs(y) * delta
                l_rec: np.float = abs(y_plus) * delta
                triangle: np.float = abs(r_rec - l_rec) / 2

                volume += min([r_rec, l_rec]) + triangle

                # console.print("Volume: {}".format(round(volume, 9)))

    return volume


def voltage_rms(voltages: List[float]) -> float:

    idx = 0

    volts_average_list = list()

    while idx < len(voltages):
        curr_half = unit_normalization(voltages[idx])
        n_volts = 0
        sum_volts = 0.0

        console.print(Panel.fit("Index: {}".format(idx)))

        while curr_half == unit_normalization(voltages[idx]):

            n_volts += 1
            sum_volts += voltages[idx]

            # Step the index
            idx += 1

            if not idx < len(voltages):
                console.log(
                    Panel.fit("[red]Vector Lenght exceded with index: {}[/]".format(idx)))
                break

        avg = sum_volts / n_volts

        volts_average_list.append(abs(avg))

        console.log("Number Measurments in Half Cicle: {}".format(n_volts))
        console.log("Volts Sum in Half Cicle: {}".format(sum_volts))
        console.log("Volt Average: {}".format(avg))

    console.log(volts_average_list)
    rms_voltage = (average(volts_average_list) * math.pi) / (2 * sqrt(2))

    return rms_voltage


def rms_average(voltages: List[float], number_of_samples: int) -> float:
    """Calculate the RMS Voltage value from the sampling average

    Args:
        voltages (List[float]): The sampling voltages list
        number_of_samples (int): The number of sampling

    Returns:
        float: The RMS Voltage
    """
    average: float = 0

    for v in voltages:
        average += abs(v) / len(voltages)

    return average * 1.111


def rms_fft(voltages: List[float], number_of_samples: int) -> float:
    """Calculate the RMS Voltage value with the Fast Fourier Transform
    of the voltage sampling list

    Args:
        voltages (List[float]): The sampling voltages list
        number_of_samples (int): The number of sampling

    Returns:
        float: The RMS Voltage
    """
    y = fft(voltages, number_of_samples)

    sum: np.float = 0

    for v in y:
        sum += pow(np.abs(v) / len(voltages), 2)

    return math.sqrt(abs(sum))


def rms_integration(voltages: List[float], N: int, Fs: float) -> float:
    """Calculate the RMS Voltage value with the Integration Technic

    Args:
        voltages (List[float]): The sampling voltages list
        number_of_samples (int): The number of sampling

    Returns:
        float: The RMS Voltage
    """
    return integrate(voltages, 1 / Fs) / (N / Fs)


def unit_normalization(value: float) -> int:
    return int(value / abs(value))


def sinc(x: float):
    return sin(math.pi * x) / (math.pi * x)


def read_voltages(frequency, Fs, number_of_samples,
                  ch_input: str = 'cDAQ9189-1CDBE0AMod1/ai1', min_voltage: float = -4, max_voltage: float = 4
                  ) -> float:

    if(frequency > Fs / 2):
        raise ValueError("The Sampling rate is low: Fs / 2 > frequency.")

    task = nidaqmx.Task('Input Voltage')
    channel1: AIChannel = task.ai_channels.add_ai_voltage_chan(
        ch_input,
        min_val=min_voltage, max_val=max_voltage)

    # Sets the Clock sampling rate
    task.timing.cfg_samp_clk_timing(Fs)

    # Pre allocate the array
    voltages = np.ndarray(shape=number_of_samples)

    # Sets the task for the stream_reader
    channel1_stream_reader = nidaqmx.stream_readers.AnalogSingleChannelReader(
        task.in_stream)

    # Sampling the voltages
    channel1_stream_reader.read_many_sample(
        voltages,
        number_of_samples_per_channel=number_of_samples
    )
    task.close()

    return voltages


class RMS_MODE(enum.Enum):
    FFT = 1
    AVERAGE = 2
    INTEGRATE = 3


def rms(frequency: float, Fs: float, number_of_samples: int, ch_input: str, max_voltage: float, min_voltage: float, rms_mode: RMS_MODE = RMS_MODE.FFT, time_report: bool = False) -> float:

    if(time_report):
        timer = Timer()

    # Pre allocate the array
    try:
        voltages = read_voltages(frequency, Fs, number_of_samples,
                                 ch_input=ch_input,
                                 max_voltage=max_voltage,
                                 min_voltage=min_voltage
                                 )
    except Exception as e:
        console.log(e)

    rms: float = None

    if(time_report):
        timer.start("[yellow]RMS Calculation Execution time[/]")

    if (rms_mode == RMS_MODE.FFT):
        rms = rms_fft(voltages, number_of_samples)
    elif (rms_mode == RMS_MODE.AVERAGE):
        rms = rms_average(voltages, number_of_samples)
    elif (rms_mode == RMS_MODE.INTEGRATE):
        rms = rms_integration(
            voltages, number_of_samples, Fs)

    if(time_report):
        timer.stop()

    return rms
