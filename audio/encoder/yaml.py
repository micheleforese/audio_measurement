from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class EncoderYAML(ABC):
    @abstractmethod
    def to_yaml_file(self, file: Path):
        pass

    @abstractmethod
    def to_yaml_string(self):
        pass

    # @abstractmethod
    # @classmethod
    # def to_yaml_object(cls, yaml: ET.Element):
    #     pass

    # @abstractmethod
    # @staticmethod
    # def yaml_is_valid(yaml: ET.Element) -> bool:
    #     pass
