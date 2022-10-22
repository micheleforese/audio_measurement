from dataclasses import dataclass
import pathlib
from math import log10
from typing import Dict, List, Optional

import click
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from audio.config.sweep import SweepConfigXML

from audio.console import console
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
from audio.model.insertion_gain import InsertionGain
from audio.model.file import CacheFile, File


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
        file_set_level_key: Optional[str] = None
        file_set_level_name: Optional[str] = None

        offset: Optional[File] = None
        file_offset_key: Optional[str] = None
        file_offset_name: Optional[str] = None

        insertion_gain: Optional[File] = None
        file_insertion_gain_key: Optional[str] = None
        file_insertion_gain_name: Optional[str] = None

        config: Optional[SweepConfigXML] = None

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

            default_sweep_config.offset = File(
                step.sweep_file_offset_key, step.sweep_file_offset_name
            )

            default_sweep_config.insertion_gain = File(
                step.sweep_file_insertion_gain_key, step.sweep_file_insertion_gain_name
            )
            default_sweep_config.config = step.sweep_config

        elif isinstance(step, ProcedureFile):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureFile()"))

            result: bool = cache_file.add(step.key, root / step.path)
            if not result:
                console.log(
                    f"[ERROR] - File key '{step.key}' already present in the project"
                )

        elif isinstance(step, ProcedureSetLevel):
            console.print(Panel(f"{idx}/{idx_tot}: ProcedureSetLevel()"))

            sampling_config = step.config
            sampling_config.print()

            file_set_level: pathlib = pathlib.Path(root / step.file_set_level_name)
            data[step.file_set_level_key] = file_set_level

            file_sweep_plot: pathlib.Path = pathlib.Path(root / step.file_plot_name)
            data[step.file_plot_key] = file_sweep_plot

            if not step.override:
                if file_set_level.exists() and file_set_level.is_file():
                    console.log(f"[FILE] - File '{file_set_level}' already exists.")
                    continue

            dBu = 4

            if step.dBu is not None:
                dBu = step.dBu

            config_set_level(
                dBu=dBu,
                config=sampling_config,
                set_level_file_path=file_set_level,
                plot_file_path=file_sweep_plot,
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
                root / step.file_calibration_name
            )

            file_set_level: pathlib.Path = pathlib.Path(root / step.file_set_level_name)

            calibration: float = SetLevel(calibration_path).set_level
            set_level: float = SetLevel(file_set_level).set_level

            gain: float = 20 * log10(calibration / set_level)

            gain_file_path: pathlib.Path = pathlib.Path(root / step.file_gain_name)
            gain_file_path.write_text(f"{gain:.5}", encoding="utf-8")

            data[step.file_gain_key] = gain_file_path

            console.print(f"GAIN: {gain} dB.")

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

            sweep_config: SweepConfigXML = step.config

            sweep_config = default_sweep_config.config.override_from_sweep_config_xml(
                sweep_config
            )
            sweep_config.print()

            if sweep_config is None:
                console.print("sweep_config is None.", style="error")
                exit()

            # Set Level & Y Offset dB
            file_set_level: File = File(
                default_sweep_config.file_set_level_key,
                default_sweep_config.file_set_level_name,
            )

            file_set_level.overload(
                key=step.file_set_level_key,
                name=root / step.file_set_level_name
                if step.file_set_level_name is not None
                else None,
            )

            data.get(file_set_level.key, None)

            if file_set_level is None:
                file_set_level = pathlib.Path(root / step.file_set_level_name)
            else:
                file_set_level = pathlib.Path(file_set_level)

            # Insertion Gain
            file_insertion_gain = data.get(step.file_insertion_gain_key, None)

            if file_insertion_gain is None:
                file_insertion_gain = pathlib.Path(root / step.file_insertion_gain_name)
            else:
                file_insertion_gain = pathlib.Path(file_insertion_gain)

            set_level = SetLevel(file_set_level).set_level
            y_offset_dB = SetLevel(file_set_level).y_offset_dB
            insertion_gain = InsertionGain(file_insertion_gain).insertion_gain_dB

            sweep_config.rigol.override(amplitude_peak_to_peak=set_level)
            sweep_config.plot.override(y_offset=y_offset_dB)
            sweep_config.plot.override(
                legend=f"{sweep_config.plot.legend}, Vpp IN={set_level:.2f} V, G={insertion_gain} dB"
            )
            sweep_config.print()

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
                config=sweep_config,
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
                plot_config=sweep_config.plot,
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
