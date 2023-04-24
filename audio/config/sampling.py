from __future__ import annotations

import typing
from dataclasses import dataclass
from enum import Enum
from typing import Self

import rich
import rich.repr
from defusedxml import ElementTree

from audio.config import Config
from audio.console import console
from audio.decoder.xml import DecoderXML

if typing.TYPE_CHECKING:
    from pathlib import Path


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

    def __str__(self: Self) -> str:
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

    def __str__(self: Self) -> str:
        return str(self.value)


@dataclass
@rich.repr.auto
class SamplingConfig(Config, DecoderXML):
    Fs_multiplier: float | None = None
    points_per_decade: float | None = None
    number_of_samples: int | None = None
    number_of_samples_max: int | None = None
    frequency_min: float | None = None
    frequency_max: float | None = None
    interpolation_rate: float | None = None
    delay_measurements: float | None = None

    def merge(self: Self, other: SamplingConfig | None) -> None:
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

    def override(self: Self, other: SamplingConfig | None) -> None:
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

    def print_object(self: Self) -> None:
        console.print(self)

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

        return cls(
            Fs_multiplier=SamplingConfig._get_sampling_frequency_multiplier_from_xml(
                xml,
            ),
            points_per_decade=SamplingConfig._get_points_per_decade_from_xml(xml),
            number_of_samples=SamplingConfig._get_number_of_samples_from_xml(xml),
            number_of_samples_max=SamplingConfig._get_number_of_samples_max_from_xml(
                xml,
            ),
            frequency_min=SamplingConfig._get_frequency_min_from_xml(xml),
            frequency_max=SamplingConfig._get_frequency_max_from_xml(xml),
            interpolation_rate=SamplingConfig._get_interpolation_rate_from_xml(xml),
            delay_measurements=SamplingConfig._get_delay_measurements_from_xml(xml),
        )

    @staticmethod
    def xml_is_valid(xml: ElementTree.ElementTree) -> bool:
        return xml.getroot().tag == SamplingConfigOptions.ROOT.value

    @staticmethod
    def _get_sampling_frequency_multiplier_from_xml(
        xml: ElementTree.ElementTree | None,
    ) -> float | None:
        if xml is None:
            return None

        elem_sampling_frequency_multiplier = xml.find(
            SamplingConfigOptionsXPATH.FS_MULTIPLIER.value,
        )
        if (
            elem_sampling_frequency_multiplier is not None
            and elem_sampling_frequency_multiplier.text is not None
        ):
            return float(elem_sampling_frequency_multiplier.text)

        return None

    @staticmethod
    def _get_points_per_decade_from_xml(
        xml: ElementTree.ElementTree | None,
    ) -> float | None:
        elem_points_per_decade = xml.find(
            SamplingConfigOptionsXPATH.POINTS_PER_DECADE.value,
        )
        if (
            elem_points_per_decade is not None
            and elem_points_per_decade.text is not None
        ):
            return float(elem_points_per_decade.text)

        return None

    @staticmethod
    def _get_number_of_samples_from_xml(
        xml: ElementTree.ElementTree | None,
    ) -> int | None:
        if xml is None:
            return None

        elem_number_of_samples = xml.find(
            SamplingConfigOptionsXPATH.NUMBER_OF_SAMPLES.value,
        )
        if (
            elem_number_of_samples is not None
            and elem_number_of_samples.text is not None
        ):
            return int(elem_number_of_samples.text)

        return None

    @staticmethod
    def _get_number_of_samples_max_from_xml(
        xml: ElementTree.ElementTree | None,
    ) -> int | None:
        if xml is None:
            return None

        elem_number_of_samples_max = xml.find(
            SamplingConfigOptionsXPATH.NUMBER_OF_SAMPLES_MAX.value,
        )
        if (
            elem_number_of_samples_max is not None
            and elem_number_of_samples_max.text is not None
        ):
            return int(elem_number_of_samples_max.text)

        return None

    @staticmethod
    def _get_frequency_min_from_xml(
        xml: ElementTree.ElementTree | None,
    ) -> float | None:
        if xml is None:
            return None

        elem_frequency_min = xml.find(SamplingConfigOptionsXPATH.FREQUENCY_MIN.value)
        if elem_frequency_min is not None and elem_frequency_min.text is not None:
            return float(elem_frequency_min.text)

        return None

    @staticmethod
    def _get_frequency_max_from_xml(
        xml: ElementTree.ElementTree | None,
    ) -> float | None:
        if xml is None:
            return None
        elem_frequency_max = xml.find(SamplingConfigOptionsXPATH.FREQUENCY_MAX.value)
        if elem_frequency_max is not None and elem_frequency_max.text is not None:
            return float(elem_frequency_max.text)

        return None

    @staticmethod
    def _get_interpolation_rate_from_xml(
        xml: ElementTree.ElementTree | None,
    ) -> float | None:
        if xml is None:
            return None

        elem_interpolation_rate = xml.find(
            SamplingConfigOptionsXPATH.INTERPOLATION_RATE.value,
        )
        if (
            elem_interpolation_rate is not None
            and elem_interpolation_rate.text is not None
        ):
            return float(elem_interpolation_rate.text)

        return None

    @staticmethod
    def _get_delay_measurements_from_xml(
        xml: ElementTree.ElementTree | None,
    ) -> float | None:
        elem_delay_measurements = xml.find(
            SamplingConfigOptionsXPATH.DELAY_MEASUREMENTS.value,
        )
        if (
            elem_delay_measurements is not None
            and elem_delay_measurements.text is not None
        ):
            return float(elem_delay_measurements.text)

        return None
        return None

        return None
        return None
