import time
from datetime import timedelta
from typing import Optional

from rich.panel import Panel

from cDAQ.console import console


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
    _message: Optional[str] = None
    _defalt_message: str = "Elapsed time"

    def __init__(self, message: Optional[str] = None):
        self._message = message

    def start(self, message: Optional[str] = None):
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError("Timer is running. Use .stop() to stop it")

        if message is not None:
            self._message = message

        self._start_time = time.perf_counter()

    def stop(self) -> Timer_Message:
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError("Timer is not running. Use start() to start it")

        message = self._message
        elapsed_time: timedelta = timedelta(
            seconds=time.perf_counter() - self._start_time
        )

        self._start_time = None
        self._message = ""
        return Timer_Message(elapsed_time, message)
