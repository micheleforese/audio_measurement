from __future__ import annotations

import pathlib
from typing import Any, Callable, Dict, Generic, Optional, Type, TypeVar, cast, overload

import rich
from pyjson5 import decode

from audio.console import console

T = TypeVar("T")


class Option(Generic[T]):

    value: Optional[T]

    def __init__(self, value: Optional[T]) -> None:
        self.value = value

    # @overload
    # def __init__(self, option: Option[T]) -> None:
    #     self.value = option.value
    def __rich_repr__(self):
        if self.value is not None:
            yield self.value
        else:
            yield "NONE"

    @classmethod
    def null(cls) -> Option[T]:
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
                _dict = dict(decode(file_content))

                config: Option[Dict] = Option[Dict](_dict)

                return Option[Dictionary](config.value)

        return Option[Dictionary].null()

    def get_dict(self) -> Dict:
        return self._dict

    T = TypeVar("T")

    def update_property(
        self,
        data: T,
        data_type: Type[T] = Any,
    ):
        data = cast(data, data_type)
        self._dict.update(data)

    T = TypeVar("T")

    def get_property(
        self,
        property_name: str,
        property_type: Type[T] = Any,
    ) -> Option[T]:

        if property_name in self._dict.keys():  # we don't want KeyError
            return Option[property_type](
                cast(self._dict.get(property_name), property_type)
            )

        return Option[property_type].null()  # just return None if not found
