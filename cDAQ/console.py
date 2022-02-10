from os import curdir
from xml.dom.expatbuilder import theDOMImplementation
from rich.console import Console
from rich import pretty
from rich.traceback import install
from rich.theme import Theme

pretty.install()
install(show_locals=True)

custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "error": "bold red",
})


console = Console(theme=custom_theme)
