from __future__ import annotations

import xml.etree.ElementTree as ET
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import rich

from audio.config import Config
from audio.config.nidaq import NiDaqConfig, NiDaqConfigOptions
from audio.config.plot import PlotConfig, PlotConfigOptions
from audio.config.rigol import RigolConfig, RigolConfigOptions
from audio.config.sampling import SamplingConfig, SamplingConfigOptions
from audio.console import console
from audio.decoder.xml import DecoderXML


class SweepConfigOptions(Enum):
    ROOT = "config"
    RIGOL = f"{RigolConfigOptions.ROOT.value}"
    NIDAQ = f"{NiDaqConfigOptions.ROOT.value}"
    SAMPLING = f"{SamplingConfigOptions.ROOT.value}"
    PLOT = f"{PlotConfigOptions.ROOT.value}"

    def __str__(self) -> str:
        return str(self.value)


class SweepConfigOptionsXPATH(Enum):
    RIGOL = f"./{SweepConfigOptions.RIGOL.value}"
    NIDAQ = f"./{SweepConfigOptions.NIDAQ.value}"
    SAMPLING = f"./{SweepConfigOptions.SAMPLING.value}"
    PLOT = f"./{SweepConfigOptions.PLOT.value}"

    def __str__(self) -> str:
        return str(self.value)


@dataclass
@rich.repr.auto
class SweepConfig(Config, DecoderXML):

    rigol: Optional[RigolConfig] = None
    nidaq: Optional[NiDaqConfig] = None
    sampling: Optional[SamplingConfig] = None
    plot: Optional[PlotConfig] = None

    @classmethod
    def from_xml_file(cls, file: Path):
        if not file.exists() or not file.is_file():
            return None

        return cls.from_xml_string(file.read_text(encoding="utf-8"))

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        root = tree.getroot()
        return cls.from_xml_object(root)

    @classmethod
    def from_xml_object(cls, xml: Optional[ET.Element]):
        if xml is None or not cls.xml_is_valid(xml):
            return None

        Erigol = SweepConfig.get_rigol_from_xml(xml)
        Enidaq = SweepConfig.get_nidaq_from_xml(xml)
        Esampling = SweepConfig.get_sampling_from_xml(xml)
        Eplot = SweepConfig.get_plot_from_xml(xml)

        rigol_config = RigolConfig.from_xml_object(Erigol)
        nidaq_config = NiDaqConfig.from_xml_object(Enidaq)
        sampling_config = SamplingConfig.from_xml_object(Esampling)
        plot_config = PlotConfig.from_xml_object(Eplot)

        return cls(
            rigol=rigol_config,
            nidaq=nidaq_config,
            sampling=sampling_config,
            plot=plot_config,
        )

    @staticmethod
    def xml_is_valid(xml: ET.Element) -> bool:
        return xml.tag == SweepConfigOptions.ROOT.value

    def merge(self, other: Optional[SweepConfig]):
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

    def override(self, other: Optional[SweepConfig]):
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

    def print(self):
        console.print(self)

    @staticmethod
    def get_rigol_from_xml(xml: ET.ElementTree):
        rigol = xml.find(SweepConfigOptionsXPATH.RIGOL.value)
        return rigol

    @staticmethod
    def get_nidaq_from_xml(xml: ET.ElementTree):
        nidaq = xml.find(SweepConfigOptionsXPATH.NIDAQ.value)
        return nidaq

    @staticmethod
    def get_sampling_from_xml(xml: ET.ElementTree):
        sampling = xml.find(SweepConfigOptionsXPATH.SAMPLING.value)
        return sampling

    @staticmethod
    def get_plot_from_xml(xml: ET.ElementTree):
        plot = xml.find(SweepConfigOptionsXPATH.PLOT.value)
        return plot
