from typing import Self

import numpy as np


class LogarithmicScale:
    min_hertz: float
    max_hertz: float

    min_index: float
    max_index: float

    points_per_decade: float

    f_log_list: list[float] = []
    f_list: list[float] = []

    def __init__(
        self: Self,
        min_hertz: float,
        max_hertz: float,
        points_per_decade: float,
    ) -> None:
        self.min_hertz = min_hertz
        self.max_hertz = max_hertz

        self.min_index = np.log10(self.min_hertz)
        self.max_index = np.log10(self.max_hertz)

        self.points_per_decade = points_per_decade

        m_step_tot: int = (
            int((self.max_index - self.min_index) * self.points_per_decade) + 1
        )

        self.f_log_list = list(
            np.linspace(self.min_index, self.max_index, num=m_step_tot, endpoint=True),
        )

        self.f_list = [np.float_power(10, f) for f in self.f_log_list]

        self.f_list = [np.float_power(10, f) for f in self.f_log_list]
