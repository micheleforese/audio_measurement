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
from numpy.lib.function_base import average
from numpy.ma.core import sin, sqrt
from rich.panel import Panel
from rich.table import Column, Table
from rich.tree import Tree
from scipy.fft import fft

from cDAQ.console import console
from cDAQ.timer import Timer
from cDAQ import utility


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
    return ((approx - exact) / exact) * 100


def transfer_function(rms: float, input_rms: float) -> float:
    return 20 * np.math.log10(rms / input_rms)


def integrate(y_values: List[float], delta) -> float:

    volume: float = 0.0

    for idx, y in enumerate(y_values):
        # If it's the last element then exit the loop
        if idx + 1 == len(y_values):
            break
        else:
            y_plus = y_values[idx + 1]

            # console.print(
            #     "Values: {} - {}".format(round(y, 5), round(y_plus, 9)))

            # if(idx % 10 == 0):
            # input()

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
    voltages_fft = fft(voltages, number_of_samples, workers=-1)

    sum: float = float(0)

    for v in voltages_fft:
        sum += (np.abs(v) / len(voltages)) ** 2

    return np.math.sqrt(abs(sum))


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


def read_voltages(
    frequency: float,
    Fs: float,
    number_of_samples: int,
    ch_input: str = "cDAQ9189-1CDBE0AMod1/ai1",
    min_voltage: float = -4,
    max_voltage: float = 4,
) -> np.ndarray:

    if frequency > Fs / 2:
        raise ValueError("The Sampling rate is low: Fs / 2 > frequency.")

    task = nidaqmx.Task("Input Voltage")
    channel1: AIChannel = task.ai_channels.add_ai_voltage_chan(
        ch_input, min_val=min_voltage, max_val=max_voltage
    )

    # Sets the Clock sampling rate
    task.timing.cfg_samp_clk_timing(Fs)

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


class RMS_MODE(enum.Enum):
    FFT = 1
    AVERAGE = 2
    INTEGRATE = 3


def rms(
    frequency: float,
    Fs: float,
    number_of_samples: int,
    ch_input: str,
    max_voltage: float,
    min_voltage: float,
    rms_mode: RMS_MODE = RMS_MODE.FFT,
    time_report: bool = False,
) -> Optional[float]:

    timer = Timer()

    # number_of_samples = 800

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
        rms: Optional[float] = None

        if time_report:
            timer.start("[yellow]RMS Calculation Execution time[/]")

        if rms_mode == RMS_MODE.FFT:
            rms = rms_fft(voltages, number_of_samples)
        elif rms_mode == RMS_MODE.AVERAGE:
            rms = rms_average(voltages, number_of_samples)
        elif rms_mode == RMS_MODE.INTEGRATE:
            rms = rms_integration(voltages, number_of_samples, Fs)

        if time_report:
            timer.stop().print()

        return rms
    except Exception as e:
        console.log(e)


def plot_log_db(
    file_path: str = "test.csv", file_png_path: str = "test.png", number_voltages=1
):
    csvfile = np.genfromtxt(file_path, delimiter=",")

    Vpp = 2.0
    frequencies = []
    voltages = []
    dBV = []

    for row in list(csvfile):
        frequencies.append(row[0])

        voltage_average = 0
        voltage_sum = 0

        for n in range(1, number_voltages + 1):
            voltage_sum += n

        voltage_average /= 4

        voltages.append((row[2] + row[3] + row[4]) / 3)
        dBV.append(20 * math.log10(row[1] * Vpp / (2 * sqrt(2))))

    plt.plot(frequencies, dBV)
    plt.xscale("log")
    plt.title("Frequency response graph")
    plt.xlabel("Frequency")
    plt.ylabel("Vout/Vin dB")
    # plt.yticks(np.arange(start=-10.0, stop=11.0, step=5.0))
    plt.savefig(file_png_path)


def plot_V_out_filter(
    csv_file_path: str = "v_out_filter.csv",
    png_graph_file_path: str = "v_out_filter.png",
    min_Hz: float = 40,
    max_Hz: float = 10000,
    frequency_p: float = 5000,
    points_for_decade: int = 100,
    Vpp: float = 2.0,
    n=1,
):

    f = open(csv_file_path, "w")

    step: float = 1 / points_for_decade
    frequencies = []
    voltages_out = []
    dBV = []

    min_index: float = math.log10(min_Hz)
    max_index: float = math.log10(max_Hz)

    steps_sum = (points_for_decade * max_index) - (points_for_decade * min_index)

    i = 0
    while i < steps_sum + 1:
        frequency = pow(10, min_index + i * step)

        V_in = Vpp / (2 * sqrt(2))

        A = abs(1 / sqrt(1 + pow(frequency / frequency_p, 2 * n))) * abs(
            1 / sqrt(1 + pow(frequency_p / frequency, 2 * n))
        )

        voltage_out_temp = V_in * A
        dBV_temp = 20 * math.log10(voltage_out_temp * Vpp / (2 * sqrt(2)))

        frequencies.append(frequency)
        voltages_out.append(voltage_out_temp)
        dBV.append(dBV_temp)

        f.write("{},{},{}\n".format(frequency, voltage_out_temp, dBV_temp))

        i += 1

    f.close()

    plt.plot(frequencies, voltages_out)
    plt.xscale("log")
    plt.title("Frequency to Voltage output RC Filter")
    plt.xlabel("Frequency")
    plt.ylabel("V output")
    plt.savefig(png_graph_file_path)


def plot_percentage_error(
    csv_expected_file_path: str,
    csv_result_file_path: str,
    csv_file_path,
    png_graph_file_path: str,
    debug: bool = False,
):
    csv_expected = np.genfromtxt(
        csv_expected_file_path,
        delimiter=",",
    )
    csv_result = np.genfromtxt(
        csv_result_file_path,
        delimiter=",",
    )

    frequency: List[float] = []
    perc_error: List[float] = []

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Frequency")
    table.add_column("Expected Voltage")
    table.add_column("Result Voltage")
    table.add_column("Percentage Error")

    f = open(csv_file_path, "w")

    for expected, result in zip(csv_expected, csv_result):

        frequency_temp: float = expected[0]
        expected_temp: float = expected[1]
        approx_temp: float = result[1]

        perc_error_temp: float = percentage_error(
            exact=expected_temp,
            approx=approx_temp,
        )

        if debug:
            table.add_row(
                f"{frequency_temp}",
                f"{expected_temp}",
                f"{approx_temp}",
                f"{perc_error_temp}",
            )

        if perc_error_temp > 100.0:
            perc_error_temp = 100

        frequency.append(frequency_temp)
        perc_error.append(perc_error_temp)
        f.write("{},{}\n".format(frequency_temp, perc_error_temp))

    if debug:
        console.print(table)

    plt.xticks(np.arange(0, 100, step=10))
    plt.plot(frequency, perc_error)
    # plt.xscale("log")
    plt.title("Percentage error, Expected Voltage / Result Voltage")
    plt.xlabel("Frequency")
    plt.ylabel("Percentage error")
    plt.savefig(png_graph_file_path)


def plot_percentage_error_temp(
    csv_expected_file_path: str,
    csv_result_file_path: str,
    csv_file_path,
    png_graph_file_path: str,
    debug: bool = False,
):
    csv_expected = np.genfromtxt(
        csv_expected_file_path,
        delimiter=",",
    )
    csv_result = np.genfromtxt(
        csv_result_file_path,
        delimiter=",",
    )

    frequency: List[float] = []
    perc_error: List[float] = []

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Frequency")
    table.add_column("Expected Voltage")
    table.add_column("Result Voltage")
    table.add_column("Percentage Error")

    f = open(csv_file_path, "w")

    for expected, result in zip(csv_expected, csv_result):

        frequency_temp: float = expected[0]
        expected_temp: float = 1 / math.sqrt(2)
        approx_temp: float = result[1]

        perc_error_temp: float = percentage_error(
            exact=expected_temp,
            approx=approx_temp,
        )

        if debug:
            table.add_row(
                f"{frequency_temp}",
                f"{expected_temp}",
                f"{approx_temp}",
                f"{perc_error_temp}",
            )

        if perc_error_temp > 100.0:
            perc_error_temp = 100

        frequency.append(frequency_temp)
        perc_error.append(perc_error_temp)
        f.write("{},{}\n".format(frequency_temp, perc_error_temp))

    if debug:
        console.print(table)

    plt.xticks(np.arange(0, 100, step=10))
    plt.plot(frequency, perc_error)
    # plt.xscale("log")
    plt.title("Percentage error, Expected Voltage / Result Voltage")
    plt.xlabel("Frequency")
    plt.ylabel("Percentage error")
    plt.savefig(png_graph_file_path)


def diff_steps(file_path: str):

    csvfile = np.genfromtxt(file_path, delimiter=",", names=["Frequency", "Voltage"])

    list_f_v = list(csvfile)

    curr_v: float
    prev_v: float = float(list_f_v[0][1])
    diff_v: float = 0.0

    curr_f: float
    prev_f: float = float(list_f_v[0][0])

    table = Table(
        Column("Prev Frequency", justify="right"),
        Column("Curr Frequency", justify="right"),
        Column("Prev Voltage", justify="right"),
        Column("Curr Voltage", justify="right"),
        Column("Step Difference", justify="right"),
        show_header=True,
    )

    for row in list_f_v:
        curr_f = float(row[0])
        curr_v = float(row[1])

        diff_v = curr_v - prev_v

        style_voltage = "green"

        if diff_v < 0:
            style_voltage = "red"

        table.add_row(
            "{}".format(prev_f),
            "{}".format(curr_f),
            "{}".format(prev_v),
            "{}".format(curr_v),
            "[{}]{}[/]".format(style_voltage, diff_v),
        )

        prev_f = curr_f
        prev_v = curr_v

    console.print(table)


def command_line(instr: usbtmc.Instrument):
    instr.open()

    """Operations"""
    isEnded = False
    cmd: str = ""
    console.print("Type the Device index followed by the command you want to execute")
    console.print("Example: TRIG:COUN 3")
    console.print("-" * 50)

    while isEnded != True:
        cmd = input("scpi> ").strip()

        if cmd == "exit":
            isEnded = True
            break

        if cmd.find("?") > 0:
            # answer = instr.ask(cmd).strip()
            instr.write(cmd)
            sleep(1)
            answer = instr.read().strip()

            console.print("{}".format(answer))
        else:
            instr.write(cmd)
