import enum
import pathlib
from typing import List, Optional

import numpy as np
import pandas as pd
from scipy.fft import fft

from audio.console import console
from audio.math import (
    find_sin_zero_offset,
    integrate,
)
from audio.math.interpolation import INTERPOLATION_KIND, interpolation_model
from audio.utility import read_voltages
from audio.utility.timer import Timer


class RMS_MODE(enum.Enum):
    FFT = 1
    AVERAGE = 2
    INTEGRATE = 3


class RMS:
    @staticmethod
    def rms(
        frequency: float,
        Fs: float,
        number_of_samples: int,
        ch_input: str,
        max_voltage: float,
        min_voltage: float,
        rms_mode: RMS_MODE = RMS_MODE.FFT,
        time_report: bool = False,
        save_file: Optional[pathlib.Path] = None,
        trim: bool = True,
        interpolation_rate: float = 10,
    ) -> Optional[float]:

        timer = Timer()

        # Pre allocate the array
        try:
            voltages = read_voltages(
                frequency,
                Fs,
                number_of_samples,
                ch_input=ch_input,
                max_voltage=max_voltage,
                min_voltage=min_voltage,
            )

            if save_file:
                with open(save_file.absolute().resolve(), "w", encoding="utf-8") as f:
                    f.write("# frequency: {}\n".format(round(frequency, 5)))
                    f.write("# Fs: {}\n".format(round(Fs, 5)))
                    pd.DataFrame(voltages).to_csv(
                        f,
                        header=["voltage"],
                        index=None,
                    )

            x_interpolated, y_interpolated = interpolation_model(
                range(0, len(voltages)),
                voltages,
                int(len(voltages) * interpolation_rate),
                kind=INTERPOLATION_KIND.CUBIC,
            )

            if trim:
                voltages = find_sin_zero_offset(y_interpolated)

            rms: Optional[float] = None

            if time_report:
                timer.start("[yellow]RMS Calculation Execution time[/]")

            if rms_mode == RMS_MODE.FFT:
                rms = RMS.fft(voltages)
            elif rms_mode == RMS_MODE.AVERAGE:
                rms = RMS.average(voltages)
            elif rms_mode == RMS_MODE.INTEGRATE:
                rms = RMS.integration(voltages, Fs)

            if time_report:
                timer.stop().print()

            return rms
        except Exception as e:
            console.log(e)

    @staticmethod
    def average(voltages: List[float]) -> float:
        """Calculate the RMS Voltage value from the sampling average

        Args:
            voltages (List[float]): The sampling voltages list
            number_of_samples (int): The number of sampling

        Returns:
            float: The RMS Voltage
        """
        average: float = 0

        n_samp = len(voltages)

        for v in voltages:
            average += abs(v) / n_samp

        return average * 1.111

    @staticmethod
    def fft(voltages) -> float:
        """Calculate the RMS Voltage value with the Fast Fourier Transform
        of the voltage sampling list

        Args:
            voltages (List[float]): The sampling voltages list
            number_of_samples (int): The number of sampling

        Returns:
            float: The RMS Voltage
        """
        n_samp = len(voltages)
        voltages_fft = fft(voltages, n_samp, workers=-1)

        summation = np.sum([np.float_power(np.absolute(v), 2) for v in voltages_fft])
        rms: float = np.sqrt(summation) / n_samp

        return rms

    @staticmethod
    def integration(voltages: List[float], Fs: float) -> float:
        """Calculate the RMS Voltage value with the Integration Technic

        Args:
            voltages (List[float]): The sampling voltages list
            number_of_samples (int): The number of sampling

        Returns:
            float: The RMS Voltage
        """
        return integrate(voltages, 1 / Fs) / (len(voltages) / Fs)
