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


@click.command()
@click.option(
    "--frequency",
    type=float,
    help="Frequency.",
    required=True,
)
@click.option(
    "--amplitude",
    type=float,
    help="Amplitude.",
    required=True,
)
@click.option(
    "--n_sample",
    "n_sample_cli",
    type=float,
    help="Amplitude.",
    required=True,
)
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
def read_rms(frequency, amplitude, n_sample_cli, debug: bool):
    # Asks for the 2 instruments
    list_devices: List[Instrument] = UsbTmc.search_devices()
    if debug:
        UsbTmc.print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    # Open the Instruments interfaces
    # Auto Close with the destructor
    generator.open()

    # Sets the Configuration for the Voltmeter
    generator_configs: list = [
        SCPI.clear(),
        SCPI.set_output(1, Switch.OFF),
        SCPI.set_function_voltage_ac(),
        SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
        SCPI.set_source_voltage_amplitude(1, round(amplitude, 5)),
        SCPI.set_source_frequency(1, round(frequency, 5)),
    ]

    SCPI.exec_commands(generator, generator_configs)

    generator_ac_curves: List[str] = [
        SCPI.set_output(1, Switch.ON),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    generator.close()

    sleep(1)

    Fs = trim_value(frequency * 100, max_value=100000)

    n_sample = n_sample_cli

    if Fs == 100000:
        n_sample = 900

    rms_value: Optional[float] = RMS.rms(
        frequency=frequency,
        Fs=Fs,
        ch_input="cDAQ9189-1CDBE0AMod1/ai1",
        max_voltage=4,
        min_voltage=-4,
        number_of_samples=n_sample,
        time_report=False,
        save_file=None,
    )

    console.print(Panel("[blue]RMS {}[/]".format(rms_value)))
