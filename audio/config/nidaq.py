from typing import Optional

import rich.repr

from audio.config import Config_Dict, IConfig
from audio.type import Dictionary, Option


@rich.repr.auto
class NiDaqConfig(Dictionary):
    def __rich_repr__(self):

        if not self.max_Fs.is_null:
            yield "max_Fs", self.max_Fs.value

        if not self.max_voltage.is_null:
            yield "max_voltage", self.max_voltage.value

        if not self.min_voltage.is_null:
            yield "min_voltage", self.min_voltage.value

        if not self.ch_input.is_null:
            yield "ch_input", self.ch_input.value

    @property
    def max_Fs(self) -> Option[float]:

        max_Fs: Option[float] = self.get_property("max_Fs", float)

        if not max_Fs.is_null:
            return Option[float](max_Fs.value)

        return Option[float].null()

    @property
    def max_voltage(self) -> Option[float]:

        max_voltage: Option[float] = self.get_property("max_voltage", float)

        if not max_voltage.is_null:
            return Option[float](max_voltage.value)

        return Option[float].null()

    @property
    def min_voltage(self) -> Option[float]:

        min_voltage: Option[float] = self.get_property("min_voltage", float)

        if not min_voltage.is_null:
            return Option[float](min_voltage.value)

        return Option[float].null()

    @property
    def ch_input(self) -> Option[str]:

        ch_input: Option[str] = self.get_property("ch_input", str)

        if not ch_input.is_null:
            return Option[str](ch_input.value)

        return Option[str].null()
