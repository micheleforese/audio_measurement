from __future__ import annotations
from enum import auto
import enum

import pathlib
import xml.etree.ElementTree as ET
from typing import Optional

import rich

from audio.config import json5_string_to_dict, json5_to_dict
from audio.config.nidaq import NiDaqConfigXML
from audio.config.plot import PlotConfigXML
from audio.config.rigol import RigolConfigXML
from audio.config.sampling import SamplingConfigXML
from audio.console import console
from audio.type import Dictionary
from rich.syntax import Syntax


class FileType(enum.Enum):
    JSON5 = auto()
    XML = auto()


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
        # console.print(ET.tostring(root, encoding="unicode"))
        console.print("\n")
        console.print(
            Syntax(ET.tostring(root, encoding="unicode"), "xml", theme="one-dark")
        )

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
        return PlotConfigXML.from_tree(ET.ElementTree(self.tree.find("./plot")))
