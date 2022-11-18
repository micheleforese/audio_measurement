import enum
import pathlib
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.fft import fft

from audio.console import console
from audio.math import integrate, trim_sin_zero_offset
from audio.math.interpolation import INTERPOLATION_KIND, interpolation_model
from audio.utility import read_voltages
from audio.utility.timer import Timer
from audio.model.sampling import VoltageSampling


class RMS_MODE(enum.Enum):
    FFT = 1
    AVERAGE = 2
    INTEGRATE = 3


class RMS:
    @staticmethod
    def rms(
        Fs: float,
        number_of_samples: int,
        ch_input: str,
        max_voltage: float,
        min_voltage: float,
        rms_mode: RMS_MODE = RMS_MODE.FFT,
        time_report: bool = False,
        save_file: Optional[pathlib.Path] = None,
        trim: bool = True,
        frequency: Optional[float] = None,
        interpolation_rate: float = 10,
    ) -> Tuple[List[float], Optional[float]]:
        """It calculates the RMS Value from the nidaq input

        Args:
            Fs (float): Sampling Frequency
            number_of_samples (int): Number of Samples per measure
            ch_input (str): Input channel for the NiDaq Chassis
            max_voltage (float): Max Voltage Input for the NiDaq Module
            min_voltage (float): Min Voltage Input for the NiDaq Module
            rms_mode (RMS_MODE, optional): Mode for calculating the RMS Value. Defaults to RMS_MODE.FFT.
            time_report (bool, optional): Gives time report on the measure. Defaults to False.
            save_file (Optional[pathlib.Path], optional): Saves the Measurements file. Defaults to None.
            trim (bool, optional): Trims the value to obtain full cycle sine waves. Defaults to True.
            frequency (Optional[float], optional): Input Frequency for max Fs check. Defaults to None.
            interpolation_rate (float, optional): Interpolation rate to reconstruct the sine wave. Defaults to 10.

        Returns:
            Tuple[List[float], Optional[float]]: Returns the list of voltages and the rms value.
        """

        timer = Timer()

        # Pre allocate the array
        voltages = read_voltages(
            sampling_frequency=Fs,
            number_of_samples=number_of_samples,
            input_channel=ch_input,
            max_voltage=max_voltage,
            min_voltage=min_voltage,
            input_frequency=frequency,
        )

        if len(voltages) != number_of_samples:
            console.log(
                f"Lenght of voltages is {len(voltages)} instead of {number_of_samples}"
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

        _, y_interpolated = interpolation_model(
            range(0, len(voltages)),
            voltages,
            int(len(voltages) * interpolation_rate),
            kind=INTERPOLATION_KIND.CUBIC,
        )

        if trim:
            trim_response = trim_sin_zero_offset(y_interpolated)

            if trim_response is not None:
                voltages_trimmed, _, _ = trim_response

                if len(voltages_trimmed) > 0:
                    voltages = voltages_trimmed
                else:
                    console.log("trim ERROR - len(voltages_trimmed) < 0")

            else:
                console.log("trim ERROR")

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

        return voltages, rms

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

    @staticmethod
    def rms_v2(
        voltages_sampling: VoltageSampling,
        rms_mode: RMS_MODE = RMS_MODE.FFT,
        time_report: bool = False,
        trim: bool = True,
        interpolation_rate: float = 10,
    ):
        timer = Timer()

        voltages = list(voltages_sampling.voltages)

        _, y_interpolated = interpolation_model(
            range(0, len(voltages)),
            voltages,
            int(len(voltages) * interpolation_rate),
            kind=INTERPOLATION_KIND.CUBIC,
        )

        voltages = y_interpolated

        if trim:
            trim_response = trim_sin_zero_offset(y_interpolated)

            if trim_response is not None:
                voltages_trimmed, _, _ = trim_response

                if len(voltages_trimmed) > 0:
                    voltages = voltages_trimmed
                else:
                    console.log("trim ERROR - len(voltages_trimmed) < 0")

            else:
                console.log("trim ERROR")

        rms: Optional[float] = None

        if time_report:
            timer.start("[yellow]RMS Calculation Execution time[/]")

        if rms_mode == RMS_MODE.FFT:
            rms = RMS.fft(voltages)
        elif rms_mode == RMS_MODE.AVERAGE:
            rms = RMS.average(voltages)
        elif rms_mode == RMS_MODE.INTEGRATE:
            rms = RMS.integration(voltages, voltages_sampling.sampling_frequency)

        if time_report:
            timer.stop().print()

        return voltages, rms
