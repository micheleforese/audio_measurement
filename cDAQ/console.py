from rich.console import Console
from rich import pretty
from rich.traceback import install

pretty.install()
install(show_locals=True)
console = Console()
