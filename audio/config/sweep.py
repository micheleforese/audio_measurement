from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Optional

import rich
from audio.config import load_json_config

from audio.config.nidaq import NiDaqConfig, NiDaqConfigXML
from audio.config.plot import PlotConfigXML, PlotConfig

from audio.config.rigol import RigolConfig, RigolConfigXML
from audio.config.sampling import SamplingConfig, SamplingConfigXML
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


@rich.repr.auto
class SweepConfigXML:

    _tree = ET.ElementTree(
        ET.fromstring(
            """
            <sweep-config>
                <rigol></rigol>
                <nidaq></nidaq>
                <sampling></sampling>
                <plot></plot>
            </sweep-config>
            """
        )
    )

    config: ET.ElementTree

    def __init__(self, tree: ET.ElementTree) -> None:
        self._tree = tree

    @classmethod
    def from_file(cls, file: pathlib.Path):

        if not file.exists() and not file.is_file():
            raise Exception("File does not exists.")

        if file.suffix == ".json5":
            return SweepConfigXML._from_file_json5(file)

    @classmethod
    def _from_file_json5(cls, file: pathlib.Path):

        if not file.exists() and not file.is_file():
            raise Exception("File does not exists.")

        sweep_config: Dictionary = Dictionary(load_json_config(file))

        return cls.from_dict(sweep_config)

    @classmethod
    def from_dict(cls, dictionary: Dictionary):
        rigol_dict = dictionary.get("rigol", None)
        nidaq_dict = dictionary.get("nidaq", None)
        sampling_dict = dictionary.get("sampling", None)
        plot_dict = dictionary.get("plot", None)

        if rigol_dict:
            rigol_dict = dict(rigol_dict)

        if nidaq_dict:
            nidaq_dict = dict(nidaq_dict)

        if sampling_dict:
            sampling_dict = dict(sampling_dict)

        if plot_dict:
            plot_dict = dict(plot_dict)

        rigol_config_xml = RigolConfigXML.from_dict(rigol_dict)
        nidaq_config_xml = NiDaqConfigXML.from_dict(nidaq_dict)
        sampling_config_xml = SamplingConfigXML.from_dict(sampling_dict)
        plot_config_xml = PlotConfigXML.from_dict(plot_dict)

        return cls.from_values(
            rigol=rigol_config_xml,
            nidaq=nidaq_config_xml,
            sampling=sampling_config_xml,
            plot=plot_config_xml,
        )

    @classmethod
    def from_values(
        cls,
        rigol: Optional[RigolConfigXML] = None,
        nidaq: Optional[NiDaqConfigXML] = None,
        sampling: Optional[SamplingConfigXML] = None,
        plot: Optional[PlotConfigXML] = None,
    ):
        tree = cls._tree
        root = tree.getroot()

        if rigol:
            root.find("./rigol").extend(rigol.get_node())
        if nidaq:
            root.find("./nidaq").extend(nidaq.get_node())
        if sampling:
            root.find("./sampling").extend(sampling.get_node())
        if plot:
            root.find("./plot").extend(plot.get_node())

        return cls(tree)

    def __repr__(self) -> str:
        root = self.tree.getroot()
        ET.indent(root)
        return ET.tostring(root, encoding="unicode")

    def print(self):
        root = self.tree.getroot()
        ET.indent(root)
        console.print(ET.tostring(root, encoding="unicode"))

    @property
    def tree(self) -> ET.ElementTree:
        return self._tree

    @property
    def rigol(self):
        return RigolConfigXML(ET.ElementTree(self.tree.find("./rigol")))

    @property
    def nidaq(self):
        return NiDaqConfigXML(ET.ElementTree(self.tree.find("./nidaq")))

    @property
    def sampling(self):
        return SamplingConfigXML(ET.ElementTree(self.tree.find("./sampling")))

    @property
    def plot(self):
        return PlotConfigXML(ET.ElementTree(self.tree.find("./plot")))
