import enum
from os import read
from platform import system
from re import A
from time import clock
from typing import List
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
from cDAQ.UsbTmc import *
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


# 192.168.1.52 cDAQ
console = Console(force_terminal=True, color_system="truecolor")


def test_thermocouple():
    task = nidaqmx.Task('Test Thermocouple')

    task.ai_channels.add_ai_thrmcpl_chan('cDAQ9189-1CDBE0AMod3/ai0')
    themperature = task.read()
    console.print(Panel.fit(
        "[bold yellow]Themperature[/]: {} °C".format(themperature)))
    task.close()


def test_ao_voltage():
    data: np.ndarray = np.ndarray((1,), dtype=float)
    task: Task = nidaqmx.Task('Test Output Voltage')

    channel: AOChannel = task.ao_channels.add_ao_voltage_chan(
        'cDAQ9189-1CDBE0AMod2/ao0',
        min_val=-4, max_val=4)

    channel1_stream_writer = nidaqmx.stream_writers.AnalogSingleChannelWriter(
        task.out_stream)
    task.timing.cfg_samp_clk_timing(100000)
    voltages = np.ndarray(shape=100)

    try:
        print_supported_output_types(channel)

        # TODO: Figure it out how to control the buffer
        task.write([-2, 3, 2], auto_start=True)
        channel1_stream_writer.write_many_sample(voltages)
    except DaqError as e:
        console.print(
            Panel.fit("[red]Error[/]: {} - {}".format(e.error_code, e.error_type.name)))

    task.close()


def test_ai_voltage(amplitude_pp, frequency, ch_input: int = 0, isLoop: bool = False):

    task = nidaqmx.Task('Test Input Voltage')
    channel1: AIChannel = task.ai_channels.add_ai_voltage_chan(
        'cDAQ9189-1CDBE0AMod1/ai{}'.format(ch_input),
        min_val=-4, max_val=4)

    task.timing.cfg_samp_clk_timing(102000)

    number_of_samples = 1000

    voltages = np.ndarray(shape=(number_of_samples))

    channel1_stream_reader = nidaqmx.stream_readers.AnalogSingleChannelReader(
        task.in_stream)

    console.print(voltages)

    channel1_stream_reader.read_many_sample(
        voltages, number_of_samples_per_channel=number_of_samples)

    # PLOT
    x: List[float] = list()

    for idx, v in enumerate(voltages):
        x.append(idx * (1/102000))

    plt.plot(x, voltages,
             color='g')
    plt.ylabel("Voltages")
    plt.title("Voltages over time.")
    plt.grid(plt.legend)
    Path("./data/cDAQ").mkdir(parents=True, exist_ok=True)
    plt.savefig("./data/cDAQ/plot.pdf")

    # REPORT
    console.print(
        Panel.fit("[yellow]Amplitude PP[/]: {}".format(amplitude_pp)))
    console.print(Panel.fit("[yellow]Frequency[/]: {}".format(frequency)))
    console.print(Panel.fit("[yellow]Max Value[/]: {}".format(max(voltages))))
    console.print(Panel.fit("[yellow]Min Value[/]: {}".format(min(voltages))))

    # console.print(Panel.fit(tree))
    task.close()


def test_rigol_ni_output(amplitude_pp: float = 2, frequency: float = 1000):
    """Asks for the 2 instruments"""
    list_devices: List[Instrument] = get_device_list()
    print_devices_list(list_devices)

    gen: usbtmc.Instrument = list_devices[0]

    """Open the Instruments interfaces"""
    gen.open()

    """Sets the Configuration for the Voltmeter"""
    configs_gen: list = [
        "*CLS",
        ":FUNCtion:VOLTage:AC",
        ":OUTPut1 OFF",
        ":OUTPut2 OFF",
    ]

    exec_commands(gen, configs_gen)

    gen.write(":SOURce1:VOLTAGE:AMPLitude {}".format(amplitude_pp))
    gen.write(":SOURce1:FREQ {}".format(round(frequency, 5)))
    gen.write(":SOURce2:VOLTAGE:AMPLitude {}".format(amplitude_pp))
    gen.write(":SOURce2:FREQ {}".format(round(frequency, 5)))

    gen.write(":OUTPut1:IMPedance 50")
    gen.write(":OUTPut2:IMPedance 50")
    gen.write(":OUTPut1:LOAD INF")
    gen.write(":OUTPut2:LOAD INF")

    gen.write(":SOURce1:PHASe 0")
    gen.write(":SOURce2:PHASe 180")

    gen.write(":SOUR1:PHAS:INIT")
    gen.write(":SOUR2:PHAS:SYNC")

    gen.write(":OUTPut2 ON")
    gen.write(":OUTPut1 ON")

    test_ai_voltage(amplitude_pp, frequency, ch_input=1)

    gen.close()


def read_rms_ai_voltage(ch_input: int = 0, isLoop: bool = False):

    task = nidaqmx.Task('Test Input Voltage')
    channel1: AIChannel = task.ai_channels.add_ai_voltage_chan(
        'cDAQ9189-1CDBE0AMod1/ai{}'.format(ch_input),
        min_val=-4, max_val=4)

    Fs = 102000

    task.timing.cfg_samp_clk_timing(Fs)

    number_of_samples = int(1000 * 1)

    voltages = np.ndarray(shape=number_of_samples)

    channel1_stream_reader = nidaqmx.stream_readers.AnalogSingleChannelReader(
        task.in_stream)

    # console.print(voltages, sep="\n")

    channel1_stream_reader.read_many_sample(
        voltages,
        number_of_samples_per_channel=number_of_samples
    )

    # Plot Sine Wave
    plt.plot(voltages)
    plt.savefig("./data/cDAQ/test.png")

    rms_voltage_average: float = rms_average(voltages, number_of_samples)
    rms_voltage_fourier: float = rms_fft(voltages, number_of_samples)
    rms_voltage_integrate: float = rms_integration(
        voltages, number_of_samples, Fs)

    console.print(Panel.fit(
        "[yellow]RMS Voltage (Avarage)[/]: [blue]{}[/] V"
        .format(round(rms_voltage_average, 5))
    ))
    console.print(Panel.fit(
        "[yellow]RMS Voltage (Fourier)[/]: [blue]{}[/] V"
        .format(round(rms_voltage_fourier, 5))
    ))
    console.print(Panel.fit(
        "[yellow]RMS Voltage (Integrate)[/]: [blue]{}[/] V"
        .format(round(rms_voltage_integrate, 5))
    ))

    # REPORT
    console.print(Panel.fit("[yellow]Max Value[/]: {}".format(max(voltages))))
    console.print(Panel.fit("[yellow]Min Value[/]: {}".format(min(voltages))))

    # console.print(Panel.fit(tree))
    task.close()


def test_rigol_rms_ni_output(
    amplitude_pp: float = 2, frequency: float = 1000,
    debug: bool = False,
    number_of_samples=1000
):
    """Asks for the 2 instruments"""
    list_devices: List[Instrument] = get_device_list()
    if(debug):
        print_devices_list(list_devices)

    gen: usbtmc.Instrument = list_devices[0]

    """Open the Instruments interfaces"""
    gen.open()

    """Sets the Configuration for the Voltmeter"""
    configs_gen: list = [
        "*CLS",
        ":FUNCtion:VOLTage:AC",
        ":OUTPut1 OFF",
        ":OUTPut2 OFF",
    ]

    exec_commands(gen, configs_gen)

    gen.write(":SOURce1:VOLTAGE:AMPLitude {}".format(amplitude_pp))
    gen.write(":SOURce1:FREQ {}".format(round(frequency, 5)))
    gen.write(":SOURce2:VOLTAGE:AMPLitude {}".format(amplitude_pp))
    gen.write(":SOURce2:FREQ {}".format(round(frequency, 5)))

    gen.write(":OUTPut1:IMPedance 50")
    gen.write(":OUTPut2:IMPedance 50")
    gen.write(":OUTPut1:LOAD INF")
    gen.write(":OUTPut2:LOAD INF")

    gen.write(":SOURce1:PHASe 0")
    gen.write(":SOURce2:PHASe 180")

    gen.write(":SOUR1:PHAS:INIT")
    gen.write(":SOUR2:PHAS:SYNC")

    gen.write(":OUTPut2 ON")
    gen.write(":OUTPut1 ON")

    for n in range(200, 1001, 10):
        rms_value = rms(amplitude_pp=amplitude_pp, frequency=frequency,
                        Fs=102000, number_of_samples=n, time_report=False)

        console.print(
            Panel.fit("[red]{} - RMS[/]: {} V".format(n, rms_value)))

    if(debug):
        console.print(
            Panel.fit("[yellow]Amplitude PP[/]: {}".format(amplitude_pp)))
        console.print(Panel.fit("[yellow]Frequency[/]: {}".format(frequency)))

    gen.close()
