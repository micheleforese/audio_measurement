import os
import pathlib
from typing import List, Optional

from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from audio.console import console
from audio.docker import Docker_CLI, User, Volume
from audio.docker.utility import exec_command


class Package:

    package_name: str
    config: Optional[List[str]]

    def __init__(self, package_name: str, config: Optional[List[str]] = None) -> None:
        self.package_name = package_name
        self.config = config


def use_package(packages: List[Package]):
    latex_packages: str = ""

    for p in packages:
        latex_packages = "{}{}".format(
            latex_packages,
            "\\usepackage{}{{{}}}\n".format(
                "[{}]".format(",".join(p.config)) if p.config else "", p.package_name
            ),
        )

    return latex_packages


def create_latex_file(
    image_file: pathlib.Path,
    home: pathlib.Path,
    latex_home: pathlib.Path,
    debug: bool = False,
):

    progress_list_task = Progress(
        SpinnerColumn(),
        "•",
        TextColumn(
            "[bold blue]{task.description}[/] - [bold green]{task.fields[task]}[/]",
        ),
        transient=True,
    )

    live_group = Group(Panel(progress_list_task))

    live = Live(
        live_group,
        transient=True,
        console=console,
    )
    live.start()

    task_latex = progress_list_task.add_task("Create Latex pdf", task="Configuration")
    progress_list_task.start_task(task_latex)

    if debug:
        console.print('[PATH - image_file] - "{}"'.format(image_file.absolute()))
        console.print('[PATH - home] - "{}"'.format(home.absolute()))

    latex_packages = use_package(
        [
            Package("tikz"),
            Package("tikz-3dplot"),
            Package("amsmath"),
            Package("mathtools"),
            Package("esdiff", ["thinc"]),
            Package("inputenc", ["utf8"]),
            Package("babel", ["italian"]),
            Package("geometry", ["margin=0in"]),
            Package("textcomp"),
            Package("calc"),
            Package("adjustbox"),
            Package("pgfplots"),
            Package("subfiles"),
            Package("graphicx"),
            Package("url"),
            Package("blindtext"),
            Package("tikzpagenodes"),
        ]
    )

    latex_start = (
        r"\documentclass[a4, landscape]{article}"
        + "\n"
        + latex_packages
        + "\pgfplotsset{compat=1.18}"
        + "\n"
        + r"\begin{document}"
        + "\n"
    )

    latex_end = "\n" + r"\end{document}"

    docker_image_file_path = image_file.name
    if debug:
        console.print(
            '[PATH - docker - image_file] - "{}"'.format(docker_image_file_path)
        )

    latex = (
        "" + "\n" + r"\null" + "\n" + r"\vfill" + "\n"
        r"\begin{figure}[h]"
        + "\centering"
        + r"\includegraphics[width=.9\paperwidth]{"
        + "{}".format(docker_image_file_path)
        + r"}"
        + "\n"
        + r"\end{figure}"
        + "\n"
        + r"\vfill"
        + "\n"
        + "\n"
        + r"\begin{tikzpicture}[remember picture,overlay,shift={(current page.north east)}]"
        + "\n"
        + r"\node[anchor=north east,xshift=-3cm,yshift=-2.5cm]{\includegraphics[width=2cm]{"
        + "{}".format("../logo-acme_systems.jpeg")
        + "}};"
        + "\n"
        + r"\end{tikzpicture}"
        + "\n"
        + r"\begin{tikzpicture}[remember picture,overlay,shift={(current page.north west)}]"
        + "\n"
        + r"\node[anchor=north west,xshift=3.5cm,yshift=-1.5cm]{\includegraphics[width=2cm]{"
        + "{}".format("../logo-livio_argentini.jpeg")
        + "}};"
        + "\n"
        + r"\end{tikzpicture}"
    )

    latex_complete = "{0}{2}{1}".format(latex_start, latex_end, latex)

    latex_file_path: pathlib.Path = image_file.with_suffix(".tex")
    docker_latex_file_path = latex_file_path.name

    pdf_file_path: pathlib.Path = latex_file_path.with_suffix(".pdf")

    with open(latex_file_path, "w") as f:
        f.write(latex_complete)

    console.print(
        Panel(
            '[bold][[blue]FILE[/blue] - [cyan]LATEX[/cyan]][/bold] - "[bold green]{}[/bold green]"'.format(
                latex_file_path.absolute().resolve()
            )
        )
    )

    # out_directory = "build"

    progress_list_task.update(task_latex, task="Docker Image Running")

    docker_image = "micheleforese/latex:full"

    # Get User ID and GROUP
    user_id, stderr = exec_command(["id", "-u"])

    if debug:
        console.print(f'USER: {os.environ.get("USER", "")}')

    if debug:
        console.log(user_id)
        console.log(stderr)

    user_group, stderr = exec_command(["id", "-g"])

    if debug:
        console.log(user_group)
        console.log(stderr)

    docker_instance = Docker_CLI()

    docker_command_run = docker_instance.run(
        docker_image,
        remove_on_exit=True,
        user=User(
            # id="".join(filter(str.isdigit, user_id)),
            # group="".join(filter(str.isdigit, user_group)),
            id=1000,
            group=1000,
        ),
        volume=Volume(local=home.absolute().resolve(), remote="/data"),
        command='pdflatex -output-format="{}" -output-directory="{}" "{}"'.format(
            "pdf",
            latex_home.name,
            docker_latex_file_path,
        ),
    )

    if debug:
        console.print(
            '[DOCKER] - Command: \n "[bold green]{}[/bold green]"'.format(
                docker_command_run
            )
        )

    stdout, stderr = exec_command(docker_command_run)

    if debug:
        console.log("RESULT:" + stdout)

    if len(str(stderr)) != 0:
        console.log("ERROR:" + stderr)

    console.print(
        Panel(
            '[bold][[blue]FILE[/blue] - [cyan]PDF[/cyan]][/bold] - "[bold green]{}[/bold green]"'.format(
                pdf_file_path.absolute().resolve()
            )
        )
    )

    progress_list_task.remove_task(task_latex)

    live.stop()
