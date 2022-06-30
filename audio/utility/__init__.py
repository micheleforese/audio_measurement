import datetime
import pathlib
from typing import List

import nidaqmx
import nidaqmx.constants
import nidaqmx.stream_readers
import nidaqmx.stream_writers
import nidaqmx.system
import numpy as np

from audio.console import console


def trim_value(value: float, max_value: float):
    return max_value if value > max_value else value


def get_subfolder(
    home: pathlib.Path, pattern: str = r"%Y-%m-%d--%H-%M-%f"
) -> List[pathlib.Path]:
    measurement_dirs: List[pathlib.Path] = []

    for directory in home.iterdir():
        try:
            datetime.datetime.strptime(directory.name, pattern)
            measurement_dirs.append(directory)
        except ValueError:
            continue

    measurement_dirs.sort(
        key=lambda name: datetime.datetime.strptime(name.stem, pattern),
    )

    return measurement_dirs


def read_voltages(
    frequency: float,
    Fs: float,
    number_of_samples: int,
    ch_input: str,
    min_voltage: float,
    max_voltage: float,
) -> np.ndarray:

    if frequency > Fs / 2:
        raise ValueError("The Sampling rate is low: Fs / 2 > frequency.")

    try:
        # 1. Create a NidaqMX Task
        task = nidaqmx.Task("Input Voltage")

        # 2. Add the AI Voltage Channel
        ai_channel = task.ai_channels.add_ai_voltage_chan(
            ch_input, min_val=min_voltage, max_val=max_voltage
        )

        # 3. Configure the task
        #   Sets the Clock sampling rate
        task.timing.cfg_samp_clk_timing(Fs)

        # 4. Pre allocate the array
        voltages = np.ndarray(number_of_samples)

        # 5. Start the Task
        task.start()

        # 6. Sets the task for the stream_reader
        channel1_stream_reader = nidaqmx.stream_readers.AnalogSingleChannelReader(
            task.in_stream
        )

        # 7. Sampling the voltages
        channel1_stream_reader.read_many_sample(
            voltages, number_of_samples_per_channel=number_of_samples
        )
        task.close()
    except Exception as e:
        console.print("[EXCEPTION] - {}".format(e))
        task.close()

    return voltages
