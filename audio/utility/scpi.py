from enum import Enum
from typing import List, Union

from audio.console import console
from audio.usb.usbtmc import UsbTmc


class Switch(Enum):
    OFF = "OFF"
    ON = "ON"


class Bandwidth(Enum):
    MIN = "MIN"
    MAX = "MAX"
    DEF = "DEF"


class SCPI:
    @staticmethod
    def exec_commands(instr: UsbTmc, commands: List[str], debug: bool = False):
        for command in commands:
            if command.find("?") > 0:
                response = instr.ask(command)

                if response == "":
                    response = "NULL"

                console.print(f"{command}:\t{response}")
            else:
                instr.write(command)

                if debug:
                    console.print(command)

    @staticmethod
    def clear() -> str:
        return "*CLS"

    @staticmethod
    def reset() -> str:
        return "*RST"

    @staticmethod
    def set_function_voltage_ac() -> str:
        return ":FUNCtion:VOLTage:AC"

    @staticmethod
    def set_voltage_ac_bandwidth(bandwidth: Union[Bandwidth, float]) -> str:
        if type(bandwidth) is Bandwidth:
            return "VOLTage:AC:BANDwidth {}".format(bandwidth.value)
        else:
            return "VOLTage:AC:BANDwidth {}".format(bandwidth)

    @staticmethod
    def set_output(n_output: int, output: Switch) -> str:
        return ":OUTPut{0} {1}".format(n_output, output.value)

    @staticmethod
    def set_voltage_ac_band(voltage_band: float) -> str:
        return ":VOLT:AC:BAND {}".format(voltage_band)

    @staticmethod
    def set_trig_source(source: str) -> str:
        return ":TRIG:SOUR {}".format(source)

    @staticmethod
    def set_trig_del_auto(output: Switch) -> str:
        return ":TRIG:DEL:AUTO {}".format(output.value)

    @staticmethod
    def set_freq_volt_rang_auto(output: Switch) -> str:
        return ":FREQ:VOLT:RANG:AUTO {}".format(output.value)

    @staticmethod
    def set_sample_source(source: str) -> str:
        return ":SAMP:SOUR {}".format(source)

    @staticmethod
    def set_sample_count(count: int) -> str:
        return ":SAMP:COUN {}".format(count)

    @staticmethod
    def check_source(source: int) -> bool:
        if source < 0:
            console.print(
                "Invalid number for Source: {}.\nMust be 0 or above".format(source),
                style="error",
            )
            return True
        else:
            return False

    @staticmethod
    def check_output(output: int) -> bool:
        if output < 0:
            console.print(
                "Invalid number for Output: {}.\nMust be 0 or above".format(output),
                style="error",
            )
            return True
        else:
            return False

    @staticmethod
    def set_source_voltage_amplitude(source: int, amplitude_pp: float) -> str:
        if SCPI.check_source(source):
            console.print("Setting Source to 0", style="warning")
            source = 0

        return ":SOURce{0}:VOLTAGE:AMPLitude {1}".format(source, amplitude_pp)

    @staticmethod
    def set_source_frequency(source: int, frequency: float) -> str:
        if SCPI.check_source(source):
            console.print("Setting Source to 0", style="warning")
            source = 0

        return ":SOURce{0}:FREQ {1}".format(source, frequency)

    @staticmethod
    def set_output_impedance(output: int, impedance: float) -> str:
        if SCPI.check_output(output):
            console.print("Setting output to 0", style="warning")
            output = 0

        return ":OUTPut{0}:IMPedance {1}".format(output, impedance)

    @staticmethod
    def set_output_load(output: int, load: str) -> str:
        if SCPI.check_output(output):
            console.print("Setting output to 0", style="warning")
            output = 0

        return ":OUTPut{0}:LOAD {1}".format(output, load)

    @staticmethod
    def set_source_phase(source: int, phase: float) -> str:
        if SCPI.check_source(source):
            console.print("Setting source to 0", style="warning")
            source = 0

        return ":SOURce{0}:PHASe {1}".format(source, phase)

    @staticmethod
    def ask_voltage_bandwidth() -> str:
        return "VOLTage:AC:BANDwidth?"

    @staticmethod
    def set_output_sync(source: int, switch: Switch):
        return f":OUTPut{source}:SYNC {switch.value}"

    @staticmethod
    def source_phase_init(source: int):
        return f":SOURce{source}:PHASe:INITiate"

    @staticmethod
    def source_phase_sync(source: int):
        return f":SOURce{source}:PHASe:SYNChronize"
