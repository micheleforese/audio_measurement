from datetime import datetime
import pathlib
import click
from cDAQ.console import console
from cDAQ.sampling import curva

# from tests.sampling.test_sampling import curva


@click.command()
@click.option("--debug", is_flag=True, help="Will print verbose messages.")
@click.argument("config", type=pathlib.Path)
def cli(debug: bool, config: pathlib.Path):
    console.print("helloooo")
    console.print("Config: [blue]{}[/]".format(config.absolute()))
    console.print("Parent: [blue]{}[/]".format(config.absolute().parent))
    console.print("Parent: [blue]{}[/]".format(config.absolute().name))

    home_path = config.absolute().parent

    config_file = config.absolute().name

    datetime_now = datetime.now().strftime(f"%Y-%m-%d--%H-%M-%f")

    curva(
        config_file_path=home_path / config_file,
        measurements_file_path=home_path / "audio-[{}].csv".format(datetime_now),
        plot_file_path=home_path / "audio-[{}].png".format(datetime_now),
        debug=debug,
    )
