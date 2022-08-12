from __future__ import annotations

from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from multipledispatch import dispatch
from rich.progress import track

from audio.math.interpolation import INTERPOLATION_KIND, logx_interpolation_model
from audio.model.sweep import SweepData


@dispatch(list[Path], Path)
def multiplot(
    csv_files_path: List[Path],
    output_file_path: Path,
):

    # Check for Files validity
    for csv in csv_files_path:
        if not csv.exists() or not csv.is_file():
            return False

    sweep_data_list: List[SweepData] = []

    for csv in csv_files_path:
        sweep_data = SweepData.from_csv_file(csv)
        sweep_data_list.append(sweep_data)

    multiplot(
        sweep_data_list=sweep_data_list,
        output_file_path=output_file_path,
    )


@dispatch(list[SweepData], Path)
def multiplot(
    sweep_data_list: List[SweepData],
    output_file_path: Path,
):
    DEFAULT = {
        "interpolation_rate": 5,
        "dpi": 400,
    }

    fig, axes = plt.subplots(
        figsize=(16 * 2, 9 * 2),
        dpi=DEFAULT.get("dpi"),
    )

    # Line at y=-3 is disabled
    #
    # axes.plot(
    #     [0, max(x_interpolated)],
    #     [-3, -3],
    #     "-",
    #     color="green",
    # )

    axes.set_title(
        "Frequency response",
        fontsize=50,
    )
    axes.set_xlabel(
        "Frequency ($Hz$)",
        fontsize=40,
    )
    axes.set_ylabel(
        # "Amplitude ($dB$) ($0 \, dB = {} \, Vpp$)".format(
        #     round(cfg.y_offset, 5) if cfg.y_offset else 0
        # ),
        "Amplitude ($dB$)",
        fontsize=40,
    )
    axes.tick_params(
        axis="both",
        labelsize=22,
    )
    axes.tick_params(axis="x", rotation=90)

    granularity_ticks = 0.1

    logLocator = ticker.LogLocator(subs=np.arange(0, 1, granularity_ticks))

    def logMinorFormatFunc(x, pos):
        return "{:.0f}".format(x)

    logMinorFormat = ticker.FuncFormatter(logMinorFormatFunc)

    # X Axis - Major
    axes.xaxis.set_major_locator(logLocator)
    axes.xaxis.set_major_formatter(logMinorFormat)

    axes.grid(True, linestyle="-", which="both", color="0.7")

    for sweep_data in track(sweep_data_list, description="Sweep Data Plotting..."):
        cfg = sweep_data.config

        x_frequency = list(sweep_data.frequency.values)
        y_dBV: List[float] = list(sweep_data.dBV.values)

        # Apply y_offset
        if cfg.y_offset:
            y_dBV = [dBV - cfg.y_offset for dBV in y_dBV]

        x_interpolated, y_interpolated = logx_interpolation_model(
            x_frequency,
            y_dBV,
            int(
                len(x_frequency)
                * (
                    cfg.interpolation_rate
                    if cfg.interpolation_rate is not None
                    else DEFAULT.get("interpolation_rate")
                )
            ),
            kind=INTERPOLATION_KIND.CUBIC,
        )
        xy_sampled = [x_frequency, y_dBV, "o"]
        xy_interpolated = [x_interpolated, y_interpolated, "-"]

        axes.semilogx(
            *xy_sampled,
            *xy_interpolated,
            linewidth=4,
            color=cfg.color if cfg.color is not None else "yellow",
        )

    plt.tight_layout()

    plt.savefig(output_file_path)
