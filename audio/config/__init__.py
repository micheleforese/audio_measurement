from abc import ABC, abstractmethod


class Config(ABC):
    @abstractmethod
    def merge(self, other):
        pass

    @abstractmethod
    def override(self, other):
        pass

    @abstractmethod
    def print(self):
        pass
