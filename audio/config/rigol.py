from typing import Optional

import rich

from audio.config import Config_Dict, IConfig


@rich.repr.auto
class AmplitudePeakToPeak(IConfig):

    name_config: str = "amplitude_pp"

    _value: Optional[float]

    def __init__(
        self,
        value: Optional[float] = None,
    ):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        amplitude_pp = data.get_value([cls.name_config], float)

        if amplitude_pp is not None:
            return cls(amplitude_pp)
        else:
            return None

    def __rich_repr__(self):
        yield self.name_config, self.value

    @property
    def value(self) -> Optional[float]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class Rigol:
    name_config: str = "rigol"

    _amplitude_pp: Optional[AmplitudePeakToPeak]

    def __init__(
        self,
        amplitude_pp: Optional[AmplitudePeakToPeak] = None,
    ) -> None:

        self._amplitude_pp = amplitude_pp

    @classmethod
    def from_value(
        cls,
        amplitude_pp: Optional[float] = None,
    ):
        amplitude_pp = AmplitudePeakToPeak(amplitude_pp)

        return cls(amplitude_pp)

    @classmethod
    def from_config(cls, data: Config_Dict):
        rigol = Config_Dict.from_dict(data.get_value([cls.name_config]))

        if rigol is not None:
            amplitude_pp = AmplitudePeakToPeak.from_dict(rigol)

            return cls(amplitude_pp)
        else:
            return None

    def override(
        self,
        amplitude_pp: Optional[float] = None,
    ):
        if amplitude_pp is not None:
            self._amplitude_pp = amplitude_pp

    @property
    def amplitude_pp(self) -> Optional[float]:
        return self._amplitude_pp.value
