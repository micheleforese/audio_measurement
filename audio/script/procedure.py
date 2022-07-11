from datetime import datetime

import pathlib
import click
from audio.console import console
from audio.procedure import Procedure, ProcedureSetLevel, ProcedureText


@click.command(context_settings={"ignore_unknown_options": True})
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

    for step in procedure.steps:

        if type(step) is ProcedureText:
            step: ProcedureText = step
            console.print(step.text)
        elif type(step) is ProcedureSetLevel:
            step: ProcedureSetLevel = step
