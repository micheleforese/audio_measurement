import math

import numpy as np


def unit_normalization(value: float) -> int:
    return int(value / abs(value))


def sinc(x: float) -> float:
    return math.sin(math.pi * x) / (math.pi * x)


def decimal_decompose(x: float) -> tuple[float, int]:
    exponent: int = int(math.floor(np.log10(abs(x)))) if x != 0 else 0
    mantissa: float = float(x / 10**exponent)
    return mantissa, exponent


def trim_sin_zero_offset(
    sample: list[float],
) -> tuple[list[float], int, int] | None:
    min_intersections = 3

    zero_index_intersections: list[tuple[float, float]] = []

    index_start: int = 0
    index_end: int = len(sample)

    # From start to end
    for n in range(1, len(sample)):
        samp_curr_index: int = n
        samp_prev_index: int = n - 1
        samp_curr: float = sample[samp_curr_index]
        samp_prev: float = sample[samp_prev_index]

        slope_normalized: float = (samp_prev * samp_curr) / np.abs(
            samp_prev * samp_curr,
        )

        if slope_normalized < 0:
            zero_index_intersections.append((samp_prev_index, samp_curr_index))

    if len(zero_index_intersections) >= min_intersections:
        (
            zero_intersection_start_first,
            zero_intersection_start_second,
        ) = zero_index_intersections[0]

        if (len(zero_index_intersections) % 2) == 0:
            (
                zero_intersection_end_first,
                zero_intersection_end_second,
            ) = zero_index_intersections[-2]

        else:
            (
                zero_intersection_end_first,
                zero_intersection_end_second,
            ) = zero_index_intersections[-1]

        index_start = (
            zero_intersection_start_first
            if np.abs(
                sample[zero_intersection_start_first]
                < sample[zero_intersection_start_second],
            )
            else zero_intersection_start_second
        )

        index_end = (
            zero_intersection_end_first
            if np.abs(
                sample[zero_intersection_end_first]
                < sample[zero_intersection_end_second],
            )
            else zero_intersection_end_second
        )

        return sample[index_start:index_end], index_start, index_end

    return None


def rms_full_cycle(sample: list[float]) -> list[float]:
    from audio.math.rms import RMS

    rms_fft_cycle_list: list[float] = []

    start_slope: float = sample[1] - sample[0]
    last_slope = 0

    # From start to end
    for n in range(2, len(sample)):
        samp_curr_index: int = n
        samp_prev_index: int = n - 1
        samp_curr: float = sample[samp_curr_index]
        samp_prev: float = sample[samp_prev_index]

        slope: float = samp_curr - samp_prev

        norm: float = (samp_prev * samp_curr) / np.abs(samp_prev * samp_curr)

        if norm < 0 and start_slope * slope > 0:
            last_slope: float = slope
            index: int = (
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


def integrate(y_values: list[float], delta: float) -> float:
    volume: float = 0.0

    for idx, y in enumerate(y_values):
        # If it's the last element then exit the loop
        if idx + 1 == len(y_values):
            break

        y_plus: float = y_values[idx + 1]

        # Make the calculations
        if y * y_plus < 0:
            r_rec: float = abs(y) * delta / 4
            l_rec: float = abs(y_plus) * delta / 4
            volume += r_rec + l_rec
        else:
            r_rec: float = abs(y) * delta
            l_rec: float = abs(y_plus) * delta
            triangle: float = abs(r_rec - l_rec) / 2

            volume += min([r_rec, l_rec]) + triangle

    return volume


def calculate_voltage_decibel(input_voltage: float, output_voltage: float) -> float:
    """Returns the dBV value.

    Args:
        V_in (float): Voltage Input
        V_out (float): Voltage Output

    Returns:
        float: dBV value.
    """
    return 20 * math.log10(output_voltage / input_voltage)
