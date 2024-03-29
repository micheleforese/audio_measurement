from __future__ import annotations

import hashlib
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import ticker
from rich.progress import track

from audio.config.sweep import SweepConfig
from audio.console import console
from audio.math.interpolation import InterpolationKind, logx_interpolation_model
from audio.model.sweep import SweepData


class CacheCsvData:
    _csvData: dict[str, SweepData]

    def __init__(self) -> None:
        self._csvData = {}

    def _create_hash(self, csv_path: Path) -> str:
        path = csv_path.absolute().resolve().as_uri().encode("utf-8")
        path_hash = hashlib.sha256(path).hexdigest()
        return path_hash

    def add_csv_file(self, csv_path: Path):
        path_hash = self._create_hash(csv_path)

        if self._csvData.get(path_hash, None) is None:
            sweep_data = SweepData.from_csv_file(csv_path)
            self._csvData[path_hash] = sweep_data

    def get_csv_file_data(self, csv_path: Path) -> SweepData | None:
        path_hash = self._create_hash(csv_path)

        return self._csvData.get(path_hash, None)


def multiplot(
    csv_files_paths: list[Path],
    output_file_path: Path,
    cache_csv_data: CacheCsvData,
    sweep_config: SweepConfig | None = None,
) -> bool:
    # Check for Files validity
    for csv in csv_files_paths:
        if not csv.exists() or not csv.is_file():
            return False

    for csv in csv_files_paths:
        cache_csv_data.add_csv_file(csv)

    DEFAULT = {
        "interpolation_rate": 5,
        "dpi": 400,
    }

    fig, axes = plt.subplots(
        figsize=(16 * 2, 9 * 2),
        dpi=DEFAULT.get("dpi"),
    )

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
        return f"{x:.0f}"

    logMinorFormat = ticker.FuncFormatter(logMinorFormatFunc)

    # X Axis - Major
    axes.xaxis.set_major_locator(logLocator)
    axes.xaxis.set_major_formatter(logMinorFormat)

    axes.grid(True, linestyle="-", which="both", color="0.7")

    for csv_file in track(
        csv_files_paths,
        transient=True,
        description="Sweep Data Plotting...",
    ):
        sweep_data: SweepData = cache_csv_data.get_csv_file_data(csv_file)
        if sweep_data is None:
            console.log(f"[ERROR] - data Not found at csv_file: {csv_file}")
            continue

        cfg = sweep_data.config

        x_frequency = list(sweep_data.frequency.values)
        y_dBV: list[float] = list(sweep_data.dBV.values)

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
                ),
            ),
            kind=InterpolationKind.CUBIC,
        )
        xy_sampled = [x_frequency, y_dBV, "o"]
        xy_interpolated = [x_interpolated, y_interpolated, "-"]

        legend: str | None = None

        if cfg is not None and cfg.legend is not None:
            legend = cfg.legend

        axes.semilogx(
            *xy_sampled,
            *xy_interpolated,
            linewidth=1,
            color=cfg.color if cfg.color is not None else "yellow",
            label=legend,
        )

        axes.legend(loc="best")

    if sweep_config is not None and sweep_config.plot is not None:
        if sweep_config.plot.y_limit is not None:
            axes.set_ylim(
                sweep_config.plot.y_limit.min_value,
                sweep_config.plot.y_limit.max_value,
            )

    plt.tight_layout()

    output_file_path.parent.mkdir(exist_ok=True, parents=True)

    plt.savefig(output_file_path)
    plt.close("all")

    console.print(f"[PLOT] - Graph: [blue]{output_file_path}[/blue]")
    return None
