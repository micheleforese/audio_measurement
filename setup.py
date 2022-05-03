from setuptools import find_packages, setup

readme = ""
with open("README.md") as f:
    readme: str = f.read()

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
        "click",
        "rich",
        "pyjson5",
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "python-usbtmc",
        "pyusb",
        "nidaqmx",
        "PyQt5",
        "PyQt6",
    ],
    entry_points={
        "console_scripts": [
            "audio_measurements = cDAQ.script.cli:cli",
        ],
    },
)
