from __future__ import annotations

import pathlib
from typing import Any, Callable, Dict, Generic, Optional, Type, TypeVar, overload

from pyjson5 import decode
from audio.console import console

T = TypeVar("T")


class Option(Generic[T]):

    value: Optional[T]

    @overload
    def __init__(self, value: Optional[T]) -> None:
        self.value = value

    @overload
    def __init__(self, value: Option[T]) -> None:
        self.value = value

    @classmethod
    def null(cls) -> Optional[T]:
        return cls[T](None)

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
    _dict: Dict

    def __init__(self, value: Dict) -> None:
        self._dict = value

    @classmethod
    def from_json(cls, path: pathlib.Path) -> Option[Dictionary]:

        if path.exists() and path.is_file():
            with open(path, encoding="utf-8") as config_file:
                file_content: str = config_file.read()
                config: Option[Dict] = Option[Dict](dict(decode(file_content)))

                return Option[Dictionary](config.value)

        return Option[Dictionary].null()

    T = TypeVar("T")

    def get_property(
        self,
        property_name: str,
        property_type: Type[T] = Any,
    ) -> Option[T]:

        if property_name in self._dict.keys():  # we don't want KeyError
            return Option[property_type](self._dict.get(property_name))

        return Option[property_type].null()  # just return None if not found
