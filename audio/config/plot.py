from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Dict, Optional

import rich
import yaml

from audio.config.type import Range
from audio.console import console


@rich.repr.auto
class PlotConfigXML:
    _tree_skeleton: str = """
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

        return cls.from_tree(tree)

    def get_node(self):
        return self._tree.getroot()

    def print(self):
        root = self._tree.getroot()
        ET.indent(root)
        console.print(ET.tostring(root, encoding="unicode"))

    #########################
    # Options from Dictionary
    #########################
    @staticmethod
    def get_y_offset_from_dictionary(dictionary: Dict) -> Optional[float]:
        y_offset: Optional[float] = dictionary.get("y_offset", None)

        if y_offset is not None:
            y_offset = float(y_offset)

        return y_offset

    @staticmethod
    def get_x_limit_from_dictionary(dictionary: Dict) -> Optional[Range[float]]:
        x_limit: Optional[Range[float]] = dictionary.get("x_limit", None)

        if x_limit is not None:
            x_limit: Range[float] = Range[float].from_list(list(x_limit))

        return x_limit

    @staticmethod
    def get_y_limit_from_dictionary(dictionary: Dict) -> Optional[Range[float]]:
        y_limit: Optional[Range[float]] = dictionary.get("y_limit", None)

        if y_limit is not None:
            y_limit: Range[float] = Range[float].from_list(list(y_limit))

        return y_limit

    @staticmethod
    def get_interpolation_rate_from_dictionary(dictionary: Dict) -> Optional[float]:
        interpolation_rate: Optional[float] = dictionary.get("interpolation_rate", None)

        if interpolation_rate is not None:
            interpolation_rate = float(interpolation_rate)

        return interpolation_rate

    @staticmethod
    def get_dpi_from_dictionary(dictionary: Dict) -> Optional[int]:
        dpi: Optional[int] = dictionary.get("dpi", None)

        if dpi is not None:
            dpi = int(dpi)

        return dpi

    @staticmethod
    def get_color_from_dictionary(dictionary: Dict) -> Optional[str]:
        color: Optional[str] = dictionary.get("color", None)

        if color is not None:
            color = str(color)

        return color

    ##################
    # Options from XML
    ##################
    @staticmethod
    def get_y_offset_from_xml(xml_tree: ET.ElementTree):
        y_offset_text: Optional[str] = xml_tree.find("./y_offset").text
        y_offset: Optional[float] = None

        if y_offset_text is not None:

            y_offset = float(y_offset_text)

        return y_offset

    @staticmethod
    def get_x_limit_from_xml(xml_tree: ET.ElementTree):

        x_limit: Optional[Range[float]] = None
        x_limit_min_text: Optional[str] = xml_tree.find("./x_limit/min").text
        x_limit_max_text: Optional[str] = xml_tree.find("./x_limit/max").text

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
        y_limit_min_text: Optional[str] = xml_tree.find("./y_limit/min").text
        y_limit_max_text: Optional[str] = xml_tree.find("./y_limit/max").text

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
            "./interpolation_rate"
        ).text

        interpolation_rate: Optional[float] = None

        if interpolation_rate_text is not None:
            interpolation_rate = float(interpolation_rate_text)

        return interpolation_rate

    @staticmethod
    def get_dpi_from_xml(xml_tree: ET.ElementTree):
        dpi_text: Optional[str] = xml_tree.find("./dpi").text
        dpi: Optional[int] = None

        if dpi_text is not None:
            dpi = int(dpi_text)

        return dpi

    @staticmethod
    def get_color_from_xml(xml_tree: ET.ElementTree):
        color: Optional[str] = xml_tree.find("./color").text

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
