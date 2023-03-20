from __future__ import annotations

import signal
from typing import Any


class InterruptHandler:
    sig: signal.Signals

    original_handles: Any
    released: bool
    interrupted: bool

    def __init__(self) -> None:
        self.sig = signal.SIGINT

    def __enter__(self):
        self.interrupted = False
        self.released = False
        self.original_handles = signal.getsignal(self.sig)

        signal.signal(self.sig, self._handler)

        return self

    def __exit__(self, type, value, tb):
        self.release()

    def _handler(self, signum, frame):
        self.release()
        self.interrupted = True

    def release(self):
        if self.released:
            return False

        signal.signal(self.sig, self.original_handles)
        self.released = True
        return True
