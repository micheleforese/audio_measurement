from __future__ import annotations
from enum import Enum, auto
import enum

import pathlib
import xml.etree.ElementTree as ET
from typing import Dict, Optional

import rich

from audio.config import json5_string_to_dict, json5_to_dict
from audio.config.nidaq import NiDaqConfigOptions, NiDaqConfigXML
from audio.config.plot import PlotConfigOptions, PlotConfigXML
from audio.config.rigol import RigolConfigOptions, RigolConfigXML
from audio.config.sampling import SamplingConfigOptions, SamplingConfigXML
from audio.console import console
from audio.type import Dictionary
from rich.syntax import Syntax


class FileType(enum.Enum):
    JSON5 = auto()
    XML = auto()


class SweepConfigOptions(Enum):
    ROOT = "sweep-config"
    RIGOL = f"{RigolConfigOptions.ROOT}"
    NIDAQ = f"{NiDaqConfigOptions.ROOT}"
    SAMPLING = f"{SamplingConfigOptions.ROOT}"
    PLOT = f"{PlotConfigOptions.ROOT}"

    def __str__(self) -> str:
        return str(self.value)


class SweepConfigOptionsXPATH(Enum):
    RIGOL = f"./{SweepConfigOptions.RIGOL}"
    NIDAQ = f"./{SweepConfigOptions.NIDAQ}"
    SAMPLING = f"./{SweepConfigOptions.SAMPLING}"
    PLOT = f"./{SweepConfigOptions.PLOT}"

    def __str__(self) -> str:
        return str(self.value)


@rich.repr.auto
class SweepConfigXML:
    TREE_SKELETON: str = """
    <{root}>
        <{rigol}></{rigol}>
        <{nidaq}></{nidaq}>
        <{sampling}></{sampling}>
        <{plot}></{plot}>
    </{root}>
    """.format(
        root=SweepConfigOptions.ROOT.value,
        rigol=SweepConfigOptions.RIGOL.value,
        nidaq=SweepConfigOptions.NIDAQ.value,
        sampling=SweepConfigOptions.SAMPLING.value,
        plot=SweepConfigOptions.PLOT.value,
    )
    # TREE_SKELETON: str = """
    # <{root}>
    #     {rigol_xml}
    #     {nidaq_xml}
    #     {sampling_xml}
    #     {plot_xml}
    # </{root}>
    # """.format(
    #     root=SweepConfigOptions.ROOT.value,
    #     rigol_xml=RigolConfigXML.TREE_SKELETON,
    #     nidaq_xml=NiDaqConfigXML.TREE_SKELETON,
    #     sampling_xml=SamplingConfigXML.TREE_SKELETON,
    #     plot_xml=PlotConfigXML.TREE_SKELETON,
    # )
    _tree: ET.ElementTree

    def __init__(self) -> None:
        self._tree = ET.ElementTree(ET.fromstring(self.TREE_SKELETON))

    def set_tree(self, tree: ET.ElementTree):
        self._tree = tree

    @classmethod
    def from_tree(cls, tree: ET.ElementTree):
        plotConfigXML = SweepConfigXML()
        plotConfigXML.set_tree(tree)

        return plotConfigXML

    @classmethod
    def from_file(cls, file: pathlib.Path):
        """Creates a SweepConfigXML object from a file path.

        Args:
            file (pathlib.Path): The Config file path.

        Raises:
            Exception: File does not exists

        Returns:
            `SweepConfigXML`: the object class
        """
        if not file.exists() and not file.is_file():
            raise Exception("File does not exists.")

        if file.suffix == ".json5":
            return SweepConfigXML._from_file_json5(file)

    @classmethod
    def from_string(cls, data: str, file_type: FileType = FileType.JSON5):
        if file_type == FileType.JSON5:
            sweep_config: Dictionary = Dictionary(json5_string_to_dict(data))
            return cls.from_dict(sweep_config)
        else:
            raise Exception("Must be one of FileType: ['JSON5']")

    @classmethod
    def _from_file_json5(cls, file: pathlib.Path):

        if not file.exists() and not file.is_file():
            raise Exception("File does not exists.")

        sweep_config: Dictionary = Dictionary(json5_to_dict(file))

        return cls.from_dict(sweep_config)

    @classmethod
    def from_dict(cls, dictionary: Optional[Dict]):
        rigol_dict: Optional[Dict] = None
        nidaq_dict: Optional[Dict] = None
        sampling_dict: Optional[Dict] = None
        plot_dict: Optional[Dict] = None

        if dictionary is not None:
            rigol_dict = dictionary.get(RigolConfigOptions.ROOT.value, None)
            nidaq_dict = dictionary.get(NiDaqConfigOptions.ROOT.value, None)
            sampling_dict = dictionary.get(SamplingConfigOptions.ROOT.value, None)
            plot_dict = dictionary.get(PlotConfigOptions.ROOT.value, None)

        if rigol_dict is not None:
            rigol_dict = dict(rigol_dict)

        if nidaq_dict is not None:
            nidaq_dict = dict(nidaq_dict)

        if sampling_dict is not None:
            sampling_dict = dict(sampling_dict)

        if plot_dict is not None:
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
        tree = ET.ElementTree(ET.fromstring(cls.TREE_SKELETON))

        root = tree.getroot()

        if rigol:
            root.find(SweepConfigOptionsXPATH.RIGOL.value).extend(rigol.get_node())
        if nidaq:
            root.find(SweepConfigOptionsXPATH.NIDAQ.value).extend(nidaq.get_node())
        if sampling:
            root.find(SweepConfigOptionsXPATH.SAMPLING.value).extend(
                sampling.get_node()
            )
        if plot:
            root.find(SweepConfigOptionsXPATH.PLOT.value).extend(plot.get_node())

        return cls.from_tree(tree)

    def __repr__(self) -> str:
        root = self.tree.getroot()
        ET.indent(root)
        return ET.tostring(root, encoding="unicode")

    def __rich_repr__(self):
        yield "config"
        yield "rigol", self.rigol
        yield "nidaq", self.nidaq
        yield "sampling", self.sampling
        yield "plot", self.plot

    def __str__(self) -> str:
        root = self.tree.getroot()
        ET.indent(root)
        return ET.tostring(root, encoding="unicode")

    def print(self):
        root = self.tree.getroot()
        ET.indent(root)
        console.print("\n")
        console.print(
            Syntax(ET.tostring(root, encoding="unicode"), "xml", theme="one-dark")
        )

    @property
    def tree(self) -> ET.ElementTree:
        return self._tree

    @property
    def rigol(self):
        return RigolConfigXML.from_tree(
            ET.ElementTree(self.tree.find(SweepConfigOptionsXPATH.RIGOL.value))
        )

    @property
    def nidaq(self):
        return NiDaqConfigXML.from_tree(
            ET.ElementTree(self.tree.find(SweepConfigOptionsXPATH.NIDAQ.value))
        )

    @property
    def sampling(self):
        return SamplingConfigXML.from_tree(
            ET.ElementTree(self.tree.find(SweepConfigOptionsXPATH.SAMPLING.value))
        )

    @property
    def plot(self):
        return PlotConfigXML.from_tree(
            ET.ElementTree(self.tree.find(SweepConfigOptionsXPATH.PLOT.value))
        )
