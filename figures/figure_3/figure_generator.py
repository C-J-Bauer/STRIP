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
)

plotParamOverrides = dict(
    doZoom = True,
    zoom = (900,4460,1337,4715),
    lowContourLevel = 0.05,
)

def here(fileName):
    return os.path.join(curr_dir, fileName)

def absorption_difference(spectrum):
    return spectrum - storage['absorption']


def make_plot_scenarios(numScenarios):
    return [
        dict(
            process_mode = ProcessMode.STRIP if i else ProcessMode.AbsoluteValue,
            plot_title = f'{i}',
            file_name = here(f'Loops_{i}.png'),
            loops = i,
        ) for i in range(numScenarios)
    ] + [
        dict(
            process_mode = ProcessMode.STRIP if i else ProcessMode.AbsoluteValue,
            plot_title = f'{i}',
            file_name = here(f'Diff_{i}.png'),
            loops = i,
            plot_choice_function = absorption_difference,
        ) for i in range(numScenarios)
    ]
    
def process(simParams, plotParams):
    nmrData = NMRData(simParams)
    plotter = Plotter(plotParams)
    return nmrData.simulate(plotter)

def main():
    plots = make_plot_scenarios(21)
    simParams = SimParams(**simParamOverrides)
    plotParams = PlotParams(**plotParamOverrides)
    simParams.processMode = ProcessMode.AmplitudeModulated
    simParams.resolutionEnhance = ResolutionEnhance.Never
    plotParams.doPlot = False
    spectrum = process(simParams, plotParams)
    maxValue = np.max(np.abs(spectrum))
    storage['absorption'] = spectrum.real.copy()
    plotParams.doPlot = True
    
    for plot in plots:
        simParams.processMode = plot['process_mode']
        simParams.loops = plot['loops']
        plotParams.plotLabel = f"{plot['loops']}"
        plotParams.plotFileName = plot['file_name']
        plotParams.plotChoiceFunction = plot.get('plot_choice_function', None)
        plotParams.maxPlotValue = maxValue
        process(simParams, plotParams)

if __name__ == '__main__':
    main()