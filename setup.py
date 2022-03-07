from importlib_metadata import entry_points
from setuptools import setup, find_packages


with open("README.md") as f:
    readme = f.read()

setup(
    name="audio_measurements",
    version="0.0.1",
    description="Audio Measurements",
    long_description=readme,
    author="Michele Forese",
    author_email="michele.forese.personal@gmail.com",
    url="https://github.com/micheleforesedev/audio_measurement",
    # license=license,
    packages=find_packages(exclude=("tests", "doc", "driver", "data", "config")),
    install_requires=[
        "Click",
    ],
    entry_points={
        "console_scripts": [
            "audio_measurements = cDAQ.script.cli:cli",
        ],
    },
)
