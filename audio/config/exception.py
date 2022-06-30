from typing import Any
from rich.text import Text


class ConfigException(Exception):
    message: str

    def __init__(self, message: str = "") -> None:
        self.message = message

    def __str__(self):
        return Text(
            r"[blue]\[Exception][/blue] ConfigException: {}".format(self.message)
        )


class ConfigError(ConfigException):
    message: str

    def __init__(self, message: str = "") -> None:
        self.message = message

    def __str__(self):
        return Text(r"[blue]\[Exception][/blue] ConfigError: {}".format(self.message))


class ConfigWarning(ConfigException):
    message: str

    def __init__(self, message: str = "") -> None:
        self.message = message

    def __str__(self):
        return Text(r"[blue]\[Exception][/blue] ConfigWarning: {}".format(self.message))


class ConfigNoneValueException(ConfigError):
    pass


class ConfigNoneValueError(ConfigNoneValueException):
    message: str
    value: Any

    def __init__(self) -> None:
        pass

    def __str__(self):
        return Text(
            r"[blue]\[Exception][/blue] ConfigNoneValueError: Value can't be None"
        )


class ConfigNoneValueWarning(ConfigNoneValueException):
    message: str
    value: Any

    def __init__(self) -> None:
        pass

    def __str__(self):
        return Text(
            r"[blue]\[Exception][/blue] ConfigNoneValueWarning: Value can't be None"
        )
