from time import sleep
from typing import List, Optional

import click
from rich.panel import Panel
from usbtmc import Instrument

from audio.console import console
from audio.math.rms import RMS
from audio.model.sampling import VoltageSampling
from audio.usb.usbtmc import UsbTmc
from audio.utility import trim_value
from audio.utility.scpi import SCPI, Bandwidth, Switch
from pandas import DataFrame
from audio.math.rms import RMSResult


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
    type=int,
    help="Amplitude.",
    required=True,
)
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
def read_rms(frequency, amplitude, n_sample_cli: int, debug: bool):
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

    sleep(1)

    Fs = trim_value(frequency * 10, max_value=1000000)

    n_sample: int = n_sample_cli

    rms_value: Optional[float]

    _, rms_value = RMS.rms(
        frequency=frequency,
        Fs=Fs,
        ch_input="cDAQ9189-1CDBE0AMod5/ai0",
        max_voltage=4,
        min_voltage=-4,
        number_of_samples=n_sample,
        time_report=False,
        save_file=None,
    )

    generator_ac_curves: List[str] = [
        SCPI.set_output(1, Switch.OFF),
    ]
    SCPI.exec_commands(generator, generator_ac_curves)
    generator.close()

    console.print(Panel("[blue]RMS {}[/]".format(rms_value)))


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
    type=int,
    help="Amplitude.",
    required=True,
)
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
def read_rms_loop(frequency, amplitude, n_sample_cli: int, debug: bool):
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

    sleep(1)

    Fs = trim_value(frequency * 10, max_value=1000000)

    n_sample: int = n_sample_cli

    while True:
        rms_value: Optional[float]

        _, rms_value = RMS.rms(
            frequency=frequency,
            Fs=Fs,
            ch_input="cDAQ9189-1CDBE0AMod5/ai0",
            max_voltage=10,
            min_voltage=-10,
            number_of_samples=n_sample,
            time_report=False,
            save_file=None,
            trim=False,
        )

        console.print(Panel("[blue]RMS {}[/]".format(rms_value)))


@click.command()
# @click.option(
#     "--frequency",
#     type=float,
#     help="Frequency.",
#     required=True,
# )
# @click.option(
#     "--amplitude",
#     type=float,
#     help="Amplitude.",
#     required=True,
# )
# @click.option(
#     "--n_sample",
#     "n_sample_cli",
#     type=int,
#     help="Amplitude.",
#     required=True,
# )
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
def read_rms_v2(
    # frequency,
    # amplitude,
    # n_sample_cli: int,
    debug: bool,
):
    amplitude = 1
    frequency = 1000
    n_sample = 200

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
        SCPI.set_output(2, Switch.OFF),
        SCPI.set_function_voltage_ac(),
        SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
        SCPI.set_source_voltage_amplitude(1, round(amplitude, 5)),
        SCPI.set_source_frequency(1, round(frequency, 5)),
    ]

    SCPI.exec_commands(generator, generator_configs)

    generator_ac_curves: List[str] = [
        SCPI.set_output(1, Switch.ON),
        SCPI.set_output(2, Switch.ON),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    sleep(1)

    from rich.prompt import Confirm

    Confirm.ask()

    from audio.device.cDAQ import ni9223

    nidaq = ni9223(n_sample)

    nidaq.create_task("Test")
    channels = [
        "cDAQ9189-1CDBE0AMod5/ai0",
        "cDAQ9189-1CDBE0AMod5/ai1",
    ]
    nidaq.add_ai_channel(channels)
    console.log(channels)

    Fs = trim_value(frequency * 20, max_value=1000000)
    nidaq.set_sampling_clock_timing(Fs)

    nidaq.task_start()
    voltages = nidaq.read_multi_voltages()
    nidaq.task_stop()

    generator_ac_curves: List[str] = [
        SCPI.set_output(1, Switch.OFF),
        SCPI.set_output(2, Switch.OFF),
    ]
    SCPI.exec_commands(generator, generator_ac_curves)
    generator.close()
    nidaq.task_close()

    voltages_sampling_1 = VoltageSampling.from_list(voltages[0], frequency, Fs)
    voltages_sampling_2 = VoltageSampling.from_list(voltages[1], frequency, Fs)

    result_1 = RMS.rms_v2(voltages_sampling_1, trim=False)
    result_2 = RMS.rms_v2(voltages_sampling_2, trim=False)
    console.log(f"RMS: {result_1.rms}")
    console.log(f"RMS: {result_2.rms}")

    import matplotlib.pyplot as plt

    plt.plot(result_1.voltages, color="#00ff00")
    plt.plot(result_2.voltages, color="#3050ff")
    # plt.show()
