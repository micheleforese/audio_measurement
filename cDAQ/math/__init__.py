import enum
import math
from typing import Callable, List, Optional, Tuple

import numpy as np
from scipy.interpolate import interp1d


def unit_normalization(value: float) -> int:
    return int(value / abs(value))


def sinc(x: float):
    return math.sin(math.pi * x) / (math.pi * x)


class INTERPOLATION_KIND(enum.Enum):
    LINEAR = "linear"
    NEAREST = "nearest"
    ZERO = "zero"
    SLINEAR = "slinear"
    QUDRATIC = "quadratic"
    CUBIC = "cubic"
    PREVIUS = "previous"
    NEXT = "next"


def interpolation_model(
    xx: List[float],
    yy: List[float],
    interpolation_rate: int,
    kind: INTERPOLATION_KIND = INTERPOLATION_KIND.LINEAR,
):

    interpolation_model = interp1d(xx, yy, kind=kind.value)

    x_interpolated = np.linspace(
        min(xx),
        max(xx),
        interpolation_rate,
    )

    y_interpolated = interpolation_model(x_interpolated)

    return x_interpolated, y_interpolated


def logx_interpolation_model(
    x_log: List[float],
    yy: List[float],
    interpolation_rate: int,
    kind: INTERPOLATION_KIND = INTERPOLATION_KIND.LINEAR,
) -> Tuple[List[float], List[float]]:
    x_log = [np.log10(x) for x in x_log]

    interpolation_model = interp1d(x_log, yy, kind=kind.value)

    x_log_interpolated = np.linspace(
        min(x_log),
        max(x_log),
        interpolation_rate,
    )

    x_interpolated = [np.float_power(10, x_intrp) for x_intrp in x_log_interpolated]

    y_interpolated = interpolation_model(x_log_interpolated)

    return x_interpolated, y_interpolated


def decimal_decompose(x) -> Tuple[float, int]:
    exponent = int(math.floor(np.log10(abs(x)))) if x != 0 else 0
    mantissa = float(x / 10**exponent)
    return mantissa, exponent


from cDAQ.console import console


def find_sin_zero_offset(sample: List[float]) -> List[float]:
    # console.print(f"[Sample] - N: {len(sample)}")

    found: bool = False
    start_found: bool = False
    end_found: bool = False

    index_start: int = 0
    index_end: int = len(sample)

    start_cycle_slope: Optional[float] = 0
    end_cycle_slope: Optional[float] = 0

    # From start to end
    for n in range(1, len(sample)):
        samp_curr_index = n
        samp_prev_index = n - 1
        samp_curr = sample[samp_curr_index]
        samp_prev = sample[samp_prev_index]
        slope = samp_curr - samp_prev

        norm: float = (samp_prev * samp_curr) / np.abs(samp_prev * samp_curr)

        if norm < 0:
            start_cycle_slope = slope
            index_start = (
                samp_curr_index
                if np.abs(samp_curr) < np.abs(samp_prev)
                else samp_prev_index
            )
            # console.print(f"[Sample] - Index Start: {index_start}")

            start_found = True
            break

    if not start_found:
        return []

    # From end to start
    # len - 2 = index(-2) of array
    for n in range(len(sample) - 2, -1, -1):
        samp_curr_index = n
        samp_prev_index = n + 1
        samp_curr = sample[samp_curr_index]
        samp_prev = sample[samp_prev_index]
        slope = samp_curr - samp_prev

        norm: float = (samp_prev * samp_curr) / np.abs(samp_prev * samp_curr)

        if norm < 0:
            end_cycle_slope = slope

            if start_cycle_slope * end_cycle_slope < 0:
                index_end = (
                    samp_curr_index
                    if np.abs(samp_curr) < np.abs(samp_prev)
                    else samp_prev_index
                )
                # console.print(f"[Sample] - Index End: {index_end}")
                end_found = True
                found = True
                break
            else:
                continue

    if not end_found:
        return []

    if found:
        # console.print(f"[Sample] - Index: {index_start:4} - {index_end:4}")

        if index_end - index_start > 1:
            return sample[index_start:index_end]
        else:
            return []
    else:
        return []


def rms_full_cycle(sample: List[float]) -> List[float]:
    from cDAQ.utility import RMS

    rms_fft_cycle_list: List[float] = []

    start_slope = sample[1] - sample[0]
    last_slope = 0

    # From start to end
    for n in range(2, len(sample)):
        samp_curr_index = n
        samp_prev_index = n - 1
        samp_curr = sample[samp_curr_index]
        samp_prev = sample[samp_prev_index]

        slope = samp_curr - samp_prev

        norm: float = (samp_prev * samp_curr) / np.abs(samp_prev * samp_curr)

        if norm < 0 and start_slope * slope > 0:
            last_slope = slope
            index = (
                samp_curr_index
                if np.abs(samp_curr) < np.abs(samp_prev)
                else samp_prev_index
            )
            rms_fft_cycle_list.append(RMS.fft(sample[0:index]))

    if start_slope * last_slope < -1:
        rms_fft_cycle_list.append(RMS.fft(sample))

    return rms_fft_cycle_list
