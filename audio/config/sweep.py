from __future__ import annotations

import typing
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Self

import rich
from defusedxml import ElementTree

from audio.config import Config
from audio.config.nidaq import NiDaqConfig, NiDaqConfigOptions
from audio.config.plot import PlotConfig, PlotConfigOptions
from audio.config.rigol import RigolConfig, RigolConfigOptions
from audio.config.sampling import SamplingConfig, SamplingConfigOptions
from audio.console import console
from audio.decoder.xml import DecoderXML

if typing.TYPE_CHECKING:
    from pathlib import Path


class SweepConfigOptions(Enum):
    ROOT = "config"
    RIGOL = f"{RigolConfigOptions.ROOT.value}"
    NIDAQ = f"{NiDaqConfigOptions.ROOT.value}"
    SAMPLING = f"{SamplingConfigOptions.ROOT.value}"
    PLOT = f"{PlotConfigOptions.ROOT.value}"

    def __str__(self: Self) -> str:
        return str(self.value)


class SweepConfigOptionsXPATH(Enum):
    RIGOL = f"./{SweepConfigOptions.RIGOL.value}"
    NIDAQ = f"./{SweepConfigOptions.NIDAQ.value}"
    SAMPLING = f"./{SweepConfigOptions.SAMPLING.value}"
    PLOT = f"./{SweepConfigOptions.PLOT.value}"

    def __str__(self: Self) -> str:
        return str(self.value)


@dataclass
@rich.repr.auto
class SweepConfig(Config, DecoderXML):
    rigol: RigolConfig | None = None
    nidaq: NiDaqConfig | None = None
    sampling: SamplingConfig | None = None
    plot: PlotConfig | None = None

    @classmethod
    def from_xml_file(cls: type[Self], file: Path) -> Self | None:
        if not file.exists() or not file.is_file():
            return None

        return cls.from_xml_string(file.read_text(encoding="utf-8"))

    @classmethod
    def from_xml_string(cls: type[Self], data: str) -> Self | None:
        tree = ElementTree.ElementTree(ElementTree.fromstring(data))
        return cls.from_xml_object(tree)

    @classmethod
    def from_xml_object(
        cls: type[Self],
        xml: ElementTree.ElementTree | None,
    ) -> Self | None:
        if xml is None or not cls.xml_is_valid(xml):
            return None

        elem_rigol = SweepConfig.get_rigol_from_xml(xml)
        elem_nidaq = SweepConfig.get_nidaq_from_xml(xml)
        elem_sampling = SweepConfig.get_sampling_from_xml(xml)
        elem_plot = SweepConfig.get_plot_from_xml(xml)

        rigol_config = RigolConfig.from_xml_object(elem_rigol)
        nidaq_config = NiDaqConfig.from_xml_object(elem_nidaq)
        sampling_config = SamplingConfig.from_xml_object(elem_sampling)
        plot_config = PlotConfig.from_xml_object(elem_plot)

        return cls(
            rigol=rigol_config,
            nidaq=nidaq_config,
            sampling=sampling_config,
            plot=plot_config,
        )

    @staticmethod
    def xml_is_valid(xml: ElementTree.ElementTree) -> bool:
        return xml.tag == SweepConfigOptions.ROOT.value

    def merge(self: Self, other: Self | None) -> None:
        if other is None:
            return

        if self.rigol is not None:
            self.rigol.merge(other.rigol)
        else:
            self.rigol = deepcopy(other.rigol)

        if self.nidaq is not None:
            self.nidaq.merge(other.nidaq)
        else:
            self.nidaq = deepcopy(other.nidaq)

        if self.sampling is not None:
            self.sampling.merge(other.sampling)
        else:
            self.sampling = deepcopy(other.sampling)

        if self.plot is not None:
            self.plot.merge(other.plot)
        else:
            self.plot = deepcopy(other.plot)

    def override(self: Self, other: SweepConfig | None) -> None:
        if other is None:
            return

        if self.rigol is not None:
            self.rigol.override(other.rigol)
        else:
            self.rigol = deepcopy(other.rigol)

        if self.nidaq is not None:
            self.nidaq.override(other.nidaq)
        else:
            self.nidaq = deepcopy(other.nidaq)

        if self.sampling is not None:
            self.sampling.override(other.sampling)
        else:
            self.sampling = deepcopy(other.sampling)

        if self.plot is not None:
            self.plot.override(other.plot)
        else:
            self.plot = deepcopy(other.plot)

    def print_object(self: Self) -> None:
        console.print(self)

    @staticmethod
    def get_rigol_from_xml(
        xml: ElementTree.ElementTree,
    ) -> ElementTree.ElementTree | None:
        return ElementTree.ElementTree(xml.find(SweepConfigOptionsXPATH.RIGOL.value))

    @staticmethod
    def get_nidaq_from_xml(
        xml: ElementTree.ElementTree,
    ) -> ElementTree.ElementTree | None:
        return ElementTree.ElementTree(xml.find(SweepConfigOptionsXPATH.NIDAQ.value))

    @staticmethod
    def get_sampling_from_xml(
        xml: ElementTree.ElementTree,
    ) -> ElementTree.ElementTree | None:
        return ElementTree.ElementTree(xml.find(SweepConfigOptionsXPATH.SAMPLING.value))

    @staticmethod
    def get_plot_from_xml(
        xml: ElementTree.ElementTree,
    ) -> ElementTree.ElementTree | None:
        return ElementTree.ElementTree(xml.find(SweepConfigOptionsXPATH.PLOT.value))
        return ElementTree.ElementTree(xml.find(SweepConfigOptionsXPATH.PLOT.value))
        return ElementTree.ElementTree(xml.find(SweepConfigOptionsXPATH.PLOT.value))
