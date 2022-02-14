

from math import log10


class LogaritmicScale():
    min_Hz: float
    max_Hz: float

    min_index: float
    max_index: float

    points_per_decade: float
    step: float

    step_max: float
    step_min: float
    step_total: float

    step_curr: float
    step_curr_Hz: float

    frequency: float

    def __init__(self,
                 min_Hz: float, max_Hz: float,
                 step: float, points_per_decade: float
                 ) -> None:

        self.min_index = log10(min_Hz)
        self.max_index = log10(max_Hz)

        self.points_per_decade = points_per_decade
        self.step = step

        self.step_max = self.points_per_decade * self.max_index
        self.step_min = self.points_per_decade * self.min_index
        self.step_total = self.step_max - self.step_min

        self.step_curr = 0
        self.step_curr_Hz = 0

        frequency = pow(10, self.step_curr_Hz)

    def check(self) -> bool:
        return self.step_curr < self.step_total + 1

    def get_frequency(self) -> float:
        return self.frequency

    def next(self):
        self.step_curr_Hz = self.min_index + self.step_curr * self.step
        self.frequency = pow(10, self.step_curr_Hz)
        self.step_curr += 1
