import pathlib
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Type, TypeVar, cast

from pyjson5 import decode as py_json5_decode

from audio.console import console
from audio.type import Dictionary


def json5_to_dict(config_file_path: pathlib.Path):

    with open(config_file_path, encoding="utf-8") as config_file:
        file_content: str = config_file.read()
        return json5_string_to_dict(file_content)


def json5_string_to_dict(data: str):
    config: Dict = dict(py_json5_decode(data))
    return config


class Dict(object):
    data: Any

    def __init__(self, data: Any) -> None:
        self.data = data

    @classmethod
    def from_json(cls, config_file_path: pathlib.Path):
        with open(config_file_path, encoding="utf-8") as config_file:
            file_content: str = config_file.read()
            config = py_json5_decode(file_content)

            if config is not None:
                return cls(config)
            else:
                return None

    @classmethod
    def from_dict(cls, data: Optional[Any]):
        if data is not None:
            return cls(data)
        else:
            return None

    T = TypeVar("T")

    def get_value(self, path: List[str], type_value: Type[T] = Any) -> Optional[T]:
        value: Any = self.data

        for p in path:
            try:
                value = value[p]
            except KeyError:
                return None

        return cast(type_value, value)

    T = TypeVar("T")

    def get_rvalue(self, path: List[str], type_value: Type[T] = Any) -> T:

        value: Any = self.data

        for p in path:
            try:
                value = value[p]
            except KeyError:
                console.print(
                    "Config [blue][{}][/blue] must be provided".format("/".join(path)),
                    style="error",
                )
                exit()

        return cast(type_value, value)
