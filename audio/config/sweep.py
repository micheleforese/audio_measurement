from __future__ import annotations

import pathlib
from typing import Any, Dict, List

from audio.config.nidaq import NiDaqConfig
from audio.config.plot import PlotConfig

from audio.config.rigol import RigolConfig
from audio.config.sampling import SamplingConfig
from audio.type import Dictionary, Option
from enum import Enum, auto, unique
import xml.etree.ElementTree as ET
from audio.console import console


@unique
class SweepConfigEnum(Enum):
    RIGOL = auto()
    NI_DAQ = auto()
    SAMPLING = auto()
    PLOT = auto()


class SweepConfig(Dictionary):
    def __rich_repr__(self):
        yield "rigol", self.rigol
        yield "nidaq", self.nidaq
        yield "sampling", self.sampling
        yield "plot", self.plot

    @classmethod
    def from_file(
        cls,
        config_file_path: pathlib.Path,
    ) -> Option[SweepConfig]:

        data = Dictionary.from_json(config_file_path)

        if data.exists():
            return Option[SweepConfig](cls(data.value))

        return Option[SweepConfig].null()

    @classmethod
    def from_dict(cls, dictionary: Dictionary):
        return Option[SweepConfig](cls(dictionary))

    def exists(self, config: SweepConfigEnum) -> bool:
        match config:
            case SweepConfigEnum.RIGOL:
                return not self.rigol.is_null
            case SweepConfigEnum.NI_DAQ:
                return not self.nidaq.is_null
            case SweepConfigEnum.SAMPLING:
                return not self.sampling.is_null
            case SweepConfigEnum.PLOT:
                return not self.plot.is_null

    @property
    def rigol(self) -> Option[RigolConfig]:
        from audio.console import console

        console.print(self.get_dict())
        data = self.get_property("rigol")
        if data.exists():
            return Option[RigolConfig](RigolConfig(dict(data.value)))
        return Option[RigolConfig].null()

    @property
    def nidaq(self) -> Option[NiDaqConfig]:
        return self.get_property("nidaq", NiDaqConfig)

    @property
    def sampling(self) -> Option[SamplingConfig]:
        return self.get_property("sampling", SamplingConfig)

    @property
    def plot(self) -> Option[PlotConfig]:
        return self.get_property("plot", PlotConfig)


class SweepConfigXML:

    config: ET.ElementTree

    def __init__(self, tree: ET.ElementTree) -> None:
        root = ET.Element("config")
        ET.SubElement(root, "rigol").text = "ciao"
        ET.indent(root)

        self.config = ET.ElementTree(root)

        console.print(print(ET.tostring(self.config.getroot(), encoding="unicode")))

    @classmethod
    def from_file():