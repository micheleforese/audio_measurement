import datetime
import pathlib
from code import interact
from datetime import datetime
from pathlib import Path
from time import sleep
from timeit import timeit
from typing import Dict, List, Optional, Tuple, Union

import click
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Column, Table
from usbtmc import Instrument

import cDAQ.ui.terminal as ui_t
from cDAQ.alghorithm import LogaritmicScale
from cDAQ.config import Config, Plot
from cDAQ.config.type import ModAuto, Range
from cDAQ.console import console
from cDAQ.docker import Docker_CLI
from cDAQ.docker.latex import create_latex_file
from cDAQ.math import (
    INTERPOLATION_KIND,
    find_sin_zero_offset,
    interpolation_model,
    logx_interpolation_model,
    rms_full_cycle,
)
from cDAQ.math.pid import (
    PID_TERM,
    PID_Controller,
    Timed_Value,
    calculate_area,
    calculate_gradient,
)
from cDAQ.sampling import config_offset, plot_from_csv, sampling_curve
from cDAQ.scpi import SCPI, Bandwidth, Switch
from cDAQ.script.gui import GuiAudioMeasurements
from cDAQ.script.test import testTimer
from cDAQ.timer import Timer, Timer_Message, timeit, timer
from cDAQ.usbtmc import UsbTmc, get_device_list, print_devices_list
from cDAQ.utility import RMS, get_subfolder, percentage_error, transfer_function


@click.group()
def cli():
    pass


@cli.command(help="Audio Sweep")
@click.option(
    "--config",
    "config_path",
    type=pathlib.Path,
    help="Configuration path of the config file in json5 format.",
    required=True,
)
@click.option(
    "--home",
    type=pathlib.Path,
    help="Home path, where the csv and plot image will be created.",
    default=pathlib.Path.cwd(),
    show_default=True,
)
@click.option(
    "--offset",
    "offset_file",
    type=pathlib.Path,
    help="Offset file path.",
    required=True,
)
# Config Overloads
@click.option(
    "--amplitude_pp",
    type=float,
    help="The Amplitude of generated wave.",
    default=None,
)
@click.option(
    "--n_fs",
    type=float,
    help="Fs * n. Oversampling.",
    default=None,
)
@click.option(
    "--spd",
    type=float,
    help="Samples per decade.",
    default=None,
)
@click.option(
    "--n_samp",
    type=int,
    help="Number of samples.",
    default=None,
)
@click.option(
    "--f_range",
    nargs=2,
    type=(float, float),
    help="Samples Frequency Range.",
    default=None,
)
@click.option(
    "--y_lim",
    nargs=2,
    type=(float, float),
    help="Range y Plot.",
    default=None,
)
@click.option(
    "--x_lim",
    nargs=2,
    type=(float, float),
    help="Range x Plot.",
    default=None,
)
@click.option(
    "--y_offset",
    type=float,
    help="Offset value.",
    default=None,
)
@click.option(
    "--y_offset_auto",
    type=click.Choice(["min", "max", "no"], case_sensitive=False),
    help='Offset Mode, can be: "min", "max" or "no".',
    default=None,
)
# Flags
@click.option(
    "--time",
    is_flag=True,
    help="Elapsed time.",
    default=False,
)
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
@click.option(
    "--simulate",
    is_flag=True,
    help="Will Simulate the Sweep.",
    default=False,
)
def sweep(
    config_path: pathlib.Path,
    home: pathlib.Path,
    offset_file: pathlib.Path,
    amplitude_pp: Optional[float],
    n_fs: Optional[float],
    spd: Optional[float],
    n_samp: Optional[int],
    f_range: Optional[Tuple[float, float]],
    y_lim: Optional[Tuple[float, float]],
    x_lim: Optional[Tuple[float, float]],
    y_offset: Optional[float],
    y_offset_auto: Optional[str],
    time: bool,
    debug: bool,
    simulate: bool,
):

    HOME_PATH = home.absolute().resolve()

    datetime_now = datetime.now().strftime(f"%Y-%m-%d--%H-%M-%f")

    # Load JSON config
    config: Config = Config()

    config_file = config_path.absolute()
    config.from_file(config_file)

    if debug:
        console.print(Panel(config.tree(), title="Configuration JSON - FROM FILE"))

    # Override Configurations
    if amplitude_pp:
        config.rigol.amplitude_pp = amplitude_pp

    if n_fs:
        config.sampling.n_fs = n_fs

    if n_samp:
        config.sampling.number_of_samples = n_samp

    if f_range:
        f_min, f_max = f_range
        config.sampling.f_range = Range(f_min, f_max)

    if spd:
        config.sampling.points_per_decade = spd

    if y_lim:
        config.plot.y_limit = Range(*y_lim)

    if x_lim:
        config.plot.x_limit = Range(*x_lim)

    amplitude_base_level = float(offset_file.read_text())

    config.rigol.amplitude_pp = amplitude_base_level

    if y_offset:
        config.plot.y_offset = y_offset
    elif y_offset_auto and not isinstance(config.plot.y_offset, float):
        if y_offset_auto == ModAuto.NO.value:
            config.plot.y_offset = ModAuto.NO
        elif y_offset_auto == ModAuto.MIN.value:
            config.plot.y_offset = ModAuto.MIN
        elif y_offset_auto == ModAuto.MAX.value:
            config.plot.y_offset = ModAuto.MAX
        else:
            config.plot.y_offset = None

    if config.validate():
        console.print("Config Error.")
        exit()

    if debug:
        config.print()

    timer = Timer("Sweep time")
    if time:
        timer.start()

    measurements_dir: pathlib.Path = HOME_PATH / "{}".format(datetime_now)

    measurements_file: pathlib.Path = measurements_dir / "sweep.csv"
    image_file: pathlib.Path = measurements_dir / "sweep.png"

    measurements_dir.mkdir(parents=True, exist_ok=True)

    if not simulate:

        sampling_curve(
            config=config,
            measurements_file_path=measurements_file,
            debug=debug,
        )

    if time:
        timer.stop().print()

    if not simulate:

        plot_from_csv(
            measurements_file_path=measurements_file,
            plot_file_path=image_file,
            plot_config=config.plot,
            debug=debug,
        )

        create_latex_file(
            image_file, home=HOME_PATH, latex_home=measurements_dir, debug=debug
        )


@cli.command(help="Plot from a csv file.")
@click.option(
    "--csv",
    type=pathlib.Path,
    help="Measurements file path in csv format.",
    default=None,
)
@click.option(
    "--home",
    type=pathlib.Path,
    help="Home path, where the plot image will be created.",
    default=pathlib.Path.cwd(),
    show_default=True,
)
@click.option(
    "--format",
    type=click.Choice(["png", "pdf"], case_sensitive=False),
    multiple=True,
    help='Format of the plot, can be: "png" or "pdf".',
    default=["png"],
    show_default=True,
)
@click.option(
    "--y_lim",
    nargs=2,
    type=(float, float),
    help="Range y Plot.",
    default=None,
)
@click.option(
    "--x_lim",
    nargs=2,
    type=(float, float),
    help="Range x Plot.",
    default=None,
)
@click.option(
    "--y_offset",
    type=float,
    help="Offset value.",
    default=None,
)
@click.option(
    "--y_offset_auto",
    type=click.Choice(["min", "max", "no"], case_sensitive=False),
    help='Offset Mode, can be: "min", "max" or "no".',
    default=None,
)
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
def plot(
    csv: Optional[pathlib.Path],
    home: pathlib.Path,
    format: List[str],
    y_lim: Optional[Tuple[float, float]],
    x_lim: Optional[Tuple[float, float]],
    y_offset: Optional[float],
    y_offset_auto: Optional[str],
    debug: bool,
):
    HOME_PATH = home.absolute()
    csv_file: pathlib.Path = pathlib.Path()
    plot_file: Optional[pathlib.Path] = None

    y_offset_mode: Optional[Union[float, ModAuto]] = None
    if y_offset:
        y_offset_mode = y_offset
    elif y_offset_auto:
        if y_offset_auto == ModAuto.NO.value:
            y_offset_mode = ModAuto.NO
        elif y_offset_auto == ModAuto.MIN.value:
            y_offset_mode = ModAuto.MIN
        elif y_offset_auto == ModAuto.MAX.value:
            y_offset_mode = ModAuto.MAX
        else:
            y_offset_mode = None

    plot_config = Plot()
    plot_config.init(
        x_limit=Range(*x_lim) if x_lim else None,
        y_limit=Range(*y_lim) if y_lim else None,
        y_offset=y_offset_mode,
    )

    is_most_recent_file: bool = False
    plot_file: Optional[pathlib.Path] = None

    if csv:
        if csv.exists() and csv.is_file():
            csv_file = csv.absolute()
            plot_file = csv_file.with_suffix("")
            console.print("plot_file: {}".format(plot_file))
        else:
            console.print(
                Panel("File: '{}' doesn't exists.".format(csv), style="error")
            )
            is_most_recent_file = Confirm.ask(
                "Do you want to search for the most recent '[italic].csv[/]' file?",
                default=False,
            )
    else:
        is_most_recent_file = True

    if is_most_recent_file:

        measurement_dirs: List[pathlib.Path] = get_subfolder(HOME_PATH)

        if len(measurement_dirs) > 0:
            csv_file = measurement_dirs[-1] / "sweep.csv"

            if csv_file.exists() and csv_file.is_file():
                plot_file = csv_file.with_suffix("")
        else:
            console.print("There is no csv file available.", style="error")

    if plot_file:
        for plot_file_format in format:
            plot_file = plot_file.with_suffix("." + plot_file_format)
            console.print('Plotting file: "{}"'.format(plot_file.absolute()))
            plot_from_csv(
                measurements_file_path=csv_file,
                plot_file_path=plot_file,
                plot_config=plot_config,
                debug=debug,
            )
            if plot_file_format == "png":
                create_latex_file(plot_file, home=home)
    else:
        console.print("Cannot create a plot file.", style="error")


@cli.command(help="Gets the config Offset Through PID Controller.")
@click.option(
    "--config",
    "config_path",
    type=pathlib.Path,
    help="Configuration path of the config file in json5 format.",
    required=True,
)
@click.option(
    "--csv",
    type=pathlib.Path,
    help="Measurements file path in csv format.",
    default=None,
)
@click.option(
    "--home",
    type=pathlib.Path,
    help="Home path, where the plot image will be created.",
    default=pathlib.Path.cwd(),
    show_default=True,
)
@click.option(
    "--y_offset",
    type=float,
    help="Offset value.",
    default=None,
)
@click.option(
    "--y_offset_auto",
    type=click.Choice(["min", "max", "no"], case_sensitive=False),
    help='Offset Mode, can be: "min", "max" or "no".',
    default=None,
)
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
def config(
    config_path: pathlib.Path,
    csv: Optional[pathlib.Path],
    home: pathlib.Path,
    y_offset: Optional[float],
    y_offset_auto: Optional[str],
    debug: bool,
):
    HOME_PATH = home.absolute().resolve()
    csv_file: pathlib.Path = pathlib.Path()
    plot_file: pathlib.Path = pathlib.Path()

    config: Config = Config()

    config_file = config_path.absolute()
    config.from_file(config_file)

    if y_offset:
        config.plot.y_offset = y_offset
    elif y_offset_auto and not isinstance(config.plot.y_offset, float):
        if y_offset_auto == ModAuto.NO.value:
            config.plot.y_offset = ModAuto.NO
        elif y_offset_auto == ModAuto.MIN.value:
            config.plot.y_offset = ModAuto.MIN
        elif y_offset_auto == ModAuto.MAX.value:
            config.plot.y_offset = ModAuto.MAX
        else:
            config.plot.y_offset = None

    if config.validate():
        console.print("Config Error.")
        exit()

    if debug:
        config.print()

    datetime_now = datetime.now().strftime(f"%Y-%m-%d--%H-%M-%f")

    config_offset(
        config=config,
        plot_file_path=home / "audio-{}.config.png".format(datetime_now),
        debug=debug,
    )


@cli.command()
@click.option(
    "--home",
    type=pathlib.Path,
    help="Home path, where the plot image will be created.",
    default=pathlib.Path.cwd(),
    show_default=True,
)
@click.option(
    "--sweep-dir",
    "sweep_dir",
    type=pathlib.Path,
    help="Home path, where the plot image will be created.",
    default=None,
)
def sweep_debug(home, sweep_dir):

    measurement_dirs: List[pathlib.Path] = get_subfolder(home)

    dir: pathlib.Path

    if len(measurement_dirs) > 0:
        dir = measurement_dirs[-1] / "sweep"
    else:
        console.print("Cannot create the debug info from sweep csvs.", style="error")
        exit()

    csv_files = [csv for csv in dir.rglob("sample.csv") if csv.is_file()]

    for csv in csv_files:
        csv_parent = csv.parent
        frequency = float(csv_parent.name.replace("_", "."))
        plot_image = csv_parent / "plot.png"

        data: pd.DataFrame = pd.read_csv(
            csv.absolute().resolve(),
            header=0,
            comment="#",
        )

        # data.plot(kind="scatter")
        plot: Tuple[Figure, Dict[str, Axes]] = plt.subplot_mosaic(
            [
                ["samp", "samp", "rms_samp"],
                ["intr_samp", "intr_samp", "rms_intr_samp"],
                ["intr_samp_offset", "intr_samp_offset", "rms_intr_samp_offset"],
                [
                    "rms_intr_samp_offset_trim",
                    "rms_intr_samp_offset_trim",
                    "rms_intr_samp_offset_trim",
                ],
                [
                    "rms_intr_samp_offset_trim_gradient",
                    "rms_intr_samp_offset_trim_gradient",
                    "rms_intr_samp_offset_trim_gradient",
                ],
                [
                    "rms_intr_samp_offset_trim_average",
                    "rms_intr_samp_offset_trim_average",
                    "rms_intr_samp_offset_trim_average",
                ],
            ],
            figsize=(30, 25),
            dpi=300,
        )

        fig, axd = plot

        fig.suptitle(f"Frequency: {frequency} Hz.", fontsize=30)

        voltages = list(data["voltage"].values)

        plot_samp = axd["samp"]
        plot_samp.plot(
            voltages,
            marker=".",
            markersize=5,
        )
        rms_samp = RMS.fft(voltages)
        plot_samp.legend([f"Samples rms={rms_samp:.5}"], loc="best")

        plot_rms_samp = axd["rms_samp"]
        rms_samp_iter_list: List[float] = [0]
        for n in range(1, len(voltages), 5):
            rms_samp_iter_list.append(RMS.fft(voltages[0:n]))

        plot_rms_samp.plot(rms_samp_iter_list)
        plot_rms_samp.legend([f"Iterations Sample RMS"], loc="best")

        plot_intr_samp = axd["intr_samp"]
        voltages_to_interpolate = voltages
        x_interpolated, y_interpolated = interpolation_model(
            range(0, len(voltages_to_interpolate)),
            voltages_to_interpolate,
            int(len(voltages_to_interpolate) * 10),
            kind=INTERPOLATION_KIND.CUBIC,
        )

        pd.DataFrame(y_interpolated).to_csv(
            pathlib.Path(csv_parent / "interpolation_sample.csv").absolute().resolve(),
            header=["voltage"],
            index=None,
        )

        plot_intr_samp.plot(
            x_interpolated,
            y_interpolated,
            "-",
            linewidth=0.5,
        )
        rms_intr = RMS.fft(y_interpolated)
        plot_intr_samp.legend([f"Interpolated Samples rms={rms_intr:.5}"], loc="best")

        plot_rms_intr_samp = axd["rms_intr_samp"]
        rms_intr_samp_iter_list: List[float] = [0]
        for n in range(1, len(y_interpolated), 20):
            rms_intr_samp_iter_list.append(RMS.fft(y_interpolated[0:n]))

        plot_rms_intr_samp.plot(rms_intr_samp_iter_list)
        plot_rms_intr_samp.legend([f"Iterations Interpolated Sample RMS"], loc="best")

        # PLOT: Interpolated Sample, Zero Offset for complete Cycles
        offset_interpolated = find_sin_zero_offset(y_interpolated)

        plot_intr_samp_offset = axd["intr_samp_offset"]
        rms_intr_offset = RMS.fft(offset_interpolated)
        plot_intr_samp_offset.plot(
            offset_interpolated,
            linewidth=0.7,
        )
        plot_intr_samp_offset.legend(
            [f"Interpolated Samples with Offset rms={rms_intr_offset:.5}"], loc="best"
        )

        plot_rms_intr_samp_offset = axd["rms_intr_samp_offset"]
        rms_intr_samp_offset_iter_list: List[float] = [0]

        for n in range(1, len(offset_interpolated), 20):
            rms_intr_samp_offset_iter_list.append(RMS.fft(offset_interpolated[0:n]))

        pd.DataFrame(rms_intr_samp_offset_iter_list).to_csv(
            pathlib.Path(csv_parent / "interpolation_rms.csv").absolute().resolve(),
            header=["voltage"],
            index=None,
        )

        plot_rms_intr_samp_offset.plot(rms_intr_samp_offset_iter_list)
        plot_rms_intr_samp_offset.legend(
            [f"Iterations Interpolated Sample with Offset RMS"], loc="best"
        )

        # PLOT: RMS every sine period
        plot_rms_intr_samp_offset_trim = axd["rms_intr_samp_offset_trim"]
        (plot_rms_fft_intr_samp_offset_trim_list) = rms_full_cycle(offset_interpolated)

        plot_rms_intr_samp_offset_trim.plot(plot_rms_fft_intr_samp_offset_trim_list)
        plot_rms_intr_samp_offset_trim.legend(
            ["RMS fft per period, Interpolated"],
            loc="best",
        )

        plot_rms_intr_samp_offset_trim_gradient = axd[
            "rms_intr_samp_offset_trim_gradient"
        ]
        # rms_fft_gradient_list = np.gradient(plot_rms_fft_intr_samp_offset_trim_list)
        # plot_rms_intr_samp_offset_trim_gradient.plot(rms_fft_gradient_list)
        # plot_rms_intr_samp_offset_trim_gradient.legend(
        #     ["RMS fft per period, Interpolated GRADIENT"],
        #     loc="best",
        # )

        plot_rms_intr_samp_offset_trim_average = axd[
            "rms_intr_samp_offset_trim_average"
        ]
        # data_frame = pd.Series(plot_rms_fft_intr_samp_offset_trim_list)
        # rms_sma = data_frame.rolling(4).mean().tolist()[4:]
        # plot_rms_intr_samp_offset_trim_average.plot(rms_sma)
        # plot_rms_intr_samp_offset_trim_average.legend(
        #     [f"RMS fft per period, Interpolated Average: {rms_sma[-1]}"],
        #     loc="best",
        # )

        plt.savefig(plot_image)
        plt.close(fig)
        plt.clf()
        plt.cla()

        # console.print(
        #     f"Plotted Frequency: [blue]{frequency:7.5}[/] - rms_samp: {rms_samp:2.5} - rms_intr: {rms_intr:2.5}."
        # )

        console.print(f"Plotted Frequency: [blue]{frequency:7.5}[/].")


@cli.group()
def test():
    pass


@cli.group()
def rigol():
    pass


@rigol.command()
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
def off(debug: bool):
    # Asks for the 2 instruments
    list_devices: List[Instrument] = get_device_list()
    if debug:
        print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    generator.open()

    generator_ac_curves: List[str] = [
        SCPI.set_output(1, Switch.OFF),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    console.print(Panel("[blue]Rigol Turned OFF[/]"))


test.add_command(testTimer)


@cli.command()
@click.option("--home", type=pathlib.Path, default=pathlib.Path.cwd())
def gui(home: pathlib.Path):
    # SimpleApp.run(log="textual.log")
    App = GuiAudioMeasurements()
    App.run()
