from typing import Optional
import enum
import math
from time import sleep
from typing import List, Optional
from matplotlib import pyplot as plt

import nidaqmx
import nidaqmx.constants
import nidaqmx.stream_readers
import nidaqmx.stream_writers
import nidaqmx.system
import numpy as np
import usbtmc
from nidaqmx._task_modules.channels.ai_channel import AIChannel
from nidaqmx._task_modules.channels.ao_channel import AOChannel
from nidaqmx.system._collections.device_collection import DeviceCollection
from nidaqmx.system.system import System
from numpy.ma.core import sin, sqrt
from rich.panel import Panel
from rich.table import Column, Table
from rich.tree import Tree
from scipy.fft import fft

from cDAQ.console import console
from cDAQ.timer import Timer
from cDAQ import utility


class ni9251:

    Fs: Optional[float] = None
    max_Fs: float = 102000
    min_voltage: float = -4
    max_voltage: float = 4
    number_of_samples: Optional[float]
    ch_input: Optional[str]

    def __init__(
        self,
        Fs: float,
        number_of_samples: Optional[int] = None,
        ch_input: Optional[str] = None,
    ) -> None:

        self.Fs = Fs
        self.number_of_samples = number_of_samples
        self.ch_input = ch_input

    def set_Fs(self, Fs: float):
        self.Fs = Fs

    def read_voltage(
        self,
        number_of_samples: int,
        frequency: Optional[float] = None,
        # Example: "cDAQ9189-1CDBE0AMod1/ai1"
        ch_input: Optional[str] = None,
    ) -> np.ndarray:

        if frequency and self.Fs and frequency > self.Fs / 2:
            raise ValueError("The Sampling rate is low: Fs / 2 > frequency.")

        task = nidaqmx.Task("Input Voltage")
        task.ai_channels.add_ai_voltage_chan(
            ch_input, min_val=self.min_voltage, max_val=self.max_voltage
        )

        # Sets the Clock sampling rate
        task.timing.cfg_samp_clk_timing(self.Fs)

        # Pre allocate the array
        voltages = np.ndarray(shape=number_of_samples)

        # Sets the task for the stream_reader
        channel1_stream_reader = nidaqmx.stream_readers.AnalogSingleChannelReader(
            task.in_stream
        )

        # Sampling the voltages
        channel1_stream_reader.read_many_sample(
            voltages, number_of_samples_per_channel=number_of_samples
        )
        task.close()

        return voltages
