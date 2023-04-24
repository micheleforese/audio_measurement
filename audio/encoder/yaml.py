from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from pathlib import Path


class EncoderYAML(ABC):
    @abstractmethod
    def to_yaml_file(self: Self, file: Path) -> None:
        pass

    @abstractmethod
    def to_yaml_string(self: Self) -> str:
        pass

    # @abstractmethod
    # @classmethod
    # def to_yaml_object(cls, yaml: ET.Element):
    #     pass

    # @abstractmethod
    # @staticmethod
    # def yaml_is_valid(yaml: ET.Element) -> bool:
    #     pass
