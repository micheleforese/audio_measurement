import math

import numpy as np


def unit_normalization(value: float) -> int:
    return int(value / abs(value))


def sinc(x: float):
    return math.sin(math.pi * x) / (math.pi * x)


def decimal_decompose(x) -> tuple[float, int]:
    exponent = int(math.floor(np.log10(abs(x)))) if x != 0 else 0
    mantissa = float(x / 10**exponent)
    return mantissa, exponent


def trim_sin_zero_offset(
    sample: list[float],
) -> tuple[list[float], int, int] | None:

    zero_index_intersections: list[tuple[float, float]] = []

    index_start: int = 0
    index_end: int = len(sample)

    # From start to end
    for n in range(1, len(sample)):
        samp_curr_index = n
        samp_prev_index = n - 1
        samp_curr = sample[samp_curr_index]
        samp_prev = sample[samp_prev_index]

        slope_normalized: float = (samp_prev * samp_curr) / np.abs(
            samp_prev * samp_curr
        )

        if slope_normalized < 0:
            zero_index_intersections.append((samp_prev_index, samp_curr_index))

    if len(zero_index_intersections) >= 3:
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
                < sample[zero_intersection_start_second]
            )
            else zero_intersection_start_second
        )

        index_end = (
            zero_intersection_end_first
            if np.abs(
                sample[zero_intersection_end_first]
                < sample[zero_intersection_end_second]
            )
            else zero_intersection_end_second
        )

        return sample[index_start:index_end], index_start, index_end
    else:
        return None


def rms_full_cycle(sample: list[float]) -> list[float]:
    from audio.math.rms import RMS

    rms_fft_cycle_list: list[float] = []

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


def integrate(y_values: list[float], delta) -> float:

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


def dBV(V_in: float, V_out: float) -> float:
    """Returns the dBV value.

    Args:
        V_in (float): Voltage Input
        V_out (float): Voltage Output

    Returns:
        float: dBV value.
    """
    return 20 * math.log10(V_out / V_in)
