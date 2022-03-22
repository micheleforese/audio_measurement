from logging import PlaceHolder
import subprocess, os, platform
import pathlib
import sys
from tkinter import Place
from typing import List, Optional
import pandas as pd
from pytest import Mark

from rich.console import RenderableType
from rich.panel import Panel
from rich.syntax import Syntax
from rich.traceback import Traceback
from rich.text import Text
from rich.table import Table
from rich.markdown import Markdown
from textual.app import App
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import (
    DirectoryTree,
    FileClick,
    Footer,
    Header,
    Placeholder,
    ScrollView,
)
import subprocess
from typing import Any, Callable, ClassVar, Type, TypeVar
from textual.driver import Driver


class Hover(Widget):

    mouse_over = Reactive(False)

    def render(self) -> Panel:
        return Panel("Hello [b]World[/b]", style=("on red" if self.mouse_over else ""))

    def on_enter(self) -> None:
        self.mouse_over = True

    def on_leave(self) -> None:
        self.mouse_over = False


class AudioMeasurementsApp(App):
    def __init__(
        self,
        home: pathlib.Path,
        screen: bool = True,
        driver_class: Optional[Type[Driver]] = None,
        log: str = "",
        log_verbosity: int = 1,
        title: str = "Textual Application",
    ):
        super().__init__(screen, driver_class, log, log_verbosity, title)
        self.home = home

    async def on_load(self) -> None:
        """Sent before going in to application mode."""

        # Bind our basic keys
        await self.bind("b", "view.toggle('sidebar')", "Toggle File Viewer")
        await self.bind("q", "quit", "Quit")

        self.body = ScrollView()
        self.bottom = ScrollView()
        self.directory_tree = DirectoryTree(
            self.home.as_posix(),
            name="Ah boh",
        )

        # Get path to show
        # self.path = os.path.abspath(os.path.join(os.path.basename(__file__), "../../"))

    async def on_mount(self) -> None:
        hovers = (Hover() for _ in range(20))
        # self.directory = DirectoryTree(self.path, "Code")

        # await self.view.dock(ScrollView(self.directory), edge="left", size=40)
        await self.view.dock(Header(), edge="top")
        await self.view.dock(Footer(), edge="bottom")
        await self.view.dock(
            ScrollView(
                DirectoryTree(
                    os.path.abspath(os.path.join(os.path.basename(__file__), "../")),
                    name="Ah boh",
                )
            ),
            # PlaceHolder(),
            edge="left",
            size=52,
            name="sidebar",
        )
        await self.view.dock(self.body, edge="top")

    async def handle_file_click(self, message: FileClick) -> None:
        """A message sent by the directory tree when a file is clicked."""

        path = pathlib.Path(message.path)

        if os.path.isfile(path):

            if path.suffix == ".csv":
                csv_file = pd.read_csv(path)

                csv_table = Table(show_lines=True)
                csv_table.add_column(header="ID", justify="right")

                for col in list(csv_file.columns.values.tolist()):
                    csv_table.add_column(header=str(col))

                for key, value in csv_file.iterrows():
                    data: List[str] = []

                    data.append("{}".format(key))

                    for v in value:
                        data.append("{}".format(v))

                    csv_table.add_row(*data)

                await self.body.update(csv_table)
            elif path.suffix == ".md":
                with open(path).read() as md:
                    markdown = Markdown(md)
                    self.app.sub_title = path
                    await self.body.update(markdown)
            elif path.suffix == ".png":
                if platform.system() == "Windows":
                    os.startfile(path.absolute())
                else:
                    subprocess.run(["open", path.absolute()], check=True)
            else:
                syntax: RenderableType
                try:
                    # Construct a Syntax object for the path in the message
                    syntax = Syntax.from_path(
                        message.path,
                        line_numbers=True,
                        word_wrap=True,
                        indent_guides=True,
                        theme="monokai",
                        # lexer="python" if pathlib.Path(message.path).suffix == ".py" else None,
                    )
                    self.app.sub_title = pathlib.Path(message.path)

                except Exception:
                    # Possibly a binary file
                    # For demonstration purposes we will show the traceback
                    syntax = Traceback(theme="monokai", width=None, show_locals=True)
                    self.app.sub_title = "Traceback"
                await self.body.update(syntax)
