import copy
import pathlib
from calendar import c
from dataclasses import dataclass
from math import log10
from typing import Dict, List, Optional

import click
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from audio.config.sweep import SweepConfig, SweepConfigXML
from audio.console import console
from audio.model.file import CacheFile, File
from audio.model.insertion_gain import InsertionGain
from audio.model.set_level import SetLevel
from audio.plot import CacheCsvData, multiplot
from audio.procedure import (
    Procedure,
    ProcedureAsk,
    ProcedureDefault,
    ProcedureFile,
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


@click.command()
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

    if not procedure_name.exists() or not procedure_name.is_file():
        console.print(
            Panel(f"[ERROR] - Procedure file: {procedure_name} does not exists.")
        )

    HOME_PATH = home

    proc = Procedure.from_xml_file(file_path=procedure_name)

    console.print(f"Start Procedure: [blue]{proc.name}", justify="center")

    root: pathlib.Path = HOME_PATH
    data: Dict = dict()
    cache_csv_data: CacheCsvData = CacheCsvData()
    cache_file: CacheFile = CacheFile()

    @dataclass
    class DefaultSweepConfig:
        set_level: Optional[File] = None

        offset: Optional[File] = None

        insertion_gain: Optional[File] = None

        config: Optional[SweepConfig] = None

    default_sweep_config = DefaultSweepConfig()

    idx_tot = len(proc.steps)

    for idx, step in enumerate(proc.steps, start=1):

        if isinstance(step, ProcedureText):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureText()"))

            console.print(step.text)

        elif isinstance(step, ProcedureAsk):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureAsk()"))

            confirm: bool = False

            while not confirm:
                confirm = Confirm.ask(step.text)

        elif isinstance(step, ProcedureDefault):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureDefault()"))

            default_sweep_config.set_level = File(
                step.sweep_file_set_level_key, step.sweep_file_set_level_name
            )

            console.print(default_sweep_config.set_level)

            default_sweep_config.offset = File(
                step.sweep_file_offset_key, step.sweep_file_offset_name
            )
            console.print(default_sweep_config.offset)

            default_sweep_config.insertion_gain = File(
                step.sweep_file_insertion_gain_key, step.sweep_file_insertion_gain_name
            )
            console.print(default_sweep_config.insertion_gain)

            default_sweep_config.config = step.sweep_config

        elif isinstance(step, ProcedureFile):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureFile()"))

            result: bool = cache_file.add(step.key, root / step.path)
            if not result:
                console.log(
                    f"[ERROR] - File key '{step.key}' already present in the project"
                )
            else:
                console.log(f"[FILE] - File added: '{step.key}' - '{step.path}'")

        elif isinstance(step, ProcedureSetLevel):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureSetLevel()"))

            sampling_config = step.config
            sampling_config.print()

            file_set_level_path: Optional[pathlib.Path] = None
            file_sweep_plot_path: Optional[pathlib.Path] = None

            if step.file_set_level_key is not None:
                file_set_level_path = cache_file.get(step.file_set_level_key)

                if file_set_level_path is None:
                    console.log(
                        f"[FILE] - key '{step.file_set_level_key}' not found.",
                        style="error",
                    )

                    console.log(cache_file.database)
            elif step.file_set_level_name is not None:
                file_set_level_path = pathlib.Path(root / step.file_set_level_name)
            else:
                console.log(f"[FILE] - File not present.", style="error")

            if step.file_plot_key is not None:
                file_sweep_plot_path = cache_file.get(step.file_plot_key)

                if file_sweep_plot_path is None:
                    console.log(
                        f"[FILE] - key '{step.file_plot_key}' not found.",
                        style="error",
                    )

                    console.log(cache_file.database)
            elif step.file_plot_name is not None:
                file_sweep_plot_path = pathlib.Path(root / step.file_plot_name)
            else:
                console.log(f"[FILE] - File not present.", style="error")

            if not step.override:
                if file_set_level_path.exists() and file_set_level_path.is_file():
                    console.log(
                        f"[FILE] - File '{file_set_level_path}' already exists."
                    )
                    continue

            dBu = 4

            if step.dBu is not None:
                dBu = step.dBu

            config_set_level(
                dBu=dBu,
                config=sampling_config,
                set_level_file_path=file_set_level_path,
                plot_file_path=file_sweep_plot_path,
                debug=True,
            )

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

            file_calibration_path: pathlib.Path
            file_set_level: pathlib.Path
            file_gain_path: pathlib.Path

            if step.file_calibration_key is not None:
                file_calibration_path = cache_file.get(step.file_calibration_key)
                if file_calibration_path is None:
                    console.log(
                        f"[FILE] - key: {step.file_calibration_key} not present."
                    )
                    console.log(cache_file)

            if step.file_set_level_key is not None:
                file_set_level = cache_file.get(step.file_set_level_key)
                if file_set_level is None:
                    console.log(f"[FILE] - key: {step.file_set_level_key} not present.")
                    console.log(cache_file)

            if step.file_gain_key is not None:
                file_gain_path = cache_file.get(step.file_gain_key)
                if file_gain_path is None:
                    console.log(f"[FILE] - key: {step.file_gain_key} not present.")
                    console.log(cache_file)

            calibration: float = SetLevel(file_calibration_path).set_level
            set_level: float = SetLevel(file_set_level).set_level
            gain: float = 20 * log10(calibration / set_level)

            file_gain_path.write_text(f"{gain:.5}", encoding="utf-8")

        elif isinstance(step, ProcedurePrint):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedurePrint()"))

            for var in step.variables:
                variable: Optional[str] = data.get(var, None)
                if variable is not None:
                    console.print(
                        "{}: {}".format(
                            var, pathlib.Path(variable).read_text(encoding="utf-8")
                        )
                    )

        elif isinstance(step, ProcedureSweep):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureSweep()"))
            file_set_level_path: Optional[pathlib.Path] = None
            file_insertion_gain_path: Optional[pathlib.Path] = None

            config: SweepConfig = copy.deepcopy(default_sweep_config.config)

            config.override(step.config)

            config.print()

            if config is None:
                console.print("config is None.", style="error")
                exit()

            # Set Level & Y Offset dB
            file_set_level: File = File(
                key=default_sweep_config.set_level.key,
                path=default_sweep_config.set_level.path,
            )
            console.print(file_set_level)

            file_set_level.overload(
                key=step.file_set_level_key, path=step.file_set_level_path
            )
            console.print(file_set_level)

            if file_set_level.key is not None:
                file_set_level_path = cache_file.get(file_set_level.key)

                if file_set_level_path is None:
                    console.log(
                        f"[FILE] - key '{file_set_level.key}' not found.",
                        style="error",
                    )

                    console.log(cache_file.database)

            elif file_set_level.path is not None:
                file_sweep_plot_path = pathlib.Path(root / file_set_level.path)
            else:
                console.log(f"[FILE] - File not present.", style="error")
                console.log(cache_file.database)
                exit()

            # Insertion Gain
            console.print(
                f"default_sweep_config.insertion_gain.key: {default_sweep_config.insertion_gain.key or ''}"
            )
            console.print(
                f"default_sweep_config.insertion_gain.path: {default_sweep_config.insertion_gain.path or ''}"
            )
            file_insertion_gain: File = File(
                default_sweep_config.insertion_gain.key,
                default_sweep_config.insertion_gain.path,
            )
            console.print(file_insertion_gain)

            console.print(
                f"step.file_insertion_gain_key: {step.file_insertion_gain_key or ''}"
            )
            console.print(
                f"step.file_insertion_gain_path: {step.file_insertion_gain_path or ''}"
            )
            file_insertion_gain.overload(
                key=step.file_insertion_gain_key, path=step.file_insertion_gain_path
            )
            console.print(file_insertion_gain)

            if file_insertion_gain.key is not None:
                file_insertion_gain_path = cache_file.get(file_insertion_gain.key)

                if file_insertion_gain_path is None:
                    console.log(
                        f"[FILE] - key '{file_insertion_gain.key}' not found.",
                        style="error",
                    )
                    console.log(cache_file.database)
            elif file_insertion_gain.path is not None:
                file_insertion_gain_path = pathlib.Path(root / file_insertion_gain.path)
            else:
                console.log(f"[FILE] - File not present.", style="error")
                console.log(cache_file.database)
                exit()

            # Retrieving the data
            set_level = SetLevel(file_set_level_path).set_level
            y_offset_dB = SetLevel(file_set_level_path).y_offset_dB
            insertion_gain = InsertionGain(file_insertion_gain_path).insertion_gain_dB

            config.rigol.amplitude_peak_to_peak = set_level
            config.plot.y_offset = y_offset_dB
            config.plot.legend = (
                f"{config.plot.legend}, Vpp IN={set_level:.2f} V, G={insertion_gain} dB"
            )
            config.print()

            home_dir_path: pathlib.Path = root / step.name_folder
            measurement_file: pathlib.Path = home_dir_path / (step.name_folder + ".csv")
            file_sweep_plot: pathlib.Path = home_dir_path / (step.name_folder + ".png")

            console.print(f"[FILE] - Measurement: '{measurement_file}'")
            console.print(f"[FILE] - Sweep plot: '{file_sweep_plot}'")

            if not step.override:
                if measurement_file.exists() and measurement_file.is_file():
                    console.log(f"[FILE] - File '{measurement_file}' already exists.")
                    continue

            sampling_curve(
                config=config,
                sweep_home_path=home_dir_path,
                sweep_file_path=measurement_file,
                debug=True,
            )

            if not step.override:
                if file_sweep_plot.exists() and file_sweep_plot.is_file():
                    console.log(f"[FILE] - File '{file_sweep_plot}' already exists.")
                    continue

            plot_from_csv(
                measurements_file_path=measurement_file,
                plot_config=config.plot,
                plot_file_path=file_sweep_plot,
                debug=True,
            )

        elif isinstance(step, ProcedureMultiPlot):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureMultiPlot()"))

            home_dir_path: pathlib.Path = root
            file_sweep_plot: pathlib.Path = home_dir_path / step.file_plot

            csv_files: List[pathlib.Path] = [
                pathlib.Path(home_dir_path / f"{dir}/{dir}.csv")
                for dir in step.folder_sweep
            ]

            multiplot(
                csv_files,
                file_sweep_plot,
                cache_csv_data,
                step.config,
            )

        elif isinstance(step, ProcedureStep):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureStep()"))
