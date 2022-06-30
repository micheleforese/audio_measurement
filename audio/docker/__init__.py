import pathlib
from typing import Optional


class User:
    id: int
    group: int

    def __init__(self, id: int, group: int) -> None:
        self.id = id
        self.group = group


class Volume:
    local: pathlib.Path
    remote: pathlib.Path

    def __init__(self, local: pathlib.Path, remote: pathlib.Path) -> None:
        self.local = local
        self.remote = remote


class Docker_CLI:
    def __init__(self) -> None:
        pass

    def run(
        self,
        image: str,
        remove_on_exit: bool = True,
        user: Optional[User] = None,
        volume: Optional[Volume] = None,
        command: Optional[str] = None,
    ) -> str:

        docker_run_command = ["docker", "run"]

        if remove_on_exit:
            docker_run_command.append("--rm")

        if user is not None:
            docker_run_command.append(
                "--user {}:{}".format(str(user.id), str(user.group))
            )

        if volume is not None:
            docker_run_command.append("-v {}:{}".format(volume.local, volume.remote))

        docker_run_command.append(image)

        if command is not None:
            docker_run_command.append(command)

        return " ".join(docker_run_command)
