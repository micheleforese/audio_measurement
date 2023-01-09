from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import rich
import yaml
from audio.config import Config

from audio.config.type import Range
from audio.console import console
from audio.decoder.xml import DecoderXML
from audio.encoder.yaml import EncoderYAML


class PlotConfigOptions(Enum):
    ROOT = "plot"
    Y_OFFSET = "y_offset"

    X_LIMIT = "x_limit"
    X_LIMIT_MIN = "min"
    X_LIMIT_MAX = "max"

    Y_LIMIT = "y_limit"
    Y_LIMIT_MIN = "min"
    Y_LIMIT_MAX = "max"

    INTERPOLATION_RATE = "interpolation_rate"
    DPI = "dpi"
    COLOR = "color"
    LEGEND = "legend"
    TITLE = "title"

    def __str__(self) -> str:
        return str(self.value)


class PlotConfigOptionsXPATH(Enum):
    Y_OFFSET = f"./{PlotConfigOptions.Y_OFFSET}"

    X_LIMIT = f"./{PlotConfigOptions.X_LIMIT}"
    X_LIMIT_MIN = f"./{PlotConfigOptions.X_LIMIT}/{PlotConfigOptions.X_LIMIT_MIN}"
    X_LIMIT_MAX = f"./{PlotConfigOptions.X_LIMIT}/{PlotConfigOptions.X_LIMIT_MAX}"

    Y_LIMIT = f"./{PlotConfigOptions.Y_LIMIT}"
    Y_LIMIT_MIN = f"./{PlotConfigOptions.Y_LIMIT}/{PlotConfigOptions.Y_LIMIT_MIN}"
    Y_LIMIT_MAX = f"./{PlotConfigOptions.Y_LIMIT}/{PlotConfigOptions.Y_LIMIT_MAX}"

    INTERPOLATION_RATE = f"./{PlotConfigOptions.INTERPOLATION_RATE}"
    DPI = f"./{PlotConfigOptions.DPI}"
    COLOR = f"./{PlotConfigOptions.COLOR}"
    LEGEND = f"./{PlotConfigOptions.LEGEND}"
    TITLE = f"./{PlotConfigOptions.TITLE}"

    def __str__(self) -> str:
        return str(self.value)


@dataclass
@rich.repr.auto
class PlotConfig(Config, DecoderXML, EncoderYAML):
    y_offset: Optional[float] = None
    x_limit: Optional[Range[float]] = None
    y_limit: Optional[Range[float]] = None
    interpolation_rate: Optional[float] = None
    dpi: Optional[int] = None
    color: Optional[str] = None
    legend: Optional[str] = None
    title: Optional[str] = None

    def merge(self, other: Optional[PlotConfig]):
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

    def override(self, other: Optional[PlotConfig]):
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

    def print(self):
        console.print(self)

    #########################
    # Decoder XML
    #########################

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
    def xml_is_valid(xml: ET.Element) -> bool:
        return xml.tag == PlotConfigOptions.ROOT.value

    @staticmethod
    def _get_x_limit_min_from_xml(xml: Optional[ET.ElementTree]):
        Ex_limit_min = xml.find(PlotConfigOptionsXPATH.X_LIMIT_MIN.value)
        if Ex_limit_min is not None:
            return float(Ex_limit_min.text)

        return None

    @staticmethod
    def _get_x_limit_max_from_xml(xml: Optional[ET.ElementTree]):
        Ex_limit_max = xml.find(PlotConfigOptionsXPATH.X_LIMIT_MAX.value)
        if Ex_limit_max is not None:
            return float(Ex_limit_max.text)

        return None

    @staticmethod
    def _get_x_limit_from_xml(xml: Optional[ET.ElementTree]):
        x_limit_min: Optional[float] = PlotConfig._get_x_limit_min_from_xml(xml)
        x_limit_max: Optional[float] = PlotConfig._get_x_limit_max_from_xml(xml)

        x_limit_range: Optional[Range[float]] = None
        if x_limit_min is not None and x_limit_max is not None:
            x_limit_range = Range.from_list([x_limit_min, x_limit_max])

        return x_limit_range

    @staticmethod
    def _get_y_limit_min_from_xml(xml: Optional[ET.ElementTree]):
        Ey_limit_min = xml.find(PlotConfigOptionsXPATH.Y_LIMIT_MIN.value)
        if Ey_limit_min is not None:
            return float(Ey_limit_min.text)

        return None

    @staticmethod
    def _get_y_limit_max_from_xml(xml: Optional[ET.ElementTree]):
        Ey_limit_max = xml.find(PlotConfigOptionsXPATH.Y_LIMIT_MAX.value)
        if Ey_limit_max is not None:
            return float(Ey_limit_max.text)

        return None

    @staticmethod
    def _get_y_limit_from_xml(xml: Optional[ET.ElementTree]):
        y_limit_min: Optional[float] = PlotConfig._get_y_limit_min_from_xml(xml)
        y_limit_max: Optional[float] = PlotConfig._get_y_limit_max_from_xml(xml)

        y_limit_range: Optional[Range[float]] = None

        if y_limit_min is not None and y_limit_max is not None:
            y_limit_range = Range.from_list([y_limit_min, y_limit_max])

        return y_limit_range

    @staticmethod
    def _get_y_offset_from_xml(xml: Optional[ET.ElementTree]):
        Ey_offset = xml.find(PlotConfigOptionsXPATH.Y_OFFSET.value)
        if Ey_offset is not None:
            return float(Ey_offset.text)

        return None

    @staticmethod
    def _get_interpolation_rate_from_xml(xml: Optional[ET.ElementTree]):
        Einterpolation_rate = xml.find(PlotConfigOptionsXPATH.INTERPOLATION_RATE.value)
        if Einterpolation_rate is not None:
            return float(Einterpolation_rate.text)

        return None

    @staticmethod
    def _get_dpi_from_xml(xml: Optional[ET.ElementTree]):
        Edpi = xml.find(PlotConfigOptionsXPATH.DPI.value)
        if Edpi is not None:
            return float(Edpi.text)

        return None

    @staticmethod
    def _get_color_from_xml(xml: Optional[ET.ElementTree]):
        Ecolor = xml.find(PlotConfigOptionsXPATH.COLOR.value)
        if Ecolor is not None:
            return Ecolor.text
        return None

    @staticmethod
    def _get_legend_from_xml(xml: Optional[ET.ElementTree]):
        Elegend = xml.find(PlotConfigOptionsXPATH.LEGEND.value)
        if Elegend is not None:
            return Elegend.text
        return None

    @staticmethod
    def _get_title_from_xml(xml: Optional[ET.ElementTree]):
        Etitle = xml.find(PlotConfigOptionsXPATH.TITLE.value)
        if Etitle is not None:
            return Etitle.text
        return None

    #########################
    # Encoder XML
    #########################

    def to_yaml_file(self, file: Path):
        file.write_text(self.to_yaml_string())

    def to_yaml_string(self):
        yaml_string_data: str = ""

        yaml_string_list: List[str] = []

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

        yaml_string_data = "\n".join(yaml_string_list)

        return yaml_string_data

    def _y_offset_to_yaml(self) -> Optional[str]:
        if self.y_offset is not None:
            return f"{PlotConfigOptions.Y_OFFSET.value}: {self.y_offset}"
        else:
            return None

    def _x_limit_to_yaml(self) -> Optional[str]:
        if self.x_limit is not None:
            return f"{PlotConfigOptions.X_LIMIT.value}: [{self.x_limit.min}, {self.x_limit.max}]"
        else:
            return None

    def _y_limit_to_yaml(self) -> Optional[str]:
        if self.y_limit is not None:
            return f"{PlotConfigOptions.Y_LIMIT.value}: [{self.y_limit.min}, {self.y_limit.max}]"
        else:
            return None

    def _interpolation_rate_to_yaml(self) -> Optional[str]:
        if self.interpolation_rate is not None:
            return f"{PlotConfigOptions.INTERPOLATION_RATE.value}: {self.interpolation_rate}"
        else:
            return None

    def _dpi_to_yaml(self) -> Optional[str]:
        if self.dpi is not None:
            return f"{PlotConfigOptions.DPI.value}: {self.dpi}"
        else:
            return None

    def _color_to_yaml(self) -> Optional[str]:
        if self.color is not None:
            return f"{PlotConfigOptions.COLOR.value}: '{self.color}'"
        else:
            return None

    def _legend_to_yaml(self) -> Optional[str]:
        if self.legend is not None:
            return f"{PlotConfigOptions.LEGEND.value}: '{self.legend}'"
        else:
            return None
