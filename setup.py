from setuptools import setup, find_packages


with open("README.md") as f:
    readme = f.read()

with open("requirements.txt", "r") as f:
    install_requires = f.read().splitlines()

setup(
    name="audio_measurements",
    version="0.0.1",
    description="Audio Measurements",
    long_description=readme,
    author="Michele Forese",
    author_email="michele.forese.personal@gmail.com",
    url="https://github.com/micheleforesedev/audio_measurement",
    # license=license,
    packages=find_packages(exclude=("test", "doc")),
    install_requires=install_requires,
)
