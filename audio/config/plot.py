from typing import Optional, Tuple

import rich.repr

from audio.config import Config_Dict, IConfig
from audio.config.type import Range
from audio.type import Dictionary, Option


class PlotConfig(Dictionary):
    def __rich_repr__(self):
        yield "y_offset", self.y_offset
        yield "y_limit", self.y_limit
        yield "x_limit", self.x_limit
        yield "interpolation_rate", self.interpolation_rate
        yield "dpi", self.dpi

    @property
    def y_offset(self) -> Option[float]:
        return Option[float](self.get_property("y_offset", float))

    @property
    def y_limit(self) -> Option[Range]:
        return Option[Range](
            Range.from_tuple(self.get_property("y_limit", Tuple[float, float]))
        )

    @property
    def x_limit(self) -> Option[float]:
        return Option[Range](
            Range.from_tuple(self.get_property("x_limit", Tuple[float, float]))
        )

    @property
    def interpolation_rate(self) -> Option[float]:
        return Option[float](self.get_property("interpolation_rate", float))

    @property
    def dpi(self) -> Option[float]:
        return Option[float](self.get_property("dpi", float))
