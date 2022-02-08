from curses.ascii import FS
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
from cDAQ.rigol import Rigol
from cDAQ.utility import *
from cDAQ.UsbTmc import *
from .utility import *
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
from rich.panel import Panel
from rich.table import Column, Table
import nidaqmx
import nidaqmx.system
from rich.tree import Tree
import numpy as np

import jstyleson


def load_json_config(config_file_path):
    with open(config_file_path) as config_file:
        config = jstyleson.loads(config_file.read())
        return config


def curva(
    config_file_path,
    debug: bool = False,
):
    """Load JSON config
    """
    config = load_json_config(config_file_path)

    frequency = float(config['frequency'])
    number_of_samples = int(config['number_of_samples'])
    Fs = int(config['Fs'])
    amplitude_pp = float(config['amplitude_pp'])
    ch_input = str(config['nidaq']["ch_input"])
    max_voltage = float(config['nidaq']['max_voltage'])
    min_voltage = float(config['nidaq']['min_voltage'])

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
        "*CLS",
        ":FUNCtion:VOLTage:AC",
        ":OUTPut1 OFF",
        ":OUTPut2 OFF",
    ]

    exec_commands(generator, generator_configs)

    generator_ac_curves: list = [
        ":SOURce1:VOLTAGE:AMPLitude {}".format(amplitude_pp),
        ":SOURce1:FREQ {}".format(round(frequency, 5)),
        ":SOURce2:VOLTAGE:AMPLitude {}".format(amplitude_pp),
        ":SOURce2:FREQ {}".format(round(frequency, 5)),

        ":OUTPut1:IMPedance 50",
        ":OUTPut2:IMPedance 50",
        ":OUTPut1:LOAD INF",
        ":OUTPut2:LOAD INF",

        ":SOURce1:PHASe 0",
        ":SOURce2:PHASe 180",

        ":SOUR1:PHAS:INIT",
        ":SOUR2:PHAS:SYNC",

        # ":OUTPut2 ON",
        ":OUTPut1 ON",
    ]

    exec_commands(generator, generator_ac_curves)

    if(debug):
        table = Table(
            Column(justify="center"),
            Column(justify="right"),
            title="Curva Info", show_header=False
        )

        table.add_row("Amplitude", "{}".format(amplitude_pp))
        table.add_row("Frequency", "{}".format(frequency))
        table.add_row("Sampling Frequency", "{}".format(Fs))
        table.add_row("Number of samples per Frequency",
                      "{}".format(number_of_samples))

        console.print(table)

    rms_value = rms(frequency=frequency, Fs=Fs,
                    ch_input=ch_input,
                    max_voltages=max_voltage,
                    min_voltages=min_voltage,
                    number_of_samples=number_of_samples, time_report=False)

    console.print(
        Panel.fit("[red]{}[/] - RMS: {} V".format(number_of_samples, rms_value)))


def sampling_filter(
    file_path: str, csv_file_path: str,
    min_Hz: np.int = 10, max_Hz: np.int = 100,
    points_for_decade: np.int = 10,
    csv_table_titles=False,
    time_report: bool = False, debug: bool = False,
):
    step: np.float = 1 / points_for_decade
    sample_number = 1
    frequency: np.float
    voltages_measurements: List[np.float]
    period: np.float
    delay: np.float = 0.0
    aperture: np.float = 0.0
    interval: np.float = 0.0

    timer = Timer()

    """Asks for the 2 instruments"""
    list_devices: list() = get_device_list()
    print_devices_list(list_devices)
    index_generator: np.int = np.int(input("Which is the Generator? "))
    index_reader: np.int = np.int(input("Which is the Reader? "))

    """Generates the instrument's interfaces"""
    gen: usbtmc.Instrument = list_devices[index_generator]
    read: usbtmc.Instrument = list_devices[index_reader]

    """Open the Instruments interfaces"""
    gen.open()
    read.open()

    """Sets the Configuration for the Voltmeter"""
    configs_gen: list = [
        "*CLS",
        Rigol.set_voltage_ac(),
        ":OUTPut1 OFF",
        ":OUTPut1 ON",
        Rigol.clear(),
    ]

    configs_read: list = [
        "*CLS",
        "CONF:VOLT:AC",
        ":VOLT:AC:BAND +3.00000000E+00",
        ":TRIG:SOUR IMM",
        ":TRIG:DEL:AUTO OFF",
        ":FREQ:VOLT:RANG:AUTO ON",
        ":SAMP:SOUR TIM",
        f":SAMP:COUN {sample_number}",
    ]

    exec_commands(gen, configs_gen)
    exec_commands(read, configs_read)

    pass
