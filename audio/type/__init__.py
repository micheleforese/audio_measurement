from __future__ import annotations

import pathlib
from typing import (
    Any,
    Generic,
    TypeVar,
)
from collections.abc import Callable

from pyjson5 import decode


T = TypeVar("T")


class Option(Generic[T]):

    value: T | None

    def __init__(self, value: T | None) -> None:
        self.value = value

    # def __str__(self) -> str:
    #     return f"{self.value}" if self.exists() else "NULL"

    def __rich_repr__(self):
        if self.exists():
            yield self.value
        else:
            yield "NONE"

    @classmethod
    def null(cls) -> Option[T]:
        return cls[T](None)

    def exists(self) -> bool:
        return not self.is_null

    @property
    def is_null(self) -> bool:
        return self.value is None

    @property
    def run(
        self,
        transform: Callable[[T], Option[T]],
    ):
        if self.value is None:
            return None

        return transform(self.value)


class Dictionary:
    _dict: dict

    def __init__(self, value: dict) -> None:
        self._dict = value

    @classmethod
    def from_json5_file(cls, path: pathlib.Path) -> Dictionary | None:

        if path.exists() and path.is_file():
            with open(path, encoding="utf-8") as config_file:
                file_content: str = config_file.read()
                return Dictionary.from_json5_string(file_content)

        return None

    @classmethod
    def from_json5_string(cls, data: str) -> Dictionary | None:
        _dict = dict(decode(data))

        return Dictionary(_dict)

    def get_dict(self) -> dict:
        return self._dict

    T = TypeVar("T")

    def update(
        self,
        property: list[str],
        data: Any = {},
        override: bool = False,
    ) -> Dictionary:

        if not len(property) > 0:
            raise Exception("Property must be at least len = 1")

        config = self.get_dict()

        if len(property) > 1:
            for p in property[:-1]:
                if p not in config.keys():
                    config[p] = {}

                config = config[p]

        prop = property[-1]
        if prop not in config.keys() or override:
            config[prop] = data

        return Dictionary(config[prop])

    T = TypeVar("T")

    def get_property(
        self,
        property_name: str,
        property_type: type[T] = Any,
    ) -> T | None:

        if property_name in self.get_dict().keys():  # we don't want KeyError
            return self._dict.get(property_name)

        return None  # just return None if not found

    def get(
        self,
        dict_path: str,
        property_type: type[T] = Any,
    ) -> T | None:

        dictionary = self.get_dict()

        for property in dict_path.split("."):
            if property in dictionary.keys():
                dictionary = dictionary.get(property, None)
            else:
                return None

        return dictionary
