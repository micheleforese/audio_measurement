import time
from typing import List, Tuple

import click
import matplotlib.ticker as ticker
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from rich.prompt import Confirm, Prompt, FloatPrompt

from audio.config.type import Range
from audio.console import console
from audio.math.algorithm import LogarithmicScale
from audio.math.rms import RMS, RMSResult, VoltageSampling
from audio.model.sweep import SweepData
from audio.usb.usbtmc import Instrument, UsbTmc
from audio.utility import trim_value
from audio.utility.interrupt import InterruptHandler
from audio.utility.scpi import SCPI, Bandwidth, Switch
from audio.utility.timer import timeit


def say_hi():
    console.print("HI!!")


@click.command(help="Test for Timer class")
def testTimer():

    decorator = timeit()
    timed_say_hi = decorator(say_hi)

    timed_say_hi()

    timeit()(say_hi)()


@click.command()
def print_devices():

    list = UsbTmc.search_devices()

    instr = list[-1]
    print(instr.ask("*IDN?"))

    console.print(list)


@click.command()
def phase_analysis():

    freq_min: float = float(
        Prompt.ask("Frequency Min (Hz) [10]", show_default=True, default=10)
    )
    freq_max: float = float(
        Prompt.ask("Frequency Max (Hz) [200_000]", show_default=True, default=200_000)
    )
    frequency_range = Range[float](freq_min, freq_max)
    amplitude: float = float(
        Prompt.ask("Amplitude (Vpp) [1]", show_default=True, default=1.0)
    )
    points_per_decade: int = int(
        Prompt.ask("Points per decade [10]", show_default=True, default=10)
    )
    n_sample: int = int(
        Prompt.ask("Sample per point [200]", show_default=True, default=200)
    )
    Fs_multiplier: int = int(
        Prompt.ask("Fs multiplier [50]", show_default=True, default=50)
    )
    interpolation_rate: int = int(
        Prompt.ask("interpolation rate [20]", show_default=True, default=20)
    )

    with InterruptHandler() as h:
        # Asks for the 2 instruments
        list_devices: List[Instrument] = UsbTmc.search_devices()

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
            SCPI.set_source_frequency(1, round(frequency_range.min, 5)),
        ]

        SCPI.exec_commands(generator, generator_configs)

        generator_ac_curves: List[str] = [
            SCPI.set_output(1, Switch.ON),
        ]

        SCPI.exec_commands(generator, generator_ac_curves)
        time.sleep(1)

        log_scale: LogarithmicScale = LogarithmicScale(
            frequency_range.min,
            frequency_range.max,
            points_per_decade,
        )

        from audio.device.cDAQ import ni9223

        nidaq = ni9223(n_sample)

        nidaq.create_task("Test")
        channels = [
            "cDAQ9189-1CDBE0AMod5/ai1",
            "cDAQ9189-1CDBE0AMod5/ai3",
        ]
        nidaq.add_ai_channel(channels)

        phase_offset_list: List[float] = []

        import matplotlib.pyplot as plt
        from rich.progress import track

        for frequency in track(
            log_scale.f_list,
            total=len(log_scale.f_list),
            console=console,
        ):
            generator_configs: list = [
                SCPI.set_source_frequency(1, round(frequency, 5)),
            ]

            SCPI.exec_commands(generator, generator_configs)
            Fs = trim_value(frequency * Fs_multiplier, max_value=1000000)
            nidaq.set_sampling_clock_timing(Fs)

            nidaq.task_start()
            voltages = nidaq.read_multi_voltages()
            nidaq.task_stop()
            voltages_sampling_0 = VoltageSampling.from_list(
                voltages[0][100:], frequency, Fs
            )
            voltages_sampling_1 = VoltageSampling.from_list(
                voltages[1][100:], frequency, Fs
            )

            result_0: RMSResult = RMS.rms_v2(
                voltages_sampling_0,
                interpolation_rate=interpolation_rate,
                trim=False,
            )
            result_1: RMSResult = RMS.rms_v2(
                voltages_sampling_1,
                interpolation_rate=interpolation_rate,
                trim=False,
            )

            voltages_sampling_0 = VoltageSampling.from_list(
                result_0.voltages,
                input_frequency=frequency,
                sampling_frequency=Fs * interpolation_rate,
            )
            voltages_sampling_1 = VoltageSampling.from_list(
                result_1.voltages,
                input_frequency=frequency,
                sampling_frequency=Fs * interpolation_rate,
            )

            from audio.math.phase import phase_offset_v2

            phase_offset = phase_offset_v2(voltages_sampling_0, voltages_sampling_1)
            from audio.constant import APP_TEST

            APP_TEST.mkdir(exist_ok=True, parents=True)

            if phase_offset is None:

                voltages_sampling_0.save(APP_TEST / f"{frequency:.5f}_0.csv")
                voltages_sampling_1.save(APP_TEST / f"{frequency:.5f}_1.csv")

            phase_offset_list.append(phase_offset)

            if h.interrupted:
                break

        generator_ac_curves: List[str] = [
            SCPI.set_output(1, Switch.OFF),
            SCPI.set_output(2, Switch.OFF),
        ]
        SCPI.exec_commands(generator, generator_ac_curves)
        generator.close()
        nidaq.task_close()

        plot: Tuple[Figure, Axes] = plt.subplots(figsize=(16 * 2, 9 * 2), dpi=600)

        fig: Figure
        axes: Axes
        fig, axes = plot

        axes.semilogx(
            log_scale.f_list,
            phase_offset_list,
            ".-",
            linewidth=2,
        )

        title = Prompt.ask("Plot Title")
        axes.set_title("LA-125-2 CH_B 0dB")
        axes.set_title("LA-125-2 CH_B 15dB")
        axes.set_title("LA-125-2 CH_B 30dB")
        axes.set_title(
            f"{title}, A: {amplitude:0.2f} Vpp",
            fontsize=50,
            pad=50,
        )

        axes.set_xlabel(
            "Frequency ($Hz$)",
            fontsize=40,
            labelpad=20,
        )
        axes.set_ylabel(
            "Angle ($deg$)",
            fontsize=40,
            labelpad=20,
        )

        axes.tick_params(
            axis="both",
            labelsize=22,
        )
        axes.tick_params(axis="x", rotation=45)
        axes.grid(True, linestyle="-", which="both", color="0.7")

        def logMinorFormatFunc(x, pos):
            return "{:.0f}".format(x)

        logMinorFormat = ticker.FuncFormatter(logMinorFormatFunc)

        # X Axis - Major
        # axes.xaxis.set_major_locator(logLocator)
        axes.xaxis.set_major_formatter(logMinorFormat)

        from audio.constant import APP_AUDIO_TEST

        directory = APP_AUDIO_TEST / "LA-125_2ch"
        directory.mkdir(exist_ok=True, parents=True)

        from datetime import datetime

        time_now = datetime.now()
        file_name = f'{time_now.strftime("%Y.%m.%d-%H:%M:%S")} {title}'

        file = directory / f"{file_name}.pdf"

        fig.savefig(file)
        console.log(f"[FILE:SAVED]: {file}")


@click.command()
def instrument():

    import usbtmc
    import usb
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
        list_devices: List[Instrument] = UsbTmc.search_devices()

        if len(list_devices) < 1:
            raise Exception("UsbTmc devices not found.")

        UsbTmc.print_devices_list(list_devices)

        generator: UsbTmc = UsbTmc(list_devices[0])

    except Exception as e:
        console.print(f"{e}")


@click.command()
def bk_precision():
    console.log("BK PRECISION")
    from rich import inspect
    from rich.panel import Panel
    import pyvisa
    from audio.utility.scpi import SCPI_v2, Function

    scpi = SCPI_v2()

    rm = pyvisa.ResourceManager("@py")
    devs = rm.list_resources()

    # dev_generator: pyvisa.resources.Resource = rm.open_resource(
    #     "USB0::6833::1603::DG8A230500644::0::INSTR"
    # )

    # dev_generator.write(f":SOURce1:FREQ 1000")

    # SCPI
    # console.log(scpi.measure.voltage.ask())
    # console.log(scpi.measure.voltage.dc.ask())
    # console.log(scpi.measure.current.ask())
    # console.log(scpi.measure.current.dc.ask())

    # ---------- ELECTRONIC LOAD ----------
    dev_elec_load: pyvisa.resources.usb.USBInstrument = rm.open_resource(
        "USB0::11975::34816::800872011777270028::0::INSTR"
    )
    dev_elec_load.timeout = 5000
    # dev_elec_load.write(scpi.reset)
    # dev_elec_load.write(scpi.trace.clear)
    dev_elec_load.write(scpi.source.resistance(166))
    dev_elec_load.write(scpi.source.input(Switch.ON))
    dev_elec_load.write(scpi.source.function(Function.RESISTANCE))
    dev_elec_load.write(scpi.sense.average.count(16))

    # ---------- POWER SUPPLY ----------
    dev_power_supply: pyvisa.resources.serial.SerialInstrument = rm.open_resource(
        "ASRL/dev/ttyUSB0::INSTR", open_timeout=5
    )
    dev_power_supply.baud_rate = 9600
    dev_power_supply.timeout = 5000
    # dev_power_supply.write("*RST")
    dev_power_supply.write("INSTrument FIRst")
    response = dev_power_supply.query("INSTrument?")
    console.log(response)
    dev_power_supply.write("VOLT 10V")
    dev_power_supply.write("CURR 0.03A")
    dev_power_supply.write("OUTP 1")
    # dev_power_supply.write("*OPC")
    # dev_power_supply.write("*CLS")
    dev_power_supply.write("SYSTem:LOCal")
    # dev_power_supply.write("SYSTem:REMote")

    import matplotlib.pyplot as plt
    import numpy as np
    from rich.prompt import Confirm

    for t in [1]:
        console.print(Panel(f"Time: {t}s"))
        dev_elec_load.write(scpi.source.resistance(986))
        # dev_elec_load.write(scpi.trace.clear)

        Confirm.ask("Ready?")
        time.sleep(3)

        res_list: List[float] = []
        power_list: List[float] = []

        for resistance in reversed(range(700, 1300, 10)):
            dev_elec_load.write(scpi.source.resistance(resistance))
            # dev_elec_load.write(scpi.trace.clear)
            time.sleep(t)

            dev_elec_load.query_delay = 0.1
            # voltage = float(dev_elec_load.query(scpi.measure.voltage.ask()))
            current = float(dev_elec_load.query(scpi.measure.current.ask()))

            voltage = 1

            power: float = voltage * current

            console.log(
                f"[MEASUREMENT] OHM: {resistance:0.5f}, VOLTAGE: {voltage:0.5f}V, CURRENT: {current:0.5f}A, POWER: {power:.05f} W"
            )
            res_list.append(resistance)
            power_list.append(power)

        plt.plot(res_list, power_list, ".-", label=f"t = {t:.1f}s")

        console.log(f"MAX Resistance: {max(power_list):.6f}")
    dev_elec_load.write("SYSTem:LOCal")
    plt.legend(loc="best")
    plt.show()

    exit()
