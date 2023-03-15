import pathlib

import click

from audio.config.plot import PlotConfig
from audio.config.sweep import SweepConfig
from audio.config.type import Range
from audio.console import console
from audio.docker.latex import create_latex_file
from audio.sampling import plot_from_csv
from audio.utility import get_subfolder


@click.command(help="Plot from a csv file.")
@click.option(
    "--csv",
    type=pathlib.Path,
    help="Measurements file path in csv format.",
    default=None,
)
@click.option(
    "--output",
    type=pathlib.Path,
    help="Plot file location.",
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
    "--config",
    "config_path",
    type=pathlib.Path,
    help="Configuration path of the config file in json5 format.",
    default=None,
)
@click.option(
    "--format-plot",
    "format_plot",
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
    "--interpolation_rate",
    "interpolation_rate",
    type=float,
    help="Interpolation Rate.",
    default=None,
)
@click.option(
    "--dpi",
    type=int,
    help="Dpi Resolution for the image.",
    default=None,
)
@click.option(
    "--pdf/--no-pdf",
    "pdf",
    help="Will skip the pdf creation.",
    default=True,
)
@click.option(
    "--debug",
    is_flag=True,
    help="Will print verbose messages.",
    default=False,
)
def plot(
    csv: pathlib.Path | None,
    output: pathlib.Path | None,
    home: pathlib.Path,
    config_path: pathlib.Path | None,
    format_plot: list[str],
    y_lim: tuple[float, float] | None,
    x_lim: tuple[float, float] | None,
    y_offset: float | None,
    interpolation_rate: float | None,
    dpi: int | None,
    pdf: bool,
    debug: bool,
):
    HOME_PATH = home
    csv_file_path: pathlib.Path | None = None
    plot_file_path: pathlib.Path | None = None

    sweep_config = SweepConfig.from_xml_file(config_path)

    if sweep_config is None:
        raise Exception("sweep_config is NULL")

    plot_config: PlotConfig = sweep_config.plot

    plot_config.override(
        y_offset=y_offset,
        x_limit=Range.from_list(x_lim),
        y_limit=Range.from_list(y_lim),
        interpolation_rate=interpolation_rate,
        dpi=dpi,
    )

    console.print(plot_config)

    is_most_recent_file: bool = False

    latex_home: pathlib.Path = pathlib.Path()

    if csv is not None and csv.exists() and csv.is_file():
        csv_file_path = csv

        if output is None:
            output = csv_file_path.with_suffix("")

        plot_file_path = output

        latex_home = csv.parent

    else:
        is_most_recent_file = True

    if is_most_recent_file:

        measurement_dirs: list[pathlib.Path] = get_subfolder(HOME_PATH)

        if len(measurement_dirs) > 0:
            csv_file_path = measurement_dirs[-1] / "sweep.csv"

            if csv_file_path.exists() and csv_file_path.is_file():
                plot_file_path = csv_file_path.with_suffix("")
                latex_home = csv_file_path.parent
        else:
            console.print("There is no csv file available.", style="error")

    if plot_file_path:
        for plot_file_format in format_plot:
            plot_file_path = plot_file_path.with_suffix("." + plot_file_format)
            console.print(f'Plotting file: "{plot_file_path.absolute()}"')
            plot_from_csv(
                measurements_file_path=csv_file_path,
                plot_file_path=plot_file_path,
                plot_config=sweep_config.plot,
                debug=debug,
            )
            if plot_file_format == "png":
                if pdf:
                    create_latex_file(
                        plot_file_path, home=HOME_PATH, latex_home=latex_home
                    )
    else:
        console.print("Cannot create a plot file.", style="error")
        console.print("Cannot create a plot file.", style="error")
