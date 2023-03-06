
import click
from rich.panel import Panel
from usbtmc import Instrument

from audio.console import console
from audio.usb.usbtmc import UsbTmc
from audio.utility.scpi import SCPI, Switch


@click.command(help="Turn On the Rigol Instrument.")
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
def turn_on(debug: bool):
    # Asks for the 2 instruments
    list_devices: list[Instrument] = UsbTmc.search_devices()
    if debug:
        UsbTmc.print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    generator.open()

    generator_ac_curves: list[str] = [
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
    list_devices: list[Instrument] = UsbTmc.search_devices()
    if debug:
        UsbTmc.print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    generator.open()

    generator_ac_curves: list[str] = [
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
    list_devices: list[Instrument] = UsbTmc.search_devices()
    if debug:
        UsbTmc.print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    generator.open()

    generator_ac_curves: list[str] = [
        SCPI.set_source_voltage_amplitude(1, round(amplitude, 5)),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    generator.close()

    console.print(Panel(f"[blue]Rigol Amplitude {amplitude}[/]"))


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
    list_devices: list[Instrument] = UsbTmc.search_devices()
    if debug:
        UsbTmc.print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    generator.open()

    generator_ac_curves: list[str] = [
        SCPI.set_source_frequency(1, round(frequency, 5)),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    generator.close()

    console.print(Panel(f"[blue]Rigol Frequency {frequency}[/]"))
