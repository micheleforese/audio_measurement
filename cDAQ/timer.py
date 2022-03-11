from email import message
import time
from datetime import timedelta
from typing import Optional

from rich.console import Console
from rich.panel import Panel

console = Console()


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""


class Timer_Message:
    elapsed_time: timedelta
    message: str

    def __init__(self, elapsed_time, message):
        self.elapsed_time = elapsed_time
        self.message = message

    def print(self):
        console.print(
            Panel(
                "[green]{}[/green]: [blue]{}[/blue]".format(
                    self.message, self.elapsed_time
                )
            )
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
            raise TimerError(f"Timer is running. Use .stop() to stop it")

        if message is not None:
            self._message = message

        self._start_time = time.perf_counter()

    def stop(self) -> Timer_Message:
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError(f"Timer is not running. Use start() to start it")

        message = self._message
        elapsed_time: timedelta = timedelta(
            seconds=time.perf_counter() - self._start_time
        )

        self._start_time = None
        self._message = ""
        return Timer_Message(elapsed_time, message)
