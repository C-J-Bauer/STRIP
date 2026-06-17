import numpy as np
import os
from pathlib import Path
from strip import B_transform
from strip_tools import NMRData,ProcessMode, ResolutionEnhance, Plotter
from strip_params import SimParams, PlotParams

storage = {}
curr_dir = Path(__file__).resolve().parents[0]

simParamOverrides = dict(
    dt1 = 0.032,
    dt2 = 0.004,
    t1Size = 1024,
    t2Size = 4096,
)

plotParamOverrides = dict(
    doZoom = True,
    zoom = (900,4460,1337,4715),
    lowContourLevel = 0.05,
)

def here(fileName):
    return os.path.join(curr_dir, fileName)

def initial_dispersive(spectrum):
    return B_transform(spectrum.real)

def new_guess(spectrum):
    return storage['phase_twist'] - initial_dispersive(spectrum)

def new_dispersive(spectrum):
    return B_transform(new_guess(spectrum))

def average_dispersive(spectrum):
    return (initial_dispersive(spectrum) + new_dispersive(spectrum)) / 2.0

def final_guess(spectrum):
    return storage['phase_twist'] - average_dispersive(spectrum)

plots = [
    dict(
        process_mode = ProcessMode.PhaseTwist,
        file_name = here('Cartoon_a.png'),
        plot_choice_function = None,
    ),
    dict(
        process_mode = ProcessMode.AbsoluteValue,
        file_name = here('Cartoon_b.png'),
        plot_choice_function = None,
    ),
    dict(
        process_mode = ProcessMode.AbsoluteValue,
        file_name = here('Cartoon_c.png'),
        plot_choice_function = initial_dispersive,
    ),
    dict(
        process_mode = ProcessMode.AbsoluteValue,
        file_name = here('Cartoon_d.png'),
        plot_choice_function = new_guess,
    ),
    dict(
        process_mode = ProcessMode.AbsoluteValue,
        file_name = here('Cartoon_e.png'),
        plot_choice_function = new_dispersive,
    ),
    dict(
        process_mode = ProcessMode.AbsoluteValue,
        file_name = here('Cartoon_f.png'),
        plot_choice_function = average_dispersive,
    ),
    dict(
        process_mode = ProcessMode.AbsoluteValue,
        file_name = here('Cartoon_g.png'),
        plot_choice_function = final_guess,
    ),
]

def process(simParams, plotParams):
    nmrData = NMRData(simParams)
    plotter = Plotter(plotParams)
    return nmrData.simulate(plotter)

def main():
    simParams = SimParams(**simParamOverrides)
    plotParams = PlotParams(**plotParamOverrides)
    simParams.processMode = ProcessMode.PhaseTwist
    simParams.resolutionEnhance = ResolutionEnhance.Never
    plotParams.doPlot = False
    spectrum = process(simParams, plotParams)
    maxValue = np.max(np.abs(spectrum))
    storage['phase_twist'] = spectrum.real.copy()
    plotParams.doPlot = True
    
    for plot in plots:
        simParams.processMode = plot['process_mode']
        plotParams.plotFileName = plot['file_name']
        plotParams.plotChoiceFunction = plot.get('plot_choice_function', None)
        plotParams.maxPlotValue = maxValue
        spectrum = process(simParams, plotParams)


if __name__ == '__main__':
    main()