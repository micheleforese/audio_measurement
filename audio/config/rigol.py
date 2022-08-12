from enum import Enum
import xml.etree.ElementTree as ET
from typing import Dict, Optional

import rich

from audio.console import console


class RigolConfigOptions(Enum):
    ROOT = "rigol"
    AMPLITAMPLITUDE_PEAK_TO_PEAK = "amplitude_peak_to_peak"

    def __str__(self) -> str:
        return str(self.value)


class RigolConfigOptionsXPATH(Enum):
    AMPLITUDE_PEAK_TO_PEAK = f"./{RigolConfigOptions.AMPLITAMPLITUDE_PEAK_TO_PEAK}"

    def __str__(self) -> str:
        return str(self.value)


@rich.repr.auto
class RigolConfigXML:
    TREE_SKELETON: str = """
    <{root}>
        <{amplitude_peak_to_peak}></{amplitude_peak_to_peak}>
    </{root}>
    """.format(
        root=RigolConfigOptions.ROOT.value,
        amplitude_peak_to_peak=RigolConfigOptions.AMPLITAMPLITUDE_PEAK_TO_PEAK.value,
    )

    _tree: ET.ElementTree

    def __init__(self) -> None:
        self._tree = ET.ElementTree(ET.fromstring(self.TREE_SKELETON))

    def set_tree(self, tree: ET.ElementTree):
        self._tree = tree

    @classmethod
    def from_tree(cls, tree: ET.ElementTree) -> None:
        # TODO: Check tree for validity
        rigolConfigXML = RigolConfigXML()
        rigolConfigXML.set_tree(tree)

        return rigolConfigXML

    @classmethod
    def from_dict(cls, dictionary: Optional[Dict]):
        amplitude_peak_to_peak: Optional[float] = None

        if dictionary is not None:
            amplitude_peak_to_peak = dictionary.get(
                RigolConfigOptions.AMPLITAMPLITUDE_PEAK_TO_PEAK.value, None
            )

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
        tree = ET.ElementTree(ET.fromstring(cls.TREE_SKELETON))

        if amplitude_peak_to_peak:
            tree.find(RigolConfigOptionsXPATH.AMPLITUDE_PEAK_TO_PEAK.value).text = str(
                amplitude_peak_to_peak
            )

        return cls.from_tree(tree)

    def get_node(self):
        return self._tree.getroot()

    def print(self):
        root = self._tree.getroot()
        ET.indent(root)
        console.print(ET.tostring(root, encoding="unicode"))

    @property
    def amplitude_peak_to_peak(self):
        amplitude_peak_to_peak = self._tree.find(
            RigolConfigOptionsXPATH.AMPLITUDE_PEAK_TO_PEAK.value
        ).text

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
            self._tree.find(
                RigolConfigOptionsXPATH.AMPLITUDE_PEAK_TO_PEAK.value
            ).text = str(amplitude_peak_to_peak)
        except Exception:
            self.print()
