import numpy as np
from high_pass_filter import HighPassFilter
import nmrglue as ng
from strip_tools import NMRData, Plotter
from strip_params import SimParams, PlotParams, ResolutionEnhance, ProcessMode
from pathlib import Path
import os
import sys

    
curr_dir = Path(__file__).resolve().parents[0]

def here(fileName):
    return os.path.join(curr_dir, fileName)

F2_PHASE_CORRECT_0 = -90.4  # Measure these in Bruker Topspin
F2_PHASE_CORRECT_1 = 0.9     
        
simOverrides = dict(
    resolutionEnhance = ResolutionEnhance.Early,
    processMode = ProcessMode.STRIP,
    loops = 15,
    f2MinSize = 32768, 
    f1MinSize = 1024,
    sineBellPhi1 = 0.5,
    sineBellPhi2 = 0.5,
    doShear = True,
    fileNameBase = here('example/1')
)

plotOverrides = dict(
    doPlot = True,
    doZoom = False,
    zoom = None,
    showZoom = False,
    lowContourLevel = 0.01,
    multiplets = None,
    shiftRef = None,
)        

class NMRDataFromBruker(NMRData):
    def __init__(self, simParams):
        self.simParams = simParams
        self.readAndProcessData()

    def readAndProcessData(self):
        dic, fid2d = ng.bruker.read(self.simParams.fileNameBase)
        self.simParams.dt2 = 1.0/dic['acqus']['SW_h']
        self.simParams.dt1 = 1.0/dic['acqu2s']['SW_h']
        shape = fid2d.shape
        self.simParams.t1Size = shape[0]
        self.simParams.t2Size = shape[1]
        window1, window2 = self.create_windows()
        window1[0] *= 0.5
        window2[0] *= 0.5
        f1size = self.calculate_zero_filled_size(shape[0], self.simParams.f1MinSize)
        f2size = self.calculate_zero_filled_size(shape[1], self.simParams.f2MinSize)
        
        # If there is a water peak in the centre it can be removed if filterK and filterM are set appropriately
        self.high_pass_filter(fid2d)
        
        for i in range(self.simParams.t1Size):
            fid2d[i] = (fid2d[i] * window2) * window1[i]
            
        after_f2_transform = np.fft.fft(fid2d, n=f2size, axis=1)
        phase_correction = self.phase_correction_vector(f2size, F2_PHASE_CORRECT_0, F2_PHASE_CORRECT_1)
        after_f2_phase_correction = after_f2_transform * phase_correction
        
        raw_spectrum = np.fft.fft(after_f2_phase_correction, n=f1size, axis=0)
        self.spectrum = np.fft.fftshift(raw_spectrum)
        self.spectrum = np.flip(self.spectrum) 
        
        self.firstIncrement = np.flip(np.fft.fftshift(after_f2_phase_correction[0]).real)
                                  


def process():
    nmrData = NMRDataFromBruker(simParams=SimParams(**simOverrides))
    if nmrData.simParams.processMode == ProcessMode.AmplitudeModulated:
        sys.exit("Wishful thinking: Amplitude-modulated data not available")
    plotParams=PlotParams(**plotOverrides)
    plotter = Plotter(plotParams)
    nmrData.simulate(plotter)
    multiplets = plotParams.multiplets
    if multiplets:
        for i, multiplet in enumerate(multiplets):
            nmrData.save_1d_f1(here('multiplet_%d.json' % i), multiplet, plotParams.shiftRef)
    nmrData.save_1d_f2(nmrData.sum_to_1d(nmrData.spectrum), here('shift_only.json'), shiftRef=plotParams.shiftRef)
    nmrData.save_1d_f2(nmrData.firstIncrement, here('first_increment.json'), shiftRef=plotParams.shiftRef)
    

    
def main():
    process()


if __name__ == '__main__':
    main()