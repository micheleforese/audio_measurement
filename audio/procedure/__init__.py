from __future__ import annotations
from asyncio import set_event_loop_policy
from calendar import c
import pathlib
from typing import Dict, List, Optional
from weakref import ProxyType
from pytest import console_main

import rich
from tomlkit import value

from audio.config import Config_Dict
from audio.config.sweep import SweepConfig
from audio.console import console
from audio.type import Dictionary, Option


class ProcedureStep:
    pass


@rich.repr.auto
class ProcedureText(ProcedureStep):
    text: str

    def __init__(self, text: str) -> None:
        self.text = text

    @classmethod
    def from_dict(cls, data: Dictionary):

        text = data.get_property("text", str)
        if text.exists():
            return cls(text)
        else:
            return None


@rich.repr.auto
class ProcedureSetLevel(ProcedureStep):
    name: str
    config: SweepConfig

    def __init__(self, name: str, config: SweepConfig) -> None:
        self.name = name
        self.config = config

    @classmethod
    def from_dict(cls, data: Dictionary):

        name = data.get_property("name", str)
        config = data.get_property("config")

        if not config.exists():
            raise Exception("config is NULL")

        config = Dictionary(dict(config.value))

        config = SweepConfig.from_dict(config)

        if name.exists() and config.exists():
            return cls(name.value, config.value)
        else:
            return None


@rich.repr.auto
class ProcedureSweep(ProcedureStep):
    name: str
    set_level: str
    name_plot: str
    config: SweepConfig

    def __init__(
        self,
        name: str,
        set_level: str,
        name_plot: str,
        config: SweepConfig,
    ) -> None:
        self.name = name
        self.set_level = set_level
        self.name_plot = name_plot
        self.config = config

    @classmethod
    def from_dict(cls, data: Dictionary):

        name = data.get_property("name", str)
        set_level = data.get_property("set_level", str)
        name_plot = data.get_property("name_plot", str)
        config = data.get_property("config")

        if not config.exists():
            raise Exception("config is NULL")

        config = SweepConfig.from_dict(Dictionary(dict(config.value)))

        if (
            name.exists()
            and config.exists()
            and set_level.exists()
            and name_plot.exists()
        ):
            return cls(name.value, set_level.value, name_plot.value, config.value)
        else:
            return None


@rich.repr.auto
class ProcedureSerialNumber(ProcedureStep):

    text: str

    def __init__(self, text: str) -> None:
        self.text = text

    @classmethod
    def from_dict(cls, data: Dictionary):

        text = data.get_property("text", str)

        if text.exists():
            return cls(text.value)
        else:
            return None


@rich.repr.auto
class ProcedureInsertionGain(ProcedureStep):

    name: str
    set_level: str

    def __init__(self, name: str, set_level: str) -> None:
        self.name = name
        self.set_level = set_level

    @classmethod
    def from_dict(cls, data: Dictionary):

        name = data.get_property("name", str)
        set_level = data.get_property("set_level", str)

        if name.exists() and set_level.exists():
            return cls(name.value, set_level.value)
        else:
            return None


@rich.repr.auto
class ProcedurePrint(ProcedureStep):

    variables: List[str] = []

    def __init__(self, variables: List[str]) -> None:
        self.variables = variables

    @classmethod
    def from_dict(cls, data: Dictionary):

        variables = data.get_property("variables", List[str])

        if variables.exists():
            return cls(variables.value)
        else:
            return None


@rich.repr.auto
class Procedure:

    name: str
    steps: List[ProcedureStep]

    def __init__(self, procedure_name: str, steps: List[ProcedureStep]) -> None:
        self.name = procedure_name
        self.steps = steps

    @classmethod
    def from_json(cls, procedure_path: pathlib.Path):
        data = Dictionary.from_json(procedure_path)

        if data.exists():

            procedure_data = data.value.get_property("procedure")
            procedure_data = Option[Dictionary](Dictionary(procedure_data.value))

            if not procedure_data.exists():
                raise Exception("procedure_data is NULL")

            procedure_name = procedure_data.value.get_property("name", str)
            procedure_steps = procedure_data.value.get_property(
                "steps", List[Dictionary]
            )

            steps: List[ProcedureStep] = []

            console.print("------------------------------------")

            for idx, step in enumerate(procedure_steps.value):
                step: Dictionary = Dictionary(step)
                procedure_type: Option[str] = step.get_property("type", str)

                if not procedure_type.exists():
                    raise Exception(f"procedure_type is NULL at idx: {idx}")

                console.print(procedure_type.value)

                procedure: Optional[ProcedureStep] = None

                procedure_type = procedure_type.value

                console.print(step.get_dict())

                step_obj = step.get_property("step")

                if not step_obj.exists():
                    raise Exception("step_obj is NULL")

                step_dictionary = Dictionary(dict(step_obj.value))

                if procedure_type == "text":
                    procedure = ProcedureText.from_dict(step_dictionary)
                elif procedure_type == "set-level":
                    procedure = ProcedureSetLevel.from_dict(step_dictionary)
                elif procedure_type == "sweep":
                    procedure = ProcedureSweep.from_dict(step_dictionary)
                elif procedure_type == "serial-number":
                    procedure = ProcedureSerialNumber.from_dict(step_dictionary)
                elif procedure_type == "insertion-gain":
                    procedure = ProcedureInsertionGain.from_dict(step_dictionary)
                elif procedure_type == "print":
                    procedure = ProcedurePrint.from_dict(step_dictionary)
                else:
                    procedure = ProcedureStep()

                if procedure is not None:
                    steps.append(procedure)
                else:
                    raise Exception

            return cls(procedure_name.value, steps)
        else:
            return None
