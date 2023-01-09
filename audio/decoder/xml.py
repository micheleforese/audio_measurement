from __future__ import annotations

import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from pathlib import Path


class DecoderXML(ABC):
    @classmethod
    @abstractmethod
    def from_xml_file(cls, file: Path):
        pass

    @classmethod
    @abstractmethod
    def from_xml_string(cls, data: str):
        pass

    @classmethod
    @abstractmethod
    def from_xml_object(cls, xml: ET.Element):
        pass

    @staticmethod
    @abstractmethod
    def xml_is_valid(xml: ET.Element) -> bool:
        pass
