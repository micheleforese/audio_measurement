import time

import click

from audio.console import console
from audio.utility.scpi import Switch


@click.command()
def bk_precision():
    console.log("BK PRECISION")
    import pyvisa
    from rich.panel import Panel

    from audio.utility.scpi import Function, SCPI_v2

    scpi = SCPI_v2()

    rm = pyvisa.ResourceManager("@py")
    rm.list_resources()

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
    from rich.prompt import Confirm

    for t in [1]:
        console.print(Panel(f"Time: {t}s"))
        dev_elec_load.write(scpi.source.resistance(986))
        # dev_elec_load.write(scpi.trace.clear)

        Confirm.ask("Ready?")
        time.sleep(3)

        res_list: list[float] = []
        power_list: list[float] = []

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
