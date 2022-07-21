from typing import Optional

import rich.repr

from audio.config import Config_Dict, IConfig
from audio.type import Dictionary, Option


class NiDaqConfig(Dictionary):
    def __rich_repr__(self):

        yield "max_Fs", self.max_Fs

        yield "max_voltage", self.max_voltage

        yield "min_voltage", self.min_voltage

        yield "ch_input", self.ch_input

    @property
    def max_Fs(self) -> Option[float]:
        return self.get_property("max_Fs", float)

    @property
    def max_voltage(self) -> Option[float]:
        return self.get_property("max_voltage", float)

    @property
    def min_voltage(self) -> Option[float]:
        return self.get_property("min_voltage", float)

    @property
    def ch_input(self) -> Option[str]:
        return self.get_property("ch_input", str)
