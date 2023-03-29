import time
from datetime import timedelta
from typing import Self


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""


class TimerAlreadyStartedError(TimerError):
    """Timer already started."""


class TimerNotStartedError(TimerError):
    """Timer didn't start."""


class Timer:
    _start_time = None
    _last_lap = None

    def start(self: Self) -> float:
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerAlreadyStartedError

        self._start_time = time.perf_counter()
        self._last_lap = self._start_time
        return self._start_time

    def stop(self: Self) -> timedelta:
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerNotStartedError

        elapsed_time: timedelta = timedelta(
            seconds=time.perf_counter() - self._start_time,
        )

        self._start_time = None
        return elapsed_time

    def lap(self: Self) -> timedelta:
        current_time: float = time.perf_counter()
        if self._last_lap is None:
            raise TimerNotStartedError
        diff: float = current_time - self._last_lap
        self._last_lap = current_time
        return timedelta(seconds=diff)
