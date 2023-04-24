import shlex
import subprocess


def exec_command(command: str) -> tuple[str, str]:
    process = subprocess.Popen(
        shlex.split(command),  # noqa: S603
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout, stderr = process.communicate()

    stdout_decoded: str = stdout.decode("utf-8")
    stderr_decoded: str = stderr.decode("utf-8")

    return stdout_decoded, stderr_decoded
    return stdout_decoded, stderr_decoded
