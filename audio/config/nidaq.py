from typing import Dict, Optional

import xml.etree.ElementTree as ET
import rich.repr

from audio.config import Config_Dict, IConfig
from audio.type import Dictionary, Option
from audio.console import console


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


@rich.repr.auto
class NiDaqConfigXML:
    _tree: ET.ElementTree = ET.ElementTree(
        ET.fromstring(
            """
            <plot>
                <Fs_max></Fs_max>
                <voltage_max></voltage_max>
                <voltage_min></voltage_min>
                <input_channel></input_channel>
            </plot>
            """
        )
    )

    def __init__(self, tree: ET.ElementTree) -> None:
        self._tree = tree

    @classmethod
    def from_dict(cls, dictionary: Optional[Dict]):
        Fs_max: Optional[float] = None
        voltage_max: Optional[float] = None
        voltage_min: Optional[float] = None
        input_channel: Optional[str] = None

        if dictionary is not None:
            Fs_max = dictionary.get("Fs_max", None)
            voltage_max = dictionary.get("voltage_max", None)
            voltage_min = dictionary.get("voltage_min", None)
            input_channel = dictionary.get("input_channel", None)

            if Fs_max:
                Fs_max = float(Fs_max)

            if voltage_max:
                voltage_max = float(voltage_max)

            if voltage_min:
                voltage_min = float(voltage_min)

            if input_channel:
                input_channel = str(input_channel)

        return cls.from_values(
            Fs_max=Fs_max,
            voltage_min=voltage_min,
            voltage_max=voltage_max,
            input_channel=input_channel,
        )

    @classmethod
    def from_values(
        cls,
        Fs_max: Optional[float] = None,
        voltage_min: Optional[float] = None,
        voltage_max: Optional[float] = None,
        input_channel: Optional[str] = None,
    ):
        tree = cls._tree

        if Fs_max:
            tree.find("./Fs_max").text = str(Fs_max)

        if voltage_min:
            tree.find("./voltage_min").text = str(voltage_min)

        if voltage_max:
            tree.find("./voltage_max").text = str(voltage_max)

        if input_channel:
            tree.find("./input_channel").text = str(input_channel)

        return cls(tree)

    def get_node(self):
        return self._tree.getroot()

    def print(self):
        root = self._tree.getroot()
        ET.indent(root)
        console.print(ET.tostring(root, encoding="unicode"))

    @property
    def Fs_max(self):
        Fs_max = self._tree.find("./Fs_max").text

        if Fs_max is not None:
            Fs_max = float(Fs_max)

        return Fs_max

    @property
    def voltage_min(self):
        voltage_min = self._tree.find("./voltage_min").text

        if voltage_min is not None:
            voltage_min = float(voltage_min)

        return voltage_min

    @property
    def voltage_max(self):
        voltage_max = self._tree.find("./voltage_max").text

        if voltage_max is not None:
            voltage_max = float(voltage_max)

        return voltage_max

    @property
    def input_channel(self):
        input_channel = self._tree.find("./input_channel").text

        if input_channel is not None:
            input_channel = str(input_channel)

        return input_channel

    def override(
        self,
        Fs_max: Optional[float] = None,
        voltage_min: Optional[float] = None,
        voltage_max: Optional[float] = None,
        input_channel: Optional[str] = None,
    ):

        if Fs_max is not None:
            self._set_Fs_max(Fs_max)

        if voltage_min is not None:
            self._set_voltage_min(voltage_min)

        if voltage_max is not None:
            self._set_voltage_max(voltage_max)

        if input_channel is not None:
            self._set_input_channel(input_channel)

    def _set_Fs_max(self, Fs_max: Optional[float]):
        self._tree.find("./Fs_max").text = str(Fs_max)

    def _set_voltage_min(self, voltage_min: Optional[float]):
        self._tree.find("./voltage_min").text = str(voltage_min)

    def _set_voltage_max(self, voltage_max: Optional[float]):
        self._tree.find("./voltage_max").text = str(voltage_max)

    def _set_input_channel(self, input_channel: Optional[str]):
        self._tree.find("./input_channel").text = str(input_channel)
