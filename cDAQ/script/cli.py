from email.policy import default
from heapq import nsmallest
import pathlib
from datetime import datetime
from typing import List, Optional, Tuple

import click
from numpy import dtype
from rich.panel import Panel
from cDAQ.config import Config
from cDAQ.console import console
from cDAQ.sampling import curva, plot_from_csv, sampling_curve
from cDAQ.timer import Timer
from rich.prompt import Prompt, Confirm


@click.group()
def cli():
    pass


@cli.command()
@click.argument("--config", type=Optional[pathlib.Path], default=None)
@click.option("--home", type=pathlib.Path, default=pathlib.Path.cwd())
@click.option("--time", is_flag=True, help="Elapsed time.", default=False)
@click.option("--n_fs", type=float, help="Fs * n. Oversampling.", default=6)
@click.option("--spd", type=float, help="Samples per decade.", default=50)
@click.option("--n_samp", type=int, help="Number of samples.", default=140)
@click.option(
    "--f_min", type=float, help="Range Minimum Samples Frequency.", default=20
)
@click.option(
    "--f_max", type=float, help="Range Maximum Samples Frequency.", default=20000
)
@click.option(
    "--debug", is_flag=True, help="Will print verbose messages.", default=False
)
def sweep(
    config: Optional[pathlib.Path],
    home: pathlib.Path,
    time: bool,
    amplitude_pp: Optional[float],
    n_fs: float,
    spd: float,
    n_samp: int,
    f_min: float,
    f_max: float,
    debug: bool,
):
    HOME_PATH = home.absolute()

    datetime_now = datetime.now().strftime(f"%Y-%m-%d--%H-%M-%f")

    timer = Timer("Sweep time")
    if time:
        timer.start()

    """Load JSON config"""
    config_obj: Config = Config()

    if config is not None:
        config_file = config.absolute()
        config_obj.from_file(config_file)

    config_obj.sampling.min_Hz = f_min
    config_obj.sampling.max_Hz = f_max

    if debug:
        config_obj.print()

    sampling_curve(
        config=config_obj,
        measurements_file_path=HOME_PATH / "audio-[{}].csv".format(datetime_now),
        amplitude_pp=amplitude_pp,
        nFs=n_fs,
        spd=spd,
        n_samp=n_samp,
        debug=debug,
    )

    y_lim_min: Optional[float] = None
    y_lim_max: Optional[float] = None

    if config_obj.plot.y_limit:
        y_lim_min, y_lim_max = config_obj.plot.y_limit

    plot_from_csv(
        measurements_file_path=HOME_PATH / "audio-[{}].csv".format(datetime_now),
        plot_file_path=HOME_PATH / "audio-[{}].png".format(datetime_now),
        y_lim_min=y_lim_min,
        y_lim_max=y_lim_max,
        debug=debug,
    )

    if time:
        timer.stop().print()


@cli.command()
@click.argument("--csv", type=pathlib.Path, default=None)
@click.option("--home", type=pathlib.Path, default=pathlib.Path.cwd())
@click.option(
    "--format",
    help="The file format of the plot.",
    type=click.Choice(["png", "pdf"], case_sensitive=False),
    multiple=True,
    default=["png"],
)
@click.option("--y_lim_min", type=float, default=None)
@click.option("--y_lim_max", type=float, default=None)
@click.option(
    "--debug", is_flag=True, help="Will print verbose messages.", default=False
)
def plot(
    csv: Optional[pathlib.Path],
    home: pathlib.Path,
    format: List[str],
    y_lim_min: Optional[float],
    y_lim_max: Optional[float],
    debug: bool,
):
    HOME_PATH = home.absolute()
    csv_file: pathlib.Path
    plot_file: pathlib.Path

    is_most_recent_file: bool = False

    if csv:
        if csv.exists() and csv.is_file():
            csv_file = csv.absolute()
            plot_file = csv_file.with_suffix("")
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
    else:
        exit()

    for plot_file_format in format:
        plot_from_csv(
            measurements_file_path=csv_file,
            plot_file_path=plot_file.with_suffix(plot_file_format),
            y_lim_max=y_lim_max,
            y_lim_min=y_lim_min,
            debug=debug,
        )
