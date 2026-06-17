# Processing Bruker data

The process_bruker.py is a simple script for processing Bruker 2D J-spectrum fid data. Bruker fid data can include additional initial points attributed to a digital filtering. This script asumes that these have been removed by running the convdta command to export a new array of fids untainted by these additional points. The script uses the nmrglue module to assist in reading in the Bruker data. If this is not installed on your system then add this to your local virtual environment with

    pip install nmrglue

In process_bruker.py you will need to override simulation and plot parameters by changing values in simOverrides and plotOverridesin in order to customize the processing for your dataset. The full range of parameters that can be changed can be seen in src/strip_params. You will also need to set F2_PHASE_CORRECT_0 and F2_PHASE_CORRECT_1 to match the zero and first order phase parameters required to phase the first increment in Topspin. Adding a ppm scale to the plot is fairly easy, just change the shiftRef parameter in plotOverrides to a tuple defining (spectrometer frequency, shift, point number). To do this zoom into the reference peak using magnifying glass icon provided by the contour display window. The cursor position in (x, y) points is shown. Take a note of the x value that corresponds to your reference point. For example, if your x value is 31576 for a TMS peak which you want at 0.0 ppm and your spectrometer fregquency is 500 MHz, you would enter

    shiftref = (500.0, 0.0, 31576)

You may want to view individual multiplets. To do this determine the x value for each of the multiplets of interest and put this into a tuple in the multiplets parameter in plotOverrides. For example,
if you have multiplets at x values of 27586 and 28259 then you would enter

    multiplets = (27586, 28259)

There will a json files created for each of the multiplets selected and also ones for the first increment and the shift only projection. There is a separate 1D file viewer, plot_1d.py, that can be used to display these. Flags on the command line can change the intensity of the 1D spectra (-x) or zoom in to a region (-z or -s). The -z zoom takes pairs of point indices to select a region, whereas the -s flag allows one to enter ppm limits. When using the -z and -s flags the two values entered are for the left and right limits of the spectrum respectively. Entering them in reverse order will reverse the displayed spectrum.

For example, to look at some weak intensity peaks with a 20 fold intensity increase in the first increment spectrum between 2.5 and 0.5 ppm one would enter

    python plot_1d.py -x 20 -s 2.5 0.5 first_increment.json
