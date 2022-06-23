from re import split
from typing import Any, List, Tuple, Union

import numpy as np
import usb
import usbtmc

from cDAQ.console import console

###########################################################


def print_info_instrument(instr: usbtmc.Instrument):
    console.print("-" * 80)
    console.print(f"Device: {instr.device}")
    console.print("-" * 80)


###########################################################


def exec_commands(instr: usbtmc.Instrument, commands: List[str], debug: bool = False):
    for command in commands:
        if command.find("?") > 0:
            response = instr.ask(command)

            if response == "":
                response = "NULL"

            console.print("{}:\t{}".format(command, response))
        else:
            instr.write(command)

            if debug:
                console.print(command)


def device_maj_min(instrument: str) -> Tuple[np.int, np.int]:
    return np.int(instrument[10:14], 16), np.int(instrument[15:19], 16)


def get_device_list() -> List[usbtmc.Instrument]:
    list = usbtmc.list_devices()
    list_devices = []

    for device in list:
        list_devices.append(str(device))

    list_instr: List[usbtmc.Instrument] = []

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

            if line[0] == "iManufacturer":
                # console.print(device_line)
                # console.print([ord(c) for c in device_line])

                option: str = "iManufacturer:\t"
                for i in range(3, len(line)):
                    option = option + " " + line[i]
                console.print(" " + option)
            elif line[0] == "iProduct":
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

    def __del__(self):
        self.close()

    def open(self):
        self.instr.open()

    def close(self):
        self.instr.close()

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

    @staticmethod
    def search_devices() -> List[usbtmc.Instrument]:

        list: List[usb.core.Device] = usbtmc.list_devices()

        for d in list:
            console.print("----------------------")
            console.print(d.iSerialNumber)

        instruments: List[usbtmc.Instrument] = []

        for device in list:
            maj, min = device_maj_min(str(device))
            instruments.append(usbtmc.Instrument(maj, min))

        return instruments


def command_line_():
    list_devices: List[usbtmc.Instrument] = get_device_list()

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
    console.print("Type the Device index followed by the command you want to execute")
    console.print("Example: 0 TRIG:COUN 3")
    console.print("-" * 50)

    while isEnded != True:
        input_string = input("> ")

        if input_string == "exit":
            isEnded = True
            break

        index: np.int = np.int(input_string[0])

        if index > len(list_devices):
            console.print("Index device out of range")
            console.print("-" * 50)
            continue

        if input_string.find("?") > 0:
            response = list_devices[index].ask(input_string[2:])

            console.print("{}:\t{}".format(input_string[2:], response))
        else:
            console.print(input_string[2:])
            list_devices[index].write(input_string[2:])

        console.print("-" * 50)

    generator.close()
    reader.close()
