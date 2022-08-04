import xml.etree.ElementTree as ET
from typing import Dict, Optional

import rich

from audio.console import console


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
