from typing import Optional
import rich.repr
from audio.console import console
from audio.config import Config_Dict, IConfig
from audio.type import Dictionary, Option


class SamplingConfig(Dictionary):
    def __rich_repr__(self):
        yield "n_fs", self.n_fs
        yield "points_per_decade", self.points_per_decade
        yield "f_min", self.f_min
        yield "f_max", self.f_max

    @property
    def n_fs(self) -> Option[float]:

        return Option[float](self.get_property("n_fs", float))

    @property
    def points_per_decade(self) -> Option[float]:

        return Option[float](self.get_property("points_per_decade", float))

    @property
    def number_of_samples(self) -> Option[int]:

        return Option[int](self.get_property("number_of_samples", int))

    @property
    def f_min(self) -> Option[float]:

        return Option[float](self.get_property("f_min", float))

    @property
    def f_max(self) -> Option[float]:

        return Option[float](self.get_property("f_max", float))
