from __future__ import annotations

import typing
from dataclasses import dataclass
from enum import Enum
from typing import Self

import rich.repr
from defusedxml import ElementTree

from audio.config import Config
from audio.console import console
from audio.decoder.xml import DecoderXML

if typing.TYPE_CHECKING:
    from pathlib import Path


class NiDaqConfigOptions(Enum):
    ROOT = "nidaq"
    FS_MAX = "Fs_max"
    VOLTAGE_MIN = "voltage_min"
    VOLTAGE_MAX = "voltage_max"
    CHANNEL = "channel"

    def __str__(self: Self) -> str:
        return str(self.value)


class NidaqConfigOptionsXPATH(Enum):
    FS_MAX = f"./{NiDaqConfigOptions.FS_MAX}"
    VOLTAGE_MIN = f"./{NiDaqConfigOptions.VOLTAGE_MIN}"
    VOLTAGE_MAX = f"./{NiDaqConfigOptions.VOLTAGE_MAX}"
    CHANNEL = f"./{NiDaqConfigOptions.CHANNEL}"

    def __str__(self: Self) -> str:
        return str(self.value)


@dataclass
class Channel:
    name: str
    comment: str | None = None


@rich.repr.auto
class NiDaqConfig(Config, DecoderXML):
    max_frequency_sampling: float | None
    voltage_min: float | None
    voltage_max: float | None
    channels: list[Channel] | None

    def __init__(
        self: Self,
        *,
        max_frequency_sampling: float | None = None,
        voltage_min: float | None = None,
        voltage_max: float | None = None,
        channels: list[Channel] | None = None,
    ) -> None:
        self.max_frequency_sampling = max_frequency_sampling
        self.voltage_min = voltage_min
        self.voltage_max = voltage_max
        self.channels = channels

    def merge(self: Self, other: NiDaqConfig | None) -> None:
        if other is None:
            return

        if self.max_frequency_sampling is None:
            self.max_frequency_sampling = other.max_frequency_sampling

        if self.voltage_min is None:
            self.voltage_min = other.voltage_min

        if self.voltage_max is None:
            self.voltage_max = other.voltage_max

        if self.channels is None or len(self.channels) == 0:
            self.channels = other.channels

    def override(self: Self, other: NiDaqConfig | None) -> None:
        if other is None:
            return

        if other.max_frequency_sampling is not None:
            self.max_frequency_sampling = other.max_frequency_sampling

        if other.voltage_min is not None:
            self.voltage_min = other.voltage_min

        if other.voltage_max is not None:
            self.voltage_max = other.voltage_max

        if self.channels is None or len(self.channels) > 0:
            self.channels = other.channels

    def print_object(self: Self) -> None:
        console.print(self)

    @classmethod
    def from_xml_file(cls: type[Self], file: Path) -> Self:
        if not file.exists() or not file.is_file():
            return None

        return cls.from_xml_string(file.read_text(encoding="utf-8"))

    @classmethod
    def from_xml_string(cls: type[Self], data: str) -> Self:
        tree = ElementTree.ElementTree(ElementTree.fromstring(data))
        return cls.from_xml_object(tree)

    @classmethod
    def from_xml_object(cls: type[Self], xml: ElementTree.ElementTree | None) -> Self:
        if xml is None or not cls.xml_is_valid(xml):
            return None

        return cls(
            Fs_max=NiDaqConfig.get_sampling_frequency_max_from_xml(xml),
            voltage_min=NiDaqConfig.get_voltage_min_from_xml(xml),
            voltage_max=NiDaqConfig.get_voltage_max_from_xml(xml),
            channels=NiDaqConfig.get_channels_from_xml(xml),
        )

    @staticmethod
    def xml_is_valid(xml: ElementTree.Element) -> bool:
        return xml.tag == NiDaqConfigOptions.ROOT.value

    @staticmethod
    def get_sampling_frequency_max_from_xml(
        xml: ElementTree.ElementTree | None,
    ) -> float | None:
        elem_sampling_frequency_max = xml.find(NidaqConfigOptionsXPATH.FS_MAX.value)
        if elem_sampling_frequency_max is not None:
            return float(elem_sampling_frequency_max.text)

        return None

    @staticmethod
    def get_voltage_min_from_xml(xml: ElementTree.ElementTree | None) -> float | None:
        elem_voltage_min = xml.find(NidaqConfigOptionsXPATH.VOLTAGE_MIN.value)
        if elem_voltage_min is not None:
            return float(elem_voltage_min.text)

        return None

    @staticmethod
    def get_voltage_max_from_xml(xml: ElementTree.ElementTree | None) -> float | None:
        elem_voltage_max = xml.find(NidaqConfigOptionsXPATH.VOLTAGE_MAX.value)
        if elem_voltage_max is not None:
            return float(elem_voltage_max.text)

        return None

    @staticmethod
    def get_channels_from_xml(
        xml: ElementTree.ElementTree | None,
    ) -> list[Channel] | None:
        if xml is None:
            return None

        channels: list[Channel] | None = None
        elem_input_channels = xml.findall(NidaqConfigOptionsXPATH.CHANNEL.value)
        for elem_channel in elem_input_channels:
            channel_name = elem_channel.text
            channel_comment = elem_channel.get("comment")

            if channel_name is not None:
                channels = []
                channels.append(Channel(name=channel_name, comment=channel_comment))

        return channels


# TODO: Make a class for Decoding NiDaqConfig object
class NiDaqConfigDecoderXML:
    pass
