from setuptools import setup, find_packages

setup(
    name="OctoSMU",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.22",
        "matplotlib>=3.5",
        "adafruit-blinka>=7.3.3",
        "adafruit-circuitpython-mcp4728>=1.0.8",
        "adafruit-circuitpython-ads1x15>=2.3.9",
        "adafruit-circuitpython-mcp230xx>=1.0.10",
        "pandas>=1.4",
    ],
    description="A Python package for Octoboard Maximum Power Point Tracker",
    author="Clemens Baretzky",
    author_email="Clemens.Baretzky@gmail.com",
    url="https://github.com/cbaretzky/octoboard",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)