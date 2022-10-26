from __future__ import annotations
from dataclasses import dataclass

import xml.etree.ElementTree as ET
from enum import Enum
from typing import Dict, Optional

import rich.repr

from audio.console import console


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


@rich.repr.auto
class SamplingConfigXML:
    TREE_SKELETON: str = """
    <{root}>
        <{Fs_multiplier}></{Fs_multiplier}>
        <{points_per_decade}></{points_per_decade}>
        <{number_of_samples}></{number_of_samples}>
        <{number_of_samples_max}></{number_of_samples_max}>
        <{frequency_min}></{frequency_min}>
        <{frequency_max}></{frequency_max}>
        <{interpolation_rate}></{interpolation_rate}>
        <{delay_measurements}></{delay_measurements}>
    </{root}>
    """.format(
        root=SamplingConfigOptions.ROOT.value,
        Fs_multiplier=SamplingConfigOptions.FS_MULTIPLIER.value,
        points_per_decade=SamplingConfigOptions.POINTS_PER_DECADE.value,
        number_of_samples=SamplingConfigOptions.NUMBER_OF_SAMPLES.value,
        number_of_samples_max=SamplingConfigOptions.NUMBER_OF_SAMPLES_MAX.value,
        frequency_min=SamplingConfigOptions.FREQUENCY_MIN.value,
        frequency_max=SamplingConfigOptions.FREQUENCY_MAX.value,
        interpolation_rate=SamplingConfigOptions.INTERPOLATION_RATE.value,
        delay_measurements=SamplingConfigOptions.DELAY_MEASUREMENTS.value,
    )

    _tree: ET.ElementTree

    def __init__(self) -> None:
        self._tree = ET.ElementTree(ET.fromstring(self.TREE_SKELETON))

    def set_tree(self, tree: ET.ElementTree):
        self._tree = tree

    @classmethod
    def from_tree(cls, tree: ET.ElementTree):
        # TODO: Check tree for validity
        samplingConfigXML = SamplingConfigXML()
        samplingConfigXML.set_tree(tree)

        return samplingConfigXML

    @classmethod
    def from_dict(cls, dictionary: Optional[Dict]):

        Fs_multiplier: Optional[float] = None
        points_per_decade: Optional[float] = None
        number_of_samples: Optional[int] = None
        number_of_samples_max: Optional[int] = None
        frequency_min: Optional[float] = None
        frequency_max: Optional[float] = None
        interpolation_rate: Optional[float] = None
        delay_measurements: Optional[float] = None

        if dictionary is not None:
            Fs_multiplier = dictionary.get("Fs_multiplier", None)
            points_per_decade = dictionary.get("points_per_decade", None)
            number_of_samples = dictionary.get("number_of_samples", None)
            number_of_samples_max = dictionary.get("number_of_samples_max", None)
            frequency_min = dictionary.get("frequency_min", None)
            frequency_max = dictionary.get("frequency_max", None)
            interpolation_rate = dictionary.get("interpolation_rate", None)
            delay_measurements = dictionary.get("delay_measurements", None)

            if Fs_multiplier:
                Fs_multiplier = float(Fs_multiplier)

            if points_per_decade:
                points_per_decade = float(points_per_decade)

            if number_of_samples:
                number_of_samples = int(number_of_samples)

            if number_of_samples_max:
                number_of_samples_max = int(number_of_samples_max)

            if frequency_min:
                frequency_min = float(frequency_min)

            if frequency_max:
                frequency_max = float(frequency_max)

            if interpolation_rate:
                interpolation_rate = float(interpolation_rate)

            if delay_measurements:
                delay_measurements = float(delay_measurements)

        return cls.from_values(
            Fs_multiplier=Fs_multiplier,
            points_per_decade=points_per_decade,
            number_of_samples=number_of_samples,
            number_of_samples_max=number_of_samples_max,
            frequency_min=frequency_min,
            frequency_max=frequency_max,
            interpolation_rate=interpolation_rate,
            delay_measurements=delay_measurements,
        )

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
        if xml is not None:
            sampling_config_xml = SamplingConfigXML.from_values(
                Fs_multiplier=SamplingConfigXML.get_Fs_multiplier_from_xml(xml),
                points_per_decade=SamplingConfigXML.get_points_per_decade_from_xml(xml),
                number_of_samples=SamplingConfigXML.get_number_of_samples_from_xml(xml),
                number_of_samples_max=SamplingConfigXML.get_number_of_samples_max_from_xml(
                    xml
                ),
                frequency_min=SamplingConfigXML.get_frequency_min_from_xml(xml),
                frequency_max=SamplingConfigXML.get_frequency_max_from_xml(xml),
                interpolation_rate=SamplingConfigXML.get_interpolation_rate_from_xml(
                    xml
                ),
                delay_measurements=SamplingConfigXML.get_delay_measurements_from_xml(
                    xml
                ),
            )

            return sampling_config_xml
        else:
            return SamplingConfigXML()

    @staticmethod
    def _get_property_from_xml(xml: Optional[ET.ElementTree], XPath: str):
        if xml is not None:
            prop = xml.find(XPath)

            if prop is not None:
                return prop.text

    @staticmethod
    def get_Fs_multiplier_from_xml(xml: Optional[ET.ElementTree]):
        Fs_multiplier = SamplingConfigXML._get_property_from_xml(
            xml, SamplingConfigOptionsXPATH.FS_MULTIPLIER.value
        )
        if Fs_multiplier is not None:
            return float(Fs_multiplier)

        return None

    @staticmethod
    def get_points_per_decade_from_xml(xml: Optional[ET.ElementTree]):
        points_per_decade = SamplingConfigXML._get_property_from_xml(
            xml, SamplingConfigOptionsXPATH.POINTS_PER_DECADE.value
        )
        if points_per_decade is not None:
            return float(points_per_decade)

        return None

    @staticmethod
    def get_number_of_samples_from_xml(xml: Optional[ET.ElementTree]):
        number_of_samples = SamplingConfigXML._get_property_from_xml(
            xml, SamplingConfigOptionsXPATH.NUMBER_OF_SAMPLES.value
        )
        if number_of_samples is not None:
            return int(number_of_samples)

        return None

    @staticmethod
    def get_number_of_samples_max_from_xml(xml: Optional[ET.ElementTree]):
        number_of_samples_max = SamplingConfigXML._get_property_from_xml(
            xml, SamplingConfigOptionsXPATH.NUMBER_OF_SAMPLES_MAX.value
        )
        if number_of_samples_max is not None:
            return int(number_of_samples_max)

        return None

    @staticmethod
    def get_frequency_min_from_xml(xml: Optional[ET.ElementTree]):
        frequency_min = SamplingConfigXML._get_property_from_xml(
            xml, SamplingConfigOptionsXPATH.FREQUENCY_MIN.value
        )
        if frequency_min is not None:
            return float(frequency_min)

        return None

    @staticmethod
    def get_frequency_max_from_xml(xml: Optional[ET.ElementTree]):
        frequency_max = SamplingConfigXML._get_property_from_xml(
            xml, SamplingConfigOptionsXPATH.FREQUENCY_MAX.value
        )
        if frequency_max is not None:
            return float(frequency_max)

        return None

    @staticmethod
    def get_interpolation_rate_from_xml(xml: Optional[ET.ElementTree]):
        interpolation_rate = SamplingConfigXML._get_property_from_xml(
            xml, SamplingConfigOptionsXPATH.INTERPOLATION_RATE.value
        )
        if interpolation_rate is not None:
            return float(interpolation_rate)

        return None

    @staticmethod
    def get_delay_measurements_from_xml(xml: Optional[ET.ElementTree]):
        delay_measurements = SamplingConfigXML._get_property_from_xml(
            xml, SamplingConfigOptionsXPATH.DELAY_MEASUREMENTS.value
        )
        if delay_measurements is not None:
            return float(delay_measurements)

        return None

    @classmethod
    def from_values(
        cls,
        Fs_multiplier: Optional[float] = None,
        points_per_decade: Optional[float] = None,
        number_of_samples: Optional[int] = None,
        number_of_samples_max: Optional[int] = None,
        frequency_min: Optional[float] = None,
        frequency_max: Optional[float] = None,
        interpolation_rate: Optional[float] = None,
        delay_measurements: Optional[float] = None,
    ):
        tree = ET.ElementTree(ET.fromstring(cls.TREE_SKELETON))

        if Fs_multiplier:
            tree.find("./Fs_multiplier").text = str(Fs_multiplier)

        if points_per_decade:
            tree.find("./points_per_decade").text = str(points_per_decade)

        if number_of_samples:
            tree.find("./number_of_samples").text = str(number_of_samples)

        if number_of_samples_max:
            tree.find("./number_of_samples_max").text = str(number_of_samples_max)

        if frequency_min:
            tree.find("./frequency_min").text = str(frequency_min)

        if frequency_max:
            tree.find("./frequency_max").text = str(frequency_max)

        if interpolation_rate:
            tree.find("./interpolation_rate").text = str(interpolation_rate)

        if delay_measurements:
            tree.find("./delay_measurements").text = str(delay_measurements)

        return cls.from_tree(tree)

    # def __rich_repr__(self):
    #     yield "sampling"
    #     yield "Fs_multiplier", self.Fs_multiplier, "NONE"
    #     yield "points_per_decade", self.points_per_decade, "NONE"
    #     yield "number_of_samples", self.number_of_samples, "NONE"
    #     yield "number_of_samples_max", self.number_of_samples_max, "NONE"
    #     yield "frequency_min", self.frequency_min, "NONE"
    #     yield "frequency_max", self.frequency_max, "NONE"
    #     yield "interpolation_rate", self.interpolation_rate, "NONE"
    #     yield "delay_measurements", self.delay_measurements, "NONE"

    def get_node(self):
        return self._tree.getroot()

    def print(self):
        root = self._tree.getroot()
        ET.indent(root)
        console.print(ET.tostring(root, encoding="unicode"))

    @property
    def Fs_multiplier(self):
        Fs_multiplier = self._tree.find("./Fs_multiplier").text

        if Fs_multiplier is not None:
            Fs_multiplier = float(Fs_multiplier)

        return Fs_multiplier

    @property
    def points_per_decade(self):
        points_per_decade = self._tree.find("./points_per_decade").text

        if points_per_decade is not None:
            points_per_decade = float(points_per_decade)

        return points_per_decade

    @property
    def number_of_samples(self):
        number_of_samples = self._tree.find("./number_of_samples").text

        if number_of_samples is not None:
            number_of_samples = int(number_of_samples)

        return number_of_samples

    @property
    def number_of_samples_max(self):
        number_of_samples_max = self._tree.find("./number_of_samples_max").text

        if number_of_samples_max is not None:
            number_of_samples_max = int(number_of_samples_max)

        return number_of_samples_max

    @property
    def frequency_min(self):
        frequency_min = self._tree.find("./frequency_min").text

        if frequency_min is not None:
            frequency_min = float(frequency_min)

        return frequency_min

    @property
    def frequency_max(self):
        frequency_max = self._tree.find("./frequency_max").text

        if frequency_max is not None:
            frequency_max = float(frequency_max)

        return frequency_max

    @property
    def interpolation_rate(self):
        interpolation_rate = self._tree.find("./interpolation_rate").text

        if interpolation_rate is not None:
            interpolation_rate = str(interpolation_rate)

        return interpolation_rate

    @property
    def delay_measurements(self):
        delay_measurements = self._tree.find("./delay_measurements").text

        if delay_measurements is not None:
            delay_measurements = float(delay_measurements)

        return delay_measurements

    def override(
        self,
        Fs_multiplier: Optional[float] = None,
        points_per_decade: Optional[float] = None,
        number_of_samples: Optional[int] = None,
        number_of_samples_max: Optional[int] = None,
        frequency_min: Optional[float] = None,
        frequency_max: Optional[float] = None,
        interpolation_rate: Optional[float] = None,
        delay_measurements: Optional[float] = None,
        new_config: Optional[SamplingConfigXML] = None,
    ):
        if new_config is not None:
            self._set_Fs_multiplier(new_config.Fs_multiplier)
            self._set_points_per_decade(new_config.points_per_decade)
            self._set_number_of_samples(new_config.number_of_samples)
            self._set_number_of_samples_max(new_config.number_of_samples_max)
            self._set_frequency_min(new_config.frequency_min)
            self._set_frequency_max(new_config.frequency_max)
            self._set_interpolation_rate(new_config.interpolation_rate)
            self._set_delay_measurements(new_config.delay_measurements)

        if Fs_multiplier is not None:
            self._set_Fs_multiplier(Fs_multiplier)

        if points_per_decade is not None:
            self._set_points_per_decade(points_per_decade)

        if number_of_samples is not None:
            self._set_number_of_samples(number_of_samples)

        if number_of_samples_max is not None:
            self._set_number_of_samples_max(number_of_samples_max)

        if frequency_min is not None:
            self._set_frequency_min(frequency_min)

        if frequency_max is not None:
            self._set_frequency_max(frequency_max)

        if interpolation_rate is not None:
            self._set_interpolation_rate(interpolation_rate)

        if delay_measurements is not None:
            self._set_interpolation_rate(delay_measurements)

    def _set_Fs_multiplier(self, Fs_multiplier: Optional[float]):
        self._tree.find("./Fs_multiplier").text = str(Fs_multiplier)

    def _set_points_per_decade(self, points_per_decade: Optional[float]):
        self._tree.find("./points_per_decade").text = str(points_per_decade)

    def _set_number_of_samples(self, number_of_samples: Optional[float]):
        self._tree.find("./number_of_samples").text = str(number_of_samples)

    def _set_number_of_samples_max(self, number_of_samples_max: Optional[float]):
        self._tree.find("./number_of_samples_max").text = str(number_of_samples_max)

    def _set_frequency_min(self, frequency_min: Optional[float]):
        self._tree.find("./frequency_min").text = str(frequency_min)

    def _set_frequency_max(self, frequency_max: Optional[float]):
        self._tree.find("./frequency_max").text = str(frequency_max)

    def _set_interpolation_rate(self, interpolation_rate: Optional[float]):
        self._tree.find("./interpolation_rate").text = str(interpolation_rate)

    def _set_delay_measurements(self, delay_measurements: Optional[float]):
        self._tree.find("./delay_measurements").text = str(delay_measurements)


@dataclass
@rich.repr.auto
class SamplingConfig:
    Fs_multiplier: Optional[float] = None
    points_per_decade: Optional[float] = None
    number_of_samples: Optional[int] = None
    number_of_samples_max: Optional[int] = None
    frequency_min: Optional[float] = None
    frequency_max: Optional[float] = None
    interpolation_rate: Optional[float] = None
    delay_measurements: Optional[float] = None

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
        if xml is not None:
            return cls(
                Fs_multiplier=SamplingConfig.get_Fs_multiplier_from_xml(xml),
                points_per_decade=SamplingConfig.get_points_per_decade_from_xml(xml),
                number_of_samples=SamplingConfig.get_number_of_samples_from_xml(xml),
                number_of_samples_max=SamplingConfig.get_number_of_samples_max_from_xml(
                    xml
                ),
                frequency_min=SamplingConfig.get_frequency_min_from_xml(xml),
                frequency_max=SamplingConfig.get_frequency_max_from_xml(xml),
                interpolation_rate=SamplingConfig.get_interpolation_rate_from_xml(xml),
                delay_measurements=SamplingConfig.get_delay_measurements_from_xml(xml),
            )
        else:
            return cls()

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

    @staticmethod
    def get_Fs_multiplier_from_xml(xml: Optional[ET.ElementTree]):
        EFs_multiplier = xml.find(SamplingConfigOptionsXPATH.FS_MULTIPLIER.value)
        if EFs_multiplier is not None:
            return float(EFs_multiplier.text)

        return None

    @staticmethod
    def get_points_per_decade_from_xml(xml: Optional[ET.ElementTree]):
        Epoints_per_decade = xml.find(
            SamplingConfigOptionsXPATH.POINTS_PER_DECADE.value
        )
        if Epoints_per_decade is not None:
            return float(Epoints_per_decade.text)

        return None

    @staticmethod
    def get_number_of_samples_from_xml(xml: Optional[ET.ElementTree]):
        Enumber_of_samples = xml.find(
            SamplingConfigOptionsXPATH.NUMBER_OF_SAMPLES.value
        )
        if Enumber_of_samples is not None:
            return int(Enumber_of_samples.text)

        return None

    @staticmethod
    def get_number_of_samples_max_from_xml(xml: Optional[ET.ElementTree]):
        Enumber_of_samples_max = xml.find(
            SamplingConfigOptionsXPATH.NUMBER_OF_SAMPLES_MAX.value
        )
        if Enumber_of_samples_max is not None:
            return int(Enumber_of_samples_max.text)

        return None

    @staticmethod
    def get_frequency_min_from_xml(xml: Optional[ET.ElementTree]):
        Efrequency_min = xml.find(SamplingConfigOptionsXPATH.FREQUENCY_MIN.value)
        if Efrequency_min is not None:
            return float(Efrequency_min.text)

        return None

    @staticmethod
    def get_frequency_max_from_xml(xml: Optional[ET.ElementTree]):
        Efrequency_max = xml.find(SamplingConfigOptionsXPATH.FREQUENCY_MAX.value)
        if Efrequency_max is not None:
            return float(Efrequency_max.text)

        return None

    @staticmethod
    def get_interpolation_rate_from_xml(xml: Optional[ET.ElementTree]):
        Einterpolation_rate = xml.find(
            SamplingConfigOptionsXPATH.INTERPOLATION_RATE.value
        )
        if Einterpolation_rate is not None:
            return float(Einterpolation_rate.text)

        return None

    @staticmethod
    def get_delay_measurements_from_xml(xml: Optional[ET.ElementTree]):
        Edelay_measurements = xml.find(
            SamplingConfigOptionsXPATH.DELAY_MEASUREMENTS.value
        )
        if Edelay_measurements is not None:
            return float(Edelay_measurements.text)

        return None
