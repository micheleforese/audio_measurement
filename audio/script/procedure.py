import pathlib
from math import log10
from typing import Dict, List, cast, get_origin

import click
from rich import inspect
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from audio.config.sweep import SweepConfigXML

from audio.console import console
from audio.model.set_level import SetLevel
from audio.plot import multiplot
from audio.procedure import (
    Procedure,
    ProcedureInsertionGain,
    ProcedureMultiPlot,
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

    # datetime_now = datetime.now().strftime(r"%Y-%m-%d--%H-%M-%f")

    proc = Procedure.from_xml_file(file_path=procedure_name)

    console.print(f"Start Procedure: [blue]{proc.name}")

    root: pathlib.Path = HOME_PATH
    data: Dict = dict()

    console.print(proc.steps)

    idx_tot = len(proc.steps)

    for idx, step in enumerate(proc.steps):

        console.print(type(step))

        if isinstance(step, ProcedureText):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureText()"))

            confirm: bool = False

            while not confirm:
                confirm = Confirm.ask(step.text)

        elif isinstance(step, ProcedureSetLevel):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureSetLevel()"))

            sampling_config = step.config
            sampling_config.print()

            file_set_level: pathlib = pathlib.Path(root / step.file_set_level_name)
            data[step.file_set_level_key] = file_set_level

            file_set_level_plot: pathlib.Path = pathlib.Path(root / step.file_plot_name)
            data[step.file_plot_key] = file_set_level_plot

            config_set_level(
                config=sampling_config,
                set_level_file_path=file_set_level,
                plot_file_path=file_set_level_plot,
                debug=True,
            )

            console.print(data)

        elif isinstance(step, ProcedureSerialNumber):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureSerialNumber()"))

            console.print(step.text)

            confirm: bool = False

            while not confirm:
                serial_number = Prompt.ask("Inserisci il serial-number")

                confirm = Confirm.ask(
                    f"The serial-number is: '[blue bold]{serial_number}[/]'"
                )

            root = pathlib.Path(HOME_PATH / serial_number)

            root.mkdir(parents=True, exist_ok=True)
            console.print(f"Created Dir at: '{root}'")

        elif isinstance(step, ProcedureInsertionGain):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureInsertionGain()"))

            calibration_path: pathlib.Path = pathlib.Path(
                HOME_PATH / "calibration.config.set_level"
            )
            gain_file_path: pathlib.Path = pathlib.Path(root / step.name)

            file_set_level: pathlib.Path = pathlib.Path(root / step.set_level)

            calibration: float = SetLevel(calibration_path).set_level
            set_level: float = SetLevel(file_set_level).set_level

            gain: float = 20 * log10(calibration / set_level)

            gain_file_path.write_text(f"{gain:.5}", encoding="utf-8")

            data[step.name] = gain_file_path

            console.print(f"GAIN: {gain} dB.")

        elif isinstance(step, ProcedurePrint):
            step: ProcedurePrint = step

            console.print(Panel(f"{idx}/{idx_tot}: ProcedurePrint()"))

            for var in step.variables:
                console.print(
                    "{}: {}".format(
                        var, pathlib.Path(data[var]).read_text(encoding="utf-8")
                    )
                )

        elif isinstance(step, ProcedureSweep):
            step: ProcedureSweep = step
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureSweep()"))

            sweep_config: SweepConfigXML = step.config
            sweep_config.print()

            if sweep_config is None:
                console.print("sweep_config is None.", style="error")

            set_level = SetLevel(data[step.set_level]).set_level
            y_offset_dB = SetLevel(data[step.set_level]).y_offset_dB

            sweep_config.rigol.override(amplitude_peak_to_peak=set_level)
            sweep_config.plot.override(y_offset=y_offset_dB)
            sweep_config.print()

            home_dir_path: pathlib.Path = root / step.name
            measurement_file: pathlib.Path = home_dir_path / (step.name + ".csv")
            file_set_level_plot: pathlib.Path = home_dir_path / (
                step.name_plot + ".png"
            )

            console.print(f"Measurement File: '{measurement_file}'")
            console.print(f"Plot File: '{file_set_level_plot}'")

            # Confirm.ask()

            sampling_curve(
                config=sweep_config,
                sweep_home_path=home_dir_path,
                sweep_file_path=measurement_file,
                debug=True,
            )

            plot_from_csv(
                measurements_file_path=measurement_file,
                plot_config=sweep_config.plot,
                plot_file_path=file_set_level_plot,
                debug=True,
            )

        elif isinstance(step, ProcedureMultiPlot):
            step: ProcedureMultiPlot = step
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureMultiPlot()"))

            home_dir_path: pathlib.Path = root
            file_set_level_plot: pathlib.Path = home_dir_path / (
                step.plot_file_name + ".png"
            )

            csv_files: List[pathlib.Path] = [
                pathlib.Path(home_dir_path / f"{csv}/{csv}.csv")
                for csv in step.csv_files
            ]

            multiplot(csv_files, file_set_level_plot, step.plot_config)

        elif isinstance(step, ProcedureStep):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureStep()"))
