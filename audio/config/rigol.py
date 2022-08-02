from enum import Enum, auto, unique
from typing import Any, Dict, Optional
import xml.etree.ElementTree as ET

import rich

from audio.config import Config_Dict, IConfig
from audio.type import Dictionary, Option


from audio.console import console


@unique
class RigolConfigEnum(Enum):
    AMPLITUDE_PEAK_TO_PEAK = auto()


class RigolConfig(Dictionary):
    def __rich_repr__(self):
        yield "amplitude_pp", self.amplitude_pp

    def exists(self, config: RigolConfigEnum) -> bool:
        match config:
            case RigolConfigEnum.AMPLITUDE_PEAK_TO_PEAK:
                return not self.amplitude_pp.is_null

    @property
    def amplitude_pp(self) -> Option[float]:
        return self.get_property("amplitude_pp", float)

    def set_amplitude_peak_to_peak(
        self,
        amplitude_pp: float,
        override: bool = False,
    ) -> Option[float]:
        if not self.exists(RigolConfigEnum.AMPLITUDE_PEAK_TO_PEAK) or override:
            self.get_dict().update({"amplitude_pp": amplitude_pp})
        return self.amplitude_pp


@rich.repr.auto
class RigolConfigXML:
    _tree: ET.ElementTree = ET.ElementTree(
        ET.fromstring(
            """
            <plot>
                <amplitude_peak_to_peak></amplitude_peak_to_peak>
            </plot>
            """
        )
    )

    def __init__(self, tree: ET.ElementTree) -> None:
        self._tree = tree

    @classmethod
    def from_dict(cls, dictionary: Optional[Dict]):
        amplitude_peak_to_peak: Optional[float] = None

        if dictionary is not None:
            amplitude_peak_to_peak = dictionary.get("amplitude_peak_to_peak", None)

            if amplitude_peak_to_peak:
                amplitude_peak_to_peak = float(amplitude_peak_to_peak)

        return cls.from_values(
            amplitude_peak_to_peak=amplitude_peak_to_peak,
        )

    @classmethod
    def from_values(
        cls,
        amplitude_peak_to_peak: Optional[float] = None,
    ):
        tree = cls._tree

        if amplitude_peak_to_peak:
            tree.find("./amplitude_peak_to_peak").text = str(amplitude_peak_to_peak)

        return cls(tree)

    def get_node(self):
        return self._tree.getroot()

    def print(self):
        root = self._tree.getroot()
        ET.indent(root)
        console.print(ET.tostring(root, encoding="unicode"))

    @property
    def amplitude_peak_to_peak(self):
        amplitude_peak_to_peak = self._tree.find("./amplitude_peak_to_peak").text

        if amplitude_peak_to_peak is not None:
            amplitude_peak_to_peak = float(amplitude_peak_to_peak)

        return amplitude_peak_to_peak

    def override(
        self,
        amplitude_peak_to_peak: Optional[float] = None,
    ):
        if amplitude_peak_to_peak is not None:
            self._set_amplitude_peak_to_peak(amplitude_peak_to_peak)

    def _set_amplitude_peak_to_peak(self, amplitude_peak_to_peak: Optional[float]):
        try:
            self._tree.find("./amplitude_peak_to_peak").text = str(
                amplitude_peak_to_peak
            )
        except Exception:
            self.print()
