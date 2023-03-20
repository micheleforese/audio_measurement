import pathlib
from datetime import datetime

import click

from audio.config.sweep import SweepConfig
from audio.config.type import Range
from audio.console import console
from audio.docker.latex import create_latex_file
from audio.model.set_level import SetLevel
from audio.sampling import plot_from_csv, sampling_curve
from audio.utility.timer import Timer


@click.command(help="Audio Sweep")
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
    "--set_level_file",
    "set_level_file",
    type=pathlib.Path,
    help="Set Level file path.",
    default=None,
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
# Flags
@click.option(
    "--time/--no-time",
    help="Show elapsed time.",
    default=False,
)
@click.option(
    "--debug/--no-debug",
    "debug",
    help="Will print verbose messages.",
    default=False,
)
@click.option(
    "--simulate",
    is_flag=True,
    help="Will Simulate the Sweep.",
    default=False,
)
@click.option(
    "--pdf/--no-pdf",
    "pdf",
    help="Will skip the pdf creation.",
    default=True,
)
def sweep(
    config_path: pathlib.Path,
    home: pathlib.Path,
    set_level_file: pathlib.Path | None,
    amplitude_pp: float | None,
    n_fs: float | None,
    spd: float | None,
    n_samp: int | None,
    f_range: tuple[float, float] | None,
    y_lim: tuple[float, float] | None,
    x_lim: tuple[float, float] | None,
    y_offset: float | None,
    time: bool,
    debug: bool,
    simulate: bool,
    pdf: bool,
):
    HOME_PATH = home.absolute().resolve()

    datetime_now = datetime.now().strftime(r"%Y-%m-%d--%H-%M-%f")

    # Load JSON config
    cfg = SweepConfig.from_xml_file(config_path)

    if cfg is None:
        raise Exception("Configurations not loaded correctly.")

    if debug:
        cfg.print_object()

    # Override Configurations
    cfg.rigol.override(amplitude_pp)

    cfg.sampling.override(
        Fs_multiplier=n_fs,
        points_per_decade=spd,
        number_of_samples=n_samp,
        frequency_min=f_range[0] if f_range else None,
        frequency_max=f_range[1] if f_range else None,
    )

    amplitude_peak_to_peak: float | None = None

    if set_level_file:
        amplitude_peak_to_peak = SetLevel.from_file(set_level_file).set_level
    else:
        set_level_data = SetLevel.from_most_recent(
            HOME_PATH,
            "*.config.offset",
            r"%Y-%m-%d--%H-%M-%f",
        )
        amplitude_peak_to_peak = set_level_data.set_level

    cfg.rigol.override(
        amplitude_peak_to_peak=amplitude_peak_to_peak,
    )

    cfg.plot.override(
        y_offset=set_level_data.y_offset_db,
        x_limit=Range.from_list(x_lim),
        y_limit=Range.from_list(y_lim),
    )

    if debug:
        cfg.print_object()

    home_measurements_dir_path: pathlib.Path = pathlib.Path(
        HOME_PATH / f"{datetime_now}",
    )
    home_measurements_dir_path.mkdir(parents=True, exist_ok=True)

    measurements_file_path: pathlib.Path = home_measurements_dir_path / "sweep.csv"
    image_file_path: pathlib.Path = home_measurements_dir_path / "sweep.png"

    if not simulate:
        timer = Timer()

        if time:
            timer.start()

        sampling_curve(
            config=cfg,
            sweep_home_path=home_measurements_dir_path,
            sweep_file_path=measurements_file_path,
            debug=debug,
        )

        if time:
            time_execution = timer.stop()

            console.log(f"Sweep time: {time_execution}")

    if not simulate:
        plot_from_csv(
            plot_config=cfg.plot,
            measurements_file_path=measurements_file_path,
            plot_file_path=image_file_path,
            debug=debug,
        )

        if pdf:
            create_latex_file(
                image_file_path,
                home=HOME_PATH,
                latex_home=home_measurements_dir_path,
                debug=debug,
            )
