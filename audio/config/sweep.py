from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
import enum

from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, Optional

import rich

from audio.config import json5_string_to_dict, json5_to_dict
from audio.config.nidaq import NiDaqConfig, NiDaqConfigOptions, NiDaqConfigXML
from audio.config.plot import PlotConfig, PlotConfigOptions, PlotConfigXML
from audio.config.rigol import RigolConfig, RigolConfigOptions, RigolConfigXML
from audio.config.sampling import (
    SamplingConfig,
    SamplingConfigOptions,
    SamplingConfigXML,
)
from audio.console import console
from audio.type import Dictionary
from rich.syntax import Syntax


class FileType(enum.Enum):
    JSON5 = auto()
    XML = auto()


class SweepConfigOptions(Enum):
    ROOT = "sweep-config"
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
class SweepConfig:

    rigol: Optional[RigolConfig] = None
    nidaq: Optional[NiDaqConfig] = None
    sampling: Optional[SamplingConfig] = None
    plot: Optional[PlotConfig] = None

    @classmethod
    def from_xml_file(cls, file_path: Path):
        if not file_path.exists() or not file_path.is_file():
            return None

        return cls.from_xml_string(file_path.read_text(encoding="utf-8"))

    @classmethod
    def from_xml_string(cls, data: str):
        tree = ET.ElementTree(ET.fromstring(data))
        return cls.from_xml(tree)

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
        if xml is not None:
            Erigol = SweepConfig.get_rigol_from_xml(xml)
            Enidaq = SweepConfig.get_nidaq_from_xml(xml)
            Esampling = SweepConfig.get_sampling_from_xml(xml)
            Eplot = SweepConfig.get_plot_from_xml(xml)

            rigol_config = RigolConfig.from_xml(Erigol)
            nidaq_config = NiDaqConfig.from_xml(Enidaq)
            sampling_config = SamplingConfig.from_xml(Esampling)
            plot_config = PlotConfig.from_xml(Eplot)

            return cls(
                rigol=rigol_config,
                nidaq=nidaq_config,
                sampling=sampling_config,
                plot=plot_config,
            )

        else:
            return None

    def merge(self, other: Optional[SweepConfig]):
        if other is None:
            return

        if self.rigol is not None:
            self.rigol.merge(other.rigol)
        if self.nidaq is not None:
            self.nidaq.merge(other.nidaq)
        if self.sampling is not None:
            self.sampling.merge(other.sampling)
        if self.plot is not None:
            self.plot.merge(other.plot)

    def override(self, other: Optional[SweepConfig]):
        if other is None:
            return

        if other.rigol is not None:
            self.rigol.override(other.rigol)
        if other.nidaq is not None:
            self.nidaq.override(other.nidaq)
        if other.sampling is not None:
            self.sampling.override(other.sampling)
        if other.plot is not None:
            self.plot.override(other.plot)

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
