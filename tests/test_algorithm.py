import numpy as np

from audio.math.algorithm import LogarithmicScale
from audio.console import console
from rich import inspect


def test_algorithm():

    log_scale: LogarithmicScale = LogarithmicScale(10, 1000, 10)
    console.print(inspect(log_scale))
    log_scale: LogarithmicScale = LogarithmicScale(20, 1000, 10)
    console.print(inspect(log_scale))
    log_scale: LogarithmicScale = LogarithmicScale(20, 1030, 10)
    console.print(inspect(log_scale))
    log_scale: LogarithmicScale = LogarithmicScale(
        np.float_power(10, 1), np.float_power(10, 3), 10
    )
    console.print(inspect(log_scale))
    log_scale: LogarithmicScale = LogarithmicScale(
        np.float_power(10, 1), np.float_power(10, 3.04), 20
    )
    console.print(inspect(log_scale))
