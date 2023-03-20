import click

from audio.console import console
from audio.usb.usbtmc import UsbTmc


@click.command()
def print_devices():
    list = UsbTmc.search_devices()

    instr = list[-1]
    print(instr.ask("*IDN?"))

    console.print(list)
