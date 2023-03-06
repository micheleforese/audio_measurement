import functools
import time
from datetime import timedelta
from typing import Optional

from rich.panel import Panel

from audio.console import console


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""


class Timer_Message:
    elapsed_time: timedelta
    message: str

    def __init__(self, elapsed_time, message):
        self.elapsed_time = elapsed_time
        self.message = message

    def __repr__(self) -> str:
        return f"[green]{self.message}[/green]: [blue]{self.elapsed_time}[/blue]"

    def print(self):
        console.print(
            Panel(f"[green]{self.message}[/green]: [blue]{self.elapsed_time}[/blue]")
        )


class Timer:
    _start_time = None
    _last_lap = None

    def start(self):
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError("Timer is running. Use .stop() to stop it")

        self._start_time = time.perf_counter()
        self._last_lap = self._start_time
        return self._start_time

    def stop(self):
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError("Timer is not running. Use start() to start it")

        elapsed_time: timedelta = timedelta(
            seconds=time.perf_counter() - self._start_time
        )

        self._start_time = None
        return elapsed_time

    def lap(self):
        current_time = time.perf_counter()
        diff = current_time - self._last_lap
        self._last_lap = current_time
        return timedelta(seconds=diff)
