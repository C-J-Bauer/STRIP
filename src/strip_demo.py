from strip_tools import NMRData, Plotter
from strip_params import SimParams, PlotParams, ResolutionEnhance, ProcessMode

simParamOverrides = dict(
    ProcessMode = ProcessMode.STRIP,               # See strip_params.ProcessMode for choices
    resolutionEnhance = ResolutionEnhance.Early,   # See strip_params.ResolutionEnhance for choices
    dt1 = 0.032,
    dt2 = 0.004,
    t1Size = 1024,
    t2Size = 4096,
    signalBox = (0, 0, 2047, 8191),
    noiseBox = (10, 1000, 210, 2000),
    gaussianBroaden1 = 0.16,
    expBroaden1 = -1.0,
    gaussianBroaden2 = 0.16,
    expBroaden2 = -1.0,
)

plotParamOverrides = dict(
    doZoom = True,
    zoom = (900,4460,1337,4715),
    plotLabel = simParamOverrides['ProcessMode'].label,
    plotLabelOffset = (10,10),
    labelSize = 30,
    lowContourLevel = 0.05,
)


def process():
    nmrData = NMRData(simParams = SimParams(**simParamOverrides))
    plotter = Plotter(plotParams = PlotParams(**plotParamOverrides))
    return nmrData.simulate(plotter)
    
def main():
    process()

if __name__ == '__main__':
    main()