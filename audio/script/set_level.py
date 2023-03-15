import pathlib
from datetime import datetime

import click

from audio.config.sweep import SweepConfig
from audio.console import console
from audio.sampling import config_set_level


@click.command(help="Gets the config Offset Through PID Controller.")
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
    help="Home path, where the plot image will be created.",
    default=pathlib.Path.cwd(),
    show_default=True,
)
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
def set_level(
    config_path: pathlib.Path,
    home: pathlib.Path,
    debug: bool,
):
    HOME_PATH = home.absolute().resolve()

    datetime_now = datetime.now().strftime(r"%Y-%m-%d--%H-%M-%f")

    config_file = config_path.absolute()
    config: SweepConfig = SweepConfig.from_xml_file(config_file)

    if debug:
        console.print(config)

    config_set_level(
        dBu=4,
        config=config,
        plot_file_path=HOME_PATH / f"{datetime_now}.config.png",
        debug=debug,
    )
