from typing import Dict, Optional
from numpy import number
import rich.repr
from audio.console import console
from audio.config import Config_Dict, IConfig
from audio.type import Dictionary, Option

import xml.etree.ElementTree as ET


@rich.repr.auto
class SamplingConfigXML:
    _tree: ET.ElementTree = ET.ElementTree(
        ET.fromstring(
            """
            <plot>
                <Fs_multiplier></Fs_multiplier>
                <points_per_decade></points_per_decade>
                <number_of_samples></number_of_samples>
                <frequency_min></frequency_min>
                <frequency_max></frequency_max>
            </plot>
            """
        )
    )

    def __init__(self, tree: ET.ElementTree) -> None:
        self._tree = tree

    @classmethod
    def from_dict(cls, dictionary: Optional[Dict]):

        Fs_multiplier: Optional[float] = None
        points_per_decade: Optional[float] = None
        number_of_samples: Optional[int] = None
        frequency_min: Optional[float] = None
        frequency_max: Optional[float] = None

        if dictionary is not None:
            Fs_multiplier = dictionary.get("Fs_multiplier", None)
            points_per_decade = dictionary.get("points_per_decade", None)
            number_of_samples = dictionary.get("number_of_samples", None)
            frequency_min = dictionary.get("frequency_min", None)
            frequency_max = dictionary.get("frequency_max", None)

            if Fs_multiplier:
                Fs_multiplier = float(Fs_multiplier)

            if points_per_decade:
                points_per_decade = float(points_per_decade)

            if number_of_samples:
                number_of_samples = int(number_of_samples)

            if frequency_min:
                frequency_min = float(frequency_min)

            if frequency_max:
                frequency_max = float(frequency_max)

        return cls.from_values(
            Fs_multiplier=Fs_multiplier,
            points_per_decade=points_per_decade,
            number_of_samples=number_of_samples,
            frequency_min=frequency_min,
            frequency_max=frequency_max,
        )

    @classmethod
    def from_values(
        cls,
        Fs_multiplier: Optional[float] = None,
        points_per_decade: Optional[float] = None,
        number_of_samples: Optional[int] = None,
        frequency_min: Optional[float] = None,
        frequency_max: Optional[float] = None,
    ):
        tree = cls._tree

        if Fs_multiplier:
            tree.find("./Fs_multiplier").text = str(Fs_multiplier)

        if points_per_decade:
            tree.find("./points_per_decade").text = str(points_per_decade)

        if number_of_samples:
            tree.find("./number_of_samples").text = str(number_of_samples)

        if frequency_min:
            tree.find("./frequency_min").text = str(frequency_min)

        if frequency_max:
            tree.find("./frequency_max").text = str(frequency_max)

        return cls(tree)

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

    def override(
        self,
        Fs_multiplier: Optional[float] = None,
        points_per_decade: Optional[float] = None,
        number_of_samples: Optional[int] = None,
        frequency_min: Optional[float] = None,
        frequency_max: Optional[float] = None,
    ):
        console.print(
            Fs_multiplier,
            points_per_decade,
            number_of_samples,
            frequency_min,
            frequency_max,
        )

        if Fs_multiplier is not None:
            self._set_Fs_multiplier(Fs_multiplier)

        if points_per_decade is not None:
            self._set_points_per_decade(points_per_decade)

        if number_of_samples is not None:
            self._set_number_of_samples(number_of_samples)

        if frequency_min is not None:
            self._set_frequency_min(frequency_min)

        if frequency_max is not None:
            self._set_frequency_max(frequency_max)

    def _set_Fs_multiplier(self, Fs_multiplier: Optional[float]):
        self._tree.find("./Fs_multiplier").text = str(Fs_multiplier)

    def _set_points_per_decade(self, points_per_decade: Optional[float]):
        self._tree.find("./points_per_decade").text = str(points_per_decade)

    def _set_number_of_samples(self, number_of_samples: Optional[float]):
        self._tree.find("./number_of_samples").text = str(number_of_samples)

    def _set_frequency_min(self, frequency_min: Optional[float]):
        self._tree.find("./frequency_min").text = str(frequency_min)

    def _set_frequency_max(self, frequency_max: Optional[float]):
        self._tree.find("./frequency_max").text = str(frequency_max)
