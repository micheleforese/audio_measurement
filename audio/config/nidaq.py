from __future__ import annotations

import xml.etree.ElementTree as ET
from enum import Enum
from typing import Dict, Optional

import rich.repr

from audio.console import console


class NiDaqConfigOptions(Enum):
    ROOT = "nidaq"
    FS_MAX = "Fs_max"
    VOLTAGE_MIN = "voltage_min"
    VOLTAGE_MAX = "voltage_max"
    INPUT_CHANNEL = "input_channel"

    def __str__(self) -> str:
        return str(self.value)


class NidaqConfigOptionsXPATH(Enum):
    FS_MAX = f"./{NiDaqConfigOptions.FS_MAX}"
    VOLTAGE_MIN = f"./{NiDaqConfigOptions.VOLTAGE_MIN}"
    VOLTAGE_MAX = f"./{NiDaqConfigOptions.VOLTAGE_MAX}"
    INPUT_CHANNEL = f"./{NiDaqConfigOptions.INPUT_CHANNEL}"

    def __str__(self) -> str:
        return str(self.value)


@rich.repr.auto
class NiDaqConfigXML:
    TREE_SKELETON: str = """
    <{root}>
        <{Fs_max}></{Fs_max}>
        <{voltage_min}></{voltage_min}>
        <{voltage_max}></{voltage_max}>
        <{input_channel}></{input_channel}>
    </{root}>
    """.format(
        root=NiDaqConfigOptions.ROOT.value,
        Fs_max=NiDaqConfigOptions.FS_MAX.value,
        voltage_min=NiDaqConfigOptions.VOLTAGE_MIN.value,
        voltage_max=NiDaqConfigOptions.VOLTAGE_MAX.value,
        input_channel=NiDaqConfigOptions.INPUT_CHANNEL.value,
    )

    _tree: ET.ElementTree

    def __init__(self) -> None:
        self._tree = ET.ElementTree(ET.fromstring(self.TREE_SKELETON))

    def set_tree(self, tree: ET.ElementTree):
        self._tree = tree

    @classmethod
    def from_tree(cls, tree: ET.ElementTree):
        # TODO: Check tree for validity
        nidaqConfigXML = NiDaqConfigXML()
        nidaqConfigXML.set_tree(tree)

        return nidaqConfigXML

    @classmethod
    def from_dict(cls, dictionary: Optional[Dict]):
        Fs_max: Optional[float] = None
        voltage_max: Optional[float] = None
        voltage_min: Optional[float] = None
        input_channel: Optional[str] = None

        if dictionary is not None:
            Fs_max = dictionary.get(NiDaqConfigOptions.FS_MAX.value, None)
            voltage_min = dictionary.get(NiDaqConfigOptions.VOLTAGE_MIN.value, None)
            voltage_max = dictionary.get(NiDaqConfigOptions.VOLTAGE_MAX.value, None)
            input_channel = dictionary.get(NiDaqConfigOptions.INPUT_CHANNEL.value, None)

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
    def from_xml(cls, xml: Optional[ET.ElementTree]):
        if xml is not None:

            nidaq_config_xml = NiDaqConfigXML.from_values(
                Fs_max=NiDaqConfigXML.get_Fs_max_from_xml(xml),
                voltage_min=NiDaqConfigXML.get_voltage_min_from_xml(xml),
                voltage_max=NiDaqConfigXML.get_voltage_max_from_xml(xml),
                input_channel=NiDaqConfigXML.get_input_channel_from_xml(xml),
            )
            return nidaq_config_xml
        else:
            return NiDaqConfigXML()

    @staticmethod
    def _get_property_from_xml(xml: Optional[ET.ElementTree], XPath: str):
        if xml is not None:
            prop = xml.find(XPath)

            if prop is not None:
                return prop.text

    @staticmethod
    def get_Fs_max_from_xml(xml: Optional[ET.ElementTree]):
        Fs_max = NiDaqConfigXML._get_property_from_xml(
            xml, NidaqConfigOptionsXPATH.FS_MAX.value
        )
        if Fs_max is not None:
            return float(Fs_max)

        return None

    @staticmethod
    def get_voltage_min_from_xml(xml: Optional[ET.ElementTree]):
        voltage_min = NiDaqConfigXML._get_property_from_xml(
            xml, NidaqConfigOptionsXPATH.VOLTAGE_MIN.value
        )
        if voltage_min is not None:
            return float(voltage_min)

        return None

    @staticmethod
    def get_voltage_max_from_xml(xml: Optional[ET.ElementTree]):
        voltage_max = NiDaqConfigXML._get_property_from_xml(
            xml, NidaqConfigOptionsXPATH.VOLTAGE_MAX.value
        )
        if voltage_max is not None:
            return float(voltage_max)

        return None

    @staticmethod
    def get_input_channel_from_xml(xml: Optional[ET.ElementTree]):
        input_channel = NiDaqConfigXML._get_property_from_xml(
            xml, NidaqConfigOptionsXPATH.INPUT_CHANNEL.value
        )
        return input_channel

    @classmethod
    def from_values(
        cls,
        Fs_max: Optional[float] = None,
        voltage_min: Optional[float] = None,
        voltage_max: Optional[float] = None,
        input_channel: Optional[str] = None,
    ):
        tree = ET.ElementTree(ET.fromstring(cls.TREE_SKELETON))

        if Fs_max:
            tree.find(NidaqConfigOptionsXPATH.FS_MAX.value).text = str(Fs_max)

        if voltage_min:
            tree.find(NidaqConfigOptionsXPATH.VOLTAGE_MIN.value).text = str(voltage_min)

        if voltage_max:
            tree.find(NidaqConfigOptionsXPATH.VOLTAGE_MAX.value).text = str(voltage_max)

        if input_channel:
            tree.find(NidaqConfigOptionsXPATH.INPUT_CHANNEL.value).text = str(
                input_channel
            )

        return cls.from_tree(tree)

    # def __rich_repr__(self):
    #     yield "nidaq"
    #     yield "Fs_max", self.Fs_max, "NONE"
    #     yield "voltage_min", self.voltage_min, "NONE"
    #     yield "voltage_min", self.voltage_min, "NONE"
    #     yield "input_channel", self.input_channel, "NONE"

    def get_node(self):
        return self._tree.getroot()

    def print(self):
        from rich.syntax import Syntax

        root = self._tree.getroot()
        ET.indent(root)
        console.print(
            Syntax(ET.tostring(root, encoding="unicode"), "xml", theme="one-dark")
        )

    @property
    def Fs_max(self):
        Fs_max = self._tree.find(NidaqConfigOptionsXPATH.FS_MAX.value).text

        if Fs_max is not None:
            Fs_max = float(Fs_max)

        return Fs_max

    @property
    def voltage_min(self):
        voltage_min = self._tree.find(NidaqConfigOptionsXPATH.VOLTAGE_MIN.value).text

        if voltage_min is not None:
            voltage_min = float(voltage_min)

        return voltage_min

    @property
    def voltage_max(self):
        voltage_max = self._tree.find(NidaqConfigOptionsXPATH.VOLTAGE_MAX.value).text

        if voltage_max is not None:
            voltage_max = float(voltage_max)

        return voltage_max

    @property
    def input_channel(self):
        input_channel = self._tree.find(
            NidaqConfigOptionsXPATH.INPUT_CHANNEL.value
        ).text

        if input_channel is not None:
            input_channel = str(input_channel)

        return input_channel

    def override(
        self,
        Fs_max: Optional[float] = None,
        voltage_min: Optional[float] = None,
        voltage_max: Optional[float] = None,
        input_channel: Optional[str] = None,
        new_config: Optional[NiDaqConfigXML] = None,
    ):
        if new_config is not None:
            self._set_Fs_max(new_config.Fs_max)
            self._set_voltage_min(new_config.voltage_min)
            self._set_voltage_max(new_config.voltage_max)
            self._set_input_channel(new_config.input_channel)

        if Fs_max is not None:
            self._set_Fs_max(Fs_max)

        if voltage_min is not None:
            self._set_voltage_min(voltage_min)

        if voltage_max is not None:
            self._set_voltage_max(voltage_max)

        if input_channel is not None:
            self._set_input_channel(input_channel)

    def _set_Fs_max(self, Fs_max: Optional[float]):
        self._tree.find(NidaqConfigOptionsXPATH.FS_MAX.value).text = str(Fs_max)

    def _set_voltage_min(self, voltage_min: Optional[float]):
        self._tree.find(NidaqConfigOptionsXPATH.VOLTAGE_MIN.value).text = str(
            voltage_min
        )

    def _set_voltage_max(self, voltage_max: Optional[float]):
        self._tree.find(NidaqConfigOptionsXPATH.VOLTAGE_MAX.value).text = str(
            voltage_max
        )

    def _set_input_channel(self, input_channel: Optional[str]):
        self._tree.find(NidaqConfigOptionsXPATH.INPUT_CHANNEL.value).text = str(
            input_channel
        )
