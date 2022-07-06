from typing import Optional

import rich

from audio.config import Config_Dict, IConfig


@rich.repr.auto
class AmplitudePeakToPeak(IConfig):

    _name_config: str = "amplitude_pp"

    _value: Optional[float]

    def __init__(
        self,
        value: Optional[float] = None,
    ):
        self._value = value

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> Optional[float]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class Rigol:
    _name_config: str = "rigol"

    _amplitude_pp: AmplitudePeakToPeak

    def __init__(
        self,
        amplitude_pp: Optional[float] = None,
    ) -> None:
        self._amplitude_pp.value = AmplitudePeakToPeak(amplitude_pp)

    def init_from_config(self, data: Config_Dict):
        self.amplitude_pp = data.get_value(
            [self.name_config, self._amplitude_pp.name_config]
        )

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def amplitude_pp(self) -> Optional[float]:
        return self._amplitude_pp

    @amplitude_pp.setter
    def amplitude_pp(self, value: Optional[float]):
        self._amplitude_pp = value
