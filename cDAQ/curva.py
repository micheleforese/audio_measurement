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
from cDAQ.alghorithm import LogaritmicScale
from cDAQ.config import Config
from cDAQ.scpi import Switch, SCPI
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


def curva(
    config_file_path,
    file_path,
    debug: bool = False,
):
    sampling_curve(config_file_path=config_file_path,
                   file_path=file_path, debug=debug)


def sampling_curve(
    config_file_path,
    file_path,
    debug: bool = False,
):
    """Load JSON config"""
    config = Config(config_file_path)

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
        SCPI.set_function_voltage_ac(),
        SCPI.set_output(1, Switch.OFF),
    ]

    SCPI.exec_commands(generator, generator_configs)

    generator_ac_curves: List[str] = [
        SCPI.set_source_voltage_amplitude(1, amplitude_pp),
        SCPI.set_source_frequency(1, round(frequency, 5)),
        SCPI.set_output_impedance(1, 50),
        SCPI.set_output_load(1, "INF"),

        SCPI.set_source_phase(1, 0),
        SCPI.set_output(1, Switch.ON),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

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

    log_scale: LogaritmicScale = LogaritmicScale(
        min_Hz, max_Hz,
        step, points_for_decade
    )

    voltages_measurements: List[float]
    period: np.float = 0.0

    delay: np.float = 0.0
    aperture: np.float = 0.0
    interval: np.float = 0.0

    delay_min: np.float = config.delay_min
    aperture_min: np.float = config.aperture_min
    interval_min: np.float = config.interval_min

    f = open(file_path, "w")
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
        gen.write(":SOURce1:FREQ {}".format(round(frequency, 5)))

        # GET MEASUREMENTS
        rms_value = rms(frequency=frequency, Fs=config.Fs,
                        ch_input=config.nidaq.ch_input,
                        max_voltages=config.nidaq.max_voltage,
                        min_voltages=config.nidaq.min_voltage,
                        number_of_samples=config.number_of_samples,
                        time_report=False)

        """File Writing"""
        f.write("{},{}\n".format(frequency, rms_value))

        """PRINTING"""
        if(debug):
            error = float(read.ask("*ESR?"))
            table_update.add_row("Step Curr", f"{step_curr}")
            table_update.add_row("Step Curr in log Hz", f"{step_curr_Hz}")
            table_update.add_row("Frequency", f"{frequency}")
            table_update.add_row("Period", f"{period}")
            table_update.add_row("Delay", f"{delay}")
            table_update.add_row("Aperture", f"{aperture}")
            table_update.add_row("Interval", f"{interval}")
            table_update.add_row("Voltages", "\n".join(voltages_measurements))
            if(error != 0):
                table_update.add_row("ERROR", f"{error}")

            console.print(table_update)

    f.close()

    console.print(
        Panel.fit("[red]{}[/] - RMS: {} V".format(number_of_samples, rms_value)))
