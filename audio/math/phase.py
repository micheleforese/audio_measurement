import math

from audio.console import console
from audio.model.sampling import VoltageSampling, VoltageSamplingV2


def phase_offset(
    voltage_sampling_0: VoltageSampling,
    voltage_sampling_1: VoltageSampling,
):
    delta_list: list[float] = []
    for voltage_0, voltage_1 in zip(
        voltage_sampling_0.voltages, voltage_sampling_1.voltages
    ):
        delta = delta_points(
            voltage_0,
            voltage_sampling_0.amplitude_peak_to_peak / 2,
            voltage_1,
            voltage_sampling_1.amplitude_peak_to_peak / 2,
        )

        delta_list.append(delta)

    return delta_list


def phase_offset_mean(
    voltage_sampling_0: VoltageSampling,
    voltage_sampling_1: VoltageSampling,
):
    import numpy as np

    return np.mean(phase_offset(voltage_sampling_0, voltage_sampling_1))


def point_to_angle_radiants(voltage: int, amplitude_peak: float):
    return math.asin(voltage / amplitude_peak)


def angle_radiants_to_degrees(angle: float):
    return angle * (180 / math.pi)


def delta_points(
    voltage_0: float,
    amplitude_peak_0: float,
    voltage_1: float,
    amplitude_peak_1: float,
):
    return angle_radiants_to_degrees(
        point_to_angle_radiants(voltage_0, amplitude_peak_0)
        - point_to_angle_radiants(voltage_1, amplitude_peak_1)
    )


def phase_offset_v2(
    voltage_sampling_0: VoltageSampling,
    voltage_sampling_1: VoltageSampling,
    debug: bool = False,
):
    zero_index_0: int | None = None
    zero_index_slope_0: float | None = None
    zero_index_1: int | None = None
    zero_index_slope_1: float | None = None
    begin_index_1: int
    alpha: float | None = None

    sign_phase: float = 1

    volts_0 = voltage_sampling_0.voltages
    volts_1 = voltage_sampling_1.voltages
    # volts_1 = volts_0

    max0: float = max(volts_0)
    min0: float = min(volts_0)
    dcoffset0: float = (max0 + min0) / 2.0

    max1: float = max(volts_1)
    min1: float = min(volts_1)
    dcoffset1: float = (max1 + min1) / 2.0

    diffoffset = dcoffset1 - dcoffset0

    if debug:
        console.log(
            f"F: {voltage_sampling_0.input_frequency:+06.05f}, max0: {max0:+.05f}, max1: {max1:+.05f}, min0: {min0:+.05f}, min1: {min1:+.05f}, dcoffset0: {dcoffset0:+.05f}, dcoffset1: {dcoffset1:+.05f}, diffoffset: {diffoffset:+.07f}"
        )

    volts_0.sub(dcoffset0)
    volts_1.sub(dcoffset1)

    for idx in range(1, len(volts_0)):
        samp_curr_index = idx
        samp_prev_index = idx - 1

        samp_curr = volts_0[samp_curr_index]
        samp_prev = volts_0[samp_prev_index]

        cross: float = samp_prev * samp_curr

        is_cross = cross < 0

        if is_cross:
            zero_index_slope_0 = samp_curr - samp_prev

            if abs(samp_curr) < abs(samp_prev):
                zero_index_0 = samp_curr_index
            else:
                zero_index_0 = samp_prev_index
            begin_index_1 = samp_prev_index

            tx0_0 = samp_prev_index * (1 / voltage_sampling_0.sampling_frequency)
            tx1_0 = samp_curr_index * (1 / voltage_sampling_0.sampling_frequency)
            m0: float = (samp_curr - samp_prev) / (tx1_0 - tx0_0)
            q0: float = samp_prev - m0 * tx0_0
            tx_0: float = -q0 / m0

            break

    if zero_index_0 is None or zero_index_slope_0 is None:
        return None

    for idx in range(max(begin_index_1, 1), len(volts_1)):
        samp_curr_index = idx
        samp_prev_index = idx - 1

        samp_curr = volts_1[samp_curr_index]
        samp_prev = volts_1[samp_prev_index]

        cross: float = samp_prev * samp_curr
        is_cross = cross < 0

        if is_cross:
            slope = samp_curr - samp_prev
            zero_index_slope_1 = slope
            if zero_index_slope_0 * zero_index_slope_1 < 0:
                sign_phase = -1

            # zero_index_1 = (
            #     samp_curr_index if samp_curr - samp_prev < 0 else samp_prev_index
            # )
            if abs(samp_curr) < abs(samp_prev):
                zero_index_1 = samp_curr_index
            else:
                zero_index_1 = samp_prev_index

            tx0_1 = samp_prev_index * (1 / voltage_sampling_1.sampling_frequency)
            tx1_1 = samp_curr_index * (1 / voltage_sampling_1.sampling_frequency)
            m1: float = (samp_curr - samp_prev) / (tx1_1 - tx0_1)
            q1: float = samp_prev - m1 * tx0_1
            tx_1: float = -q1 / m1

            break

    if zero_index_1 is None:
        return None

    time = tx_1 - tx_0
    T = 1 / voltage_sampling_0.input_frequency

    alpha = (time / T) * 360
    if sign_phase < 0:
        alpha -= 180

    return alpha


def phase_offset_v3(
    voltage_sampling_0: VoltageSamplingV2,
    voltage_sampling_1: VoltageSamplingV2,
    debug: bool = False,
):
    zero_index_0: int | None = None
    zero_index_slope_0: float | None = None
    zero_index_1: int | None = None
    zero_index_slope_1: float | None = None
    begin_index_1: int
    alpha: float | None = None

    sign_phase: float = 1

    max0: float = max(voltage_sampling_0.voltages)
    min0: float = min(voltage_sampling_0.voltages)
    dcoffset0: float = (max0 + min0) / 2.0

    max1: float = max(voltage_sampling_1.voltages)
    min1: float = min(voltage_sampling_1.voltages)
    dcoffset1: float = (max1 + min1) / 2.0

    diffoffset = dcoffset1 - dcoffset0

    if debug:
        console.log(
            f"F: {voltage_sampling_0.input_frequency:+06.05f}, max0: {max0:+.05f}, max1: {max1:+.05f}, min0: {min0:+.05f}, min1: {min1:+.05f}, dcoffset0: {dcoffset0:+.05f}, dcoffset1: {dcoffset1:+.05f}, diffoffset: {diffoffset:+.07f}",
        )

    voltage_sampling_0.voltages.sub(dcoffset0)
    voltage_sampling_1.voltages.sub(dcoffset1)

    for idx in range(1, len(voltage_sampling_0.voltages)):
        samp_curr_index = idx
        samp_prev_index = idx - 1

        samp_curr = voltage_sampling_0.voltages[samp_curr_index]
        samp_prev = voltage_sampling_0.voltages[samp_prev_index]

        cross: float = samp_prev * samp_curr

        is_cross = cross < 0

        if is_cross:
            zero_index_slope_0 = samp_curr - samp_prev

            if abs(samp_curr) < abs(samp_prev):
                zero_index_0 = samp_curr_index
            else:
                zero_index_0 = samp_prev_index
            begin_index_1 = samp_prev_index

            tx0_0 = voltage_sampling_0.times[samp_prev_index]
            tx1_0 = voltage_sampling_0.times[samp_curr_index]

            m0: float = (samp_curr - samp_prev) / (tx1_0 - tx0_0)
            q0: float = samp_prev - m0 * tx0_0
            tx_0: float = -q0 / m0

            break

    if zero_index_0 is None or zero_index_slope_0 is None:
        return None

    for idx in range(max(begin_index_1, 1), len(voltage_sampling_1.voltages)):
        samp_curr_index = idx
        samp_prev_index = idx - 1

        samp_curr = voltage_sampling_1.voltages[samp_curr_index]
        samp_prev = voltage_sampling_1.voltages[samp_prev_index]

        cross: float = samp_prev * samp_curr
        is_cross = cross < 0

        if is_cross:
            slope = samp_curr - samp_prev
            zero_index_slope_1 = slope
            if zero_index_slope_0 * zero_index_slope_1 < 0:
                sign_phase = -1

            if abs(samp_curr) < abs(samp_prev):
                zero_index_1 = samp_curr_index
            else:
                zero_index_1 = samp_prev_index

            tx0_1 = voltage_sampling_1.times[samp_prev_index]
            tx1_1 = voltage_sampling_1.times[samp_curr_index]

            m1: float = (samp_curr - samp_prev) / (tx1_1 - tx0_1)
            q1: float = samp_prev - m1 * tx0_1
            tx_1: float = -q1 / m1

            break

    if zero_index_1 is None:
        return None

    time = tx_1 - tx_0
    T = 1 / voltage_sampling_0.input_frequency

    alpha = (time / T) * 360
    if sign_phase < 0:
        alpha -= 180

    return alpha, sign_phase


def phase_offset_v4(
    voltage_sampling_0: VoltageSamplingV2,
    voltage_sampling_1: VoltageSamplingV2,
    debug: bool = False,
):

    global_index: int | None = None
    alpha: float | None = None

    max0: float = max(voltage_sampling_0.voltages)
    min0: float = min(voltage_sampling_0.voltages)
    dcoffset0: float = (max0 + min0) / 2.0

    max1: float = max(voltage_sampling_1.voltages)
    min1: float = min(voltage_sampling_1.voltages)
    dcoffset1: float = (max1 + min1) / 2.0

    diffoffset = dcoffset1 - dcoffset0
    voltage_sampling_0.voltages.sub(dcoffset0)
    voltage_sampling_1.voltages.sub(dcoffset1)

    if debug:
        console.log(
            f"F: {voltage_sampling_0.input_frequency:+06.05f}, max0: {max0:+.05f}, max1: {max1:+.05f}, min0: {min0:+.05f}, min1: {min1:+.05f}, dcoffset0: {dcoffset0:+.05f}, dcoffset1: {dcoffset1:+.05f}, diffoffset: {diffoffset:+.07f}",
        )

    tx_0: float | None = None
    tx_1: float | None = None

    for idx in range(1, len(voltage_sampling_0.voltages)):
        samp_curr_index = idx
        samp_prev_index = idx - 1

        samp_curr = voltage_sampling_0.voltages[samp_curr_index]
        samp_prev = voltage_sampling_0.voltages[samp_prev_index]

        cross: float = samp_curr * samp_prev
        slope: float = samp_curr - samp_prev

        is_cross = cross < 0
        is_positive_slope = slope > 0

        if is_cross and is_positive_slope:
            global_index = samp_curr_index

            tx0_0 = voltage_sampling_0.times[samp_prev_index]
            tx1_0 = voltage_sampling_0.times[samp_curr_index]

            m0: float = (samp_curr - samp_prev) / (tx1_0 - tx0_0)
            q0: float = samp_prev - m0 * tx0_0
            tx_0 = -q0 / m0

            break

    if tx_0 is None:
        return None

    for idx in range(global_index, len(voltage_sampling_1.voltages)):
        samp_curr_index: int = idx
        samp_prev_index: int = idx - 1

        samp_curr: float = voltage_sampling_1.voltages[samp_curr_index]
        samp_prev: float = voltage_sampling_1.voltages[samp_prev_index]

        cross: float = samp_curr * samp_prev
        slope: float = samp_curr - samp_prev

        is_cross: bool = cross < 0
        is_positive_slope: bool = slope > 0

        if is_cross and is_positive_slope:

            tx0_1: float = voltage_sampling_1.times[samp_prev_index]
            tx1_1: float = voltage_sampling_1.times[samp_curr_index]

            m1: float = (samp_curr - samp_prev) / (tx1_1 - tx0_1)
            q1: float = samp_prev - m1 * tx0_1
            tx_1 = -q1 / m1

            break

    if tx_1 is None:
        return None

    delta_time = tx_1 - tx_0
    period_time = 1 / voltage_sampling_0.input_frequency

    return (delta_time / period_time) * 360
