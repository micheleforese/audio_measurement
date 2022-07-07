from re import split
from typing import Any, List, Optional, Tuple, Union

import numpy as np
import usb
import usbtmc

from audio.console import console


class Instrument:
    instrument: usbtmc.Instrument

    def __init__(
        self,
        dev_maj: Optional[int] = None,
        dev_min: Optional[int] = None,
        device: Optional[usb.core.Device] = None,
    ) -> None:
        if dev_maj and dev_min:
            self.instrument = usbtmc.Instrument(dev_maj, dev_min)
        elif device:
            dev_maj, dev_min = Instrument.device_maj_min(str(device))
            self.instrument = usbtmc.Instrument(dev_maj, dev_min)
        else:
            raise Exception("No Device specified.")

    @staticmethod
    def device_maj_min(instrument: str) -> Tuple[int, int]:
        return int(instrument[10:14], 16), int(instrument[15:19], 16)


class UsbTmc:
    instr: Instrument

    def __init__(self, instrument: Instrument) -> None:
        """The class UsbTmc driver

        Args:
            instrument (usbtmc.Instrument): The Instrument
        """
        self.instr = instrument

    def __del__(self):
        if self.instr.instrument.connected:
            self.instr.instrument.close()

    def open(self):
        self.instr.instrument.open()

    def close(self):
        self.instr.instrument.close()

    def write(self, command):
        """Execute a command."""
        self.instr.instrument.write(command)

    def ask(self, command):
        """Asks to retrive a value."""
        return self.instr.instrument.ask(command)

    def reset(self):
        """Resets the Instrument to the default options."""
        self.instr.instrument.write("*RST")

    def clear_status(self):
        """Clears the status."""
        self.instr.instrument.write("*CLS")

    def query_event_status_register(self) -> Union[list, Any, str]:
        """Asks for the Standard Event Status Registrer.

        Returns:
            Union[list, Any, str]: the result of the query.
        """
        return self.instr.instrument.ask("*ESR?")

    def query_identification(self):
        """Ask the ID of the instrument."""
        return self.instr.instrument.ask("*IDN?")

    def query_current_state_commands(self):
        """Ask for the commands to arrive at this configuration."""
        return self.instr.instrument.ask("*LRN?")

    def set_aperture(self, aperture: np.float):
        """Sets the frequency's Aperture.

        Args:
            aperture (np.float): This is the Aperture of the Instrument
        """
        self.instr.instrument.write(f":FREQuency:APERture {aperture}")

    @staticmethod
    def search_devices() -> List[Instrument]:

        list_devices: List[usb.core.Device] = usbtmc.list_devices()

        instruments: List[Instrument] = []

        for device in list_devices:
            instruments.append(Instrument(device=device))

        return instruments

    @staticmethod
    def print_devices_list(list_devices: List[Instrument]):

        for index, device in enumerate(list_devices):

            device_lines = split("\n", str(device.instrument.device))
            console.print(f"Device {index}:")

            for device_line in device_lines:

                line: List[str] = device_line.strip().split()

                if line[0] == "iManufacturer":

                    option: str = "iManufacturer:\t"
                    for i in range(3, len(line)):
                        option = option + " " + line[i]
                    console.print(" " + option)
                elif line[0] == "iProduct":

                    option2 = "iProduct:\t"
                    for i in range(3, len(line)):
                        option2 = option2 + " " + line[i]
                    console.print(" " + option2)

            console.print()


def command_line_():
    list_devices: List[usbtmc.Instrument] = UsbTmc.search_devices()

    UsbTmc.print_devices_list(list_devices)

    index_generator: np.int = np.int(input("Which is the Generator? "))
    index_reader: np.int = np.int(input("Which is the Reader? "))

    generator: usbtmc.Instrument = list_devices[index_generator]
    reader: usbtmc.Instrument = list_devices[index_reader]

    generator.open()
    reader.open()

    # Operations
    isEnded = False
    input_string: str = ""
    console.print("Type the Device index followed by the command you want to execute")
    console.print("Example: 0 TRIG:COUN 3")
    console.print("-" * 50)

    while not isEnded:
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
