from __future__ import annotations
from enum import Enum

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import rich
import yaml

from audio.config.type import Range
from audio.console import console
from functools import singledispatchmethod


class PlotConfigOptions(Enum):
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

    def __str__(self) -> str:
        return str(self.value)


@rich.repr.auto
class PlotConfigXML:
    _tree_skeleton: str = """
        <plot>
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
        </plot>
        """.format(
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
    )

    _tree: ET.ElementTree

    def __init__(self) -> None:
        self._tree = ET.ElementTree(ET.fromstring(self._tree_skeleton))

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

        if dictionary is not None:
            y_offset = PlotConfigXML.get_y_offset_from_dictionary(dictionary)
            x_limit = PlotConfigXML.get_x_limit_from_dictionary(dictionary)
            y_limit = PlotConfigXML.get_y_limit_from_dictionary(dictionary)
            interpolation_rate = PlotConfigXML.get_interpolation_rate_from_dictionary(
                dictionary
            )
            dpi = PlotConfigXML.get_dpi_from_dictionary(dictionary)
            color = PlotConfigXML.get_color_from_dictionary(dictionary)

        return cls.from_values(
            y_offset=y_offset,
            x_limit=x_limit,
            y_limit=y_limit,
            interpolation_rate=interpolation_rate,
            dpi=dpi,
            color=color,
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
    def from_values(
        cls,
        y_offset: Optional[float] = None,
        x_limit: Optional[Range[float]] = None,
        y_limit: Optional[Range[float]] = None,
        interpolation_rate: Optional[float] = None,
        dpi: Optional[int] = None,
        color: Optional[str] = None,
    ):
        tree = ET.ElementTree(ET.fromstring(cls._tree_skeleton))

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

        yaml_string_data = "\n".join(yaml_string_list)

        return yaml_string_data

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
            return f"{PlotConfigOptions.Y_OFFSET}: {self.y_offset}"
        else:
            return None

    def x_limit_to_yaml(self) -> Optional[str]:
        if self.x_limit is not None:
            return (
                f"{PlotConfigOptions.X_LIMIT}: [{self.x_limit.min}, {self.x_limit.max}]"
            )
        else:
            return None

    def y_limit_to_yaml(self) -> Optional[str]:
        if self.y_limit is not None:
            return (
                f"{PlotConfigOptions.Y_LIMIT}: [{self.y_limit.min}, {self.y_limit.max}]"
            )
        else:
            return None

    def interpolation_rate_to_yaml(self) -> Optional[str]:
        if self.interpolation_rate is not None:
            return f"{PlotConfigOptions.INTERPOLATION_RATE}: {self.interpolation_rate}"
        else:
            return None

    def dpi_to_yaml(self) -> Optional[str]:
        if self.dpi is not None:
            return f"{PlotConfigOptions.DPI}: {self.dpi}"
        else:
            return None

    def color_to_yaml(self) -> Optional[str]:
        if self.color is not None:
            return f"{PlotConfigOptions.COLOR}: '{self.color}'"
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

    ##################
    # Options from XML
    ##################
    @staticmethod
    def get_y_offset_from_xml(xml_tree: ET.ElementTree):
        y_offset_text: Optional[str] = xml_tree.find(
            f"{PlotConfigOptionsXPATH.Y_OFFSET}"
        ).text
        y_offset: Optional[float] = None

        if y_offset_text is not None:

            y_offset = float(y_offset_text)

        return y_offset

    @staticmethod
    def get_x_limit_from_xml(xml_tree: ET.ElementTree):

        x_limit: Optional[Range[float]] = None
        x_limit_min_text: Optional[str] = xml_tree.find(
            PlotConfigOptionsXPATH.X_LIMIT_MIN.value
        ).text
        x_limit_max_text: Optional[str] = xml_tree.find(
            PlotConfigOptionsXPATH.X_LIMIT_MAX.value
        ).text

        x_limit_min: Optional[float] = None
        x_limit_max: Optional[float] = None

        if x_limit_min_text is not None and x_limit_max_text is not None:
            x_limit_min = float(x_limit_min_text)
            x_limit_max = float(x_limit_max_text)
            x_limit = Range(x_limit_min, x_limit_max)

        return x_limit

    @staticmethod
    def get_y_limit_from_xml(xml_tree: ET.ElementTree):
        y_limit: Optional[Range[float]] = None
        y_limit_min_text: Optional[str] = xml_tree.find(
            PlotConfigOptionsXPATH.Y_LIMIT_MIN.value
        ).text
        y_limit_max_text: Optional[str] = xml_tree.find(
            PlotConfigOptionsXPATH.Y_LIMIT_MAX.value
        ).text

        y_limit_min: Optional[float] = None
        y_limit_max: Optional[float] = None

        if y_limit_min_text is not None and y_limit_max_text is not None:
            y_limit_min = float(y_limit_min_text)
            y_limit_max = float(y_limit_max_text)
            y_limit = Range(y_limit_min, y_limit_max)

        return y_limit

    @staticmethod
    def get_interpolation_rate_from_xml(xml_tree: ET.ElementTree):
        interpolation_rate_text: Optional[float] = xml_tree.find(
            PlotConfigOptionsXPATH.INTERPOLATION_RATE.value
        ).text

        interpolation_rate: Optional[float] = None

        if interpolation_rate_text is not None:
            interpolation_rate = float(interpolation_rate_text)

        return interpolation_rate

    @staticmethod
    def get_dpi_from_xml(xml_tree: ET.ElementTree):
        dpi_text: Optional[str] = xml_tree.find(PlotConfigOptionsXPATH.DPI.value).text
        dpi: Optional[int] = None

        if dpi_text is not None:
            dpi = int(dpi_text)

        return dpi

    @staticmethod
    def get_color_from_xml(xml_tree: ET.ElementTree):
        color: Optional[str] = xml_tree.find(PlotConfigOptionsXPATH.COLOR.value).text

        if color is not None:
            color = str(color)

        return color

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

    def override(
        self,
        y_offset: Optional[float] = None,
        x_limit: Optional[Range[float]] = None,
        y_limit: Optional[Range[float]] = None,
        interpolation_rate: Optional[float] = None,
        dpi: Optional[int] = None,
        color: Optional[float] = None,
        new_config: Optional[PlotConfigXML] = None,
    ):
        if new_config is not None:
            self._set_y_offset(new_config.y_offset)
            self._set_x_limit(new_config.x_limit)
            self._set_y_limit(new_config.y_limit)
            self._set_interpolation_rate(new_config.interpolation_rate)
            self._set_dpi(new_config.dpi)
            self._set_color(new_config.color)

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

    def _set_color(self, color: Optional[float]):
        if color is not None:
            self._tree.find(PlotConfigOptionsXPATH.COLOR.value).text = str(color)
