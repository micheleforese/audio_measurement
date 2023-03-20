import subprocess

from audio.console import console


def exec_command(command: str) -> tuple[str, str]:
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout, stderr = process.communicate()
    try:
        stdout: str = stdout.decode("utf-8")
        stderr: str = stderr.decode("utf-8")
    except Exception as e:
        console.print(f"{e}")
    return stdout, stderr
