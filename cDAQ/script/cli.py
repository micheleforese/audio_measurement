from email.policy import default
from os import PathLike
import pathlib
from datetime import datetime
from typing import List, Tuple

import click
from cDAQ.config import Config
from cDAQ.console import console
from cDAQ.sampling import curva, plot_from_csv

# from tests.sampling.test_sampling import curva


@click.group()
def cli():
    pass


@cli.command()
@click.argument("config", type=pathlib.Path)
@click.argument("home", type=pathlib.Path)
@click.option(
    "--debug", is_flag=True, help="Will print verbose messages.", default=False
)
def sweep(config: pathlib.Path, home: pathlib.Path, debug: bool = False):
    home_path = home.absolute()

    config_file = config.absolute()

    datetime_now = datetime.now().strftime(f"%Y-%m-%d--%H-%M-%f")

    curva(
        config_file_path=config_file,
        measurements_file_path=home_path / "audio-[{}].csv".format(datetime_now),
        plot_file_path=home_path / "audio-[{}].png".format(datetime_now),
        debug=debug,
    )


@cli.command()
@click.argument("measurements", type=pathlib.Path)
@click.argument("home", type=pathlib.Path)
@click.option(
    "--format",
    help="The file format of the plot.",
    type=click.Choice(["png", "pdf"], case_sensitive=False),
    multiple=True,
    default=["png"],
)
@click.option("--y_lim_min", default=-10)
@click.option("--y_lim_max", default=10)
@click.option(
    "--debug", is_flag=True, help="Will print verbose messages.", default=False
)
def plot(
    measurements: pathlib.Path,
    home: pathlib.Path,
    format: List[str],
    y_lim_min: float,
    y_lim_max: float,
    debug: bool,
):
    home_path = home.absolute()

    measurements_file = measurements.absolute()

    plot_file = measurements.absolute().stem

    for plot_file_format in format:
        plot_from_csv(
            measurements_file_path=measurements_file,
            plot_file_path=home_path / "{}.{}".format(plot_file, plot_file_format),
            y_lim_max=y_lim_max,
            y_lim_min=y_lim_min,
            debug=debug,
        )
