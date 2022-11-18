from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
)

from audio.console import console


progress_list_task = Progress(
    SpinnerColumn(),
    "•",
    TextColumn(
        "[bold blue]{task.description}[/] - [bold green]{task.fields[task]}[/]",
    ),
    transient=True,
)
