from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Self

if typing.TYPE_CHECKING:
    from pathlib import Path
    from xml.etree import ElementTree


class DecoderXML(ABC):
    @classmethod
    @abstractmethod
    def from_xml_file(cls: type[Self], file: Path) -> Self | None:
        pass

    @classmethod
    @abstractmethod
    def from_xml_string(cls: type[Self], data: str) -> Self | None:
        pass

    @classmethod
    @abstractmethod
    def from_xml_object(
        cls: type[Self],
        xml: ElementTree.ElementTree | None,
    ) -> Self | None:
        pass

    @staticmethod
    @abstractmethod
    def xml_is_valid(xml: ElementTree.ElementTree) -> bool:
        pass
