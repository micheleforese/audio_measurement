from __future__ import annotations

import abc
from enum import Enum
from typing import TYPE_CHECKING, Literal, Self

from audio.console import console

if TYPE_CHECKING:
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
    def exec_commands(
        instr: UsbTmc,
        commands: list[str],
        *,
        debug: bool = False,
    ) -> None:
        for command in commands:
            if command.find("?") > 0:
                response = instr.ask(command)

                if not response:
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
        return False

    @staticmethod
    def check_output(output: int) -> bool:
        if output < 0:
            console.print(
                f"Invalid number for Output: {output}.\nMust be 0 or above",
                style="error",
            )
            return True
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
    def set_output_sync(source: int, switch: Switch) -> str:
        return f":OUTPut{source}:SYNC {switch.value}"

    @staticmethod
    def source_phase_init(source: int) -> str:
        return f":SOURce{source}:PHASe:INITiate"

    @staticmethod
    def source_phase_sync(source: int) -> str:
        return f":SOURce{source}:PHASe:SYNChronize"


class ScpiCommand(abc.ABC):
    _cmd: str = ""

    def __init__(self: Self, cmd: str | None = None) -> None:
        if cmd is not None:
            self._cmd = f"{cmd}:{self.cmd}"

    def __str__(self: Self) -> str:
        return self.cmd

    @property
    def cmd(self: Self) -> str:
        return self._cmd


class ScpiV2:
    @property
    def reset(self: Self) -> Literal["*RST"]:
        return "*RST"

    @property
    def trace(self: Self) -> ScpiTrace:
        return ScpiTrace()

    @property
    def source(self: Self) -> ScpiSource:
        return ScpiSource()

    @property
    def sense(self: Self) -> ScpiSense:
        return ScpiSense()

    @property
    def measure(self: Self) -> ScpiMeasure:
        return ScpiMeasure()


class ScpiMeasure(ScpiCommand):
    _cmd: str = "MEASure"

    @property
    def voltage(self: Self) -> ScpiVoltage:
        return ScpiVoltage(self.cmd)

    @property
    def current(self: Self) -> ScpiCurrent:
        return ScpiCurrent(self.cmd)


class ScpiVoltage(ScpiCommand):
    _cmd: str = "VOLTage"

    # def __call__(self, function: Function) -> str:

    @property
    def dc(self: Self) -> Self:
        return self

    def ask(self: Self) -> str:
        return f"{self._cmd}?"


class ScpiCurrent(ScpiCommand):
    _cmd: str = "CURRent"

    # def __call__(self, function: Function) -> str:

    @property
    def dc(self: Self) -> Self:
        return self

    def ask(self: Self) -> str:
        return f"{self._cmd}?"


class ScpiSense(ScpiCommand):
    _cmd: str = "SENSe"

    @property
    def average(self: Self) -> ScpiAverage:
        return ScpiAverage(self.cmd)


class ScpiTrace(ScpiCommand):
    _cmd: str = "TRACe"

    @property
    def clear(self: Self) -> str:
        return f"{self.cmd}:CLEar"


class ScpiSource(ScpiCommand):
    _cmd: str = "SOURce"

    @property
    def input_(self: Self) -> ScpiInput:
        return ScpiInput(self._cmd)

    @property
    def resistance(self: Self) -> ScpiResistance:
        return ScpiResistance(self._cmd)

    @property
    def function(self: Self) -> ScpiFunction:
        return ScpiFunction(self._cmd)


class ScpiAverage(ScpiCommand):
    _cmd: str = "AVERage"

    @property
    def count(self: Self) -> ScpiCount:
        return ScpiCount(self.cmd)


class ScpiCount(ScpiCommand):
    _cmd: str = "COUNt"
    MIN_COUNT = 2
    MAX_COUNT = 16

    def __call__(self: Self, num: int) -> str | None:
        if num >= self.MIN_COUNT and num <= self.MAX_COUNT:
            return f"{self._cmd} {num}"

        return None

    def ask(self: Self) -> str:
        return f"{self._cmd}?"


class ScpiInput(ScpiCommand):
    _cmd: str = "INPut"

    def __call__(self: Self, state: Switch) -> str:
        return f"{self._cmd} {state.value}"

    def ask(self: Self) -> str:
        return f"{self._cmd}?"


class ScpiResistance(ScpiCommand):
    _cmd: str = "RESistance"

    def __call__(self: Self, ohms: float) -> str:
        return f"{self._cmd} {ohms}"

    def ask(self: Self) -> str:
        return f"{self._cmd}?"


class ScpiFunction(ScpiCommand):
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
