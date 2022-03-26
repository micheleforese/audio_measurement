import enum
import math
from typing import Callable, List, Tuple

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

    return tuple(x_interpolated, y_interpolated)
