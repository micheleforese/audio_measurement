from __future__ import annotations

import typing
from dataclasses import dataclass
from enum import Enum
from typing import Self
from xml.etree.ElementTree import ElementTree

import rich

from audio.config import Config
from audio.console import console
from audio.decoder.xml import DecoderXML

if typing.TYPE_CHECKING:
    from pathlib import Path


class RigolConfigOptions(Enum):
    ROOT = "rigol"
    AMPLITAMPLITUDE_PEAK_TO_PEAK = "amplitude_peak_to_peak"

    def __str__(self: Self) -> str:
        return str(self.value)


class RigolConfigOptionsXPATH(Enum):
    AMPLITUDE_PEAK_TO_PEAK = f"./{RigolConfigOptions.AMPLITAMPLITUDE_PEAK_TO_PEAK}"

    def __str__(self: Self) -> str:
        return str(self.value)


@dataclass
@rich.repr.auto
class RigolConfig(Config, DecoderXML):
    amplitude_peak_to_peak: float | None = None

    def merge(self: Self, other: RigolConfig | None) -> None:
        if other is None:
            return

        if self.amplitude_peak_to_peak is None:
            self.amplitude_peak_to_peak = other.amplitude_peak_to_peak

    def override(self: Self, other: RigolConfig | None) -> None:
        if other is None:
            return

        if other.amplitude_peak_to_peak is not None:
            self.amplitude_peak_to_peak = other.amplitude_peak_to_peak

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
            amplitude_peak_to_peak=RigolConfig._get_amplitude_peak_to_peak_from_xml(
                xml,
            ),
        )

    @staticmethod
    def xml_is_valid(xml: ElementTree.Element) -> bool:
        return xml.tag == RigolConfigOptions.ROOT.value

    @staticmethod
    def _get_amplitude_peak_to_peak_from_xml(
        xml: ElementTree.ElementTree | None,
    ) -> float | None:
        elem_amplitude_peak_to_peak = xml.find(
            RigolConfigOptionsXPATH.AMPLITUDE_PEAK_TO_PEAK.value,
        )
        if elem_amplitude_peak_to_peak is not None:
            return float(elem_amplitude_peak_to_peak.text)

        return None
