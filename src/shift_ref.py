class ShiftRef(object):
    def __init__(self, freqMHz, shift, refPoint, sw=10000.0, firstPoint=0, numPoints=16384):
        self.freqMHz = freqMHz
        self.shift = shift
        self.refPoint = refPoint
        self.sw = sw
        self.firstPoint = firstPoint
        self.numPoints = numPoints
        self.freqPerPoint = self.sw/self.numPoints
        self.ppmPerPoint = self.freqPerPoint/self.freqMHz
        
    def point_to_ppm(self, point):
        return self.shift - (self.firstPoint + point - self.refPoint) * self.ppmPerPoint
    
    def ppm_to_point(self, ppm):
        return self.refPoint + (self.shift - ppm) / self.ppmPerPoint + self.firstPoint
        

    
    