This repository contains Python code for interfacing with equipment in PHYS 320 (Electronics with Lab) at Truman State University.

Installation
============

1. Install [NI-VISA](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html) for your operating system.

1. Install the `conda` package manager on your system via [either Miniconda or Miniforge](https://conda.io/projects/conda/en/latest/user-guide/install/index.html) or, on macOS/Linux, your favorite package manager. For macOS I recommend [Homebrew](https://brew.sh).

1. Install [Visual Studio Code](https://code.visualstudio.com/download), then use the Extension Manager to install the official Microsoft-provided Python and Jupyter extensions for code and notebook editing. 

1. Download the contents of this repository using `git clone https://github.com/tdwiser/phys320-python` or the Visual Studio interface ("Clone Git Repository..."). (Windows users may have to install `git` first to use the clone option, but downloading updates will be as easy as `git pull`.)

1. Using a terminal (on Windows, a Conda terminal) navigate to the directory with the downloaded or `git clone`d code. Create a conda environment with `conda env create -f environment.yml`. This will download and install several Python packages and might take a bit.

Use
===

Whenever you open a new terminal you'll need to activate the appropriate Python environment with `conda activate phys320`.
To open a JupyterLab interface in the browser, run `jupyter lab`.
In VSCode, you can select the `phys320` conda environment using the command "Python: Select Interpreter..." or "Notebook: Select Kernel..." for notebooks.
You may also need "Jupyter: Select Interpreter to Start Notebook Server..." depending on your installation.

References
==========

1. [Tektronix Programming Manual][tek-prog-manual]

[tek-prog-manual]: https://www.tek.com/en/oscilloscope/tds210-manual/tds200-tds1000-tds2000-tds1000b-tds2000b-and-tps2000-programmer
