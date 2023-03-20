from pathlib import Path

from setuptools import find_packages, setup

setup(
    name="audio_measurements",
    version="0.0.1",
    description="Audio Measurements",
    long_description=Path("README.md").read_text(),
    author="Michele Forese",
    author_email="michele.forese.personal@gmail.com",
    url="https://github.com/micheleforesedev/audio_measurement",
    packages=find_packages(exclude=("tests", "doc", "driver", "data", "config")),
    install_requires=Path("requirements.txt").read_text().splitlines(),
    entry_points={
        "console_scripts": [
            "audio_measurements = audio.script.cli:cli",
        ],
    },
)
