import click

from audio.console import console
from audio.usb.usbtmc import Instrument, UsbTmc


@click.command()
def instrument():
    from rich import inspect

    from audio.usb.usbtmc import ResourceManager

    rm = ResourceManager()
    rm.print_devices()
    instr = rm.open_resource()

    inspect(instr.instr.device, all=True)
    instr.open()
    response = instr.ask("*LRN?")
    if response is None:
        console.log("response")

    instr.close()
    exit()

    try:
        list_devices: list[Instrument] = UsbTmc.search_devices()

        if len(list_devices) < 1:
            raise Exception("UsbTmc devices not found.")

        UsbTmc.print_devices_list(list_devices)

        UsbTmc(list_devices[0])

    except Exception as e:
        console.print(f"{e}")
