import numpy as np
import os
from pathlib import Path
from strip_tools import NMRData,ProcessMode, ResolutionEnhance, Plotter
from strip_params import SimParams, PlotParams

storage = {}
curr_dir = Path(__file__).resolve().parents[0]

simParamOverrides = dict(
    dt1 = 0.032,
    dt2 = 0.004,
    t1Size = 1024,
    t2Size = 4096,
    gaussianBroaden1 = 0.16,
    expBroaden1 = -1.0,
    gaussianBroaden2 = 0.16,
    expBroaden2 = -1.0
)

plotParamOverrides = dict(
    doZoom = True,
    zoom = (900,4460,1337,4715),
    lowContourLevel = 0.05,
)

def here(fileName):
    return os.path.join(curr_dir, fileName)

def dispersion(spectrum):
    return spectrum.real - storage['pure_absorption'].real

def strip_dispersion(spectrum):
    return storage['phase_twist'].real - spectrum.real

def dispersion_enhanced(spectrum):
    return spectrum.real - storage['pure_absorption_enhanced'].real

def strip_dispersion_enhanced(spectrum):
    return storage['phase_twist_enhanced'].real - spectrum.real

plots = [
    dict(
        process_mode = ProcessMode.PhaseTwist,
        file_name = here('Figure_1a.png'),
    ),
    dict(
        process_mode = ProcessMode.AmplitudeModulated,
        file_name = here('Figure_1b.png'),
    ),
    dict(
        process_mode = ProcessMode.PhaseTwist,
        file_name = here('Figure_1c.png'),
        plot_choice_function = dispersion,
    ),
    dict(
        process_mode = ProcessMode.AbsoluteValue,
        file_name = here('Figure_1d.png'),
    ),
    dict(
        process_mode = ProcessMode.STRIP,
        file_name = here('Figure_1e.png'),
    ),
    dict(
        process_mode = ProcessMode.STRIP,
        file_name = here('Figure_1f.png'),
        plot_choice_function = strip_dispersion,
    ),
]

plots_resolution_enhanced = [
    dict(
        process_mode = ProcessMode.PhaseTwist,
        file_name = here('Figure_4a.png'),
    ),
    dict(
        process_mode = ProcessMode.AmplitudeModulated,
        file_name = here('Figure_4b.png'),
    ),
    dict(
        process_mode = ProcessMode.PhaseTwist,
        file_name = here('Figure_4c.png'),
        plot_choice_function = dispersion_enhanced,
    ),
    dict(
        process_mode = ProcessMode.AbsoluteValue,
        file_name = here('Figure_4d.png'),
    ),
    dict(
        process_mode = ProcessMode.STRIP,
        file_name = here('Figure_4e.png'),
    ),
    dict(
        process_mode = ProcessMode.STRIP,
        file_name = here('Figure_4f.png'),
        plot_choice_function = strip_dispersion_enhanced,
    ),
]

def process(simParams, plotParams):
    nmrData = NMRData(simParams)
    plotter = Plotter(plotParams)
    return nmrData.simulate(plotter)

def main():
    simParams = SimParams(**simParamOverrides)
    plotParams = PlotParams(**plotParamOverrides)
    plotParams.doPlot = False
    
    simParams.processMode = ProcessMode.PhaseTwist
    simParams.resolutionEnhance = ResolutionEnhance.Never
    spectrum = process(simParams, plotParams)
    maxValue = np.max(np.abs(spectrum))
    storage['phase_twist'] = spectrum.real.copy()
    simParams.processMode = ProcessMode.AmplitudeModulated
    simParams.resolutionEnhance = ResolutionEnhance.Never
    spectrum = process(simParams, plotParams)
    storage['pure_absorption'] = spectrum.real.copy()
    simParams.processMode = ProcessMode.AmplitudeModulated
    simParams.resolutionEnhance = ResolutionEnhance.Early
    spectrum = process(simParams, plotParams)
    maxValueEnhanced = np.max(np.abs(spectrum))
    simParams.processMode = ProcessMode.PhaseTwist
    spectrum = process(simParams, plotParams)
    storage['phase_twist_enhanced'] = spectrum.real.copy()
    simParams.processMode = ProcessMode.AmplitudeModulated
    spectrum = process(simParams, plotParams)
    storage['pure_absorption_enhanced'] = spectrum.real.copy()
    
    plotParams.doPlot = True
    for plot in plots:
        simParams.processMode = plot['process_mode']
        simParams.resolutionEnhance = ResolutionEnhance.Never
        plotParams.plotLabel = plot.get('plot_title', '')
        plotParams.plotFileName = plot['file_name']
        plotParams.plotChoiceFunction = plot.get('plot_choice_function', None)    
        plotParams.maxPlotValue = maxValue
        process(simParams, plotParams)

    for plot in plots_resolution_enhanced:
        simParams.processMode = plot['process_mode']
        simParams.resolutionEnhance = ResolutionEnhance.Early
        plotParams.plotLabel = plot.get('plot_title', '')
        plotParams.plotFileName = plot['file_name']
        plotParams.plotChoiceFunction = plot.get('plot_choice_function', None)
        plotParams.maxPlotValue = maxValueEnhanced
        process(simParams, plotParams)
    

if __name__ == '__main__':
    main()