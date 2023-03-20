import copy
import sys
from collections.abc import Callable
from enum import Enum, auto
from math import log10
from pathlib import Path

import click
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from audio.config.sweep import SweepConfig
from audio.console import console
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
from audio.sampling import config_set_level


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
            Panel(f"[ERROR] - Procedure file: {procedure_name} does not exists."),
        )

    proc = Procedure.from_xml_file(file=procedure_name)
    procedure_data = DataProcedure(proc.name, home)

    console.print(f"Start Procedure: [blue]{procedure_data.name}", justify="center")

    exec_proc(procedure_data, proc.steps)


class AppAction(Enum):
    EXIT_APP = auto()
    EXIT_TASK = auto()


def exec_proc(data: DataProcedure, list_step: list[ProcedureStep]) -> None:
    idx_tot = len(list_step)

    procedure_step_dict: dict[
        type,
        Callable[[DataProcedure, ProcedureStep], AppAction | None],
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

        app_action: AppAction | None = procedure_step_dict.get(
            type(step),
            step_not_implemented,
        )(data, step)

        if app_action is not None:
            if app_action == AppAction.EXIT_APP:
                sys.exit()
            elif app_action == AppAction.EXIT_TASK:
                return


def step_not_implemented(_: DataProcedure, step: ProcedureStep):
    console.print("[STEP] - Unknown.")

    return


def step_procedure_text(_: DataProcedure, step: ProcedureText):
    console.print(step.text)

    return


def step_procedure_ask(_: DataProcedure, step: ProcedureAsk):
    confirm: bool = False

    while not confirm:
        confirm = Confirm.ask(step.text)

    return


def step_procedure_default(data: DataProcedure, step: ProcedureDefault):
    data.default_sweep_config.set_level = copy.deepcopy(step.sweep_file_set_level)
    data.default_sweep_config.offset = copy.deepcopy(step.sweep_file_offset)
    data.default_sweep_config.offset_sweep = copy.deepcopy(step.sweep_file_offset_sweep)
    data.default_sweep_config.insertion_gain = copy.deepcopy(
        step.sweep_file_insertion_gain,
    )

    data.default_sweep_config.config = step.sweep_config

    return


def step_procedure_file(data: DataProcedure, step: ProcedureFile):
    result: bool = data.cache_file.add(step.key, data.root / step.path)
    if not result:
        console.log(f"[ERROR] - File key '{step.key}' already present in the project")
    else:
        console.log(f"[FILE] - File added: '{step.key}' - '{step.path}'")

    return


def step_procedure_set_level(data: DataProcedure, step: ProcedureSetLevel):
    sampling_config = step.config
    if sampling_config is None:
        return
    sampling_config.print_object()

    file_set_level_path: Path | None = None
    file_sweep_plot_path: Path | None = None

    # TODO: create the

    dBu: float = 0.0

    if step.dBu is not None:
        dBu = step.dBu

    if sampling_config is None:
        return

    if file_sweep_plot_path is None:
        return

    config_set_level(
        dBu=dBu,
        config=sampling_config,
        set_level_file_path=file_set_level_path,
        plot_file_path=file_sweep_plot_path,
        debug=True,
    )

    return


def step_procedure_serial_number(data: DataProcedure, step: ProcedureSerialNumber):
    console.print(step.text)

    confirm: bool = False

    while not confirm:
        serial_number = Prompt.ask("Insert il serial-number")

        confirm = Confirm.ask(f"The serial-number is: '[blue bold]{serial_number}[/]'")

    data.root = Path(data.root / serial_number)

    data.root.mkdir(parents=True, exist_ok=True)
    console.print(f"Created Dir at: '{data.root}'")

    return


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

    calibration: float = SetLevel.from_file(file_calibration_path).set_level
    set_level: float = SetLevel.from_file(file_set_level).set_level
    gain: float = 20 * log10(calibration / set_level)

    file_gain_path.write_text(f"{gain:.5}", encoding="utf-8")

    return


def step_procedure_print(data: DataProcedure, step: ProcedurePrint):
    for var in step.variables:
        variable: str | None = data.data.get(var, None)
        if variable is not None:
            console.print(
                "{}: {}".format(var, Path(variable).read_text(encoding="utf-8")),
            )

    return


def step_procedure_sweep(data: DataProcedure, step: ProcedureSweep):
    if data.default_sweep_config.config is None:
        # TODO: decide if config must be None
        return

    config: SweepConfig = copy.deepcopy(data.default_sweep_config.config)

    config.override(step.config)

    config.print_object()

    if config is None:
        console.print("config is None.", style="error")
        sys.exit()

    # TODO: retrieve Set Level from somewhere
    # Set Level
    # if data.default_sweep_config.set_level is not None:

    # if step.file_set_level is not None:
    #     file_set_level.overload(

    # if file_set_level.key is not None:

    #     if file_set_level_path is None:
    #         console.log(

    # TODO: retrieve Y Offset dB value from somewhere
    # Y Offset dB
    # if data.default_sweep_config.offset is not None:

    # if step.file_offset is not None:

    # if file_offset.key is not None:

    #     if file_offset_path is None:
    #         console.log(

    # TODO: retrieve Y Offset dB - file_offset_sweep_path value from somewhere
    # Y Offset dB - file_offset_sweep_path
    #
    # if data.default_sweep_config.offset_sweep is not None:

    # if step.file_offset_sweep is not None:
    #     file_offset_sweep.overload(

    # if file_offset_sweep.key is not None:

    #     if file_offset_sweep_path is None:
    #         console.log(

    # TODO: retrieve Insertion Gain value from somewhere
    # Insertion Gain
    #
    # if data.default_sweep_config.insertion_gain is not None:

    # if step.file_insertion_gain is not None:
    #     file_insertion_gain.overload(

    # if file_insertion_gain.key is not None:

    #     if file_insertion_gain_path is None:
    #         console.log(

    # TODO: retrieve all above object value from somewhere
    # Retrieving the data
    #

    # config.plot.legend = (

    # TODO: rewrite the sweep process with the new Database

    # sampling_curve(

    # plot_from_csv(


def step_procedure_multiplot(data: DataProcedure, step: ProcedureMultiPlot):
    home_dir_path: Path = data.root
    file_sweep_plot: Path = home_dir_path / step.file_plot

    csv_files: list[Path] = [Path(home_dir_path / dir) for dir in step.folder_sweep]

    multiplot(
        csv_files,
        file_sweep_plot,
        data.cache_csv_data,
        step.config,
    )

    return


def step_procedure_task(data: DataProcedure, step: ProcedureTask):
    console.print(Panel.fit(f"[TASK] - [green]{step.text}[/]"), justify="center")

    exec_proc(data, list_step=step.steps)
    return


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
