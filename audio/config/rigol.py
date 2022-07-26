from enum import Enum, auto, unique
from typing import Any, Dict, Optional

import rich

from audio.config import Config_Dict, IConfig
from audio.type import Dictionary, Option


from audio.console import console


@unique
class RigolConfigEnum(Enum):
    AMPLITUDE_PEAK_TO_PEAK = auto()


class RigolConfig(Dictionary):
    def __rich_repr__(self):
        yield "amplitude_pp", self.amplitude_pp

    def exists(self, config: RigolConfigEnum) -> bool:
        match config:
            case RigolConfigEnum.AMPLITUDE_PEAK_TO_PEAK:
                return not self.amplitude_pp.is_null

    @property
    def amplitude_pp(self) -> Option[float]:
        return self.get_property("amplitude_pp", float)

    def set_amplitude_peak_to_peak(
        self,
        amplitude_pp: float,
        override: bool = False,
    ) -> Option[float]:
        if not self.exists(RigolConfigEnum.AMPLITUDE_PEAK_TO_PEAK) or override:
            self.get_dict().update({"amplitude_pp": amplitude_pp})
        return self.amplitude_pp
