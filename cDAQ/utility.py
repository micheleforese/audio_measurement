import datetime
import enum
import pathlib
from cmath import sqrt
from typing import List, Optional

import nidaqmx
import nidaqmx.constants
import nidaqmx.stream_readers
import nidaqmx.stream_writers
import nidaqmx.system
import numpy as np
import pandas as pd
from nidaqmx._task_modules.channels.ai_channel import AIChannel
from nidaqmx._task_modules.channels.ao_channel import AOChannel
from nidaqmx.system._collections.device_collection import DeviceCollection
from nidaqmx.system.system import System
from rich.panel import Panel
from rich.table import Column, Table
from rich.tree import Tree
from scipy.fft import fft

from cDAQ.console import console
from cDAQ.timer import Timer


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


def percentage_error(exact: float, approx: float) -> float:
    return (approx - exact) / exact


def transfer_function(rms: float, input_rms: float) -> float:
    return 20 * np.log10(rms / input_rms)


def integrate(y_values: List[float], delta) -> float:

    volume: float = 0.0

    for idx, y in enumerate(y_values):
        # If it's the last element then exit the loop
        if idx + 1 == len(y_values):
            break
        else:
            y_plus = y_values[idx + 1]

            # Make the calculations
            if y * y_plus < 0:
                r_rec: float = abs(y) * delta / 4
                l_rec: float = abs(y_plus) * delta / 4
                volume += r_rec + l_rec
                # console.print("Volume: {}".format(round(volume, 9)))
            else:
                r_rec: float = abs(y) * delta
                l_rec: float = abs(y_plus) * delta
                triangle: float = abs(r_rec - l_rec) / 2

                volume += min([r_rec, l_rec]) + triangle

                # console.print("Volume: {}".format(round(volume, 9)))

    return volume


class RMS_MODE(enum.Enum):
    FFT = 1
    AVERAGE = 2
    INTEGRATE = 3


class RMS:
    @staticmethod
    def rms(
        frequency: float,
        Fs: float,
        number_of_samples: int,
        ch_input: str,
        max_voltage: float,
        min_voltage: float,
        rms_mode: RMS_MODE = RMS_MODE.FFT,
        time_report: bool = False,
        save_file: Optional[pathlib.Path] = None,
    ) -> Optional[float]:

        timer = Timer()

        # Pre allocate the array
        try:
            voltages = read_voltages(
                frequency,
                Fs,
                number_of_samples,
                ch_input=ch_input,
                max_voltage=max_voltage,
                min_voltage=min_voltage,
            )

            if save_file:
                pd.DataFrame(voltages).to_csv(
                    save_file.absolute().resolve(),
                    header=["voltage"],
                    index=None,
                )

            rms: Optional[float] = None

            if time_report:
                timer.start("[yellow]RMS Calculation Execution time[/]")

            if rms_mode == RMS_MODE.FFT:
                rms = RMS.fft(voltages)
            elif rms_mode == RMS_MODE.AVERAGE:
                rms = RMS.average(voltages)
            elif rms_mode == RMS_MODE.INTEGRATE:
                rms = RMS.integration(voltages, Fs)

            if time_report:
                timer.stop().print()

            return rms
        except Exception as e:
            console.log(e)

    @staticmethod
    def average(voltages: List[float]) -> float:
        """Calculate the RMS Voltage value from the sampling average

        Args:
            voltages (List[float]): The sampling voltages list
            number_of_samples (int): The number of sampling

        Returns:
            float: The RMS Voltage
        """
        average: float = 0

        n_samp = len(voltages)

        for v in voltages:
            average += abs(v) / n_samp

        return average * 1.111

    @staticmethod
    def fft(voltages) -> float:
        """Calculate the RMS Voltage value with the Fast Fourier Transform
        of the voltage sampling list

        Args:
            voltages (List[float]): The sampling voltages list
            number_of_samples (int): The number of sampling

        Returns:
            float: The RMS Voltage
        """
        n_samp = len(voltages)
        voltages_fft = fft(voltages, n_samp, workers=-1)

        sum = 0
        for v in voltages_fft:
            sum += np.float_power(np.absolute(v), 2)

        rms: float = np.sqrt(sum) / n_samp

        return rms

    @staticmethod
    def integration(voltages: List[float], Fs: float) -> float:
        """Calculate the RMS Voltage value with the Integration Technic

        Args:
            voltages (List[float]): The sampling voltages list
            number_of_samples (int): The number of sampling

        Returns:
            float: The RMS Voltage
        """
        return integrate(voltages, 1 / Fs) / (len(voltages) / Fs)


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

    return voltages


def get_subfolder(
    home: pathlib.Path, pattern: str = r"%Y-%m-%d--%H-%M-%f"
) -> List[pathlib.Path]:
    measurement_dirs: List[pathlib.Path] = []

    for dir in home.iterdir():
        try:
            datetime.datetime.strptime(dir.name, pattern)
            measurement_dirs.append(dir)
        except ValueError:
            continue

    measurement_dirs.sort(
        key=lambda name: datetime.datetime.strptime(name.stem, pattern),
    )

    return measurement_dirs
