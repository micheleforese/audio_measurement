import pathlib
from typing import List, Optional

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

        text = data.get_value(["text"], str)
        if text is not None:
            return cls(text)
        else:
            return None


@rich.repr.auto
class ProcedureSetLevel(ProcedureStep):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @classmethod
    def from_dict(cls, data: Config_Dict):

        name = data.get_value(["name"], str)
        if name is not None:
            return cls(name)
        else:
            return None


@rich.repr.auto
class ProcedureSweep(ProcedureStep):
    name: str

    config: SweepConfig

    def __init__(self, name: str, config: SweepConfig) -> None:
        self.name = name
        self.config = config

    @classmethod
    def from_dict(cls, data: Config_Dict):

        name = data.get_value(["name"], str)
        config = SweepConfig.from_dict(Config_Dict(data.get_value(["config"])))
        if name is not None and config is not None:
            return cls(name, config)
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
                procedure: Optional[ProcedureStep]

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
                else:
                    raise Exception

                if procedure is not None:
                    steps.append(procedure)
                else:
                    raise Exception

            return cls(procedure_name, steps)
        else:
            return None
