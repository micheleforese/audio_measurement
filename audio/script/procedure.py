from datetime import datetime
from math import log10

import pathlib
from typing import Optional
import click
from audio.config import Dict
from audio.console import console
from audio.procedure import (
    Procedure,
    ProcedureInsertionGain,
    ProcedurePrint,
    ProcedureSerialNumber,
    ProcedureSetLevel,
    ProcedureStep,
    ProcedureText,
)

from rich.prompt import Prompt
from rich.prompt import Confirm

from audio.sampling import config_set_level


@click.command(
    # context_settings={"ignore_unknown_options": True}
)
@click.argument("procedure_name", type=pathlib.Path)
@click.option(
    "--home",
    type=pathlib.Path,
    help="Home path, where the csv and plot image will be created.",
    default=pathlib.Path.cwd(),
    show_default=True,
)
def procedure(
    procedure_name: pathlib.Path,
    home: pathlib.Path,
):

    HOME_PATH = home

    datetime_now = datetime.now().strftime(r"%Y-%m-%d--%H-%M-%f")

    procedure = Procedure.from_json(procedure_path=procedure_name)

    console.print(f"Start Procedure: [blue]{procedure.name}")

    root: pathlib.Path = HOME_PATH
    data: Dict = dict()

    console.print(procedure.steps)

    for idx, step in enumerate(procedure.steps):

        if isinstance(step, ProcedureText):
            step: ProcedureText = step
            console.print(f"{idx}: ProcedureText()")

            confirm: bool = False

            while not confirm:
                confirm = Confirm.ask(step.text)

        elif isinstance(step, ProcedureSetLevel):
            step: ProcedureSetLevel = step
            console.print(f"{idx}: ProcedureSetLevel()")

            sampling_config = step.config

            set_level_file: pathlib.Path = pathlib.Path(root / step.name)
            plot_file: pathlib.Path = set_level_file.with_suffix(".png")

            config_set_level(
                config=sampling_config,
                plot_file_path=plot_file,
                set_level_file_path=set_level_file,
                debug=False,
            )
            data[step.name] = set_level_file

            console.print(data)
        elif isinstance(step, ProcedureSerialNumber):
            step: ProcedureSerialNumber = step
            console.print(f"{idx}: ProcedureSerialNumber()")

            console.print(step.text)

            confirm: bool = False

            while not confirm:
                serial_number = Prompt.ask("Inserisci il serial-number")

                confirm = Confirm.ask(
                    f"The serial-number is: '[blue bold]{serial_number}[/]'"
                )

            root = pathlib.Path(HOME_PATH / serial_number)

            console.print(f"Create Dir at: '{root}'")
            root.mkdir(parents=True, exist_ok=True)
        elif isinstance(step, ProcedureInsertionGain):
            step: ProcedureInsertionGain = step

            calibration_path: pathlib.Path = pathlib.Path(
                HOME_PATH / "calibration.config.set_level"
            )
            gain_file_path: pathlib.Path = pathlib.Path(root / step.name)

            set_level_file: pathlib.Path = pathlib.Path(root / step.set_level)

            calibration: float = float(calibration_path.read_text(encoding="utf-8"))
            set_level: float = float(set_level_file.read_text(encoding="utf-8"))

            gain: float = 20 * log10(calibration / set_level)

            gain_file_path.write_text(f"{gain:.5}", encoding="utf-8")

            console.print(f"GAIN: {gain} dB.")
        elif isinstance(step, ProcedurePrint):
            step: ProcedurePrint = step

            for var in step.variables:
                console.print(
                    "{}: {}".format(
                        var, pathlib.Path(data[var]).read_text(encoding="utf-8")
                    )
                )

        elif isinstance(step, ProcedureStep):
            console.print(f"{idx}: ProcedureStep()")
