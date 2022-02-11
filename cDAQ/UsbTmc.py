#!/usr/bin/env python3

from datetime import datetime
from time import sleep
from numpy.lib.npyio import genfromtxt
from numpy.ma.core import sin, log10, sqrt
from re import split
from rich import style
from rich.console import Console
from rich.table import Column, Table
from rich.panel import Panel
from typing import Any, List, Tuple, Union
import csv
import matplotlib.pyplot as plt
import numpy as np
import os
import usbtmc
from usbtmc.usbtmc import Instrument
from cDAQ.timer import Timer, Timer_Message

console = Console()

###########################################################


def print_info_instrument(instr: usbtmc.Instrument):
    console.print("-"*80)
    console.print(f"Device: {instr.device}")
    console.print("-"*80)

###########################################################


def exec_commands(
    instr: usbtmc.Instrument,
    commands: List[str],
    debug: bool = False
):
    for command in commands:
        if(command.find("?") > 0):
            response = instr.ask(command)

            if(response == ""):
                response = "NULL"

            console.print("{}:\t{}".format(command, response))
        else:
            instr.write(command)

            if(debug):
                console.print(command)


def device_maj_min(instrument: str) -> Tuple[np.int, np.int]:
    return np.int(instrument[10:14], 16), np.int(instrument[15:19], 16)


def set_frequency(instrument: usbtmc.Instrument, frequency: np.int):
    instrument.write(f"FREQ {frequency}")


def get_ac_voltage(instrument: usbtmc.Instrument) -> np.int:
    return instrument.ask("MEASure:VOLTage:AC?")


def get_dc_voltage(instrument: usbtmc.Instrument) -> np.int:
    return instrument.ask("MEASure:VOLTage:DC?")


def sendReset(instrument: usbtmc.Instrument):
    instrument.write("*RST")


def get_device_list() -> List[usbtmc.Instrument]:
    list = usbtmc.list_devices()
    list_devices = []

    for device in list:
        list_devices.append(str(device))

    list_instr: List[Tuple[np.int, np.int]] = []

    for device in list_devices:
        maj, min = device_maj_min(device)
        list_instr.append(usbtmc.Instrument(maj, min))

    return list_instr


def print_devices_list(list_devices: List[usbtmc.Instrument]):
    for index, device in enumerate(list_devices):

        device_lines = split("\n", str(device.device))
        console.print(f"Device {index}:")

        for device_line in device_lines:

            line: List[str] = device_line.strip().split()

            if(line[0] == "iManufacturer"):
                # console.print(device_line)
                # console.print([ord(c) for c in device_line])

                option: str = "iManufacturer:\t"
                for i in range(3, len(line)):
                    option = option + " " + line[i]
                console.print(" " + option)
            elif(line[0] == "iProduct"):
                # console.print(device_line)
                # console.print([ord(c) for c in device_line])

                option2 = "iProduct:\t"
                for i in range(3, len(line)):
                    option2 = option2 + " " + line[i]
                console.print(" " + option2)

        console.print()


class UsbTmc:
    instr: usbtmc.Instrument

    def __init__(self, instrument: usbtmc.Instrument) -> None:
        """The class UsbTmc driver

        Args:
            instrument (usbtmc.Instrument): The Instrument
        """
        self.instr = instrument

    def write(self, command):
        """Execute a command."""
        self.instr.write(command)

    def ask(self, command):
        """Asks to retrive a value."""
        return self.instr.ask(command)

    def reset(self):
        """Resets the Instrument to the default options."""
        self.instr.write("*RST")

    def clear_status(self):
        """Clears the status."""
        self.instr.write("*CLS")

    def query_event_status_register(self) -> Union[list, Any, str]:
        """Asks for the Standard Event Status Registrer.

        Returns:
            Union[list, Any, str]: the result of the query.
        """
        return self.instr.ask("*ESR?")

    def query_identification(self):
        """Ask the ID of the instrument."""
        return self.instr.ask("*IDN?")

    def query_current_state_commands(self):
        """Ask for the commands to arrive at this configuration."""
        return self.instr.ask("*LRN?")

    def set_aperture(self, aperture: np.float):
        """Sets the frequency's Aperture.

        Args:
            aperture (np.float): This is the Aperture of the Instrument
        """
        self.instr.write(f":FREQuency:APERture {aperture}")


def command_line():
    list_devices: list() = get_device_list()

    print_devices_list(list_devices)

    index_generator: np.int = np.int(input("Which is the Generator? "))
    index_reader: np.int = np.int(input("Which is the Reader? "))

    generator: usbtmc.Instrument = list_devices[index_generator]
    reader: usbtmc.Instrument = list_devices[index_reader]

    generator.open()
    reader.open()

    """Operations"""
    isEnded = False
    input_string: str = ""
    console.print(
        "Type the Device index followed by the command you want to execute")
    console.print("Example: 0 TRIG:COUN 3")
    console.print("-" * 50)

    while(isEnded != True):
        input_string = input("> ")

        if(input_string == "exit"):
            isEnded = True
            break

        index: np.int = np.int(input_string[0])

        if(index > len(list_devices)):
            console.print("Index device out of range")
            console.print("-" * 50)
            continue

        if(input_string.find("?") > 0):
            response = list_devices[index].ask(input_string[2:])

            console.print("{}:\t{}".format(input_string[2:], response))
        else:
            console.print(input_string[2:])
            list_devices[index].write(input_string[2:])

        console.print("-" * 50)

    generator.close()
    reader.close()


def algorthm(min_Hz: np.int = 10, max_Hz: np.int = 100000, points_for_decade: np.int = 10):

    step: np.float = 1 / points_for_decade
    frequency: np.float
    voltage: List[np.float]
    period: np.float
    sample_number: np.int = 3
    sample_time: np.float

    f = open("measurements.csv", "w")

    min_index: np.float = log10(min_Hz)
    max_index: np.float = log10(max_Hz)

    steps_sum = (points_for_decade * max_index) - \
        (points_for_decade * min_index)

    i = 0
    while i < steps_sum + 1:
        frequency = pow(10, min_index + i * step)
        period = 1000 / frequency
        sample_time = period * sample_number
        f.write("{},{},{}\n".format(frequency, period, sample_time))
        console.print("{:.15}:\t{},\t{},\t{}".format(
            min_index + i * step, frequency, period, sample_time))

        i += 1
    f.close()


def plot():
    x = np.linspace(0, 2, 100)

    # Note that even in the OO-style, we use `.pyplot.figure` to create the figure.
    fig, ax = plt.subplots()  # Create a figure and an axes.
    ax.plot(x, x, label='linear')  # Plot some data on the axes.
    ax.plot(x, x**2, label='quadratic')  # Plot more data on the axes...
    ax.plot(x, x**3, label='cubic')  # ... and some more.
    ax.set_xlabel('x label')  # Add an x-label to the axes.
    ax.set_ylabel('y label')  # Add a y-label to the axes.
    ax.set_title("Simple Plot")  # Add a title to the axes.
    ax.legend()  # Add a legend.
    plt.savefig('foo.pdf')


def csv_to_plot():

    x = []
    y = []

    with open("measurements.csv", "r") as csvfile:
        lines = csv.reader(csvfile)
        for row in lines:
            x.append(row[0])
            y.append(row[2])

    plt.plot(x, y, color='g', linestyle='dashed',
             marker='o', label="Sample Time")

    plt.xlabel("Frequency")
    plt.ylabel("Sample Time")
    plt.title("Sample tile per Frequencies")
    plt.grid(plt.legend)
    plt.savefig("plot.pdf")


def test_sampling(
    file_path: str,
    min_Hz: np.int = 10, max_Hz: np.int = 100,
    points_for_decade: np.int = 10,
    sample_number=1,
    time_report: bool = False, debug: bool = False
):

    table_config = Table(title="Configurations")
    table_config.add_column("Configuration", style="cyan", no_wrap=True)

    step: np.float = 1 / points_for_decade
    amplitude = 4.47
    frequency: np.float
    voltages_measurements: List[np.float]
    period: np.float = 0.0
    delay: np.float = 0.0
    aperture: np.float = 0.0
    interval: np.float = 0.0

    """Sets minimum for Delay, Aperture and Interval"""
    delay_min: np.float = 0.001
    aperture_min: np.float = 0.01
    interval_min: np.float = 0.01

    table_config.add_row("Step", f"{step}",
                         style="")
    table_config.add_row("Sample Number", f"{sample_number}",
                         style="")
    table_config.add_row("Amplitude", f"{amplitude}",
                         style="")

    start: datetime = 0
    stop: datetime = 0

    """Asks for the 2 instruments"""
    list_devices: List[Instrument] = get_device_list()
    print_devices_list(list_devices)
    index_generator: np.int = np.int(input("Which is the Generator? "))
    index_reader: np.int = np.int(input("Which is the Reader? "))

    table_config.add_row("Generator Index", f"{index_generator}",
                         style="")
    table_config.add_row("Reader Index", f"{index_reader}",
                         style="")

    """Generates the insttrument's interfaces"""
    gen: usbtmc.Instrument = list_devices[index_generator]
    read: usbtmc.Instrument = list_devices[index_reader]

    """Open the Instruments interfaces"""
    gen.open()
    read.open()

    """Sets the Configuration for the Voltmeter"""
    configs_gen: List[str] = [
        "*CLS",
        ":FUNCtion:VOLTage:AC",
        f":SOUR1:VOLTAGE:AMPLitude {amplitude}"
        ":OUTPut1 OFF",
        ":OUTPut1 ON",
    ]

    configs_read: List[str] = [
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

    min_index: np.float = log10(min_Hz)
    max_index: np.float = log10(max_Hz)

    table_config.add_row("min Hz", f"{min_Hz}",
                         style="")
    table_config.add_row("max Hz", f"{max_Hz}",
                         style="")

    table_config.add_row("min index", f"{min_index}",
                         style="")
    table_config.add_row("max index", f"{max_index}",
                         style="")

    table_config.add_row("Generator Config SCPI", "\n".join(configs_gen),
                         style="")
    table_config.add_row("Reader Config SCPI", "\n".join(configs_read),
                         style="")

    step_max = points_for_decade * max_index
    step_min = points_for_decade * min_index
    step_total = step_max - step_min

    table_config.add_row("Step Max", f"{step_max}",
                         style="")
    table_config.add_row("Step Min", f"{step_min}",
                         style="")
    table_config.add_row("Step Total", f"{step_total}",
                         style="")

    console.print(table_config)

    """Open the file for the measurements"""
    f = open(file_path, "w")

    """Start time"""
    timer = Timer()
    timer.start()

    step_curr = 0
    while step_curr < step_total + 1:

        table_update = Table(
            Column(),
            Column(justify="right"),
            show_header=False
        )

        step_curr_Hz = min_index + step_curr * step
        # Frequency in Hz
        frequency = pow(10, step_curr_Hz)

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

        # Sets the aperture
        # read.write(f":VOLT:APER {aperture}")

        # Sets the delay between the trigger and the first measurement
        read.write("TRIG:DEL {}".format(delay))

        # Sets the interval of the measurements
        read.write(":SAMP:TIM {}".format(interval))

        # Init the measurements
        read.write("INIT")
        while(int(read.ask("*OPC?")) == 0):
            console.log("waiting")
            sleep(1)
        voltages_measurements = read.ask("FETCh?").split(",")

        """File Writing"""
        f.write("{},{}\n".format(frequency, ",".join(voltages_measurements)))

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

        step_curr += 1

    f.close()

    """Stop time"""
    timer_message: Timer_Message = timer.stop()

    if(time_report):
        console.print(
            Panel(
                "{}: {} s".format(timer_message.message, timer_message.elapsed_time),
                title="Execution Time"
            )
        )

    """Closes the Instruments interfaces"""
    gen.close()
    read.close()


def test_filter(
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

    start: datetime
    stop: datetime

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
        ":FUNCtion:VOLTage:AC",
        ":OUTPut1 OFF",
        ":OUTPut1 ON",
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

    min_index: np.float = log10(min_Hz)
    max_index: np.float = log10(max_Hz)

    steps_sum = (points_for_decade * max_index) - \
        (points_for_decade * min_index)

    i = 0

    """Open the file for the measurements"""
    f = open(file_path, "w")

    # Only for Debugging
    if(csv_table_titles):
        if os.stat(file_path).st_size == 0:
            f.write("min_Hz\t\t{}\n".format(min_Hz))
            f.write("max_Hz\t\t{}\n".format(max_Hz))
            f.write("points_for_decade\t{}\n".format(points_for_decade))
            f.write("Delay,Interval,Frequency,VoltageMeasurements\n")

    csv_file = list(genfromtxt(csv_file_path, delimiter=",", names=[
        "Frequency", "Voltage", "dBV"], dtype="f8,f8,f8"))

    """Start time"""
    start = datetime.now()

    while i < steps_sum + 1:

        # Frequency in Hz
        frequency = pow(10, min_index + i * step)

        # Period in seconds
        period = 1 / frequency

        # Delay in seconds
        delay = round(period * 3, 3)

        # Aperture in seconds
        aperture = round(period * 0.5, 4)

        # Interval in seconds
        # Interval is 10% more than aperture
        interval = round((period * 0.5) * 1.1, 4)

        """Sets minimum for Delay, Aperture and Interval"""
        delay_min: np.float = 0.001
        aperture_min: np.float = 0.01
        interval_min: np.float = 0.01

        if(delay < delay_min):
            delay = delay_min

        if(aperture < aperture_min):
            aperture = aperture_min

        if(interval < interval_min):
            interval = interval_min

        amplitude = csv_file[i][1] * 2 * sqrt(2)
        gen.write(f":SOUR1:VOLTAGE:AMPLitude {amplitude}")

        # Sets the Frequency
        gen.write(":SOURce1:FREQ {}".format(round(frequency, 5)))

        # Sets the aperture
        read.write(f":VOLT:APER {aperture}")

        # Sets the delay (Period * 2)
        # Sets the delay between the trigger and the first measurement
        read.write("TRIG:DEL {}".format(delay))

        # Sets the Interval = (Period * 0.5)
        # Sets the interval of the measurements
        read.write(":SAMP:TIM {}".format(interval))

        # Init the measurements
        read.write("INIT")
        while(read.ask("*OPC?") == 0):
            console.print("waiting")
        voltages_measurements = read.ask("FETCh?").split(",")

        """File Writing"""
        f.write("{},{}\n".format(frequency, ",".join(voltages_measurements)))

        """PRINTING"""
        if(debug):
            error = read.ask("*ESR?")

            console.print(
                "[bold]Frequency[/]:\t{}".format(round(frequency, 5)))
            console.print("[bold]Amplitude[/]:\t{}".format(amplitude))
            console.print("[bold]Delay[/]:\t\t{}".format(delay))
            console.print("[bold]Aperture[/]:\t{}".format(aperture))
            console.print("[bold]Interval[/]:\t{}".format(interval))
            if(error != 0):
                console.print('[bold]ERROR[/]:\t\t{}'.format(error))
            console.print("[bold]Voltages[/]:{}".format(voltages_measurements))

        i += 1

    f.close()

    """Stop time"""
    stop = datetime.now()

    if(time_report):
        console.print("-" * 100)
        console.print("Exec Time: {}".format((stop-start).total_seconds()))
        console.print("-" * 100)

    """Closes the Instruments interfaces"""
    gen.close()
    read.close()
