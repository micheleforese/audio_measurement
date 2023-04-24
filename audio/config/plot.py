from __future__ import annotations

import typing
from dataclasses import dataclass
from enum import Enum
from typing import Self

import rich
from defusedxml import ElementTree

from audio.config import Config
from audio.config.type import Range
from audio.console import console
from audio.decoder.xml import DecoderXML
from audio.encoder.yaml import EncoderYAML

if typing.TYPE_CHECKING:
    from pathlib import Path


class PlotConfigOptions(Enum):
    ROOT = "plot"
    Y_OFFSET = "y_offset"

    X_LIMIT = "x_limit"
    Y_LIMIT = "y_limit"
    XY_LIMIT_MIN = "min"
    XY_LIMIT_MAX = "max"

    INTERPOLATION_RATE = "interpolation_rate"
    DPI = "dpi"
    COLOR = "color"
    LEGEND = "legend"
    TITLE = "title"

    def __str__(self: Self) -> str:
        return str(self.value)


class PlotConfigOptionsXPATH(Enum):
    Y_OFFSET = f"./{PlotConfigOptions.Y_OFFSET}"

    X_LIMIT = f"./{PlotConfigOptions.X_LIMIT}"
    X_LIMIT_MIN = f"./{PlotConfigOptions.X_LIMIT}/{PlotConfigOptions.XY_LIMIT_MIN}"
    X_LIMIT_MAX = f"./{PlotConfigOptions.X_LIMIT}/{PlotConfigOptions.XY_LIMIT_MAX}"

    Y_LIMIT = f"./{PlotConfigOptions.Y_LIMIT}"
    Y_LIMIT_MIN = f"./{PlotConfigOptions.Y_LIMIT}/{PlotConfigOptions.XY_LIMIT_MIN}"
    Y_LIMIT_MAX = f"./{PlotConfigOptions.Y_LIMIT}/{PlotConfigOptions.XY_LIMIT_MAX}"

    INTERPOLATION_RATE = f"./{PlotConfigOptions.INTERPOLATION_RATE}"
    DPI = f"./{PlotConfigOptions.DPI}"
    COLOR = f"./{PlotConfigOptions.COLOR}"
    LEGEND = f"./{PlotConfigOptions.LEGEND}"
    TITLE = f"./{PlotConfigOptions.TITLE}"

    def __str__(self: Self) -> str:
        return str(self.value)


@dataclass
@rich.repr.auto
class PlotConfig(Config, DecoderXML, EncoderYAML):
    y_offset: float | None = None
    x_limit: Range[float] | None = None
    y_limit: Range[float] | None = None
    interpolation_rate: float | None = None
    dpi: int | None = None
    color: str | None = None
    legend: str | None = None
    title: str | None = None

    def merge(self: Self, other: PlotConfig | None) -> None:
        if other is None:
            return

        if self.y_offset is None:
            self.y_offset = other.y_offset
        if self.x_limit is None:
            self.x_limit = other.x_limit
        if self.y_limit is None:
            self.y_limit = other.y_limit
        if self.interpolation_rate is None:
            self.interpolation_rate = other.interpolation_rate
        if self.dpi is None:
            self.dpi = other.dpi
        if self.color is None:
            self.color = other.color
        if self.legend is None:
            self.legend = other.legend
        if self.title is None:
            self.title = other.title

    def override(self: Self, other: PlotConfig | None) -> None:
        if other is None:
            return

        if other.y_offset is not None:
            self.y_offset = other.y_offset
        if other.x_limit is not None:
            self.x_limit = other.x_limit
        if other.y_limit is not None:
            self.y_limit = other.y_limit
        if other.interpolation_rate is not None:
            self.interpolation_rate = other.interpolation_rate
        if other.dpi is not None:
            self.dpi = other.dpi
        if other.color is not None:
            self.color = other.color
        if other.legend is not None:
            self.legend = other.legend
        if other.title is not None:
            self.title = other.title

    def print_object(self: Self) -> None:
        console.print(self)

    #########################
    # Decoder XML
    #########################

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
        if xml is None or not cls.xml_is_valid(xml.getroot()):
            return None

        return cls(
            y_offset=cls._get_y_offset_from_xml(xml),
            x_limit=PlotConfig._get_x_limit_from_xml(xml),
            y_limit=PlotConfig._get_y_limit_from_xml(xml),
            interpolation_rate=PlotConfig._get_interpolation_rate_from_xml(xml),
            dpi=PlotConfig._get_dpi_from_xml(xml),
            color=PlotConfig._get_color_from_xml(xml),
            legend=PlotConfig._get_legend_from_xml(xml),
            title=PlotConfig._get_title_from_xml(xml),
        )

    @staticmethod
    def xml_is_valid(xml: ElementTree.Element) -> bool:
        return xml.tag == PlotConfigOptions.ROOT.value

    @staticmethod
    def _get_x_limit_min_from_xml(xml: ElementTree.ElementTree | None) -> float | None:
        if xml is None:
            return None

        elem_x_limit_min = xml.find(PlotConfigOptionsXPATH.X_LIMIT_MIN.value)
        if elem_x_limit_min is not None and elem_x_limit_min.text is not None:
            return float(elem_x_limit_min.text)

        return None

    @staticmethod
    def _get_x_limit_max_from_xml(xml: ElementTree.ElementTree | None) -> float | None:
        if xml is None:
            return None
        elem_x_limit_max = xml.find(PlotConfigOptionsXPATH.X_LIMIT_MAX.value)
        if elem_x_limit_max is not None and elem_x_limit_max.text is not None:
            return float(elem_x_limit_max.text)

        return None

    @staticmethod
    def _get_x_limit_from_xml(
        xml: ElementTree.ElementTree | None,
    ) -> Range[float] | None:
        x_limit_min: float | None = PlotConfig._get_x_limit_min_from_xml(xml)
        x_limit_max: float | None = PlotConfig._get_x_limit_max_from_xml(xml)

        if x_limit_min is not None and x_limit_max is not None:
            return Range.from_list((x_limit_min, x_limit_max))

        return None

    @staticmethod
    def _get_y_limit_min_from_xml(xml: ElementTree.ElementTree | None) -> float | None:
        if xml is None:
            return None

        elem_y_limit_min = xml.find(PlotConfigOptionsXPATH.Y_LIMIT_MIN.value)
        if elem_y_limit_min is not None and elem_y_limit_min.text is not None:
            return float(elem_y_limit_min.text)

        return None

    @staticmethod
    def _get_y_limit_max_from_xml(xml: ElementTree.ElementTree | None) -> float | None:
        if xml is None:
            return None

        elem_y_limit_max = xml.find(PlotConfigOptionsXPATH.Y_LIMIT_MAX.value)
        if elem_y_limit_max is not None and elem_y_limit_max.text is not None:
            return float(elem_y_limit_max.text)

        return None

    @staticmethod
    def _get_y_limit_from_xml(
        xml: ElementTree.ElementTree | None,
    ) -> Range[float] | None:
        y_limit_min: float | None = PlotConfig._get_y_limit_min_from_xml(xml)
        y_limit_max: float | None = PlotConfig._get_y_limit_max_from_xml(xml)

        if y_limit_min is not None and y_limit_max is not None:
            return Range.from_list((y_limit_min, y_limit_max))

        return None

    @staticmethod
    def _get_y_offset_from_xml(xml: ElementTree.ElementTree | None) -> float | None:
        if xml is None:
            return None

        elem_y_offset = xml.find(PlotConfigOptionsXPATH.Y_OFFSET.value)
        if elem_y_offset is not None and elem_y_offset.text is not None:
            return float(elem_y_offset.text)

        return None

    @staticmethod
    def _get_interpolation_rate_from_xml(
        xml: ElementTree.ElementTree | None,
    ) -> float | None:
        if xml is None:
            return None

        elem_interpolation_rate = xml.find(
            PlotConfigOptionsXPATH.INTERPOLATION_RATE.value,
        )
        if (
            elem_interpolation_rate is not None
            and elem_interpolation_rate.text is not None
        ):
            return float(elem_interpolation_rate.text)

        return None

    @staticmethod
    def _get_dpi_from_xml(xml: ElementTree.ElementTree | None) -> int | None:
        if xml is None:
            return None

        elem_dpi = xml.find(PlotConfigOptionsXPATH.DPI.value)
        if elem_dpi is not None and elem_dpi.text is not None:
            return int(elem_dpi.text)

        return None

    @staticmethod
    def _get_color_from_xml(xml: ElementTree.ElementTree | None) -> str | None:
        if xml is None:
            return None
        elem_color = xml.find(PlotConfigOptionsXPATH.COLOR.value)
        if elem_color is not None and elem_color.text is not None:
            return elem_color.text
        return None

    @staticmethod
    def _get_legend_from_xml(xml: ElementTree.ElementTree | None) -> str | None:
        if xml is None:
            return None

        elem_legend = xml.find(PlotConfigOptionsXPATH.LEGEND.value)
        if elem_legend is not None and elem_legend.text is not None:
            return elem_legend.text
        return None

    @staticmethod
    def _get_title_from_xml(xml: ElementTree.ElementTree | None) -> str | None:
        if xml is None:
            return None
        elem_title = xml.find(PlotConfigOptionsXPATH.TITLE.value)
        if elem_title is not None and elem_title.text is not None:
            return elem_title.text
        return None

    #########################
    # Encoder YAML
    #########################

    def to_yaml_file(self: Self, file: Path) -> None:
        file.write_text(self.to_yaml_string())

    def to_yaml_string(self: Self) -> str:
        yaml_string_list: list[str] = []

        y_offset = self._y_offset_to_yaml()
        if y_offset is not None:
            yaml_string_list.append(y_offset)

        x_limit = self._x_limit_to_yaml()
        if x_limit is not None:
            yaml_string_list.append(x_limit)

        y_limit = self._y_limit_to_yaml()
        if y_limit is not None:
            yaml_string_list.append(y_limit)

        interpolation_rate = self._interpolation_rate_to_yaml()
        if interpolation_rate is not None:
            yaml_string_list.append(interpolation_rate)

        dpi = self._dpi_to_yaml()
        if dpi is not None:
            yaml_string_list.append(dpi)

        color = self._color_to_yaml()
        if color is not None:
            yaml_string_list.append(color)

        legend = self._legend_to_yaml()
        if legend is not None:
            yaml_string_list.append(legend)

        return "\n".join(yaml_string_list)

    def _y_offset_to_yaml(self: Self) -> str | None:
        if self.y_offset is not None:
            return f"{PlotConfigOptions.Y_OFFSET.value}: {self.y_offset}"
        return None

    def _x_limit_to_yaml(self: Self) -> str | None:
        if self.x_limit is not None:
            return f"{PlotConfigOptions.X_LIMIT.value}: [{self.x_limit.min_value}, {self.x_limit.max_value}]"
        return None

    def _y_limit_to_yaml(self: Self) -> str | None:
        if self.y_limit is not None:
            return f"{PlotConfigOptions.Y_LIMIT.value}: [{self.y_limit.min_value}, {self.y_limit.max_value}]"
        return None

    def _interpolation_rate_to_yaml(self: Self) -> str | None:
        if self.interpolation_rate is not None:
            return f"{PlotConfigOptions.INTERPOLATION_RATE.value}: {self.interpolation_rate}"
        return None

    def _dpi_to_yaml(self: Self) -> str | None:
        if self.dpi is not None:
            return f"{PlotConfigOptions.DPI.value}: {self.dpi}"
        return None

    def _color_to_yaml(self: Self) -> str | None:
        if self.color is not None:
            return f"{PlotConfigOptions.COLOR.value}: '{self.color}'"
        return None

    def _legend_to_yaml(self: Self) -> str | None:
        if self.legend is not None:
            return f"{PlotConfigOptions.LEGEND.value}: '{self.legend}'"
        return None
        return None
