import pathlib
from datetime import datetime
from math import log10
from typing import Dict

import click
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

# from audio.config import Dict
from audio.console import console
from audio.model.set_level import SetLevel
from audio.procedure import (
    Procedure,
    ProcedureInsertionGain,
    ProcedurePrint,
    ProcedureSerialNumber,
    ProcedureSetLevel,
    ProcedureStep,
    ProcedureSweep,
    ProcedureText,
)
from audio.sampling import config_set_level, plot_from_csv, sampling_curve


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

    procedure = Procedure.from_json5_file(procedure_path=procedure_name)

    console.print(f"Start Procedure: [blue]{procedure.name}")

    root: pathlib.Path = HOME_PATH
    data: Dict = dict()

    console.print(procedure.steps)

    for idx, step in enumerate(procedure.steps):

        if isinstance(step, ProcedureText):
            step: ProcedureText = step
            console.print(Panel(f"{idx}: ProcedureText()"))

            confirm: bool = False

            while not confirm:
                confirm = Confirm.ask(step.text)

        elif isinstance(step, ProcedureSetLevel):
            step: ProcedureSetLevel = step
            console.print(Panel(f"{idx}: ProcedureSetLevel()"))

            sampling_config = step.config

            set_level_file: pathlib.Path = pathlib.Path(root / step.name)
            plot_file: pathlib.Path = set_level_file.with_suffix(".png")

            config_set_level(
                config=sampling_config,
                plot_file_path=plot_file,
                set_level_file_path=set_level_file,
                debug=True,
            )
            data[step.name] = set_level_file

            console.print(data)

        elif isinstance(step, ProcedureSerialNumber):
            step: ProcedureSerialNumber = step
            console.print(Panel(f"{idx}: ProcedureSerialNumber()"))

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

            console.print(Panel(f"{idx}: ProcedureInsertionGain()"))

            calibration_path: pathlib.Path = pathlib.Path(
                HOME_PATH / "calibration.config.set_level"
            )
            gain_file_path: pathlib.Path = pathlib.Path(root / step.name)

            set_level_file: pathlib.Path = pathlib.Path(root / step.set_level)

            calibration: float = SetLevel(calibration_path).set_level
            set_level: float = SetLevel(set_level_file).set_level

            gain: float = 20 * log10(calibration / set_level)

            gain_file_path.write_text(f"{gain:.5}", encoding="utf-8")

            data[step.name] = gain_file_path

            console.print(f"GAIN: {gain} dB.")

        elif isinstance(step, ProcedurePrint):
            step: ProcedurePrint = step

            console.print(Panel(f"{idx}: ProcedurePrint()"))

            for var in step.variables:
                console.print(
                    "{}: {}".format(
                        var, pathlib.Path(data[var]).read_text(encoding="utf-8")
                    )
                )

        elif isinstance(step, ProcedureSweep):
            step: ProcedureSweep = step
            console.print(Panel(f"{idx}: ProcedureSweep()"))

            sweep_config = step.config

            if sweep_config is None:
                console.print("sweep_config is None.", style="error")

            set_level = SetLevel(data[step.set_level]).set_level
            y_offset_dB = SetLevel(data[step.set_level]).y_offset_dB

            sweep_config.rigol.override(amplitude_peak_to_peak=set_level)
            sweep_config.plot.override(y_offset=y_offset_dB)
            sweep_config.print()

            measurement_file: pathlib.Path = root / (step.name + ".csv")
            plot_file: pathlib.Path = root / (step.name_plot + ".png")

            console.print(f"Measurement File: '{measurement_file}'")
            console.print(f"PLot File: '{plot_file}'")

            Confirm.ask()

            sampling_curve(
                config=sweep_config,
                measurements_file_path=measurement_file,
                debug=True,
            )

            plot_from_csv(
                measurements_file_path=measurement_file,
                plot_file_path=plot_file,
                sweep_config=sweep_config,
                debug=True,
            )

        elif isinstance(step, ProcedureStep):
            console.print(Panel(f"{idx}: ProcedureStep()"))
