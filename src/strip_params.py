from enum import Enum
import json

class ResolutionEnhance(Enum):
    Never = 1
    Early = 2
    Late = 3
    
class ProcessMode(Enum):
    PhaseTwist = 1              # Do nothing special for phase twist
    AbsoluteValue = 2           # Convert to absolute value spectrum 
    STRIP = 3                   # Reduce double dispersive component using STRIP
    AmplitudeModulated = 4      # Use amplitude modulated data instead

    @property
    def label(self):
        return {ProcessMode.PhaseTwist: 'Phase-twist',
                ProcessMode.AbsoluteValue: 'Absolute value',
                ProcessMode.STRIP: 'STRIP',
                ProcessMode.AmplitudeModulated: 'Amplitude-modulated'}.get(self, '')
        
        
        
class SimParams(object):
    def __init__(self, **overrides):
        self.t1Size = 1024
        self.t2Size = 1024
        self.f1MinSize = 0
        self.f2MinSize = 0
        self.dt2 = 0.001
        self.dt1 = 0.001
        self.relaxation = 1.0
        self.noiseLevel = 0.0
        self.posNoise = False
        self.resolutionEnhance = ResolutionEnhance.Never
        self.processMode = ProcessMode.STRIP
        self.loops = 15
        self.useQuickAndDirty = False
        self.noiseBox = None
        self.signalBox = None
        self.gaussianBroaden1 = None
        self.expBroaden1 = None
        self.gaussianBroaden2 = None
        self.expBroaden2 = None
        self.sineBellPhi1 = None
        self.sineBellPhi2 = None
        self.sineBellEnd1 = None
        self.sineBellEnd2 = None
        self.doShear = False
        self.shearDirection = 'anticlockwise'
        self.filterK = None
        self.filterM = None
        self.numWorkers = 6
        self.fileNameBase = 'spectrum'
        
        for key, value in overrides.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
class PlotParams(object):
    def __init__(self, **overrides):
        self.doPlot = True
        self.doZoom = False
        self.showZoom = False
        self.zoom = None
        self.plotLabel = ''
        self.plotLabelOffset = (10,10)
        self.labelSize = 30
        self.lowContourLevel = 0.05
        self.numContourLevels = 13
        self.contourMultiplier = None
        self.maxPlotValue = None
        self.plotFileName = None
        self.plotChoiceFunction = None
        self.shiftRef = None   # enter array of [freqMHz, shift, refPoint] or None  (where 'refPoint' is the index of the point in the spectrum that corresponds to 'shift' ppm)
        self.showAxis = False
        self.innerBox = None
        self.showBoxes = False
        self.mirrorBoxes = False
        self.boxesFilename = None
        self.boxesProjFilename = None
        self.multiplets = None
        
        for key, value in overrides.items():
            if hasattr(self, key):
                setattr(self, key, value)
                