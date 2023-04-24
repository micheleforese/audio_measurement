from __future__ import annotations

import abc
from enum import Enum
from typing import Self

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
    def exec_commands(instr: UsbTmc, commands: list[str], debug: bool = False):
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
    def set_voltage_ac_bandwidth(bandwidth: Bandwidth | float) -> str:
        if type(bandwidth) is Bandwidth:
            return f"VOLTage:AC:BANDwidth {bandwidth.value}"
        else:
            return f"VOLTage:AC:BANDwidth {bandwidth}"

    @staticmethod
    def set_output(n_output: int, output: Switch) -> str:
        return f":OUTPut{n_output} {output.value}"

    @staticmethod
    def set_voltage_ac_band(voltage_band: float) -> str:
        return f":VOLT:AC:BAND {voltage_band}"

    @staticmethod
    def set_trig_source(source: str) -> str:
        return f":TRIG:SOUR {source}"

    @staticmethod
    def set_trig_del_auto(output: Switch) -> str:
        return f":TRIG:DEL:AUTO {output.value}"

    @staticmethod
    def set_freq_volt_rang_auto(output: Switch) -> str:
        return f":FREQ:VOLT:RANG:AUTO {output.value}"

    @staticmethod
    def set_sample_source(source: str) -> str:
        return f":SAMP:SOUR {source}"

    @staticmethod
    def set_sample_count(count: int) -> str:
        return f":SAMP:COUN {count}"

    @staticmethod
    def check_source(source: int) -> bool:
        if source < 0:
            console.print(
                f"Invalid number for Source: {source}.\nMust be 0 or above",
                style="error",
            )
            return True
        else:
            return False

    @staticmethod
    def check_output(output: int) -> bool:
        if output < 0:
            console.print(
                f"Invalid number for Output: {output}.\nMust be 0 or above",
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

        return f":SOURce{source}:VOLTAGE:AMPLitude {amplitude_pp}"

    @staticmethod
    def set_source_frequency(source: int, frequency: float) -> str:
        if SCPI.check_source(source):
            console.print("Setting Source to 0", style="warning")
            source = 0

        return f":SOURce{source}:FREQ {frequency}"

    @staticmethod
    def set_output_impedance(output: int, impedance: float) -> str:
        if SCPI.check_output(output):
            console.print("Setting output to 0", style="warning")
            output = 0

        return f":OUTPut{output}:IMPedance {impedance}"

    @staticmethod
    def set_output_load(output: int, load: str) -> str:
        if SCPI.check_output(output):
            console.print("Setting output to 0", style="warning")
            output = 0

        return f":OUTPut{output}:LOAD {load}"

    @staticmethod
    def set_source_phase(source: int, phase: float) -> str:
        if SCPI.check_source(source):
            console.print("Setting source to 0", style="warning")
            source = 0

        return f":SOURce{source}:PHASe {phase}"

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


class SCPI_Command(abc.ABC):
    _cmd: str = ""

    def __init__(self, cmd: str | None = None) -> None:
        if cmd is not None:
            self._cmd = f"{cmd}:{self.cmd}"

    def __str__(self) -> str:
        return self.cmd

    @property
    def cmd(self):
        return self._cmd


class SCPI_v2:
    @property
    def reset(self):
        return "*RST"

    @property
    def trace(self):
        return SCPI_trace()

    @property
    def source(self):
        return SCPI_source()

    @property
    def sense(self):
        return SCPI_sense()

    @property
    def measure(self):
        return SCPI_measure()


class SCPI_measure(SCPI_Command):
    _cmd: str = "MEASure"

    @property
    def voltage(self):
        return SCPI_voltage(self.cmd)

    @property
    def current(self):
        return SCPI_current(self.cmd)


class SCPI_voltage(SCPI_Command):
    _cmd: str = "VOLTage"

    # def __call__(self, function: Function) -> str:

    @property
    def dc(self):
        return self

    def ask(self):
        return f"{self._cmd}?"


class SCPI_current(SCPI_Command):
    _cmd: str = "CURRent"

    # def __call__(self, function: Function) -> str:

    @property
    def dc(self):
        return self

    def ask(self):
        return f"{self._cmd}?"


class SCPI_sense(SCPI_Command):
    _cmd: str = "SENSe"

    @property
    def average(self):
        return SCPI_average(self.cmd)


class SCPI_trace(SCPI_Command):
    _cmd: str = "TRACe"

    @property
    def clear(self) -> str:
        return f"{self.cmd}:CLEar"


class SCPI_source(SCPI_Command):
    _cmd: str = "SOURce"

    @property
    def input(self):
        return SCPI_input(self._cmd)

    @property
    def resistance(self):
        return SCPI_resistance(self._cmd)

    @property
    def function(self):
        return SCPI_function(self._cmd)


class SCPI_average(SCPI_Command):
    _cmd: str = "AVERage"

    @property
    def count(self):
        return SCPI_count(self.cmd)


class SCPI_count(SCPI_Command):
    _cmd: str = "COUNt"

    def __call__(self, num: int) -> str | None:
        if num >= 2 and num <= 16:
            return f"{self._cmd} {num}"

        return None

    def ask(self):
        return f"{self._cmd}?"


class SCPI_input(SCPI_Command):
    _cmd: str = "INPut"

    def __call__(self, state: Switch) -> str:
        return f"{self._cmd} {state.value}"

    def ask(self):
        return f"{self._cmd}?"


class SCPI_resistance(SCPI_Command):
    _cmd: str = "RESistance"

    def __call__(self, ohms: float) -> str:
        return f"{self._cmd} {ohms}"

    def ask(self):
        return f"{self._cmd}?"


class SCPI_function(SCPI_Command):
    _cmd: str = "FUNCtion"

    def __call__(self: Self, function: Function) -> str:
        return f"{self._cmd} {function.value}"

    def ask(self: Self) -> str:
        return f"{self._cmd}?"


class Function(Enum):
    CURRENT = "CURRent"
    RESISTANCE = "RESistance"
    VOLTAGE = "VOLTage"
    POWER = "POWer"
