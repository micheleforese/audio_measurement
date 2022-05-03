import subprocess


def exec_command(command):
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    stdout, stderr = process.communicate()
    try:
        stdout = stdout.decode("utf-8")
        stderr = stderr.decode("utf-8")
    except:
        pass
    return stdout, stderr
