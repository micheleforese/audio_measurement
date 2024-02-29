from pathlib import Path
from typing import Self


class User:
    user_id: int
    group: int

    def __init__(self: Self, user_id: int, group: int) -> None:
        self.user_id = user_id
        self.group = group


class Volume:
    local: Path
    remote: str

    def __init__(self: Self, local: Path, remote: str) -> None:
        self.local = local
        self.remote = remote


class DockerCLI:
    def __init__(self: Self) -> None:
        pass

    def run(
        self: Self,
        image: str,
        user: User | None = None,
        volume: Volume | None = None,
        command: str | None = None,
        *,
        remove_on_exit: bool = True,
    ) -> str:
        docker_run_command: list[str] = ["docker", "run"]

        if remove_on_exit:
            docker_run_command.append("--rm")

        if user is not None:
            docker_run_command.append(
                f"--user {user.user_id!s}:{user.group!s}",
            )

        if volume is not None:
            docker_run_command.append(f"-v {volume.local}:{volume.remote}")

        docker_run_command.append(image)

        if command is not None:
            docker_run_command.append(command)

        return " ".join(docker_run_command)
