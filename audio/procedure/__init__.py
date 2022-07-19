import pathlib
from typing import List, Optional
from weakref import ProxyType

import rich

from audio.config import Config_Dict
from audio.config.sweep import SweepConfig
from audio.console import console


class ProcedureStep:
    pass


@rich.repr.auto
class ProcedureText(ProcedureStep):
    text: str

    def __init__(self, text: str) -> None:
        self.text = text

    @classmethod
    def from_dict(cls, data: Config_Dict):

        text = data.get_rvalue(["text"], str)
        if text is not None:
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
    def from_dict(cls, data: Config_Dict):

        name = data.get_rvalue(["name"], str)
        config = SweepConfig.from_dict(Config_Dict(data.get_rvalue(["config"])))

        if name is not None and config is not None:
            return cls(name, config)
        else:
            return None


@rich.repr.auto
class ProcedureSweep(ProcedureStep):
    name: str
    set_level: str
    name_plot: str
    config: Optional[SweepConfig]

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
    def from_dict(cls, data: Config_Dict):

        name = data.get_rvalue(["name"], str)
        set_level = data.get_rvalue(["set_level"], str)
        name_plot = data.get_rvalue(["name_plot"], str)
        config = SweepConfig.from_dict(Config_Dict(data.get_rvalue(["config"])))

        if (
            name is not None
            and config is not None
            and set_level is not None
            and name_plot is not None
        ):
            return cls(name, set_level, name_plot, config)
        else:
            return None


@rich.repr.auto
class ProcedureSerialNumber(ProcedureStep):

    text: str

    def __init__(self, text: str) -> None:
        self.text = text

    @classmethod
    def from_dict(cls, data: Config_Dict):

        text = data.get_rvalue(["text"], str)

        if text is not None:
            return cls(text)
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
    def from_dict(cls, data: Config_Dict):

        name = data.get_rvalue(["name"], str)
        set_level = data.get_rvalue(["set_level"], str)

        if name is not None and set_level is not None:
            return cls(name, set_level)
        else:
            return None


@rich.repr.auto
class ProcedurePrint(ProcedureStep):

    variables: List[str] = []

    def __init__(self, variables: List[str]) -> None:
        self.variables = variables

    @classmethod
    def from_dict(cls, data: Config_Dict):

        variables = data.get_rvalue(["variables"], List[str])

        if variables is not None:
            return cls(variables)
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
        data = Config_Dict.from_json(procedure_path)

        if data is not None:
            procedure_data = Config_Dict.from_dict(data.get_rvalue(["procedure"]))

            procedure_name = procedure_data.get_rvalue(["name"], str)

            procedure_steps = Config_Dict.from_dict(
                procedure_data.get_rvalue(["steps"])
            )

            steps: List[ProcedureStep] = []

            for idx, step in enumerate(procedure_steps.data):
                procedure_type: str = step["type"]
                procedure: Optional[ProcedureStep] = None

                if procedure_type == "text":
                    procedure = ProcedureText.from_dict(
                        Config_Dict.from_dict(step["step"])
                    )
                elif procedure_type == "set-level":
                    procedure = ProcedureSetLevel.from_dict(
                        Config_Dict.from_dict(step["step"])
                    )
                elif procedure_type == "sweep":
                    procedure = ProcedureSweep.from_dict(
                        Config_Dict.from_dict(step["step"])
                    )
                elif procedure_type == "serial-number":
                    procedure = ProcedureSerialNumber.from_dict(
                        Config_Dict.from_dict(step["step"])
                    )
                elif procedure_type == "insertion-gain":
                    procedure = ProcedureInsertionGain.from_dict(
                        Config_Dict.from_dict(step["step"])
                    )
                elif procedure_type == "print":
                    procedure = ProcedurePrint.from_dict(
                        Config_Dict.from_dict(step["step"])
                    )
                else:
                    procedure = ProcedureStep()

                if procedure is not None:
                    steps.append(procedure)
                else:
                    raise Exception

            return cls(procedure_name, steps)
        else:
            return None
