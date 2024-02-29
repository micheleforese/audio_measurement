from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

import nidaqmx
import nidaqmx.constants
import nidaqmx.stream_readers
import nidaqmx.stream_writers
import nidaqmx.system
import numpy as np
from nidaqmx.errors import DaqError
from nidaqmx.system import Device
from nidaqmx.utils import flatten_channel_string

from audio.config.type import Range
from audio.console import console


class CDAQAIDevice:
    pass


class Ni9251(CDAQAIDevice):
    sampling_frequency: float | None = None
    max_sampling_frequency: float = 102000
    min_voltage: float = -4
    max_voltage: float = 4
    number_of_samples: float | None
    ch_input: str | None

    def __init__(
        self: Self,
        sampling_frequency: float,
        number_of_samples: int | None = None,
        ch_input: str | None = None,
    ) -> None:
        self.sampling_frequency = sampling_frequency
        self.number_of_samples = number_of_samples
        self.ch_input = ch_input

    def set_sampling_frequency(self: Self, sampling_frequency: float) -> None:
        self.sampling_frequency = sampling_frequency

    def read_voltage(
        self: Self,
        number_of_samples: int,
        frequency: float | None = None,
        ch_input: str | None = None,
    ) -> np.ndarray:
        if (
            frequency
            and self.sampling_frequency
            and frequency > self.sampling_frequency / 2
        ):
            _msg = "The Sampling rate is low: Fs / 2 > frequency."
            raise ValueError(_msg)

        task: nidaqmx.Task = nidaqmx.Task("Input Voltage")
        task.ai_channels.add_ai_voltage_chan(
            ch_input,
            min_val=self.min_voltage,
            max_val=self.max_voltage,
        )

        # Sets the Clock sampling rate
        task.timing.cfg_samp_clk_timing(self.sampling_frequency)

        # Pre allocate the array
        voltages: np.ndarray = np.ndarray(shape=number_of_samples)

        # Sets the task for the stream_reader
        channel1_stream_reader: nidaqmx.stream_readers.AnalogSingleChannelReader = (
            nidaqmx.stream_readers.AnalogSingleChannelReader(
                task.in_stream,
            )
        )

        # Sampling the voltages
        channel1_stream_reader.read_many_sample(
            voltages,
            number_of_samples_per_channel=number_of_samples,
        )
        task.close()

        return voltages


@dataclass
class Ni9223(CDAQAIDevice):
    number_of_samples: int
    sampling_frequency: float | None = None
    input_channel: list[str] = field(default=list)
    task: nidaqmx.Task = None
    device: Device | None = None

    def init_device(self: Self) -> None:
        self.device = Device(self.input_channel)

    @property
    def device_voltage_ranges(self: Self) -> Range[float] | None:
        if self.device is None:
            return None

        ranges: tuple[float, float] = self.device.ai_voltage_rngs
        range_min, range_max = ranges
        return Range[float](range_min, range_max)

    @property
    def device_sampling_frequency_max(self: Self) -> float | None:
        if self.device is None:
            return None
        return self.device.ai_max_single_chan_rate

    def create_task(self: Self, name: str = "") -> None:
        try:
            # 1. Create a NidaqMX Task
            self.task = nidaqmx.Task(name)
        except DaqError as e:
            console.print(f"[EXCEPTION] - {e}")
            self.task_close()

    def set_sampling_clock_timing(self: Self, sampling_frequency: float) -> None:
        self.task.timing.cfg_samp_clk_timing(sampling_frequency)
        self.sampling_frequency = sampling_frequency

    def add_ai_channel(self: Self, input_channel: list[str]) -> None:
        # 2. Add the AI Voltage Channel
        self.task.ai_channels.add_ai_voltage_chan(
            flatten_channel_string(input_channel),
        )
        self.input_channel = input_channel

    def add_rms_channel(self: Self) -> None:
        self.task.ai_channels.add_ai_voltage_rms_chan(
            physical_channel=self.input_channel,
        )

    def task_start(self: Self) -> None:
        self.task.start()

    def task_stop(self: Self) -> None:
        while not self.task.is_task_done():
            pass
        self.task.stop()

    def task_close(self: Self) -> None:
        self.task.close()

    def read_single_voltages(self: Self) -> np.ndarray:
        # 4. Pre allocate the array
        voltages: np.ndarray = np.ndarray(self.number_of_samples, dtype=float)

        # 6. Sets the task for the stream_reader
        channel1_stream_reader: nidaqmx.stream_readers.AnalogSingleChannelReader = (
            nidaqmx.stream_readers.AnalogSingleChannelReader(
                self.task.in_stream,
            )
        )

        # 7. Sampling the voltages
        channel1_stream_reader.read_many_sample(
            voltages,
            number_of_samples_per_channel=self.number_of_samples,
        )

        return voltages

    def read_multi_voltages(self: Self) -> list[float] | None:
        reader: nidaqmx.stream_readers.AnalogMultiChannelReader = (
            nidaqmx.stream_readers.AnalogMultiChannelReader(self.task.in_stream)
        )

        values_read = np.zeros(
            (len(self.input_channel), self.number_of_samples),
            dtype=np.float64,
        )
        try:
            reader.read_many_sample(
                values_read,
                number_of_samples_per_channel=self.number_of_samples,
            )
        except DaqError as e:
            console.log(f"[EXCEPTION]: {e}")
            return None
        return list(values_read.tolist())
