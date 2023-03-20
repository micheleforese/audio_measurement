import logging

from rich import pretty, traceback
from rich.console import Console
from rich.theme import Theme

from audio.constant import APP_HOME

pretty.install()
traceback.install(show_locals=True)

custom_theme = Theme(
    {
        "info": "dim cyan",
        "warning": "magenta",
        "error": "bold red",
    },
)


console = Console(theme=custom_theme, force_terminal=True)

FORMAT = "%(message)s"
LOG_FILE_PATH = APP_HOME / "logging/app.log"


logging.basicConfig(
    level="NOTSET",
    format=FORMAT,
    datefmt="[%X]",
    stream=LOG_FILE_PATH.open(mode="a"),
    #     RichHandler(
    # ],
)

log = logging.getLogger()
