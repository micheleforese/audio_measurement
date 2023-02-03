import copy
from enum import Enum, auto
from math import log10
from pathlib import Path
from typing import Callable, Dict, List, Optional, Type

import click
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from audio.config.sweep import SweepConfig
from audio.console import console
from audio.model.file import File
from audio.model.insertion_gain import InsertionGain
from audio.model.set_level import SetLevel
from audio.plot import multiplot
from audio.procedure import DataProcedure, Procedure
from audio.procedure.step import (
    ProcedureAsk,
    ProcedureDefault,
    ProcedureFile,
    ProcedureInsertionGain,
    ProcedureMultiPlot,
    ProcedurePhaseSweep,
    ProcedurePrint,
    ProcedureSerialNumber,
    ProcedureSetLevel,
    ProcedureStep,
    ProcedureSweep,
    ProcedureTask,
    ProcedureText,
)
from audio.sampling import config_set_level, plot_from_csv, sampling_curve


@click.command()
@click.argument("procedure_name", type=Path)
@click.option(
    "--home",
    type=Path,
    help="Home path, where the csv and plot image will be created.",
    default=Path.cwd(),
    show_default=True,
)
def procedure(
    procedure_name: Path,
    home: Path,
):

    if not procedure_name.exists() or not procedure_name.is_file():
        console.print(
            Panel(f"[ERROR] - Procedure file: {procedure_name} does not exists.")
        )

    proc = Procedure.from_xml_file(file=procedure_name)
    procedure_data = DataProcedure(proc.name, home)

    console.print(f"Start Procedure: [blue]{procedure_data.name}", justify="center")

    exec_proc(procedure_data, proc.steps)


class AppAction(Enum):
    EXIT_APP = auto()
    EXIT_TASK = auto()


def exec_proc(data: DataProcedure, list_step: List[ProcedureStep]):
    idx_tot = len(list_step)

    procedure_step_dict: Dict[
        Type, Callable[[DataProcedure, ProcedureStep], Optional[AppAction]]
    ] = {
        ProcedureText: step_procedure_text,
        ProcedureAsk: step_procedure_ask,
        ProcedureDefault: step_procedure_default,
        ProcedureFile: step_procedure_file,
        ProcedureSetLevel: step_procedure_set_level,
        ProcedureSerialNumber: step_procedure_serial_number,
        ProcedureInsertionGain: step_procedure_insertion_gain,
        ProcedurePrint: step_procedure_print,
        ProcedureSweep: step_procedure_sweep,
        ProcedureMultiPlot: step_procedure_multiplot,
        ProcedureTask: step_procedure_task,
        ProcedurePhaseSweep: step_procedure_phase_sweep,
    }

    for idx, step in enumerate(list_step, start=1):
        console.print(Panel(f"{idx}/{idx_tot}: {step.__class__.__name__}()"))

        app_action: Optional[AppAction] = procedure_step_dict.get(
            type(step), step_not_implemented
        )(data, step)

        if app_action is not None:
            if app_action == AppAction.EXIT_APP:
                exit()
            elif app_action == AppAction.EXIT_TASK:
                return None

    return None


def step_not_implemented(_: DataProcedure, step: ProcedureStep):
    console.print("[STEP] - Unknown.")

    return None


def step_procedure_text(_: DataProcedure, step: ProcedureText):
    console.print(step.text)

    return None


def step_procedure_ask(_: DataProcedure, step: ProcedureAsk):
    confirm: bool = False

    while not confirm:
        confirm = Confirm.ask(step.text)

    return None


def step_procedure_default(data: DataProcedure, step: ProcedureDefault):
    data.default_sweep_config.set_level = copy.deepcopy(step.sweep_file_set_level)
    data.default_sweep_config.offset = copy.deepcopy(step.sweep_file_offset)
    data.default_sweep_config.offset_sweep = copy.deepcopy(step.sweep_file_offset_sweep)
    data.default_sweep_config.insertion_gain = copy.deepcopy(
        step.sweep_file_insertion_gain
    )

    data.default_sweep_config.config = step.sweep_config

    return None


def step_procedure_file(data: DataProcedure, step: ProcedureFile):
    result: bool = data.cache_file.add(step.key, data.root / step.path)
    if not result:
        console.log(f"[ERROR] - File key '{step.key}' already present in the project")
    else:
        console.log(f"[FILE] - File added: '{step.key}' - '{step.path}'")

    return None


def step_procedure_set_level(data: DataProcedure, step: ProcedureSetLevel):
    sampling_config = step.config
    sampling_config.print()

    file_set_level_path: Optional[Path] = None
    file_sweep_plot_path: Optional[Path] = None

    if step.file_set_level_key is not None:
        file_set_level_path = data.cache_file.get(step.file_set_level_key)

        if file_set_level_path is None:
            console.log(
                f"[FILE] - key '{step.file_set_level_key}' not found.",
                style="error",
            )

            console.log(data.cache_file.database)
    elif step.file_set_level_name is not None:
        file_set_level_path = Path(data.root / step.file_set_level_name)
    else:
        console.log(f"[FILE] - File not present.", style="error")

    if step.file_plot_key is not None:
        file_sweep_plot_path = data.cache_file.get(step.file_plot_key)

        if file_sweep_plot_path is None:
            console.log(
                f"[FILE] - key '{step.file_plot_key}' not found.",
                style="error",
            )

            console.log(data.cache_file.database)
    elif step.file_plot_name is not None:
        file_sweep_plot_path = Path(data.root / step.file_plot_name)
    else:
        console.log(f"[FILE] - File not present.", style="error")

    if not step.override:
        if file_set_level_path.exists() and file_set_level_path.is_file():
            console.log(f"[FILE] - File '{file_set_level_path}' already exists.")
            return

    dBu = 0

    if step.dBu is not None:
        dBu = step.dBu

    config_set_level(
        dBu=dBu,
        config=sampling_config,
        set_level_file_path=file_set_level_path,
        plot_file_path=file_sweep_plot_path,
        debug=True,
    )

    return None


def step_procedure_serial_number(data: DataProcedure, step: ProcedureSerialNumber):
    console.print(step.text)

    confirm: bool = False

    while not confirm:
        serial_number = Prompt.ask("Inserisci il serial-number")

        confirm = Confirm.ask(f"The serial-number is: '[blue bold]{serial_number}[/]'")

    data.root = Path(data.root / serial_number)

    data.root.mkdir(parents=True, exist_ok=True)
    console.print(f"Created Dir at: '{data.root}'")

    return None


def step_procedure_insertion_gain(data: DataProcedure, step: ProcedureInsertionGain):
    file_calibration_path: Path
    file_set_level: Path
    file_gain_path: Path

    if step.file_calibration_key is not None:
        file_calibration_path = data.cache_file.get(step.file_calibration_key)
        if file_calibration_path is None:
            console.log(f"[FILE] - key: {step.file_calibration_key} not present.")
            console.log(data.cache_file)

    if step.file_set_level_key is not None:
        file_set_level = data.cache_file.get(step.file_set_level_key)
        if file_set_level is None:
            console.log(f"[FILE] - key: {step.file_set_level_key} not present.")
            console.log(data.cache_file)

    if step.file_gain_key is not None:
        file_gain_path = data.cache_file.get(step.file_gain_key)
        if file_gain_path is None:
            console.log(f"[FILE] - key: {step.file_gain_key} not present.")
            console.log(data.cache_file)

    calibration: float = SetLevel(file_calibration_path).set_level
    set_level: float = SetLevel(file_set_level).set_level
    gain: float = 20 * log10(calibration / set_level)

    file_gain_path.write_text(f"{gain:.5}", encoding="utf-8")

    return None


def step_procedure_print(data: DataProcedure, step: ProcedurePrint):
    for var in step.variables:
        variable: Optional[str] = data.data.get(var, None)
        if variable is not None:
            console.print(
                "{}: {}".format(var, Path(variable).read_text(encoding="utf-8"))
            )

    return None


def step_procedure_sweep(data: DataProcedure, step: ProcedureSweep):
    file_set_level_path: Optional[Path] = None
    file_offset_path: Optional[Path] = None
    file_offset_sweep_path: Optional[Path] = None
    file_insertion_gain_path: Optional[Path] = None

    config: SweepConfig = copy.deepcopy(data.default_sweep_config.config)

    config.override(step.config)

    config.print()

    if config is None:
        console.print("config is None.", style="error")
        exit()

    # Set Level
    file_set_level: File = File()
    if data.default_sweep_config.set_level is not None:
        file_set_level = data.default_sweep_config.set_level

    if step.file_set_level is not None:
        file_set_level.overload(
            key=step.file_set_level.key, path=step.file_set_level.path
        )
    console.print(file_set_level)

    if file_set_level.key is not None:
        file_set_level_path = data.cache_file.get(file_set_level.key)

        if file_set_level_path is None:
            console.log(
                f"[FILE] - key '{file_set_level.key}' not found.",
                style="error",
            )

            console.log(data.cache_file.database)

    elif file_set_level.path is not None:
        file_set_level_path = Path(data.root / file_set_level.path)
    else:
        console.log(f"[FILE] - File not present.", style="error")
        console.log(data.cache_file.database)
        exit()

    # Y Offset dB
    file_offset: File = File()
    if data.default_sweep_config.offset is not None:
        file_offset = data.default_sweep_config.offset

    if step.file_offset is not None:
        file_offset.overload(key=step.file_offset.key, path=step.file_offset.path)
    console.print(file_offset)

    if file_offset.key is not None:
        file_offset_path = data.cache_file.get(file_offset.key)

        if file_offset_path is None:
            console.log(
                f"[FILE] - key '{file_offset.key}' not found.",
                style="error",
            )

            console.log(data.cache_file.database)

    elif file_offset.path is not None:
        file_offset_path = Path(data.root / file_offset.path)
    else:
        console.log(f"[FILE] - File not present.", style="error")
        console.log(data.cache_file.database)
        exit()

    # Y Offset dB - file_offset_sweep_path
    file_offset_sweep: File = File()
    if data.default_sweep_config.offset_sweep is not None:
        file_offset_sweep = data.default_sweep_config.offset_sweep

    console.log(["file_offset_sweep", step.file_offset_sweep])
    console.log(["STP", step])

    if step.file_offset_sweep is not None:
        file_offset_sweep.overload(
            key=step.file_offset_sweep.key, path=step.file_offset_sweep.path
        )

    console.print(file_offset_sweep)

    console.log(file_offset_sweep.key)
    if file_offset_sweep.key is not None:
        file_offset_sweep_path = data.cache_file.get(file_offset_sweep.key)

        if file_offset_sweep_path is None:
            console.log(
                f"[FILE] - key '{file_offset_sweep.key}' not found.",
                style="error",
            )

            console.log(data.cache_file.database)

    elif file_offset_sweep.path is not None:
        file_offset_sweep_path = Path(data.root / file_offset_sweep.path)
    else:
        file_offset_sweep_path = None

    # Insertion Gain
    file_insertion_gain: File = File()
    if data.default_sweep_config.insertion_gain is not None:
        file_insertion_gain = data.default_sweep_config.insertion_gain

    if step.file_insertion_gain is not None:
        file_insertion_gain.overload(
            key=step.file_insertion_gain.key, path=step.file_insertion_gain.path
        )
    console.print(file_insertion_gain)

    if file_insertion_gain.key is not None:
        file_insertion_gain_path = data.cache_file.get(file_insertion_gain.key)

        if file_insertion_gain_path is None:
            console.log(
                f"[FILE] - key '{file_insertion_gain.key}' not found.",
                style="error",
            )
            console.log(data.cache_file.database)
    elif file_insertion_gain.path is not None:
        file_insertion_gain_path = Path(data.root / file_insertion_gain.path)
    else:
        console.log(f"[FILE] - File not present.", style="error")
        console.log(data.cache_file.database)
        exit()

    # Retrieving the data
    set_level = SetLevel(file_set_level_path).set_level
    y_offset_dB = SetLevel(file_offset_path).y_offset_dB
    insertion_gain = InsertionGain(file_insertion_gain_path).insertion_gain_dB

    config.rigol.amplitude_peak_to_peak = set_level
    config.plot.y_offset = y_offset_dB
    config.plot.legend = (
        f"{config.plot.legend}, Vpp IN={set_level:.2f} V, G={insertion_gain} dB"
    )
    config.print()

    home_dir_path: Path = data.root / step.name_folder
    measurement_file: Path = home_dir_path / (step.name_folder + ".csv")
    file_sweep_plot: Path = home_dir_path / (step.name_folder + ".png")

    console.print(f"[FILE] - Measurement: '{measurement_file}'")
    console.print(f"[FILE] - Sweep plot: '{file_sweep_plot}'")

    if not step.override:
        if measurement_file.exists() and measurement_file.is_file():
            console.log(f"[FILE] - File '{measurement_file}' already exists.")
            return

    sampling_curve(
        config=config,
        sweep_home_path=home_dir_path,
        sweep_file_path=measurement_file,
        debug=True,
    )

    if not step.override:
        if file_sweep_plot.exists() and file_sweep_plot.is_file():
            console.log(f"[FILE] - File '{file_sweep_plot}' already exists.")
            return

    plot_from_csv(
        measurements_file_path=measurement_file,
        plot_config=config.plot,
        file_offset_sweep_path=file_offset_sweep_path,
        plot_file_path=file_sweep_plot,
        debug=True,
    )

    return None


def step_procedure_multiplot(data: DataProcedure, step: ProcedureMultiPlot):
    home_dir_path: Path = data.root
    file_sweep_plot: Path = home_dir_path / step.file_plot

    csv_files: List[Path] = [Path(home_dir_path / dir) for dir in step.folder_sweep]

    multiplot(
        csv_files,
        file_sweep_plot,
        data.cache_csv_data,
        step.config,
    )

    return None


def step_procedure_task(data: DataProcedure, step: ProcedureTask):
    console.print(Panel.fit(f"[TASK] - [green]{step.text}[/]"), justify="center")

    exec_proc(data, list_step=step.steps)
    return None


def step_procedure_phase_sweep(data: DataProcedure, step: ProcedurePhaseSweep):
    from datetime import datetime

    from audio.sweep.phase import phase_sweep

    if step.data.folder_path is not None:
        folder_path = data.root / step.data.folder_path
    else:
        time_now = datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
        folder_path = data.root / f"{time_now} phase_sweep"

    if step.data.graph_path is not None:
        graph_path = folder_path / step.data.graph_path
    else:
        graph_path = folder_path / "graph.pdf"

    name: str = step.data.name if step.data.name is not None else "Phase Sweep"

    phase_sweep(
        name=name,
        folder_path=folder_path,
        graph_path=graph_path,
        config=step.data.config,
    )
