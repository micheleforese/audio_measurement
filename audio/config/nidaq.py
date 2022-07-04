import rich.repr
from audio.config import IConfig


@rich.repr.auto
class FsMax(IConfig):
    _name_config: str = "max_Fs"

    _value: float

    def __init__(self, value: float):
        self._value = value

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> float:
        return self._value


@rich.repr.auto
class VoltageMax(IConfig):
    _name_config: str = "max_voltage"

    _value: float

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> float:
        return self._value


@rich.repr.auto
class VoltageMin(IConfig):
    _name_config: str = "min_voltage"

    _value: int

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> int:
        return self._value


@rich.repr.auto
class InputChannel(IConfig):
    _name_config: str = "ch_input"

    _value: str

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> str:
        return self._value


@rich.repr.auto
class NiDaq:

    _max_Fs: FsMax
    _max_voltage: VoltageMax
    _min_voltage: VoltageMin
    _ch_input: InputChannel

    def __init__(
        self,
        max_Fs=102000,
        max_voltage=4,
        min_voltage=-4,
        ch_input="cDAQ9189-1CDBE0AMod1/ai1",
    ) -> None:
        self._max_Fs = FsMax(max_Fs)
        self._max_voltage = VoltageMax(max_voltage)
        self._min_voltage = VoltageMin(min_voltage)
        self._ch_input = InputChannel(ch_input)

    @property
    def max_Fs(self) -> float:
        return self._max_Fs.value

    @property
    def max_voltage(self) -> float:
        return self._max_voltage.value

    @property
    def min_voltage(self) -> float:
        return self._min_voltage.value

    @property
    def ch_input(self) -> str:
        return self._ch_input.value
