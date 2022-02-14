from enum import Enum
from typing import List
from cDAQ.UsbTmc import UsbTmc
from cDAQ.console import console
import usbtmc


class Switch(Enum):
    OFF = "OFF"
    ON = "ON"


class SCPI:

    def exec_commands(
        instr: usbtmc.Instrument,
        commands: List[str],
        debug: bool = False
    ):
        for command in commands:
            if(command.find("?") > 0):
                response = instr.ask(command)

                if(response == ""):
                    response = "NULL"

                console.print("{}:\t{}".format(command, response))
            else:
                instr.write(command)

                if(debug):
                    console.print(command)

    def clear() -> str:
        return "*CLS"

    def set_function_voltage_ac() -> str:
        return ":FUNCtion:VOLTage:AC"

    def set_output(n_output: int, output: Switch) -> str:
        return ":OUTPut{0} {1}".format(n_output, output.value)

    def set_voltage_ac_band(voltage_band: float) -> str:
        return ":VOLT:AC:BAND {}".format(voltage_band)

    def set_trig_source(source: str) -> str:
        return ":TRIG:SOUR {}".format(source)

    def set_trig_del_auto(output: Switch) -> str:
        return ":TRIG:DEL:AUTO {}".format(output.value)

    def set_freq_volt_rang_auto(output: Switch) -> str:
        return ":FREQ:VOLT:RANG:AUTO {}".format(output.value)

    def set_sample_source(source: str) -> str:
        return ":SAMP:SOUR {}".format(source)

    def set_sample_count(count: int) -> str:
        return ":SAMP:COUN {}".format(count)

    def check_source(source: int) -> bool:
        if(source < 0):
            console.print(
                "Invalid number for Source: {}.\nMust be 0 or above".format(
                    source),
                style="error")
            return 1
        else:
            return 0

    def check_output(output: int) -> bool:
        if(output < 0):
            console.print(
                "Invalid number for Output: {}.\nMust be 0 or above".format(
                    output),
                style="error")
            return 1
        else:
            return 0

    def set_source_voltage_amplitude(source: int, amplitude_pp: float) -> str:
        if(SCPI.check_source(source)):
            console.print("Setting Source to 0", style="warning")
            source = 0

        return ":SOURce{0}:VOLTAGE:AMPLitude {1}".format(source, amplitude_pp)

    def set_source_frequency(source: int, frequency: float) -> str:
        if(SCPI.check_source(source)):
            console.print("Setting Source to 0", style="warning")
            source = 0

        return ":SOURce{0}:FREQ {1}".format(source, frequency)

    def set_output_impedance(output: int, impedance: float) -> str:
        if(SCPI.check_output(output)):
            console.print("Setting output to 0", style="warning")
            source = 0

        return ":OUTPut{0}:IMPedance {1}".format(output, impedance)

    def set_output_load(output: int, load: str) -> str:
        if(SCPI.check_output(output)):
            console.print("Setting output to 0", style="warning")
            source = 0

        return ":OUTPut{0}:LOAD {1}".format(output, load)

    def set_source_phase(source: int, phase: float) -> str:
        if(SCPI.check_source(source)):
            console.print("Setting source to 0", style="warning")
            source = 0

        return ":SOURce{0}:PHASe {1}".format(source, phase)
