import pathlib
from datetime import datetime
from typing import List, Optional, Tuple, Union

import click
from cDAQ.config import Config
from cDAQ.config.type import Range
from cDAQ.console import console
from cDAQ.sampling import plot_from_csv, sampling_curve
from cDAQ.script.gui import AudioMeasurementsApp
from cDAQ.timer import Timer
from rich.panel import Panel
from rich.prompt import Confirm


@click.group()
def cli():
    return 0


@cli.command()
@click.option("--config", "config_path", type=pathlib.Path, required=True)
@click.option("--home", type=pathlib.Path, default=pathlib.Path.cwd())
# Config Overloads
@click.option(
    "--amplitude_pp", type=float, help="The Amplitude of generated wave.", default=None
)
@click.option("--n_fs", type=float, help="Fs * n. Oversampling.", default=None)
@click.option("--spd", type=float, help="Samples per decade.", default=None)
@click.option("--n_samp", type=int, help="Number of samples.", default=None)
@click.option(
    "--f_range",
    nargs=2,
    type=(float, float),
    help="Samples Frequency Range.",
    default=None,
)
@click.option(
    "--y_lim", nargs=2, type=(float, float), help="Range y Plot.", default=None
)
@click.option(
    "--x_lim", nargs=2, type=(float, float), help="Range x Plot.", default=None
)
@click.option("--y_offset", type=float, default=None)
@click.option(
    "--y_offset_auto",
    type=click.Choice(["min", "max", "no"], case_sensitive=False),
    default=None,
)
# Flags
@click.option("--time", is_flag=True, help="Elapsed time.", default=False)
@click.option(
    "--debug", is_flag=True, help="Will print verbose messages.", default=False
)
def sweep(
    config_path: pathlib.Path,
    home: pathlib.Path,
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
):
    HOME_PATH = home.absolute()

    datetime_now = datetime.now().strftime(f"%Y-%m-%d--%H-%M-%f")

    # Load JSON config
    config: Config = Config()

    config_file = config_path.absolute()
    config.from_file(config_file)

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

    y_offset_mode: Optional[Union[float, str]] = None
    if y_offset:
        y_offset_mode = y_offset
    elif y_offset_auto:
        y_offset_mode = y_offset_auto

    # TODO: Implement Configuration validation
    if config.validate():
        console.print("Config Error.")
        exit()

    config.calculate_step()

    if debug:
        config.print()

    timer = Timer("Sweep time")
    if time:
        timer.start()

    sampling_curve(
        config=config,
        measurements_file_path=HOME_PATH / "audio-[{}].csv".format(datetime_now),
        debug=debug,
    )

    if time:
        timer.stop().print()

    plot_from_csv(
        measurements_file_path=HOME_PATH / "audio-[{}].csv".format(datetime_now),
        plot_file_path=HOME_PATH / "audio-[{}].png".format(datetime_now),
        y_lim=config.plot.y_limit,
        x_lim=config.plot.x_limit,
        y_offset=y_offset_mode,
        debug=debug,
    )


@cli.command()
@click.option("--csv", type=pathlib.Path, default=None)
@click.option("--home", type=pathlib.Path, default=pathlib.Path.cwd())
@click.option(
    "--format",
    help="The file format of the plot.",
    type=click.Choice(["png", "pdf"], case_sensitive=False),
    multiple=True,
    default=["png"],
)
@click.option(
    "--y_lim",
    nargs=2,
    type=(float, float),
    help="Range y Plot.",
)
@click.option(
    "--x_lim",
    nargs=2,
    type=(float, float),
    help="Range x Plot.",
)
@click.option("--y_offset", type=float, default=None)
@click.option(
    "--y_offset_auto",
    type=click.Choice(["min", "max", "no"], case_sensitive=False),
    default=None,
)
@click.option(
    "--debug", is_flag=True, help="Will print verbose messages.", default=False
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
    plot_file: pathlib.Path = pathlib.Path()

    y_offset_mode: Optional[Union[float, str]] = None
    if y_offset:
        y_offset_mode = y_offset
    elif y_offset_auto:
        y_offset_mode = y_offset_auto

    is_most_recent_file: bool = False

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
        # Take the most recent csv File.
        csv_file_list: List[pathlib.Path] = [
            csv for csv in HOME_PATH.rglob("*.csv") if csv.is_file() and csv.stem
        ]

        csv_file_list.sort(
            key=lambda name: datetime.strptime(
                name.stem, f"audio-[%Y-%m-%d--%H-%M-%f]"
            ),
            reverse=True,
        )
        try:
            csv_file = csv_file_list.pop()
            date_pattern = datetime.now().strftime(f"%Y-%m-%d--%H-%M-%f")

            plot_file = HOME_PATH / date_pattern
        except IndexError:
            console.print("There is no csv file available.", style="error")
            exit()

    for plot_file_format in format:
        plot_file = plot_file.with_suffix("." + plot_file_format)
        console.print("Plotting file: {}".format(plot_file))
        plot_from_csv(
            measurements_file_path=csv_file,
            plot_file_path=plot_file,
            x_lim=Range(*x_lim) if x_lim else None,
            y_lim=Range(*y_lim) if y_lim else None,
            y_offset=y_offset_mode,
            debug=debug,
        )


@cli.command()
@click.option("--home", type=pathlib.Path, default=pathlib.Path.cwd())
def gui(home: pathlib.Path):
    # SimpleApp.run(log="textual.log")
    App = AudioMeasurementsApp(home)
    App.run(title="Audio Measurements", log="audio_measurements_app.log", home=home)
