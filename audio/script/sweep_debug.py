import pathlib

import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from audio.console import console
from audio.math import rms_full_cycle, trim_sin_zero_offset
from audio.math.interpolation import InterpolationKind, interpolation_model
from audio.math.rms import RMS
from audio.model.sweep import SingleSweepData
from audio.utility import get_subfolder


@click.command()
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
@click.option(
    "--iteration-rms/--no-iteration-rms",
    "iteration_rms",
    help="Home path, where the plot image will be created.",
    default=False,
)
def sweep_debug(
    home,
    sweep_dir: pathlib.Path | None,
    iteration_rms: bool,
):
    measurement_dir: pathlib.Path = pathlib.Path()

    if sweep_dir is not None:
        measurement_dir = sweep_dir / "sweep"

    else:
        measurement_dirs: list[pathlib.Path] = get_subfolder(home)

        if len(measurement_dirs) > 0:
            measurement_dir = measurement_dirs[-1] / "sweep"
        else:
            raise Exception("Cannot create the debug info from sweep csvs.")

    if not measurement_dir.exists() or not measurement_dir.is_dir():
        raise Exception("The measurement directory doesn't exists.")

    csv_files = [csv for csv in measurement_dir.rglob("sample.csv") if csv.is_file()]

    if len(csv_files) > 0:
        csv_files.sort(key=lambda name: float(name.parent.name.replace("_", ".")))

    for csv in csv_files:
        csv_parent = csv.parent
        plot_image = csv_parent / "plot.png"

        single_sweep_data = SingleSweepData(csv)

        plot: tuple[Figure, dict[str, Axes]] = plt.subplot_mosaic(
            [
                ["samp", "samp", "rms_samp"],
                ["intr_samp", "intr_samp", "rms_intr_samp"],
                ["intr_samp_offset", "intr_samp_offset", "rms_intr_samp_offset"],
                [
                    "rms_intr_samp_offset_trim",
                    "rms_intr_samp_offset_trim",
                    "rms_intr_samp_offset_trim",
                ],
            ],
            figsize=(30, 20),
            dpi=300,
        )

        fig, axd = plot

        for ax_key in axd:
            axd[ax_key].grid(True)

        fig.suptitle(f"Frequency: {single_sweep_data.frequency} Hz.", fontsize=30)
        fig.subplots_adjust(
            wspace=0.5,  # the amount of width reserved for blank space between subplots
            hspace=0.5,  # the amount of height reserved for white space between subplots
        )

        # PLOT: Samples on Time Domain
        ax_time_domain_samples = axd["samp"]

        rms_samp = RMS.fft(single_sweep_data.voltages.values)

        ax_time_domain_samples.plot(
            np.linspace(
                0,
                len(single_sweep_data.voltages) / single_sweep_data.Fs,
                len(single_sweep_data.voltages),
            ),
            single_sweep_data.voltages,
            marker=".",
            markersize=3,
            linestyle="-",
            linewidth=1,
            label=f"Voltage Sample - rms={rms_samp:.5}",
        )
        ax_time_domain_samples.set_title(
            f"Samples on Time Domain - Frequency: {round(single_sweep_data.frequency, 5)}",
        )
        ax_time_domain_samples.set_ylabel("Voltage [$V$]")
        ax_time_domain_samples.set_xlabel("Time [$s$]")
        ax_time_domain_samples.legend(loc="best")

        # PLOT: RMS iterating every 5 values
        if iteration_rms:
            plot_rms_samp = axd["rms_samp"]
            rms_samp_iter_list: list[float] = [0]
            for n in range(5, len(single_sweep_data.voltages.values), 5):
                rms_samp_iter_list.append(
                    RMS.fft(single_sweep_data.voltages.values[0:n]),
                )

            plot_rms_samp.plot(
                np.arange(
                    0,
                    len(single_sweep_data.voltages),
                    5,
                ),
                rms_samp_iter_list,
                label="Iterations Sample RMS",
            )
            plot_rms_samp.legend(loc="best")

        plot_intr_samp = axd["intr_samp"]
        voltages_to_interpolate = single_sweep_data.voltages.values

        INTERPOLATION_RATE = 10

        x_interpolated, y_interpolated = interpolation_model(
            range(0, len(voltages_to_interpolate)),
            voltages_to_interpolate,
            int(len(voltages_to_interpolate) * INTERPOLATION_RATE),
            kind=InterpolationKind.CUBIC,
        )

        pd.DataFrame(y_interpolated).to_csv(
            pathlib.Path(csv_parent / "interpolation_sample.csv").absolute().resolve(),
            header=["voltage"],
            index=None,
        )

        rms_intr = RMS.fft(y_interpolated)
        plot_intr_samp.plot(
            np.linspace(
                0,
                len(y_interpolated) / (single_sweep_data.Fs * INTERPOLATION_RATE),
                len(y_interpolated),
            ),
            # x_interpolated,
            y_interpolated,
            linestyle="-",
            linewidth=0.5,
            label=f"rms={rms_intr:.5}",
        )
        plot_intr_samp.set_title("Interpolated Samples")
        plot_intr_samp.set_ylabel("Voltage [$V$]")
        plot_intr_samp.set_xlabel("Time [$s$]")
        plot_intr_samp.legend(loc="best")

        if iteration_rms:
            plot_rms_intr_samp = axd["rms_intr_samp"]
            rms_intr_samp_iter_list: list[float] = [0]
            for n in range(1, len(y_interpolated), 20):
                rms_intr_samp_iter_list.append(RMS.fft(y_interpolated[0:n]))

            plot_rms_intr_samp.plot(
                rms_intr_samp_iter_list,
                label="Iterations Interpolated Sample RMS",
            )
            plot_rms_intr_samp.legend(loc="best")

        # PLOT: Interpolated Sample, Zero Offset for complete Cycles
        offset_interpolated, idx_start, idx_end = trim_sin_zero_offset(y_interpolated)

        plot_intr_samp_offset = axd["intr_samp_offset"]
        rms_intr_offset = RMS.fft(offset_interpolated)
        plot_intr_samp_offset.plot(
            np.linspace(
                idx_start / single_sweep_data.Fs,
                len(offset_interpolated) / (single_sweep_data.Fs * INTERPOLATION_RATE),
                len(offset_interpolated),
            ),
            offset_interpolated,
            linewidth=0.7,
            label=f"rms={rms_intr_offset:.5}",
        )
        plot_intr_samp_offset.set_title("Interpolated Samples with Offset")
        plot_intr_samp_offset.set_ylabel("Voltage [$V$]")
        plot_intr_samp_offset.set_xlabel("Time [$s$]")
        plot_intr_samp_offset.legend(loc="best")

        if iteration_rms:
            plot_rms_intr_samp_offset = axd["rms_intr_samp_offset"]
            rms_intr_samp_offset_iter_list: list[float] = [0]

            for n in range(1, len(offset_interpolated), 20):
                rms_intr_samp_offset_iter_list.append(RMS.fft(offset_interpolated[0:n]))

            pd.DataFrame(rms_intr_samp_offset_iter_list).to_csv(
                pathlib.Path(csv_parent / "interpolation_rms.csv").absolute().resolve(),
                header=["voltage"],
                index=None,
            )

            plot_rms_intr_samp_offset.plot(
                rms_intr_samp_offset_iter_list,
                label="Iterations Interpolated Sample with Offset RMS",
            )
            plot_rms_intr_samp_offset.legend(loc="best")

        # PLOT: RMS every sine period
        plot_rms_intr_samp_offset_trim = axd["rms_intr_samp_offset_trim"]
        (plot_rms_fft_intr_samp_offset_trim_list) = rms_full_cycle(offset_interpolated)

        plot_rms_intr_samp_offset_trim.plot(
            plot_rms_fft_intr_samp_offset_trim_list,
            label="RMS fft per period, Interpolated",
        )
        plot_rms_intr_samp_offset_trim.legend(loc="best")

        plt.savefig(plot_image)
        plt.close("all")

        console.print(f"Plotted Frequency: [blue]{single_sweep_data.frequency:7.5}[/].")
