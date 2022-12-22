from __future__ import annotations
from dataclasses import dataclass, field

import xml.etree.ElementTree as ET
from enum import Enum
from typing import Dict, List, Optional

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


@dataclass
@rich.repr.auto
class NiDaqConfig:
    Fs_max: Optional[float] = None
    voltage_min: Optional[float] = None
    voltage_max: Optional[float] = None
    input_channel: Optional[str] = None
    input_channels: List[str] = field(default_factory=[])

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
        if xml is not None:
            return cls(
                Fs_max=NiDaqConfig.get_Fs_max_from_xml(xml),
                voltage_min=NiDaqConfig.get_voltage_min_from_xml(xml),
                voltage_max=NiDaqConfig.get_voltage_max_from_xml(xml),
                input_channel=NiDaqConfig.get_input_channel_from_xml(xml),
                input_channels=NiDaqConfig.get_input_channels_from_xml(xml),
            )
        else:
            return cls()

    def merge(self, other: Optional[NiDaqConfig]):
        if other is None:
            return

        if self.Fs_max is None:
            self.Fs_max = other.Fs_max

        if self.voltage_min is None:
            self.voltage_min = other.voltage_min

        if self.voltage_max is None:
            self.voltage_max = other.voltage_max

        if self.input_channel is None:
            self.input_channel = other.input_channel

        if self.input_channels is None:
            self.input_channels = other.input_channels

    def override(self, other: Optional[NiDaqConfig]):
        if other is None:
            return

        if other.Fs_max is not None:
            self.Fs_max = other.Fs_max

        if other.voltage_min is not None:
            self.voltage_min = other.voltage_min

        if other.voltage_max is not None:
            self.voltage_max = other.voltage_max

        if other.input_channel is not None:
            self.input_channel = other.input_channel

        if other.input_channels is not None:
            self.input_channels = other.input_channels

    @staticmethod
    def get_Fs_max_from_xml(xml: Optional[ET.ElementTree]):
        EFs_max = xml.find(NidaqConfigOptionsXPATH.FS_MAX.value)
        if EFs_max is not None:
            return float(EFs_max.text)

        return None

    @staticmethod
    def get_voltage_min_from_xml(xml: Optional[ET.ElementTree]):
        Evoltage_min = xml.find(NidaqConfigOptionsXPATH.VOLTAGE_MIN.value)
        if Evoltage_min is not None:
            return float(Evoltage_min.text)

        return None

    @staticmethod
    def get_voltage_max_from_xml(xml: Optional[ET.ElementTree]):
        Evoltage_max = xml.find(NidaqConfigOptionsXPATH.VOLTAGE_MAX.value)
        if Evoltage_max is not None:
            return float(Evoltage_max.text)

        return None

    @staticmethod
    def get_input_channel_from_xml(xml: Optional[ET.ElementTree]):
        Einput_channel = xml.find(NidaqConfigOptionsXPATH.INPUT_CHANNEL.value)
        if Einput_channel is not None:
            return Einput_channel.text
        return None

    @staticmethod
    def get_input_channels_from_xml(xml: Optional[ET.ElementTree]):
        channels: List[str] = []
        Einput_channels = xml.findall(NidaqConfigOptionsXPATH.INPUT_CHANNEL.value)
        for Echannel in Einput_channels:
            input_channel = Echannel.text

            if input_channel is not None:
                channels.append(input_channel)

        return channels
