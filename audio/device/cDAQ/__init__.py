from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import nidaqmx
import nidaqmx.constants
import nidaqmx.stream_readers
import nidaqmx.stream_writers
import nidaqmx.system
import numpy
import numpy as np
from nidaqmx._task_modules.channels.ao_channel import AOChannel
from nidaqmx.constants import VoltageUnits
from nidaqmx.system import Device, System
from nidaqmx.system._collections.device_collection import DeviceCollection
from nidaqmx.utils import flatten_channel_string
from rich.panel import Panel
from rich.table import Column, Table
from rich.tree import Tree

from audio.console import console


class cDAQ:
    """
    Class for Initialize the nidaqmx driver connection
    """

    system: System

    def __init__(self) -> None:

        # Get the system instance for the nidaqmx-driver
        self.system = System.local()

    def print_driver_version(self, debug: bool = False):
        """Prints the Version for the nidaqmx driver

        Args:
            debug (bool): if true, prints the versions divided in a table
        """

        if not debug:
            console.print(
                Panel.fit(
                    "Version: [blue]{}[/].[blue]{}[/].[blue]{}[/]".format(
                        self.system.driver_version.major_version,
                        self.system.driver_version.minor_version,
                        self.system.driver_version.update_version,
                    )
                )
            )
        else:
            table = Table(
                Column(justify="left"),
                Column(justify="right"),
                title="cDAQ Driver info",
                show_header=False,
            )

            # Major Version
            table.add_row(
                "Major Version", "{}".format(self.system.driver_version.major_version)
            )

            # Minor Version
            table.add_row(
                "Minor Version", "{}".format(self.system.driver_version.minor_version)
            )

            # Update Version
            table.add_row(
                "Update Version", "{}".format(self.system.driver_version.update_version)
            )
            console.print(table)

    def _list_devices(self) -> DeviceCollection:
        """Returns the Device connected to the machine

        Returns:
            DeviceCollection: Device List
        """

        return self.system.devices

    def print_list_devices(self):
        """Prints the Devices connected to the machine"""

        table = Table(title="Device List")
        table.add_column("[yellow]Name[/]", justify="left", style="blue", no_wrap=True)

        for device in self._list_devices():
            table.add_row(device.name)
        console.print(table)


def print_supported_output_types(channel: AOChannel):
    supported_types: Tree = Tree(
        "[yellow]Supported Types[/]",
    )

    for t in channel.physical_channel.ao_output_types:
        supported_types.add(
            "[green]{}[/green]: [blue]{}[/blue]".format(t.name, int(t.value))
        )

    console.print(Panel.fit(supported_types))


class cDAQAIDevice:
    pass


class ni9251(cDAQAIDevice):

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


from audio.config.type import Range


@dataclass
class ni9223(cDAQAIDevice):
    number_of_samples: int
    sampling_frequency: float = None
    input_channel: List[str] = None
    task: nidaqmx.Task = None
    device: Optional[Device] = None

    def init_device(self):
        self.device = Device(self.input_channel)

    @property
    def device_voltage_ranges(self) -> Range[float]:
        ranges: Tuple[float, float] = self.device.ai_voltage_rngs
        range_min, range_max = ranges
        r: Range[float] = Range(range_min, range_max)
        return r

    @property
    def device_Fs_max(self) -> float:
        self.device.anlg_trig_supported
        return self.device.ai_max_single_chan_rate

    def create_task(self, name: str = ""):
        try:
            # 1. Create a NidaqMX Task
            self.task = nidaqmx.Task(name)
        except Exception as e:
            console.print("[EXCEPTION] - {}".format(e))
            self.task_close()

    def set_sampling_clock_timing(self, sampling_frequency: float):
        self.task.timing.cfg_samp_clk_timing(sampling_frequency)
        self.sampling_frequency = sampling_frequency

    def add_ai_channel(self, input_channel: List[str]):
        # 2. Add the AI Voltage Channel
        self.task.ai_channels.add_ai_voltage_chan(
            flatten_channel_string(input_channel),
        )
        self.input_channel = input_channel

    def add_rms_channel(self):
        self.task.ai_channels.add_ai_voltage_rms_chan(
            physical_channel=self.input_channel,
        )

    def task_start(self):
        self.task.start()

    def task_stop(self):
        # self.task.wait_until_done()
        while not self.task.is_task_done():
            pass
        self.task.stop()

    def task_close(self):
        self.task.close()

    def read_single_voltages(self):
        # 4. Pre allocate the array
        voltages = np.ndarray(self.number_of_samples, dtype=float)

        # 6. Sets the task for the stream_reader
        channel1_stream_reader = nidaqmx.stream_readers.AnalogSingleChannelReader(
            self.task.in_stream
        )

        # 7. Sampling the voltages
        channel1_stream_reader.read_many_sample(
            voltages, number_of_samples_per_channel=self.number_of_samples
        )

        return voltages

    def read_multi_voltages(self):
        reader = nidaqmx.stream_readers.AnalogMultiChannelReader(self.task.in_stream)

        values_read = numpy.zeros(
            (len(self.input_channel), self.number_of_samples),
            dtype=numpy.float64,
        )
        try:
            reader.read_many_sample(
                values_read, number_of_samples_per_channel=self.number_of_samples
            )
        except Exception as e:
            console.log(f"[EXCEPTION]: {e}")
            return None
        return values_read
