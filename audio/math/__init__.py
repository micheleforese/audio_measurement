import math
from typing import List, Optional, Tuple

import numpy as np


def unit_normalization(value: float) -> int:
    return int(value / abs(value))


def sinc(x: float):
    return math.sin(math.pi * x) / (math.pi * x)


def decimal_decompose(x) -> Tuple[float, int]:
    exponent = int(math.floor(np.log10(abs(x)))) if x != 0 else 0
    mantissa = float(x / 10**exponent)
    return mantissa, exponent


def find_sin_zero_offset(sample: List[float]) -> Tuple[List[float], int, int]:
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
            return sample[index_start:index_end], index_start, index_end
        else:
            return []
    else:
        return []


def rms_full_cycle(sample: List[float]) -> List[float]:
    from audio.math.rms import RMS

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


def percentage_error(exact: float, approx: float) -> float:
    return (approx - exact) / exact


def transfer_function(rms: float, input_rms: float) -> float:
    return 20 * np.log10(rms / input_rms)


def integrate(y_values: List[float], delta) -> float:

    volume: float = 0.0

    for idx, y in enumerate(y_values):
        # If it's the last element then exit the loop
        if idx + 1 == len(y_values):
            break
        else:
            y_plus = y_values[idx + 1]

            # Make the calculations
            if y * y_plus < 0:
                r_rec: float = abs(y) * delta / 4
                l_rec: float = abs(y_plus) * delta / 4
                volume += r_rec + l_rec
                # console.print("Volume: {}".format(round(volume, 9)))
            else:
                r_rec: float = abs(y) * delta
                l_rec: float = abs(y_plus) * delta
                triangle: float = abs(r_rec - l_rec) / 2

                volume += min([r_rec, l_rec]) + triangle

                # console.print("Volume: {}".format(round(volume, 9)))

    return volume
