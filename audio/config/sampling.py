from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

import rich.repr
from audio.config import Config
from audio.console import console
from audio.decoder.xml import DecoderXML


class SamplingConfigOptions(Enum):
    ROOT = "sampling"

    FS_MULTIPLIER = "Fs_multiplier"
    POINTS_PER_DECADE = "points_per_decade"
    NUMBER_OF_SAMPLES = "number_of_samples"
    NUMBER_OF_SAMPLES_MAX = "number_of_samples_max"
    FREQUENCY_MIN = "frequency_min"
    FREQUENCY_MAX = "frequency_max"
    INTERPOLATION_RATE = "interpolation_rate"
    DELAY_MEASUREMENTS = "delay_measurements"

    def __str__(self) -> str:
        return str(self.value)


class SamplingConfigOptionsXPATH(Enum):
    FS_MULTIPLIER = f"./{SamplingConfigOptions.FS_MULTIPLIER.value}"
    POINTS_PER_DECADE = f"./{SamplingConfigOptions.POINTS_PER_DECADE.value}"
    NUMBER_OF_SAMPLES = f"./{SamplingConfigOptions.NUMBER_OF_SAMPLES.value}"
    NUMBER_OF_SAMPLES_MAX = f"./{SamplingConfigOptions.NUMBER_OF_SAMPLES_MAX.value}"
    FREQUENCY_MIN = f"./{SamplingConfigOptions.FREQUENCY_MIN.value}"
    FREQUENCY_MAX = f"./{SamplingConfigOptions.FREQUENCY_MAX.value}"
    INTERPOLATION_RATE = f"./{SamplingConfigOptions.INTERPOLATION_RATE.value}"
    DELAY_MEASUREMENTS = f"./{SamplingConfigOptions.DELAY_MEASUREMENTS.value}"

    def __str__(self) -> str:
        return str(self.value)


@dataclass
@rich.repr.auto
class SamplingConfig(Config, DecoderXML):
    Fs_multiplier: Optional[float] = None
    points_per_decade: Optional[float] = None
    number_of_samples: Optional[int] = None
    number_of_samples_max: Optional[int] = None
    frequency_min: Optional[float] = None
    frequency_max: Optional[float] = None
    interpolation_rate: Optional[float] = None
    delay_measurements: Optional[float] = None

    def merge(self, other: Optional[SamplingConfig]):
        if other is None:
            return

        if self.Fs_multiplier is None:
            self.Fs_multiplier = other.Fs_multiplier
        if self.points_per_decade is None:
            self.points_per_decade = other.points_per_decade
        if self.number_of_samples is None:
            self.number_of_samples = other.number_of_samples
        if self.number_of_samples_max is None:
            self.number_of_samples_max = other.number_of_samples_max
        if self.frequency_min is None:
            self.frequency_min = other.frequency_min
        if self.frequency_max is None:
            self.frequency_max = other.frequency_max
        if self.interpolation_rate is None:
            self.interpolation_rate = other.interpolation_rate
        if self.delay_measurements is None:
            self.delay_measurements = other.delay_measurements

    def override(self, other: Optional[SamplingConfig]):
        if other is None:
            return

        if other.Fs_multiplier is not None:
            self.Fs_multiplier = other.Fs_multiplier
        if other.points_per_decade is not None:
            self.points_per_decade = other.points_per_decade
        if other.number_of_samples is not None:
            self.number_of_samples = other.number_of_samples
        if other.number_of_samples_max is not None:
            self.number_of_samples_max = other.number_of_samples_max
        if other.frequency_min is not None:
            self.frequency_min = other.frequency_min
        if other.frequency_max is not None:
            self.frequency_max = other.frequency_max
        if other.interpolation_rate is not None:
            self.interpolation_rate = other.interpolation_rate
        if other.delay_measurements is not None:
            self.delay_measurements = other.delay_measurements

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
            Fs_multiplier=SamplingConfig._get_Fs_multiplier_from_xml(xml),
            points_per_decade=SamplingConfig._get_points_per_decade_from_xml(xml),
            number_of_samples=SamplingConfig._get_number_of_samples_from_xml(xml),
            number_of_samples_max=SamplingConfig._get_number_of_samples_max_from_xml(
                xml
            ),
            frequency_min=SamplingConfig._get_frequency_min_from_xml(xml),
            frequency_max=SamplingConfig._get_frequency_max_from_xml(xml),
            interpolation_rate=SamplingConfig._get_interpolation_rate_from_xml(xml),
            delay_measurements=SamplingConfig._get_delay_measurements_from_xml(xml),
        )

    @staticmethod
    def xml_is_valid(xml: ET.Element) -> bool:
        return xml.tag == SamplingConfigOptions.ROOT.value

    @staticmethod
    def _get_Fs_multiplier_from_xml(xml: Optional[ET.ElementTree]):
        EFs_multiplier = xml.find(SamplingConfigOptionsXPATH.FS_MULTIPLIER.value)
        if EFs_multiplier is not None:
            return float(EFs_multiplier.text)

        return None

    @staticmethod
    def _get_points_per_decade_from_xml(xml: Optional[ET.ElementTree]):
        Epoints_per_decade = xml.find(
            SamplingConfigOptionsXPATH.POINTS_PER_DECADE.value
        )
        if Epoints_per_decade is not None:
            return float(Epoints_per_decade.text)

        return None

    @staticmethod
    def _get_number_of_samples_from_xml(xml: Optional[ET.ElementTree]):
        Enumber_of_samples = xml.find(
            SamplingConfigOptionsXPATH.NUMBER_OF_SAMPLES.value
        )
        if Enumber_of_samples is not None:
            return int(Enumber_of_samples.text)

        return None

    @staticmethod
    def _get_number_of_samples_max_from_xml(xml: Optional[ET.ElementTree]):
        Enumber_of_samples_max = xml.find(
            SamplingConfigOptionsXPATH.NUMBER_OF_SAMPLES_MAX.value
        )
        if Enumber_of_samples_max is not None:
            return int(Enumber_of_samples_max.text)

        return None

    @staticmethod
    def _get_frequency_min_from_xml(xml: Optional[ET.ElementTree]):
        Efrequency_min = xml.find(SamplingConfigOptionsXPATH.FREQUENCY_MIN.value)
        if Efrequency_min is not None:
            return float(Efrequency_min.text)

        return None

    @staticmethod
    def _get_frequency_max_from_xml(xml: Optional[ET.ElementTree]):
        Efrequency_max = xml.find(SamplingConfigOptionsXPATH.FREQUENCY_MAX.value)
        if Efrequency_max is not None:
            return float(Efrequency_max.text)

        return None

    @staticmethod
    def _get_interpolation_rate_from_xml(xml: Optional[ET.ElementTree]):
        Einterpolation_rate = xml.find(
            SamplingConfigOptionsXPATH.INTERPOLATION_RATE.value
        )
        if Einterpolation_rate is not None:
            return float(Einterpolation_rate.text)

        return None

    @staticmethod
    def _get_delay_measurements_from_xml(xml: Optional[ET.ElementTree]):
        Edelay_measurements = xml.find(
            SamplingConfigOptionsXPATH.DELAY_MEASUREMENTS.value
        )
        if Edelay_measurements is not None:
            return float(Edelay_measurements.text)

        return None
