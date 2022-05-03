import pathlib
from turtle import clear
from typing import List, Optional
import pandas as pd

from rich.console import RenderableType
from rich.panel import Panel
from rich.syntax import Syntax
from rich.traceback import Traceback
from rich.text import Text
from rich.table import Table
from rich.markdown import Markdown

import subprocess
from typing import Any, Callable, ClassVar, Type, TypeVar


import tkinter as tk


class GuiAudioMeasurements:
    window: tk.Tk

    def __init__(self, home: pathlib.Path) -> None:
        self.window = tk.Tk()

        frame1 = tk.Frame(master=self.window, width=200, height=100, bg="red")
        frame1.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        frame2 = tk.Frame(master=self.window, width=100, bg="yellow")
        frame2.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        frame3 = tk.Frame(master=self.window, width=50, bg="blue")
        frame3.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        label = tk.Label(text="{}".format(home))

    def run(self):
        self.window.mainloop()
