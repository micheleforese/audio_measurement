from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

import rich.repr

from audio.config import Config
from audio.console import console
from audio.decoder.xml import DecoderXML


class NiDaqConfigOptions(Enum):
    ROOT = "nidaq"
    FS_MAX = "Fs_max"
    VOLTAGE_MIN = "voltage_min"
    VOLTAGE_MAX = "voltage_max"
    CHANNEL = "channel"

    def __str__(self) -> str:
        return str(self.value)


class NidaqConfigOptionsXPATH(Enum):
    FS_MAX = f"./{NiDaqConfigOptions.FS_MAX}"
    VOLTAGE_MIN = f"./{NiDaqConfigOptions.VOLTAGE_MIN}"
    VOLTAGE_MAX = f"./{NiDaqConfigOptions.VOLTAGE_MAX}"
    CHANNEL = f"./{NiDaqConfigOptions.CHANNEL}"

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class Channel:
    name: str
    comment: Optional[str] = None


@rich.repr.auto
class NiDaqConfig(Config, DecoderXML):
    Fs_max: Optional[float]
    voltage_min: Optional[float]
    voltage_max: Optional[float]
    channels: List[Channel]

    def __init__(
        self,
        *,
        Fs_max: Optional[float] = None,
        voltage_min: Optional[float] = None,
        voltage_max: Optional[float] = None,
        channels: List[Channel],
    ) -> None:
        self.Fs_max = Fs_max
        self.voltage_min = voltage_min
        self.voltage_max = voltage_max
        self.channels = channels

    def merge(self, other: Optional[NiDaqConfig]):
        if other is None:
            return

        if self.Fs_max is None:
            self.Fs_max = other.Fs_max

        if self.voltage_min is None:
            self.voltage_min = other.voltage_min

        if self.voltage_max is None:
            self.voltage_max = other.voltage_max

        if len(self.channels) == 0:
            self.channels = other.channels

    def override(self, other: Optional[NiDaqConfig]):
        if other is None:
            return

        if other.Fs_max is not None:
            self.Fs_max = other.Fs_max

        if other.voltage_min is not None:
            self.voltage_min = other.voltage_min

        if other.voltage_max is not None:
            self.voltage_max = other.voltage_max

        if len(self.channels) > 0:
            self.channels = other.channels

    def print(self):
        console.print(self)

    @classmethod
    def from_xml_file(cls, file: Path):
        if not file.exists() or not file.is_file():
            return None

        return cls.from_xml_string(file.read_text(encoding="utf-8"))

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        return cls.from_xml_object(tree)

    @classmethod
    def from_xml_object(cls, xml: Optional[ET.ElementTree]):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        return cls(
            Fs_max=NiDaqConfig._get_Fs_max_from_xml(xml),
            voltage_min=NiDaqConfig._get_voltage_min_from_xml(xml),
            voltage_max=NiDaqConfig._get_voltage_max_from_xml(xml),
            channels=NiDaqConfig._get_channels_from_xml(xml),
        )

    @staticmethod
    def xml_is_valid(xml: ET.Element) -> bool:
        return xml.tag == NiDaqConfigOptions.ROOT.value

    @staticmethod
    def _get_Fs_max_from_xml(xml: Optional[ET.ElementTree]):
        EFs_max = xml.find(NidaqConfigOptionsXPATH.FS_MAX.value)
        if EFs_max is not None:
            return float(EFs_max.text)

        return None

    @staticmethod
    def _get_voltage_min_from_xml(xml: Optional[ET.ElementTree]):
        Evoltage_min = xml.find(NidaqConfigOptionsXPATH.VOLTAGE_MIN.value)
        if Evoltage_min is not None:
            return float(Evoltage_min.text)

        return None

    @staticmethod
    def _get_voltage_max_from_xml(xml: Optional[ET.ElementTree]):
        Evoltage_max = xml.find(NidaqConfigOptionsXPATH.VOLTAGE_MAX.value)
        if Evoltage_max is not None:
            return float(Evoltage_max.text)

        return None

    @staticmethod
    def _get_channels_from_xml(xml: Optional[ET.ElementTree]):
        channels: List[Channel] = []
        Einput_channels = xml.findall(NidaqConfigOptionsXPATH.CHANNEL.value)
        for Echannel in Einput_channels:
            channel_name = Echannel.text
            channel_comment = Echannel.get("comment")

            if channel_name is not None:
                channels.append(Channel(name=channel_name, comment=channel_comment))

        return channels
