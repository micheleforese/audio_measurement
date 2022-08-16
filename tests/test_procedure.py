import pathlib
import unittest
from math import log10
from pathlib import Path
from typing import Dict, List, cast

import click
from rich import inspect
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

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


class Test_TestProcedure(unittest.TestCase):
    def test_procedure(self):

        HOME_PATH = Path(__file__).parent

        procedure_name = HOME_PATH / "multiplot_10Hz_100kHz.procedure.json5"
        proc = Procedure.from_json5_file(procedure_path=procedure_name)

        console.print(f"Start Procedure: [blue]{proc.name}")

        root: Path = HOME_PATH
        data: Dict = dict()

        console.print(proc.steps)

        idx_tot = len(proc.steps)

        for idx, step in enumerate(proc.steps):

            if isinstance(step, ProcedureText):
                step: ProcedureText = step
                console.print(Panel(f"{idx}/{idx_tot}: ProcedureText()"))

                confirm: bool = False

                while not confirm:
                    confirm = Confirm.ask(step.text)

            elif isinstance(step, ProcedureSetLevel):
                step: ProcedureSetLevel = step
                console.print(Panel(f"{idx}/{idx_tot}: ProcedureSetLevel()"))

                sampling_config = step.config
                sampling_config.print()

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
                console.print(Panel(f"{idx}/{idx_tot}: ProcedureSerialNumber()"))

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

                console.print(Panel(f"{idx}/{idx_tot}: ProcedureInsertionGain()"))

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

                sweep_config = step.config
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
                plot_file: pathlib.Path = home_dir_path / (step.name_plot + ".png")

                console.print(f"Measurement File: '{measurement_file}'")
                console.print(f"PLot File: '{plot_file}'")

                Confirm.ask()

                sampling_curve(
                    config=sweep_config,
                    sweep_home_path=home_dir_path,
                    sweep_file_path=measurement_file,
                    debug=True,
                )

                plot_from_csv(
                    plot_config=sweep_config.plot,
                    measurements_file_path=measurement_file,
                    plot_file_path=plot_file,
                    debug=True,
                )

            elif isinstance(step, ProcedureMultiPlot):
                step: ProcedureMultiPlot = step
                console.print(Panel(f"{idx}/{idx_tot}: ProcedureMultiPlot()"))

                home_dir_path: pathlib.Path = root
                plot_file: pathlib.Path = home_dir_path / (step.plot_file_name + ".png")

                csv_files: List[pathlib.Path] = [
                    pathlib.Path(home_dir_path / csv / csv + ".csv")
                    for csv in step.csv_files
                ]

                multiplot(csv_files, plot_file)

            elif isinstance(step, ProcedureStep):
                console.print(Panel(f"{idx}/{idx_tot}: ProcedureStep()"))

        assert 1 == 1
