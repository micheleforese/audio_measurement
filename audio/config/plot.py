from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import rich
import yaml

from audio.config.type import Range
from audio.console import console


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


@rich.repr.auto
class PlotConfigXML:
    TREE_SKELETON: str = """
        <{root}>
            <{y_offset}></{y_offset}>
            <{x_limit}>
                <{x_limit_min}></{x_limit_min}>
                <{x_limit_max}></{x_limit_max}>
            </{x_limit}>
            <{y_limit}>
                <{y_limit_min}></{y_limit_min}>
                <{y_limit_max}></{y_limit_max}>
            </{y_limit}>
            <{interpolation_rate}></{interpolation_rate}>
            <{dpi}></{dpi}>
            <{color}></{color}>
            <{legend}></{legend}>
        </{root}>
        """.format(
        root=PlotConfigOptions.ROOT.value,
        y_offset=PlotConfigOptions.Y_OFFSET.value,
        x_limit=PlotConfigOptions.X_LIMIT.value,
        x_limit_min=PlotConfigOptions.X_LIMIT_MIN.value,
        x_limit_max=PlotConfigOptions.X_LIMIT_MAX.value,
        y_limit=PlotConfigOptions.Y_LIMIT.value,
        y_limit_min=PlotConfigOptions.Y_LIMIT_MIN.value,
        y_limit_max=PlotConfigOptions.Y_LIMIT_MAX.value,
        interpolation_rate=PlotConfigOptions.INTERPOLATION_RATE.value,
        dpi=PlotConfigOptions.DPI.value,
        color=PlotConfigOptions.COLOR.value,
        legend=PlotConfigOptions.LEGEND.value,
    )

    _tree: ET.ElementTree

    def __init__(self) -> None:
        self._tree = ET.ElementTree(ET.fromstring(self.TREE_SKELETON))

    def set_tree(self, tree: ET.ElementTree):
        # TODO: Check tree before assign it to the class variable
        self._tree = tree

    @classmethod
    def from_tree(cls, tree: ET.ElementTree):
        plotConfigXML = PlotConfigXML()
        plotConfigXML.set_tree(tree)

        return plotConfigXML

    @classmethod
    def from_dict(cls, dictionary: Optional[Dict]):

        y_offset: Optional[float] = None
        x_limit: Optional[Range[float]] = None
        y_limit: Optional[Range[float]] = None
        interpolation_rate: Optional[float] = None
        dpi: Optional[int] = None
        color: Optional[str] = None
        legend: Optional[str] = None

        if dictionary is not None:
            y_offset = PlotConfigXML.get_y_offset_from_dictionary(dictionary)
            x_limit = PlotConfigXML.get_x_limit_from_dictionary(dictionary)
            y_limit = PlotConfigXML.get_y_limit_from_dictionary(dictionary)
            interpolation_rate = PlotConfigXML.get_interpolation_rate_from_dictionary(
                dictionary
            )
            dpi = PlotConfigXML.get_dpi_from_dictionary(dictionary)
            color = PlotConfigXML.get_color_from_dictionary(dictionary)
            legend = PlotConfigXML.get_legend_from_dictionary(dictionary)

        return cls.from_values(
            y_offset=y_offset,
            x_limit=x_limit,
            y_limit=y_limit,
            interpolation_rate=interpolation_rate,
            dpi=dpi,
            color=color,
            legend=legend,
        )

    @classmethod
    def from_yaml(cls, yaml_str: str):
        yaml_dict: Dict = dict(yaml.safe_load(yaml_str))

        y_offset = PlotConfigXML.get_y_offset_from_dictionary(yaml_dict)
        x_limit = PlotConfigXML.get_x_limit_from_dictionary(yaml_dict)
        y_limit = PlotConfigXML.get_y_limit_from_dictionary(yaml_dict)
        interpolation_rate = PlotConfigXML.get_interpolation_rate_from_dictionary(
            yaml_dict
        )
        dpi = PlotConfigXML.get_dpi_from_dictionary(yaml_dict)
        color = PlotConfigXML.get_color_from_dictionary(yaml_dict)

        return PlotConfigXML.from_values(
            y_offset=y_offset,
            x_limit=x_limit,
            y_limit=y_limit,
            interpolation_rate=interpolation_rate,
            dpi=dpi,
            color=color,
        )

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
        if xml is not None:
            x_limit_min: Optional[float] = PlotConfigXML.get_x_limit_min_from_xml(xml)
            x_limit_max: Optional[float] = PlotConfigXML.get_x_limit_max_from_xml(xml)
            y_limit_min: Optional[float] = PlotConfigXML.get_y_limit_min_from_xml(xml)
            y_limit_max: Optional[float] = PlotConfigXML.get_y_limit_max_from_xml(xml)

            x_limit_range: Optional[Range[float]] = None
            y_limit_range: Optional[Range[float]] = None
            if x_limit_min is not None and x_limit_max is not None:
                x_limit_range = Range.from_list([x_limit_min, x_limit_max])

            if y_limit_min is not None and y_limit_max is not None:
                y_limit_range = Range.from_list([y_limit_min, y_limit_max])

            plot_config_xml = PlotConfigXML.from_values(
                x_limit=x_limit_range,
                y_limit=y_limit_range,
                y_offset=PlotConfigXML.get_y_offset_from_xml(xml),
                interpolation_rate=PlotConfigXML.get_interpolation_rate_from_xml(xml),
                dpi=PlotConfigXML.get_dpi_from_xml(xml),
                color=PlotConfigXML.get_color_from_xml(xml),
                legend=PlotConfigXML.get_legend_from_xml(xml),
            )

            return plot_config_xml
        else:
            return PlotConfigXML()

    @classmethod
    def from_values(
        cls,
        y_offset: Optional[float] = None,
        x_limit: Optional[Range[float]] = None,
        y_limit: Optional[Range[float]] = None,
        interpolation_rate: Optional[float] = None,
        dpi: Optional[int] = None,
        color: Optional[str] = None,
        legend: Optional[str] = None,
    ):
        tree = ET.ElementTree(ET.fromstring(cls.TREE_SKELETON))

        if y_offset is not None:
            tree.find(PlotConfigOptionsXPATH.Y_OFFSET.value).text = str(y_offset)

        if x_limit is not None:
            tree.find(PlotConfigOptionsXPATH.X_LIMIT_MIN.value).text = str(x_limit.min)
            tree.find(PlotConfigOptionsXPATH.X_LIMIT_MAX.value).text = str(x_limit.max)

        if y_limit is not None:
            tree.find(PlotConfigOptionsXPATH.Y_LIMIT_MIN.value).text = str(y_limit.min)
            tree.find(PlotConfigOptionsXPATH.Y_LIMIT_MAX.value).text = str(y_limit.max)

        if interpolation_rate is not None:
            tree.find(PlotConfigOptionsXPATH.INTERPOLATION_RATE.value).text = str(
                interpolation_rate
            )

        if dpi is not None:
            tree.find(PlotConfigOptionsXPATH.DPI.value).text = str(dpi)

        if color is not None:
            tree.find(PlotConfigOptionsXPATH.COLOR.value).text = str(color)

        if legend is not None:
            tree.find(PlotConfigOptionsXPATH.LEGEND.value).text = str(legend)

        return cls.from_tree(tree)

    def to_yaml(self):
        yaml_string_data: str = ""

        yaml_string_list: List[str] = []

        y_offset = self.y_offset_to_yaml()
        if y_offset is not None:
            yaml_string_list.append(y_offset)

        x_limit = self.x_limit_to_yaml()
        if x_limit is not None:
            yaml_string_list.append(x_limit)

        y_limit = self.y_limit_to_yaml()
        if y_limit is not None:
            yaml_string_list.append(y_limit)

        interpolation_rate = self.interpolation_rate_to_yaml()
        if interpolation_rate is not None:
            yaml_string_list.append(interpolation_rate)

        dpi = self.dpi_to_yaml()
        if dpi is not None:
            yaml_string_list.append(dpi)

        color = self.color_to_yaml()
        if color is not None:
            yaml_string_list.append(color)

        legend = self.legend_to_yaml()
        if legend is not None:
            yaml_string_list.append(legend)

        yaml_string_data = "\n".join(yaml_string_list)

        return yaml_string_data

    # def __rich_repr__(self):
    #     yield "plot"
    #     yield "y_offset", self.y_offset, "NONE"
    #     yield "x_limit", self.x_limit, "NONE"
    #     yield "y_limit", self.y_limit, "NONE"
    #     yield "interpolation_rate", self.interpolation_rate, "NONE"
    #     yield "dpi", self.dpi, "NONE"
    #     yield "color", self.color, "NONE"

    def get_node(self):
        return self._tree.getroot()

    def print(self):
        root = self._tree.getroot()
        ET.indent(root)
        console.print(ET.tostring(root, encoding="unicode"))

    #########################
    # Options to Yaml
    #########################
    def y_offset_to_yaml(self) -> Optional[str]:
        if self.y_offset is not None:
            return f"{PlotConfigOptions.Y_OFFSET.value}: {self.y_offset}"
        else:
            return None

    def x_limit_to_yaml(self) -> Optional[str]:
        if self.x_limit is not None:
            return f"{PlotConfigOptions.X_LIMIT.value}: [{self.x_limit.min}, {self.x_limit.max}]"
        else:
            return None

    def y_limit_to_yaml(self) -> Optional[str]:
        if self.y_limit is not None:
            return f"{PlotConfigOptions.Y_LIMIT.value}: [{self.y_limit.min}, {self.y_limit.max}]"
        else:
            return None

    def interpolation_rate_to_yaml(self) -> Optional[str]:
        if self.interpolation_rate is not None:
            return f"{PlotConfigOptions.INTERPOLATION_RATE.value}: {self.interpolation_rate}"
        else:
            return None

    def dpi_to_yaml(self) -> Optional[str]:
        if self.dpi is not None:
            return f"{PlotConfigOptions.DPI.value}: {self.dpi}"
        else:
            return None

    def color_to_yaml(self) -> Optional[str]:
        if self.color is not None:
            return f"{PlotConfigOptions.COLOR.value}: '{self.color}'"
        else:
            return None

    def legend_to_yaml(self) -> Optional[str]:
        if self.legend is not None:
            return f"{PlotConfigOptions.LEGEND.value}: '{self.legend}'"
        else:
            return None

    #########################
    # Options from Dictionary
    #########################
    @staticmethod
    def get_y_offset_from_dictionary(dictionary: Dict) -> Optional[float]:
        y_offset: Optional[float] = dictionary.get(
            f"{PlotConfigOptions.Y_OFFSET}", None
        )

        if y_offset is not None:
            y_offset = float(y_offset)

        return y_offset

    @staticmethod
    def get_x_limit_from_dictionary(dictionary: Dict) -> Optional[Range[float]]:
        x_limit: Optional[Range[float]] = dictionary.get(
            f"{PlotConfigOptions.X_LIMIT}", None
        )

        if x_limit is not None:
            x_limit: Range[float] = Range[float].from_list(list(x_limit))

        return x_limit

    @staticmethod
    def get_y_limit_from_dictionary(dictionary: Dict) -> Optional[Range[float]]:
        y_limit: Optional[Range[float]] = dictionary.get(
            f"{PlotConfigOptions.Y_LIMIT}", None
        )

        if y_limit is not None:
            y_limit: Range[float] = Range[float].from_list(list(y_limit))

        return y_limit

    @staticmethod
    def get_interpolation_rate_from_dictionary(dictionary: Dict) -> Optional[float]:
        interpolation_rate: Optional[float] = dictionary.get(
            f"{PlotConfigOptions.INTERPOLATION_RATE}", None
        )

        if interpolation_rate is not None:
            interpolation_rate = float(interpolation_rate)

        return interpolation_rate

    @staticmethod
    def get_dpi_from_dictionary(dictionary: Dict) -> Optional[int]:
        dpi: Optional[int] = dictionary.get(f"{PlotConfigOptions.DPI}", None)

        if dpi is not None:
            dpi = int(dpi)

        return dpi

    @staticmethod
    def get_color_from_dictionary(dictionary: Dict) -> Optional[str]:
        color: Optional[str] = dictionary.get(f"{PlotConfigOptions.COLOR}", None)

        if color is not None:
            color = str(color)

        return color

    @staticmethod
    def get_legend_from_dictionary(dictionary: Dict) -> Optional[str]:
        legend: Optional[str] = dictionary.get(f"{PlotConfigOptions.LEGEND}", None)

        if legend is not None:
            legend = str(legend)

        return legend

    ##################
    # Options from XML
    ##################
    @staticmethod
    def _get_property_from_xml(xml: Optional[ET.ElementTree], XPath: str):
        if xml is not None:
            prop = xml.find(XPath)

            if prop is not None:
                return prop.text

    @staticmethod
    def get_x_limit_min_from_xml(xml: Optional[ET.ElementTree]):
        x_limit_min = PlotConfigXML._get_property_from_xml(
            xml, PlotConfigOptionsXPATH.X_LIMIT_MIN.value
        )
        if x_limit_min is not None:
            return float(x_limit_min)

        return None

    @staticmethod
    def get_x_limit_max_from_xml(xml: Optional[ET.ElementTree]):
        x_limit_max = PlotConfigXML._get_property_from_xml(
            xml, PlotConfigOptionsXPATH.X_LIMIT_MAX.value
        )
        if x_limit_max is not None:
            return float(x_limit_max)

        return None

    @staticmethod
    def get_x_limit_from_xml(xml: Optional[ET.ElementTree]):
        x_limit_min: Optional[float] = PlotConfigXML.get_x_limit_min_from_xml(xml)
        x_limit_max: Optional[float] = PlotConfigXML.get_x_limit_max_from_xml(xml)

        x_limit_range: Optional[Range[float]] = None
        if x_limit_min is not None and x_limit_max is not None:
            x_limit_range = Range.from_list([x_limit_min, x_limit_max])

        return x_limit_range

    @staticmethod
    def get_y_limit_min_from_xml(xml: Optional[ET.ElementTree]):
        y_limit_min = PlotConfigXML._get_property_from_xml(
            xml, PlotConfigOptionsXPATH.Y_LIMIT_MIN.value
        )
        if y_limit_min is not None:
            return float(y_limit_min)

        return None

    @staticmethod
    def get_y_limit_max_from_xml(xml: Optional[ET.ElementTree]):
        y_limit_max = PlotConfigXML._get_property_from_xml(
            xml, PlotConfigOptionsXPATH.Y_LIMIT_MAX.value
        )
        if y_limit_max is not None:
            return float(y_limit_max)

        return None

    @staticmethod
    def get_y_limit_from_xml(xml: Optional[ET.ElementTree]):
        y_limit_min: Optional[float] = PlotConfigXML.get_y_limit_min_from_xml(xml)
        y_limit_max: Optional[float] = PlotConfigXML.get_y_limit_max_from_xml(xml)

        y_limit_range: Optional[Range[float]] = None

        if y_limit_min is not None and y_limit_max is not None:
            y_limit_range = Range.from_list([y_limit_min, y_limit_max])

        return y_limit_range

    @staticmethod
    def get_y_offset_from_xml(xml: Optional[ET.ElementTree]):
        y_offset = PlotConfigXML._get_property_from_xml(
            xml, PlotConfigOptionsXPATH.Y_OFFSET.value
        )
        if y_offset is not None:
            return float(y_offset)

        return None

    @staticmethod
    def get_interpolation_rate_from_xml(xml: Optional[ET.ElementTree]):
        interpolation_rate = PlotConfigXML._get_property_from_xml(
            xml, PlotConfigOptionsXPATH.INTERPOLATION_RATE.value
        )
        if interpolation_rate is not None:
            return float(interpolation_rate)

        return None

    @staticmethod
    def get_dpi_from_xml(xml: Optional[ET.ElementTree]):
        dpi = PlotConfigXML._get_property_from_xml(
            xml, PlotConfigOptionsXPATH.DPI.value
        )
        if dpi is not None:
            return float(dpi)

        return None

    @staticmethod
    def get_color_from_xml(xml: Optional[ET.ElementTree]):
        color = PlotConfigXML._get_property_from_xml(
            xml, PlotConfigOptionsXPATH.COLOR.value
        )
        return color

    @staticmethod
    def get_legend_from_xml(xml: Optional[ET.ElementTree]):
        legend = PlotConfigXML._get_property_from_xml(
            xml, PlotConfigOptionsXPATH.LEGEND.value
        )
        return legend

    ####################
    # Options from Class
    ####################
    @property
    def y_offset(self):
        return self.get_y_offset_from_xml(self._tree)

    @property
    def x_limit(self) -> Optional[Range[float]]:
        return self.get_x_limit_from_xml(self._tree)

    @property
    def y_limit(self) -> Optional[Range[float]]:
        return self.get_y_limit_from_xml(self._tree)

    @property
    def interpolation_rate(self):
        return self.get_interpolation_rate_from_xml(self._tree)

    @property
    def dpi(self):
        return self.get_dpi_from_xml(self._tree)

    @property
    def color(self):
        return self.get_color_from_xml(self._tree)

    @property
    def legend(self):
        return self.get_legend_from_xml(self._tree)

    def override(
        self,
        y_offset: Optional[float] = None,
        x_limit: Optional[Range[float]] = None,
        y_limit: Optional[Range[float]] = None,
        interpolation_rate: Optional[float] = None,
        dpi: Optional[int] = None,
        color: Optional[str] = None,
        legend: Optional[str] = None,
        new_config: Optional[PlotConfigXML] = None,
    ):
        if new_config is not None:
            self._set_y_offset(new_config.y_offset)
            self._set_x_limit(new_config.x_limit)
            self._set_y_limit(new_config.y_limit)
            self._set_interpolation_rate(new_config.interpolation_rate)
            self._set_dpi(new_config.dpi)
            self._set_color(new_config.color)
            self._set_legend(new_config.legend)

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

        if legend is not None:
            self._set_legend(legend)

    def _set_y_offset(self, y_offset: Optional[float]):
        if y_offset is not None:
            self._tree.find(PlotConfigOptionsXPATH.Y_OFFSET.value).text = str(y_offset)

    def _set_x_limit(self, x_limit: Optional[Range[float]]):
        if x_limit is not None:
            self._tree.find(PlotConfigOptionsXPATH.X_LIMIT_MIN.value).text = str(
                x_limit.min
            )
            self._tree.find(PlotConfigOptionsXPATH.X_LIMIT_MAX.value).text = str(
                x_limit.max
            )

    def _set_y_limit(self, y_limit: Optional[Range[float]]):
        if y_limit is not None:
            self._tree.find(PlotConfigOptionsXPATH.Y_LIMIT_MIN.value).text = str(
                y_limit.min
            )
            self._tree.find(PlotConfigOptionsXPATH.Y_LIMIT_MAX.value).text = str(
                y_limit.max
            )

    def _set_interpolation_rate(self, interpolation_rate: Optional[float]):
        if interpolation_rate is not None:
            self._tree.find(PlotConfigOptionsXPATH.INTERPOLATION_RATE.value).text = str(
                interpolation_rate
            )

    def _set_dpi(self, dpi: Optional[float]):
        if dpi is not None:
            self._tree.find(PlotConfigOptionsXPATH.DPI.value).text = str(dpi)

    def _set_color(self, color: Optional[str]):
        if color is not None:
            self._tree.find(PlotConfigOptionsXPATH.COLOR.value).text = str(color)

    def _set_legend(self, legend: Optional[str]):
        if legend is not None:
            self._tree.find(PlotConfigOptionsXPATH.LEGEND.value).text = str(legend)


@dataclass
@rich.repr.auto
class PlotConfig:
    y_offset: Optional[float] = None
    x_limit: Optional[Range[float]] = None
    y_limit: Optional[Range[float]] = None
    interpolation_rate: Optional[float] = None
    dpi: Optional[int] = None
    color: Optional[str] = None
    legend: Optional[str] = None
    title: Optional[str] = None

    @classmethod
    def from_xml(cls, xml: Optional[ET.ElementTree]):
        if xml is not None:
            return cls(
                y_offset=PlotConfig.get_y_offset_from_xml(xml),
                x_limit=PlotConfig.get_x_limit_from_xml(xml),
                y_limit=PlotConfig.get_y_limit_from_xml(xml),
                interpolation_rate=PlotConfig.get_interpolation_rate_from_xml(xml),
                dpi=PlotConfig.get_dpi_from_xml(xml),
                color=PlotConfig.get_color_from_xml(xml),
                legend=PlotConfig.get_legend_from_xml(xml),
                title=PlotConfig.get_title_from_xml(xml),
            )
        else:
            return cls()

    def to_yaml(self):
        yaml_string_data: str = ""

        yaml_string_list: List[str] = []

        y_offset = self.y_offset_to_yaml()
        if y_offset is not None:
            yaml_string_list.append(y_offset)

        x_limit = self.x_limit_to_yaml()
        if x_limit is not None:
            yaml_string_list.append(x_limit)

        y_limit = self.y_limit_to_yaml()
        if y_limit is not None:
            yaml_string_list.append(y_limit)

        interpolation_rate = self.interpolation_rate_to_yaml()
        if interpolation_rate is not None:
            yaml_string_list.append(interpolation_rate)

        dpi = self.dpi_to_yaml()
        if dpi is not None:
            yaml_string_list.append(dpi)

        color = self.color_to_yaml()
        if color is not None:
            yaml_string_list.append(color)

        legend = self.legend_to_yaml()
        if legend is not None:
            yaml_string_list.append(legend)

        yaml_string_data = "\n".join(yaml_string_list)

        return yaml_string_data

    #########################
    # Options to Yaml
    #########################
    def y_offset_to_yaml(self) -> Optional[str]:
        if self.y_offset is not None:
            return f"{PlotConfigOptions.Y_OFFSET.value}: {self.y_offset}"
        else:
            return None

    def x_limit_to_yaml(self) -> Optional[str]:
        if self.x_limit is not None:
            return f"{PlotConfigOptions.X_LIMIT.value}: [{self.x_limit.min}, {self.x_limit.max}]"
        else:
            return None

    def y_limit_to_yaml(self) -> Optional[str]:
        if self.y_limit is not None:
            return f"{PlotConfigOptions.Y_LIMIT.value}: [{self.y_limit.min}, {self.y_limit.max}]"
        else:
            return None

    def interpolation_rate_to_yaml(self) -> Optional[str]:
        if self.interpolation_rate is not None:
            return f"{PlotConfigOptions.INTERPOLATION_RATE.value}: {self.interpolation_rate}"
        else:
            return None

    def dpi_to_yaml(self) -> Optional[str]:
        if self.dpi is not None:
            return f"{PlotConfigOptions.DPI.value}: {self.dpi}"
        else:
            return None

    def color_to_yaml(self) -> Optional[str]:
        if self.color is not None:
            return f"{PlotConfigOptions.COLOR.value}: '{self.color}'"
        else:
            return None

    def legend_to_yaml(self) -> Optional[str]:
        if self.legend is not None:
            return f"{PlotConfigOptions.LEGEND.value}: '{self.legend}'"
        else:
            return None

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

    ##################
    # Options from XML
    ##################

    @staticmethod
    def get_x_limit_min_from_xml(xml: Optional[ET.ElementTree]):
        Ex_limit_min = xml.find(PlotConfigOptionsXPATH.X_LIMIT_MIN.value)
        if Ex_limit_min is not None:
            return float(Ex_limit_min.text)

        return None

    @staticmethod
    def get_x_limit_max_from_xml(xml: Optional[ET.ElementTree]):
        Ex_limit_max = xml.find(PlotConfigOptionsXPATH.X_LIMIT_MAX.value)
        if Ex_limit_max is not None:
            return float(Ex_limit_max.text)

        return None

    @staticmethod
    def get_x_limit_from_xml(xml: Optional[ET.ElementTree]):
        x_limit_min: Optional[float] = PlotConfigXML.get_x_limit_min_from_xml(xml)
        x_limit_max: Optional[float] = PlotConfigXML.get_x_limit_max_from_xml(xml)

        x_limit_range: Optional[Range[float]] = None
        if x_limit_min is not None and x_limit_max is not None:
            x_limit_range = Range.from_list([x_limit_min, x_limit_max])

        return x_limit_range

    @staticmethod
    def get_y_limit_min_from_xml(xml: Optional[ET.ElementTree]):
        Ey_limit_min = xml.find(PlotConfigOptionsXPATH.Y_LIMIT_MIN.value)
        if Ey_limit_min is not None:
            return float(Ey_limit_min.text)

        return None

    @staticmethod
    def get_y_limit_max_from_xml(xml: Optional[ET.ElementTree]):
        Ey_limit_max = xml.find(PlotConfigOptionsXPATH.Y_LIMIT_MAX.value)
        if Ey_limit_max is not None:
            return float(Ey_limit_max.text)

        return None

    @staticmethod
    def get_y_limit_from_xml(xml: Optional[ET.ElementTree]):
        y_limit_min: Optional[float] = PlotConfigXML.get_y_limit_min_from_xml(xml)
        y_limit_max: Optional[float] = PlotConfigXML.get_y_limit_max_from_xml(xml)

        y_limit_range: Optional[Range[float]] = None

        if y_limit_min is not None and y_limit_max is not None:
            y_limit_range = Range.from_list([y_limit_min, y_limit_max])

        return y_limit_range

    @staticmethod
    def get_y_offset_from_xml(xml: Optional[ET.ElementTree]):
        Ey_offset = xml.find(PlotConfigOptionsXPATH.Y_OFFSET.value)
        if Ey_offset is not None:
            return float(Ey_offset.text)

        return None

    @staticmethod
    def get_interpolation_rate_from_xml(xml: Optional[ET.ElementTree]):
        Einterpolation_rate = xml.find(PlotConfigOptionsXPATH.INTERPOLATION_RATE.value)
        if Einterpolation_rate is not None:
            return float(Einterpolation_rate.text)

        return None

    @staticmethod
    def get_dpi_from_xml(xml: Optional[ET.ElementTree]):
        Edpi = xml.find(PlotConfigOptionsXPATH.DPI.value)
        if Edpi is not None:
            return float(Edpi.text)

        return None

    @staticmethod
    def get_color_from_xml(xml: Optional[ET.ElementTree]):
        Ecolor = xml.find(PlotConfigOptionsXPATH.COLOR.value)
        if Ecolor is not None:
            return Ecolor.text
        return None

    @staticmethod
    def get_legend_from_xml(xml: Optional[ET.ElementTree]):
        Elegend = xml.find(PlotConfigOptionsXPATH.LEGEND.value)
        if Elegend is not None:
            return Elegend.text
        return None

    @staticmethod
    def get_title_from_xml(xml: Optional[ET.ElementTree]):
        Etitle = xml.find(PlotConfigOptionsXPATH.TITLE.value)
        if Etitle is not None:
            return Etitle.text
        return None
