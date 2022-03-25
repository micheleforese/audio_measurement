from math import log10
from typing import List

import numpy as np


class LogaritmicScale:
    min_Hz: float
    max_Hz: float

    min_index: float
    max_index: float

    points_per_decade: float

    f_log_list: List[float] = []
    f_list: List[float] = []

    def __init__(self, min_Hz: float, max_Hz: float, points_per_decade: float) -> None:
        self.min_Hz = min_Hz
        self.max_Hz = max_Hz

        self.min_index = log10(self.min_Hz)
        self.max_index = log10(self.max_Hz)

        self.points_per_decade = points_per_decade

        m_step_tot: int = (
            int((self.max_index - self.min_index) * self.points_per_decade) + 1
        )

        self.f_log_list = list(
            np.linspace(self.min_index, self.max_index, num=m_step_tot, endpoint=True)
        )

        self.f_list = [np.math.pow(10, f) for f in self.f_log_list]
