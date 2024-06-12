This repository contains Python code for interfacing with equipment in PHYS 320 (Electronics with Lab) at Truman State University.

Installation
============

1. Install the `conda` package manager on your system via [either Miniconda or Miniforge](https://conda.io/projects/conda/en/latest/user-guide/install/index.html) or, on macOS/Linux, your favorite package manager. For macOS I recommend [Homebrew](https://brew.sh).

2. Download the contents of this repository using `git clone https://github.com/tdwiser/phys320-python` or the GitHub web interface. (Windows users will have to install `git` first to use the clone option, but downloading updates will be as easy as `git pull`.)

3. Using a terminal (on Windows, a Conda terminal) navigate to the directory with the downloaded or `git clone`d code. Create a conda environment with `conda env create -f environment.yml`. This will download and install several Python packages and might take a bit.

Use
===

Whenever you open a new terminal you'll need to activate the appropriate Python environment with `conda activate phys320`. To open a JupyterLab interface, run `jupyter lab`.

