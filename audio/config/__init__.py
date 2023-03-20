from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self


class Config(ABC):
    @abstractmethod
    def merge(self: Self, other: Self | None) -> None:
        pass

    @abstractmethod
    def override(self: Self, other: Self | None) -> None:
        pass

    @abstractmethod
    def print_object(self: Self) -> None:
        pass
