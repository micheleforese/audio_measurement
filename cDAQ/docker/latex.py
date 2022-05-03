import os
import pathlib
from struct import pack
from typing import List, Optional

from matplotlib import use
from cDAQ.console import console
from cDAQ.docker import Docker, User, Volume
from cDAQ.docker.utility import exec_command
from rich.panel import Panel


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
    debug: bool = False,
):

    console.print(Panel("[blue]Latex pdf creation start[/]"))

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

    latex_udc = (
        r"\newcommand{\der}[3][]{\frac{d^{#1} #2}{d #3^{#1}}}"
        + "\n"
        + r"\newcommand{\dder}[3][]{\frac{\partial{d}^{#1} #2}{\partial{d} #3^{#1} }}"
        + "\n"
        + r"\newcommand{\uvec}[1]{\hat{#1}}"
        + "\n"
        + r"\newcommand{\cvec}[2]{#1\uvec{#2}}"
        + "\n"
        + r"\newcommand{\veccomp}[4][]{\cvec{#2}{i^{#1}} + \cvec{#3}{j^{#1}} + \cvec{#4}{k^{#1}}}"
        + "\n"
    )

    # latex_udc = ""

    latex_start = (
        r"\documentclass[a4, landscape]{article}"
        + "\n"
        + latex_packages
        + "\pgfplotsset{compat=1.18}"
        + "\n"
        + latex_udc
        + r"\begin{document}"
        + "\n"
    )

    latex_end = "\n" + r"\end{document}"

    docker_image_file_path = image_file.name
    console.print('[PATH - docker - image_file] - "{}"'.format(docker_image_file_path))

    latex = (
        ""
        # +"\n"
        # + "\n"
        # + "\n"
        + "\n" + r"\null" + "\n" + r"\vfill"
        # + r"}}}}"
        # + r"\makebox[\textwidth]{"
        + "\n"
        r"\begin{figure}[h]"
        # + "\n"
        + "\centering"
        # + "\n"
        # + r"\hvspace*{-1in}"
        # + "\n"
        + r"\includegraphics[width=.9\paperwidth]{"
        + "{}".format(docker_image_file_path)
        + r"}"
        # + r"\includegraphics[width=\textwidth]{{{}}}".format(docker_image_file_path)
        + "\n" + r"\end{figure}" + "\n" + r"\vfill"
        # + r"\paragraph{First Paragraph}"
        #######
        # + "\n"
        # + r"\begin{tikzpicture}[remember picture,overlay]"
        # + "\n"
        # + r"\node[]{\includegraphics[width=.9\paperwidth]{"
        # + "{}".format(docker_image_file_path)
        # + "}};"
        # + "\n"
        # + r"\end{tikzpicture}"
        ########
        + "\n"
        + "\n"
        + r"\begin{tikzpicture}[remember picture,overlay,shift={(current page.north east)}]"
        + "\n"
        + r"\node[anchor=north east,xshift=-3cm,yshift=-2.5cm]{\includegraphics[width=2cm]{"
        + "{}".format("logo-acme_systems.jpeg")
        + "}};"
        + "\n"
        + r"\end{tikzpicture}"
        + "\n"
        + r"\begin{tikzpicture}[remember picture,overlay,shift={(current page.north west)}]"
        + "\n"
        + r"\node[anchor=north west,xshift=3.5cm,yshift=-1.5cm]{\includegraphics[width=2cm]{"
        + "{}".format("logo-livio_argentini.jpeg")
        + "}};"
        + "\n"
        + r"\end{tikzpicture}"
    )

    latex_complete = "{0}{2}{1}".format(latex_start, latex_end, latex)

    latex_file_path: pathlib.Path = image_file.with_suffix(".tex")
    docker_latex_file_path = latex_file_path.name

    console.print('[PATH - latex_file_path] - "{}"'.format(latex_file_path))

    with open(latex_file_path, "w") as f:
        f.write(latex_complete)

    out_directory = "build"

    docker_image = "micheleforese/latex:full"

    # Get User ID and GROUP
    console.print("[DOCKER] - Retriving id user.")
    user_id, stderr = exec_command(["id", "-u"])

    if debug:
        console.log(user_id)
        console.log(stderr)

    console.print("[DOCKER] - Retriving id group.")
    user_group, stderr = exec_command(["id", "-g"])

    if debug:
        console.log(user_group)
        console.log(stderr)

    docker_instance = Docker()

    console.print("[DOCKER] - Running image.")
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
        command="pdflatex -output-format={} {}".format(
            "pdf",
            latex_file_path.name,
        ),
    )

    console.print("[DOCKER] - Command: \n\t{}".format(docker_command_run))

    console.print("[DOCKER] - Running image.")
    stdout, stderr = exec_command(docker_command_run)

    if debug:
        console.log("RESULT:" + stdout)
        console.log("ERROR:" + stderr)

    console.print(Panel("[blue]Latex pdf creation end[/]"))
