from __future__ import annotations

from re import split
from typing import Any, Self

import usb
import usbtmc
from rich.panel import Panel

from audio.console import console


class Instrument:
    instrument: usbtmc.Instrument

    def __init__(
        self: Self,
        dev_maj: int,
        dev_min: int,
    ) -> None:
        self.instrument = usbtmc.Instrument(dev_maj, dev_min)

    @classmethod
    def from_device(
        cls: type[Self],
        device: usb.core.Device | None = None,
    ) -> Self | None:
        dev_maj, dev_min = Instrument.device_maj_min(str(device))

        if dev_maj is None or dev_min is None:
            return None

        return cls(dev_maj, dev_min)

    @staticmethod
    def device_maj_min(instrument: str) -> tuple[int, int]:
        return int(instrument[10:14], 16), int(instrument[15:19], 16)


class UsbTmc:
    instr: Instrument

    def __init__(self: Self, instrument: Instrument) -> None:
        """The class UsbTmc driver

        Args:
            instrument (usbtmc.Instrument): The Instrument
        """
        self.instr = instrument

    def __del__(self: Self) -> None:
        if self.instr.instrument.connected:
            self.instr.instrument.close()

    def open(self: Self) -> None:
        self.instr.instrument.open()

    def close(self: Self) -> None:
        self.instr.instrument.close()

    def write(self: Self, command: str) -> None:
        """Execute a command."""
        self.instr.instrument.write(command)

    def ask(self: Self, command: str):
        """Asks to retrive a value."""
        return self.instr.instrument.ask(command)

    def reset(self: Self) -> None:
        """Resets the Instrument to the default options."""
        self.instr.instrument.write("*RST")

    def clear_status(self: Self) -> None:
        """Clears the status."""
        self.instr.instrument.write("*CLS")

    def query_event_status_register(self: Self) -> list | Any | str:
        """Asks for the Standard Event Status Registrer.

        Returns:
            Union[list, Any, str]: the result of the query.
        """
        return self.instr.instrument.ask("*ESR?")

    def query_identification(self: Self):
        """Ask the ID of the instrument."""
        return self.instr.instrument.ask("*IDN?")

    def query_current_state_commands(self: Self):
        """Ask for the commands to arrive at this configuration."""
        return self.instr.instrument.ask("*LRN?")

    def set_aperture(self: Self, aperture: float) -> None:
        """Sets the frequency's Aperture.

        Args:
            aperture (float): This is the Aperture of the Instrument
        """
        self.instr.instrument.write(f":FREQuency:APERture {aperture}")

    def execute(
        self: Self,
        commands: list[str],
        *,
        debug: bool = False,
    ) -> None:
        for command in commands:
            if command.find("?") > 0:
                response = self.ask(command)

                if response == "":
                    response = "NULL"

                console.print(f"{command}:\t{response}")
            else:
                self.write(command)

                if debug:
                    console.print(command)

    @staticmethod
    def search_devices() -> list[Instrument]:
        list_devices: list[usb.core.Device] = usbtmc.list_devices()
        instruments: list[Instrument] = []

        for device in list_devices:
            instr: Instrument | None = Instrument.from_device(device)
            if instr is not None:
                instruments.append(instr)

        return instruments

    @staticmethod
    def print_devices_list(list_devices: list[Instrument]) -> None:
        for index, device in enumerate(list_devices):
            device_lines = split("\n", str(device.instrument.device))
            console.print(f"Device {index}:")

            for device_line in device_lines:
                line: list[str] = device_line.strip().split()

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


def command_line_() -> None:
    list_devices: list[usbtmc.Instrument] = UsbTmc.search_devices()

    UsbTmc.print_devices_list(list_devices)

    index_generator: int = int(input("Which is the Generator? "))
    index_reader: int = int(input("Which is the Reader? "))

    generator: usbtmc.Instrument = list_devices[index_generator]
    reader: usbtmc.Instrument = list_devices[index_reader]

    generator.open()
    reader.open()

    # Operations
    isEnded: bool = False
    input_string: str = ""
    console.print("Type the Device index followed by the command you want to execute")
    console.print("Example: 0 TRIG:COUN 3")
    console.print("-" * 50)

    while not isEnded:
        input_string = input("> ")

        if input_string == "exit":
            isEnded = True
            break

        index: int = int(input_string[0])

        if index > len(list_devices):
            console.print("Index device out of range")
            console.print("-" * 50)
            continue

        if input_string.find("?") > 0:
            response = list_devices[index].ask(input_string[2:])

            console.print(f"{input_string[2:]}:\t{response}")
        else:
            console.print(input_string[2:])
            list_devices[index].write(input_string[2:])

        console.print("-" * 50)

    generator.close()
    reader.close()


class ResourceManager:
    def search_resources(self: Self) -> list[usb.core.Device]:
        devices: list[usb.core.Device] = usbtmc.list_devices()

        return devices

    def open_resource(
        self: Self,
        device: usb.core.Device | None = None,
    ) -> UsbTmcInstrument | None:
        if device is None:
            devices = self.search_resources()
            if len(devices) == 1:
                device = devices[0]
            else:
                return None

        return UsbTmcInstrument(usbtmc.Instrument(device))

    def print_devices(self: Self) -> None:
        resources = self.search_resources()

        for idx, resource in enumerate(resources):
            console.print(Panel(resource.__str__(), title=f"Resource index: {idx}"))


class UsbTmcInstrument:
    instr: usbtmc.Instrument

    def __init__(self: Self, instrument: usbtmc.Instrument) -> None:
        self.instr = instrument

    def __del__(self: Self) -> None:
        if self.instr.connected:
            self.instr.close()

    def open(self: Self) -> None:
        if not self.instr.connected:
            self.instr.open()

    def close(self: Self) -> None:
        if self.instr.connected:
            self.instr.close()

    def write(self: Self, command: str) -> bool:
        """Execute a command."""
        try:
            self.instr.write(command)
        except Exception as e:
            console.log(f"{e}")
            return False
        return True

    def ask(self: Self, command: str):
        """Asks to retrive a value."""
        try:
            response = self.instr.ask(command)
        except Exception as e:
            console.log(f"{e}")
            return None
        return response

    def reset(self: Self) -> None:
        """Resets the Instrument to the default options."""
        self.instr.write("*RST")

    def clear_status(self: Self) -> None:
        """Clears the status."""
        self.instr.write("*CLS")

    def query_event_status_register(self: Self) -> list | Any | str:
        """Asks for the Standard Event Status Registrer.

        Returns:
            Union[list, Any, str]: the result of the query.
        """
        return self.instr.ask("*ESR?")

    def query_identification(self: Self):
        """Ask the ID of the instrument."""
        return self.instr.ask("*IDN?")

    def query_current_state_commands(self: Self):
        """Ask for the commands to arrive at this configuration."""
        return self.instr.ask("*LRN?")

    def set_aperture(self, aperture: float) -> None:
        """Sets the frequency's Aperture.

        Args:
            aperture (float): This is the Aperture of the Instrument
        """
        self.instr.write(f":FREQuency:APERture {aperture}")

    def execute(
        self: Self,
        commands: list[str],
        *,
        debug: bool = False,
    ) -> None:
        for command in commands:
            if command.find("?") > 0:
                response = self.ask(command)

                if response == "":
                    response = "NULL"

                console.print(f"{command}:\t{response}")
            else:
                self.write(command)

                if debug:
                    console.print(command)
