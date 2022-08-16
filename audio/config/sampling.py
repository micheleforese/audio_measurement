from enum import Enum
import xml.etree.ElementTree as ET
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
    def from_tree(cls, tree: ET.ElementTree) -> None:
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

    def __rich_repr__(self):
        yield "sampling"
        yield "Fs_multiplier", self.Fs_multiplier, "NONE"
        yield "points_per_decade", self.points_per_decade, "NONE"
        yield "number_of_samples", self.number_of_samples, "NONE"
        yield "number_of_samples_max", self.number_of_samples_max, "NONE"
        yield "frequency_min", self.frequency_min, "NONE"
        yield "frequency_max", self.frequency_max, "NONE"
        yield "interpolation_rate", self.interpolation_rate, "NONE"
        yield "delay_measurements", self.delay_measurements, "NONE"

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
            delay_measurements = str(delay_measurements)

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
    ):

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
