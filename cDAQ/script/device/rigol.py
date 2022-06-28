from time import sleep
from typing import List, Optional

import click
from rich.panel import Panel
from usbtmc import Instrument

from cDAQ.console import console
from cDAQ.util.scpi import SCPI, Bandwidth, Switch
from cDAQ.usb.usbtmc import UsbTmc
from cDAQ.utility import (
    RMS,
    trim_value,
)


@click.command(help="Turn On the Rigol Instrument.")
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
def turn_on(debug: bool):
    # Asks for the 2 instruments
    list_devices: List[Instrument] = UsbTmc.search_devices()
    if debug:
        UsbTmc.print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    generator.open()

    generator_ac_curves: List[str] = [
        SCPI.set_output(1, Switch.ON),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    generator.close()

    console.print(Panel("[blue]Rigol Turned ON[/]"))


@click.command(help="Turn Off the Rigol Instrument.")
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
def turn_off(debug: bool):
    # Asks for the 2 instruments
    list_devices: List[Instrument] = UsbTmc.search_devices()
    if debug:
        UsbTmc.print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    generator.open()

    generator_ac_curves: List[str] = [
        SCPI.set_output(1, Switch.OFF),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    generator.close()

    console.print(Panel("[blue]Rigol Turned OFF[/]"))


@click.command(help="Sets the Amplitude peak-to-peak.")
@click.argument(
    "amplitude",
    type=float,
)
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
def set_amplitude(amplitude: float, debug: bool):

    # Asks for the 2 instruments
    list_devices: List[Instrument] = UsbTmc.search_devices()
    if debug:
        UsbTmc.print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    generator.open()

    generator_ac_curves: List[str] = [
        SCPI.set_source_voltage_amplitude(1, round(amplitude, 5)),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    generator.close()

    console.print(Panel("[blue]Rigol Amplitude {}[/]".format(amplitude)))


@click.command()
@click.argument(
    "frequency",
    type=float,
)
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
def set_frequency(frequency, debug: bool):

    # Asks for the 2 instruments
    list_devices: List[Instrument] = UsbTmc.search_devices()
    if debug:
        UsbTmc.print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    generator.open()

    generator_ac_curves: List[str] = [
        SCPI.set_source_frequency(1, round(frequency, 5)),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    generator.close()

    console.print(Panel("[blue]Rigol Frequency {}[/]".format(frequency)))
