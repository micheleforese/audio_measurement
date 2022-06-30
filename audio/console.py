from rich import pretty, traceback
from rich.console import Console
from rich.theme import Theme

pretty.install()
traceback.install(show_locals=True)

custom_theme = Theme(
    {
        "info": "dim cyan",
        "warning": "magenta",
        "error": "bold red",
    }
)


console = Console(theme=custom_theme, force_terminal=True)
