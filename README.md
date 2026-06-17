# STRIP

An algorithm to improve the quality of phase modulated NMR data by reducing the double dispersive component.

The organization of directories is as follows:

- src: contains algorithm source code files and utility functions to process and plot using STRIP
- documents: contains the STRIP preprint
- figures: contains python code to generate plots used for the figures
- spectrometer: for scripts to process real data. Initally there is only a processing example for Bruker data

## Installation

Steps to install on a linux system will be shown below. If the procedure is different on Windows I will
indicate the alternative commands that need to be performed. I do not have a macOS PC to test installation.

The code has been tested using Python versions 3.13 and 3.14, and it is highly likely that it will work
on some earlier versions. Hopefully it should work on later versions too. However, if you are having problems
that appear to be related to python features failing then perhaps testing using version 3.14 may be a
sensible approach.

The first installation step is to download or unzip the STRIP directory. If you have git installed on your
system the simplest way may be to just execute the following command

    git clone https://github.com/C-J-Bauer/STRIP.git

and this will create a STRIP directory in the current directory.

Some of the Python modules required will not already be available on your system.
The recommended way to ensure that you can use these modules is to create a local python virtual environment in the
top-level STRIP directory and use the pip command to install the modules there.

The commands to do this are

    cd STRIP
    python -m venv env
    source env/bin/activate
    pip install -e .
    pip install -r requirements.txt

On Windows (in a PowerShell) the third command to be executed above (to activate the local virtual environment) should be

    env\Scripts\Activate.ps1 

Note that most of the above commands need only be executed once on installation. The exception is the activate command
(the third command) which must be executed in the STRIP directory whenever a new shell is used. This command
ensures that the local virtual environment is being used. Full details of python virtual environments are here https://docs.python.org/3/library/venv.html

## CuPy installation

Massive performance improvements for STRIP can be gained by running the algorithm on a graphics card.
To do this the CuPy module must be installed. It is claimed that CuPy can be used with AMD graphics cards,
but since I do not have one of these I can not guarantee that this will work. STRIP using CuPy has been tested
using both of the following

    Nvidia RTX 2060 (with version 12.2 of Cuda toolkit)
    Nvidia RTX 5060 Ti (with version 13.3 of Cuda toolkit)

I will give instructions here for installing CuPy on Nvidia cards. The first step is to install the Cuda toolkit on your system.
Instructions to to this can be found here https://docs.nvidia.com/cuda

Note that depending on your model of graphics card, you will need to install a cuda toolkit with a major version number of either 12 or 13.
There are different CuPy module installation commands depending on which major version of the Cuda toolkit you have installed.

For example, if Cuda Toolkit of 12.2 is installed, Cupy will be installed in the local environment with

    cd STRIP
    source env/bin/activate
    pip install cupy-cuda12x

whereas, if Cuda Toolkit of 13.3 is installed, Cupy will be installed in the local environment with

    cd STRIP
    source env/bin/activate
    pip install cupy-cuda13x

On Windows in a PowerShell the command to activate the local environment is different, see above.
Full details on cupy installation are here https://docs.cupy.dev/en/stable/install.html

Note that if you do not have an appropriate graphics card, or you have problems installing Cupy, the scripts provided here will still run, albeit more slowly.
The code is designed to default to using Numpy and SciPy for the STRIP algorithm if CuPy is not installed.


## Testing

In the src directory there is very simple python script, strip_demo.py, which runs STRIP on a single peak. This should run without error. Note that if CuPy is used you may see a warning about cupyx.jit.rawkernel being experimental. This warning can safely be ignored since it is a well-known bug/feature related to the use of the signal processing functions of CuPy.

## Generating figures

In the documents directory is a copy of the preprint of STRIP. The code required to generate the figures for this document are provided in the figures directory.
Here are instructions on how to create the figures.

### Figures 1 and 4

    cd STRIP/figures/figure_1_and_4
    python figure_generator.py

This will create a bunch of PNG images. There are a couple of LaTeX source files provided in that directory, Figure_1.tex and Figure_4.tex, that can then compiled using these PNG images to create the figures.

### Figure 2

    cd STRIP/figures/figure_2
    python figure_generator.py

This will create a bunch of PNG images. There is a LaTeX source file provided in that directory, Figure_2.tex, that can then compiled using these PNG images to create the figure.

### Figure 3

    cd STRIP/figures/figure_3
    python figure_generator.py

This will create a bunch of PNG images. More images than are actually used in the figure are created. The figure was generated using a subset of these. 

### Figure 5

    cd STRIP/figures/figure_5
    python figure_generator.py

This figure shows a zoomed in region of a set of 100 peaks. The list of peaks and their attributes are stored in the file random_peaks.json. The first time figure_generator.py is run it calculates and sums the spectra of all of the peaks. This is time comsuming, and so the results of the summation are cached in two files, amplitude_modulated.npy and phase_modulated.npy. This ensures that future run quicker. There is also a python script,
random_peaks.py, that can be run to create a different set of peaks in random_peaks.json. Note that if you do create a new set of random peaks you will need to delete the cached files in order to process the new peaks.
Furthermore, you may find that the zoomed-in region is no longer interesting. A different region can be selected by adjusting the zoom plot parameter

### Figure 6

    cd STRIP/figures/figure_6
    python figure_generator.py

Running the figure_generator.py script will use a new (and consequently different) set of random numbers from that used in the preprint. The statistics should be similar, but the actual noise traces will be different.

### Figure 7

This figure uses a J-spectrum generated from a simulation using the GAMMA library (Smith SA, Levante TO, Meier BH, and Ernst RR. Computer Simulations in Magnetic Resonance. An Object Oriented Programming Approach. J Magn. Res. 1994; 106a:75-105). If GAMMA is not already installed on your system, build and installation instructions are here (https://pygamma-mrs.github.io/gamma.io/release/GammaBuildingLibrary.html). Once GAMMA is installed, the supplied jspectrum simulation program can be compiled and run

    cd STRIP/figures/figure_7
    gamma -o jspectrum jspectrum.cc
    ./jspectrum spin_system.sys

This generates two files, fid_jspectrum.fid and fid_jspectrum.json, which contain the binary data of the fid and acquisition parameters respectively. Finally to process the fid, improve the spectrum with STRIP and create the figure run

    python figure_generator.py