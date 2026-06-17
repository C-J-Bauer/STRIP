import numpy as np
import matplotlib.pyplot as plt
import json
import os
from pathlib import Path
from strip_tools import NMRData, ResolutionEnhance, ProcessMode, Plotter
from strip_params import SimParams, PlotParams
from matplotlib.gridspec import GridSpec

# Try to use CuPy if available - otherwise use Numpy
try:
    import cupy as cp
    from strip_cupy import STRIP, STRIP_quick_and_dirty
except ImportError:
    from strip import STRIP, STRIP_quick_and_dirty
    
curr_dir = Path(__file__).resolve().parents[0]

def here(fileName):
    return os.path.join(curr_dir, fileName)
    
# Set this to True to show all figure plots or False for 2d spectrum only    
SHOW_FIGURE_PLOTS = True    

simOverrides = dict(
    resolutionEnhance = ResolutionEnhance.Early,
    processMode = ProcessMode.STRIP,
    loops = 15,
    gaussianBroaden1 = 0.18,
    expBroaden1 = -0.6,
    gaussianBroaden2 = 0.18,
    expBroaden2 = -0.6,
    noiseLevel = 0.0,
    signalBox = None,
    noiseBox = None,
    doShear = True,
    fileNameBase = here('fid_jspectrum')
)

plotOverrides = dict(
    doPlot = not SHOW_FIGURE_PLOTS,
    doZoom = False,
    zoom = None,
    showZoom = False,
    lowContourLevel = 0.1,
    multiplets = [1474, 3441, 3605, 6717],
    plotFileName = here("Figure_7")
)

class NMRDataFromGamma(NMRData):
    def __init__(self, simParams):
        self.simParams = simParams
        self.readParams()
        self.readAndProcessData()

    def readParams(self):
        params_filename = self.simParams.fileNameBase + '.json'
        with open(params_filename) as f:
            data = f.read()
            params = json.loads(data)
            for key, value in params.items():
                if hasattr(self.simParams, key):
                    setattr(self.simParams, key, value)
          
            
    def readAndProcessData(self):
        fid_filename = self.simParams.fileNameBase + '.fid'
        data = np.fromfile(fid_filename, dtype=np.float64)
        # check size
        if len(data) != self.simParams.t1Size * self.simParams.t2Size * 2:
            raise Exception('Data size mismatch')            
        # make a 2D array
        data = data.reshape((self.simParams.t1Size*2, self.simParams.t2Size))

        window1, window2 = self.create_windows()
        f1size = self.calculate_zero_filled_size(self.simParams.t1Size, self.simParams.f1MinSize)
        f2size = self.calculate_zero_filled_size(self.simParams.t2Size, self.simParams.f2MinSize)
        Fid2d = np.zeros((self.simParams.t1Size, self.simParams.t2Size), dtype=complex)
        for i in range(self.simParams.t1Size):
            real = data[2*i]
            imag = data[2*i+1]
            noise = np.random.normal(0, self.simParams.noiseLevel, self.simParams.t2Size) + 1j * np.random.normal(0, self.simParams.noiseLevel, self.simParams.t2Size)
            complex_fid = (np.array(real) + 1j * np.array(imag) + noise) * window2
            Fid2d[i] = complex_fid * window1[i]

        first_spec = np.fft.fft(Fid2d[0], n = f2size)
        shifted = np.fft.fftshift(first_spec)
        self.firstIncrement = shifted.real
        
        raw_spectrum = np.fft.fft2(Fid2d, s=[f1size, f2size])
        self.spectrum = np.fft.fftshift(raw_spectrum)                                

def add_spec_1d(ax, spec):
    x =  np.arange(len(spec))
    y = spec
    ax.plot(x, y)
    ax.set_xticks([])
    ax.set_yticks([])
  
def shorten(spectrum, amount):
    # If a numpy array is of length z, trim both ends so that length of array is reduced to z*(1-amount)
    # amount is a float between 0 and 1
    return spectrum[int(amount*len(spectrum)):int((1-amount)*len(spectrum))]

def plot_multi_spectrum(spectrum, first_increment, pure_shift, multiplet_1, multiplet_2, multiplet_3, multiplet_4, plotParams):  
    plt.style.use('_mpl-gallery')
    plt.rcParams["figure.figsize"] = (18, 10)
  
    first_increment = shorten(first_increment,0.05)
    pure_shift = shorten(pure_shift,0.05) #shorten
    
    maxValue = np.max(np.abs(spectrum))
    
    colours = []
    low_level_contour = plotParams.lowContourLevel
    num_levels = plotParams.numContourLevels
    log_contour_levels = np.logspace(np.log10(low_level_contour),0.0, num_levels) * maxValue
    negative_contour_levels = np.flip(log_contour_levels) * -1.0
    levels = np.concatenate((negative_contour_levels, log_contour_levels))

    for i in levels:
        if i < 0:
            colours.append('red')
        else:
            colours.append('black')

    fig = plt.figure(layout="constrained")

    gs = GridSpec(4, 3, figure=fig)
    contour = plt.subplot(gs[2:4, 0:2])
    fi = plt.subplot(gs[1, 0:2])
    ps = plt.subplot(gs[0, 0:2])
    m1 = plt.subplot(gs[0, 2])
    m2 = plt.subplot(gs[1, 2])
    m3 = plt.subplot(gs[2, 2])
    m4 = plt.subplot(gs[3, 2])
    
    add_spec_1d(fi, first_increment)
    add_spec_1d(ps, pure_shift)
    add_spec_1d(m1, multiplet_1)
    add_spec_1d(m2, multiplet_2)
    add_spec_1d(m3, multiplet_3)
    add_spec_1d(m4, multiplet_4)
    contour.contour(spectrum, levels=levels, colors=colours)
    contour.set_xticks([])
    contour.set_yticks([])
    
    max = np.max(np.abs(pure_shift))
    ps.text(800, 0.8*max, "A", size=30, color='black')
    ps.text(2780, 0.8*max, "B", size=30, color='black')
    ps.text(3280, 0.8*max, "C", size=30, color='black')
    ps.text(6000, 0.8*max, "D", size=30, color='black')
    max = np.max(np.abs(multiplet_1))
    m1.text(100, 0.8*max, "A", size=30, color='black')
    max = np.max(np.abs(multiplet_2))
    m2.text(100, 0.8*max, "B", size=30, color='black')
    max = np.max(np.abs(multiplet_3))
    m3.text(100, 0.8*max, "C", size=30, color='black')
    max = np.max(np.abs(multiplet_4))
    m4.text(100, 0.8*max, "D", size=30, color='black')

    fig.savefig(here("Figure_7"))
    plt.show()
    
def process():
    nmrData = NMRDataFromGamma(simParams=SimParams(**simOverrides))
    plotParams=PlotParams(**plotOverrides)
    plotter = Plotter(plotParams)
    spectrum = nmrData.simulate(plotter)
    multiplets = plotParams.multiplets
    pureShift = nmrData.sum_to_1d(spectrum)
    if SHOW_FIGURE_PLOTS:
        plot_multi_spectrum(spectrum,
                            nmrData.firstIncrement,
                            pureShift,
                            spectrum[:,multiplets[0]],
                            spectrum[:,multiplets[1]],
                            spectrum[:,multiplets[2]],
                            spectrum[:,multiplets[3]],
                            plotParams)
    
def main():
    process()   


if __name__ == '__main__':
    main()