import enum

import numpy as np
from scipy.interpolate import interp1d


class INTERPOLATION_KIND(enum.Enum):
    LINEAR = "linear"
    NEAREST = "nearest"
    ZERO = "zero"
    SLINEAR = "slinear"
    QUADRATIC = "quadratic"
    CUBIC = "cubic"
    PREVIUS = "previous"
    NEXT = "next"


def interpolation_model(
    xx: list[float],
    yy: list[float],
    interpolation_rate: int,
    kind: INTERPOLATION_KIND = INTERPOLATION_KIND.LINEAR,
):

    intrp_model = interp1d(xx, yy, kind=kind.value)

    x_interpolated = np.linspace(
        min(xx),
        max(xx),
        interpolation_rate,
    )

    y_interpolated: np.ndarray = intrp_model(x_interpolated)

    return x_interpolated, y_interpolated


def logx_interpolation_model(
    x_log: list[float],
    yy: list[float],
    interpolation_rate: int,
    kind: INTERPOLATION_KIND = INTERPOLATION_KIND.LINEAR,
) -> tuple[list[float], list[float]]:
    x_log = [np.log10(x) for x in x_log]

    intrp_model = interp1d(x_log, yy, kind=kind.value)

    x_log_interpolated = np.linspace(
        min(x_log),
        max(x_log),
        interpolation_rate,
    )

    x_interpolated = [np.float_power(10, x_intrp) for x_intrp in x_log_interpolated]

    y_interpolated = intrp_model(x_log_interpolated)

    return x_interpolated, y_interpolated


def logx_interpolation_model_Bspline(
    x_log: list[float],
    yy: list[float],
    interpolation_rate: int,
    lam: float,
) -> tuple[list[float], list[float]]:
    x_log = [np.log10(x) for x in x_log]

    from scipy.interpolate import make_smoothing_spline

    intrp_model = make_smoothing_spline(x_log, yy, lam=lam)

    x_log_interpolated = np.linspace(
        min(x_log),
        max(x_log),
        int(len(x_log) * interpolation_rate),
    )

    y_interpolated = intrp_model(x_log_interpolated)
    x_interpolated = [np.float_power(10, x_intrp) for x_intrp in x_log_interpolated]

    return x_interpolated, y_interpolated
