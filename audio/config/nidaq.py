from typing import Optional

import rich.repr

from audio.config import Config_Dict, IConfig


@rich.repr.auto
class FsMax(IConfig):
    name_config = "max_Fs"

    _value: Optional[float]

    def __init__(self, value: Optional[float] = None):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        fs_max = data.get_value([cls.name_config], float)

        if fs_max is not None:
            return cls(fs_max)
        else:
            return None

    @property
    def value(self) -> Optional[float]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class VoltageMax(IConfig):
    name_config: str = "max_voltage"

    _value: Optional[float]

    def __init__(self, value: Optional[float] = None):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        voltage_max = data.get_value([cls.name_config], float)

        if voltage_max is not None:
            return cls(voltage_max)
        else:
            return None

    @property
    def value(self) -> Optional[float]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class VoltageMin(IConfig):
    name_config: str = "min_voltage"

    _value: Optional[int]

    def __init__(self, value: Optional[int] = None):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        voltage_min = data.get_value([cls.name_config], float)

        if voltage_min is not None:
            return cls(voltage_min)
        else:
            return None

    @property
    def value(self) -> Optional[int]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class InputChannel(IConfig):
    name_config: str = "ch_input"

    _value: Optional[str]

    def __init__(self, value: Optional[str] = None):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        input_channel = data.get_value([cls.name_config], str)

        if input_channel is not None:
            return cls(input_channel)
        else:
            return None

    @property
    def value(self) -> Optional[str]:
        return self._value

    @value.setter
    def value(self, value: Optional[str]):
        self._value = value


@rich.repr.auto
class NiDaq:
    name_config = "nidaq"

    _max_Fs: Optional[FsMax]
    _max_voltage: Optional[VoltageMax]
    _min_voltage: Optional[VoltageMin]
    _ch_input: Optional[InputChannel]

    def __init__(
        self,
        max_Fs: Optional[FsMax] = None,
        max_voltage: Optional[VoltageMax] = None,
        min_voltage: Optional[VoltageMin] = None,
        ch_input: Optional[InputChannel] = None,
    ) -> None:

        self._max_Fs = max_Fs
        self._max_voltage = max_voltage
        self._min_voltage = min_voltage
        self._ch_input = ch_input

    @classmethod
    def from_value(
        cls,
        max_Fs: Optional[float] = None,
        max_voltage: Optional[float] = None,
        min_voltage: Optional[float] = None,
        # ex: "cDAQ9189-1CDBE0AMod1/ai1"
        ch_input: Optional[str] = None,
    ):
        max_Fs = FsMax(max_Fs)
        max_voltage = VoltageMax(max_voltage)
        min_voltage = VoltageMin(min_voltage)
        ch_input = InputChannel(ch_input)

        return cls(max_Fs, max_voltage, min_voltage, ch_input)

    @classmethod
    def from_config(cls, data: Config_Dict):
        nidaq = Config_Dict.from_dict(data.get_value([cls.name_config]))

        if nidaq is not None:

            fs_max = FsMax.from_dict(nidaq)
            max_voltage = VoltageMax.from_dict(nidaq)
            min_voltage = VoltageMin.from_dict(nidaq)
            ch_input = InputChannel.from_dict(nidaq)

            return cls(
                fs_max,
                max_voltage,
                min_voltage,
                ch_input,
            )
        else:
            return None

    def override(
        self,
        max_Fs: Optional[float] = None,
        max_voltage: Optional[float] = None,
        min_voltage: Optional[float] = None,
        # ex: "cDAQ9189-1CDBE0AMod1/ai1"
        ch_input: Optional[str] = None,
    ):
        if max_Fs is not None:
            self.max_Fs = max_Fs

        if max_voltage is not None:
            self.max_voltage = max_voltage

        if min_voltage is not None:
            self.min_voltage = min_voltage

        if ch_input is not None:
            self.ch_input = ch_input

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
