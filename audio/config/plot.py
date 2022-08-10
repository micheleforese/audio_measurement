from __future__ import annotations
from typing import Dict, Optional

import rich


from audio.config.type import Range
from audio.type import Dictionary, Option
import xml.etree.ElementTree as ET
from audio.console import console


@rich.repr.auto
class PlotConfigXML:
    _tree: ET.ElementTree = ET.ElementTree(
        ET.fromstring(
            """
            <plot>
                <y_offset></y_offset>
                <x_limit>
                    <min></min>
                    <max></max>
                </x_limit>
                <y_limit>
                    <min></min>
                    <max></max>
                </y_limit>
                <interpolation_rate></interpolation_rate>
                <dpi></dpi>
                <color></color>
            </plot>
            """
        )
    )

    def __init__(self, tree: ET.ElementTree) -> None:
        self._tree = tree

    @classmethod
    def from_dict(cls, dictionary: Optional[Dict]):

        y_offset: Optional[float] = None
        x_limit: Optional[Range[float]] = None
        y_limit: Optional[Range[float]] = None
        interpolation_rate: Optional[float] = None
        dpi: Optional[float] = None
        color: Optional[str] = None

        if dictionary is not None:
            y_offset = dictionary.get("y_offset", None)
            x_limit = dictionary.get("x_limit", None)
            y_limit = dictionary.get("y_limit", None)
            interpolation_rate = dictionary.get("interpolation_rate", None)
            dpi = dictionary.get("dpi", None)
            color = dictionary.get("color", None)

            if y_offset is not None:
                y_offset = float(y_offset)

            if x_limit is not None:
                x_limit: Range[float] = Range[float].from_list(list(x_limit))

            if y_limit is not None:
                y_limit: Range[float] = Range[float].from_list(list(y_limit))

            if interpolation_rate is not None:
                interpolation_rate = float(interpolation_rate)

            if dpi is not None:
                dpi = float(dpi)

            if color is not None:
                color = str(color)

        return cls.from_values(
            y_offset=y_offset,
            x_limit=x_limit,
            y_limit=y_limit,
            interpolation_rate=interpolation_rate,
            dpi=dpi,
            color=color,
        )

    @classmethod
    def from_values(
        cls,
        y_offset: Optional[float] = None,
        x_limit: Optional[Range[float]] = None,
        y_limit: Optional[Range[float]] = None,
        interpolation_rate: Optional[float] = None,
        dpi: Optional[float] = None,
        color: Optional[str] = None,
    ):
        tree = cls._tree

        if y_offset is not None:
            tree.find("./y_offset").text = str(y_offset)

        if x_limit is not None:
            tree.find("./x_limit/min").text = str(x_limit.min)
            tree.find("./x_limit/max").text = str(x_limit.max)

        if y_limit is not None:
            tree.find("./y_limit/min").text = str(y_limit.min)
            tree.find("./y_limit/max").text = str(y_limit.max)

        if interpolation_rate is not None:
            tree.find("./interpolation_rate").text = str(interpolation_rate)

        if dpi is not None:
            tree.find("./dpi").text = str(dpi)

        if color is not None:
            tree.find("./color").text = str(color)

        return cls(tree)

    def get_node(self):
        return self._tree.getroot()

    def print(self):
        root = self._tree.getroot()
        ET.indent(root)
        console.print(ET.tostring(root, encoding="unicode"))

    @property
    def y_offset(self):
        y_offset = self._tree.find("./y_offset").text

        if y_offset is not None:
            y_offset = float(y_offset)

        return y_offset

    @property
    def x_limit(self) -> Optional[Range]:
        x_limit: Optional[Range] = None
        x_limit_min = self._tree.find("./x_limit/min").text
        x_limit_max = self._tree.find("./x_limit/max").text

        if x_limit_min is not None and x_limit_max is not None:
            x_limit_min: float = float(x_limit_min)
            x_limit_max: float = float(x_limit_max)
            x_limit = Range(x_limit_min, x_limit_max)

        return x_limit

    @property
    def y_limit(self) -> Optional[Range]:
        y_limit: Optional[Range] = None
        y_limit_min = self._tree.find("./y_limit/min").text
        y_limit_max = self._tree.find("./y_limit/max").text

        if y_limit_min is not None and y_limit_max is not None:
            y_limit_min: float = float(y_limit_min)
            y_limit_max: float = float(y_limit_max)
            y_limit = Range(y_limit_min, y_limit_max)

        return y_limit

    @property
    def interpolation_rate(self):
        interpolation_rate = self._tree.find("./interpolation_rate").text

        if interpolation_rate is not None:
            interpolation_rate = float(interpolation_rate)

        return interpolation_rate

    @property
    def dpi(self):
        dpi = self._tree.find("./dpi").text

        if dpi is not None:
            dpi = float(dpi)

        return dpi

    @property
    def color(self):
        color = self._tree.find("./color").text

        if color is not None:
            color = str(color)

        return color

    def override(
        self,
        y_offset: Optional[float] = None,
        x_limit: Optional[Range[float]] = None,
        y_limit: Optional[Range[float]] = None,
        interpolation_rate: Optional[float] = None,
        dpi: Optional[float] = None,
        color: Optional[float] = None,
    ):
        if y_offset is not None:
            self._set_y_offset(y_offset)

        if x_limit is not None:
            self._set_x_limit(x_limit)

        if y_limit is not None:
            self._set_y_limit(y_limit)

        if interpolation_rate is not None:
            self._set_interpolation_rate(interpolation_rate)

        if dpi is not None:
            self._set_dpi(dpi)

        if color is not None:
            self._set_color(color)

    def _set_y_offset(self, y_offset: Optional[float]):
        self._tree.find("./y_offset").text = str(y_offset)

    def _set_x_limit(self, x_limit: Optional[Range[float]]):
        self._tree.find("./x_limit/min").text = str(x_limit.min)
        self._tree.find("./x_limit/max").text = str(x_limit.max)

    def _set_y_limit(self, y_limit: Optional[Range[float]]):
        self._tree.find("./y_limit/min").text = str(y_limit.min)
        self._tree.find("./y_limit/max").text = str(y_limit.max)

    def _set_interpolation_rate(self, interpolation_rate: Optional[float]):
        self._tree.find("./interpolation_rate").text = str(interpolation_rate)

    def _set_dpi(self, dpi: Optional[float]):
        self._tree.find("./dpi").text = str(dpi)

    def _set_color(self, color: Optional[float]):
        self._tree.find("./color").text = str(color)
