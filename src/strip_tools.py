import numpy as np
import matplotlib.pyplot as plt
import math
from scipy.signal import hilbert
from scipy.fft import set_workers
from enum import Enum
import json
import time
from shift_ref import ShiftRef
from high_pass_filter import HighPassFilter
from boxes import Boxes, set_up_cursors
from strip_params import ResolutionEnhance, ProcessMode

# Try to use CuPy if available - otherwise use Numpy
try:
    import cupy as cp
    from strip_cupy import STRIP, STRIP_quick_and_dirty
except ImportError:
    from strip import STRIP, STRIP_quick_and_dirty


class NMRData(object):
    def __init__(self, simParams):
        self.simParams = simParams
        self.inventData()

    def get_amplitude_modulated_spectrum(self, intensity, freq1, freq2, relaxation, window1, window2):
        dt2 = self.simParams.dt2
        dt1 = self.simParams.dt1
        noiseLevel = self.simParams.noiseLevel
        t2Data = np.zeros(self.simParams.t2Size, dtype=complex)
        f1size = self.calculate_zero_filled_size(self.simParams.t1Size, self.simParams.f1MinSize)
        f2size = self.calculate_zero_filled_size(self.simParams.t2Size, self.simParams.f2MinSize)
        
        Fid2d = np.zeros((self.simParams.t1Size, self.simParams.t2Size*2), dtype=complex)
        for i in range(self.simParams.t2Size):
            sample_time = i * dt2
            decay = math.exp(-sample_time/relaxation)
            c = math.cos(2.0*np.pi*freq2*sample_time)
            s = math.sin(2.0*np.pi*freq2*sample_time)
            signal = intensity * decay * (c +  1J * s)
            if i == 0:
                t2Data[i] = 0.5 * signal
            else:
                t2Data[i] = signal
        for i in range(self.simParams.t1Size):
            noise = np.random.normal(0, noiseLevel, self.simParams.t2Size) + 1j * np.random.normal(0, noiseLevel, self.simParams.t2Size)
            fid = math.exp(-i * dt1 / relaxation) * t2Data + noise
            spec_1d = np.fft.fft(fid * window2, n=f2size)
            t1_real_modulation = math.cos(2.0*np.pi*freq1 * i * dt1)
            t1_imag_modulation = math.sin(2.0*np.pi*freq1 * i * dt1)
            if i == 0:
                Fid2d[i] = 0.5 * (t1_real_modulation * spec_1d.real + 1J * t1_imag_modulation * spec_1d.real) * window1[i]
            else:
                Fid2d[i] = (t1_real_modulation * spec_1d.real + 1J * t1_imag_modulation * spec_1d.real) * window1[i]
            
        after_f2_transform = Fid2d
        raw_spectrum = np.fft.fft(after_f2_transform, n=f1size, axis=-2)
        spectrum = np.fft.fftshift(raw_spectrum)
        
        return spectrum

    def get_phase_modulated_spectrum(self, intensity, freq1, freq2, relaxation, window1, window2):        
        t2Data = np.zeros(self.simParams.t2Size, dtype=complex)
        dt2 = self.simParams.dt2
        dt1 = self.simParams.dt1
        noiseLevel = self.simParams.noiseLevel
        f1size = self.calculate_zero_filled_size(self.simParams.t1Size, self.simParams.f1MinSize)
        f2size = self.calculate_zero_filled_size(self.simParams.t2Size, self.simParams.f2MinSize) 
        
        Fid2d = np.zeros((self.simParams.t1Size, self.simParams.t2Size), dtype=complex)
        for i in range(self.simParams.t2Size):
            sample_time = i * dt2
            decay = math.exp(-sample_time/relaxation)
            c = math.cos(2.0*np.pi*freq2*sample_time)
            s = math.sin(2.0*np.pi*freq2*sample_time)
            signal = intensity * decay * (c +  1J * s)
            if i == 0:
                t2Data[i] = 0.5 * signal
            else:
                t2Data[i] = signal
        for i in range(self.simParams.t1Size):
            noise = np.random.normal(0, noiseLevel, self.simParams.t2Size) + 1j * np.random.normal(0, noiseLevel, self.simParams.t2Size)
            t1_modulation = (math.cos(2.0*np.pi*freq1 * i * dt1) + 1j * math.sin(2.0*np.pi*freq1 * i * dt1))
            t1_decay = math.exp(-i * dt1 / relaxation)
            if i == 0:
                Fid2d[i] = 0.5 * (t1_decay * t1_modulation * t2Data + noise) * window1[i] * window2
            else:
                Fid2d[i] = (t1_decay * t1_modulation * t2Data + noise) * window1[i] * window2
             
        raw_spectrum = np.fft.fft2(Fid2d, s=[f1size, f2size])
        spectrum = np.fft.fftshift(raw_spectrum)
        return spectrum

    def inventData(self):
        self.simParams.t1Size = 1024
        self.simParams.t2Size = 4096
        window1, window2 = self.create_windows()   
        
        if self.simParams.processMode == ProcessMode.AmplitudeModulated:
            self.spectrum = self.get_amplitude_modulated_spectrum(1.0, 1.5, 15, self.simParams.relaxation, window1, window2) 
        else:
            self.spectrum = self.get_phase_modulated_spectrum(1.0, 1.5, 15, self.simParams.relaxation, window1, window2) 
              
    def create_windows(self):
        if self.simParams.resolutionEnhance != ResolutionEnhance.Never:
            if self.simParams.sineBellPhi1 !=  None:
                bellEnd = self.simParams.sineBellEnd1 or self.simParams.t1Size
                window1 = self.resolution_enhance_array_sinebell(self.simParams.t1Size, bellEnd, self.simParams.sineBellPhi1)
            else:
                window1 = self.resolution_enhance_array_gaussian(1, self.simParams.t1Size)
            if self.simParams.sineBellPhi2 !=  None:
                bellEnd = self.simParams.sineBellEnd2 or self.simParams.t2Size
                window2 = self.resolution_enhance_array_sinebell(self.simParams.t2Size, bellEnd, self.simParams.sineBellPhi2)
            else:
                window2 = self.resolution_enhance_array_gaussian(2, self.simParams.t2Size)
        else:
            window1 = np.ones(self.simParams.t1Size)
            window2 = np.ones(self.simParams.t2Size)    
        return window1, window2
                  
    def resolution_enhance_array_gaussian(self, dim, numPoints):
        if dim == 1:
            dt = self.simParams.dt1
            exp_broaden = self.simParams.expBroaden1
            gauss_broaden = self.simParams.gaussianBroaden1
        else:
            dt = self.simParams.dt2
            exp_broaden = self.simParams.expBroaden2
            gauss_broaden = self.simParams.gaussianBroaden2
        array = np.zeros(numPoints)

        if exp_broaden == None:
            exp_broaden = 0.0
        if gauss_broaden == None:
            gauss_broaden = 0.0
    
        for i in range(numPoints):
            sample_time = i * dt
            array[i] = np.exp(-(exp_broaden * sample_time) - (gauss_broaden * sample_time * sample_time)) 
        return array
    
    def resolution_enhance_array_sinebell(self, numPoints, bell_end, phi):
        """
        numPoints: Total number of points in the dataset
        bell_end: Number of points in the bell
        phi: Phase shift as a fraction of pi (0.0 to 0.5)
        """
        # Create an array of indices from 0 to N-1
        bell_end = min(bell_end, numPoints)
        n = np.arange(bell_end)
        
        # Calculate the window weights using the discrete formula
        # W(n) = sin(pi*phi + (1-phi)*pi*n/(N-1))
        weights = np.sin(np.pi * phi + (1 - phi) * np.pi * n / (bell_end - 1))
        zeros_len = numPoints - bell_end
        weights = np.append(weights, np.zeros(zeros_len))
        return weights
    
    def high_pass_filter(self, fid2d):
        if self.simParams.filterK != None:
            highPassFilter = HighPassFilter(K=self.simParams.filterK, M=self.simParams.filterM)
            for i in range(self.simParams.t1Size):
                fid2d[i] = highPassFilter.filter(fid2d[i])
    
    def post_process(self):
        if self.simParams.processMode == ProcessMode.AbsoluteValue:
            self.spectrum = np.abs(self.spectrum)
        elif self.simParams.processMode == ProcessMode.STRIP:
            with set_workers(self.simParams.numWorkers):
                print('Processing ...')
                start = time.time()
                if self.simParams.useQuickAndDirty:
                    self.spectrum = STRIP_quick_and_dirty(self.spectrum, loops=self.simParams.loops)
                else:
                    self.spectrum = STRIP(self.spectrum, loops=self.simParams.loops)
                print("Time taken: %.1f seconds" % (time.time() - start))
        if self.simParams.doShear:
            self.shear(self.simParams.shearDirection)
                  
                
    # Utility functions go here             
    def save_1d_f1(self, filename, pos, shiftRef=None):
        params = dict(
            direction = 0,
            pos = pos,
            shape = self.spectrum.shape,
            dt1 = self.simParams.dt1,
            dt2 = self.simParams.dt2,
            shiftRef = shiftRef,
        )
        line = self.spectrum[:,pos]
        self.save(dict(params=params,spectrum=line.tolist()), filename)
        
    def save_1d_f2(self, spectrum_1d, filename, pos=None, shiftRef=None):
        params = dict(
            direction = 1,
            pos = pos,
            shape = self.spectrum.shape,
            dt1 = self.simParams.dt1,
            dt2 = self.simParams.dt2,
            shiftRef = shiftRef,
        )
        self.save(dict(params=params,spectrum=spectrum_1d.real.tolist()), filename)
        
    def save(self, spectrum_1d, filename):
        with open(filename, 'w') as f:
            json.dump(spectrum_1d, f)
            
    def sum_to_1d(self, spectrum, axis=0):
        return np.sum(spectrum.real, axis)
    
            
    def find_max_row(self):
        f1Size, f2Size = self.spectrum.shape
        max = 0.0
        max_index = 0
        for i in range(f1Size):
            if np.max(self.spectrum[i]) > max:
                max = np.max(self.spectrum[i])
                max_index = i    
        return max_index
            
    def calculate_zero_filled_size(self, size, smallest=512):
        # first check if it is a power of 2.
        if size & (size-1) == 0:
            next_power_of_2 = size
        else:
            next_power_of_2 = 2**(int(np.log2(size)) + 1)
        # remember to double the size
        doubled = next_power_of_2 * 2
        return max(doubled, smallest)
    
    def phase_correction_vector(self, length, phase_zero, phase_gradient):
        correction = np.zeros(length, dtype=complex)
        angle = phase_zero * np.pi / 180.0
        gradient_scaling = phase_gradient * np.pi / (180.0 * length)
        for i in range(length):
            correction[i] = np.exp(-1j * (angle + gradient_scaling * i))
        return correction
        
    def signal_to_noise(self, title, pos_noise=False):
        print(title)
        real = self.spectrum.real
        noiseBox = self.simParams.noiseBox
        signalBox = self.simParams.signalBox
        std_dev_mean = np.mean(real[noiseBox[0]:noiseBox[2], noiseBox[1]:noiseBox[3]])
        signal_plus = np.max(real[signalBox[0]:signalBox[2], signalBox[1]:signalBox[3]])
        signal_min = np.min(real[signalBox[0]:signalBox[2], signalBox[1]:signalBox[3]])
        signal = np.max([signal_plus, -signal_min])
        print("signal = %f" % signal)
        
        if pos_noise:
            sample_data = real[noiseBox[0]:noiseBox[2], noiseBox[1]:noiseBox[3]].flatten()
            noise_mean = np.mean(sample_data)
            sample_data = sample_data[sample_data > 0]
            noise = np.std(sample_data)
        else:
            noise = np.std(real[noiseBox[0]:noiseBox[2], noiseBox[1]:noiseBox[3]], mean=std_dev_mean)
            noise_mean = np.mean(real[noiseBox[0]:noiseBox[2], noiseBox[1]:noiseBox[3]])
        print("noise = %f (noise mean = %f)" % (noise, noise_mean))
        
        snr = signal/noise
        print("SNR = %.2f\n\n" % snr)
        return snr
    
    def late_resolution_enhance(self):
        (f1size, f2size) = self.spectrum.shape
        window1, window2 = self.create_windows()
        window1 = np.pad(window1, (0, f1size - window1.size), mode='constant')
        window2 = np.pad(window2, (0, f2size - window2.size), mode='constant')
        spec_complex = np.zeros(self.spectrum.shape, dtype=complex)
        # recreate imaginary part and enhance f2
        spec_complex.real = self.spectrum.real
        spec_complex.imag = -hilbert(self.spectrum.real, axis=1).imag
        time_domain = np.fft.ifft(spec_complex, axis = 1)
        for i in range(f1size):
            time_domain[i] = time_domain[i] * window2
        self.spectrum = np.fft.fft(time_domain, axis = 1)
        
        # recreate imaginary part and enhance f1
        spec_complex.real = self.spectrum.real
        spec_complex.imag = -hilbert(self.spectrum.real, axis=0).imag
        time_domain = np.fft.ifft(spec_complex, axis =0)
        for i in range(f2size):
            time_domain[:,i] = time_domain[:,i] * window1
        spec_complex = np.fft.fft(time_domain, axis = 0)
        
        self.spectrum = spec_complex.real
        
    def shear(self, direction):
        f1Size, f2Size = self.spectrum.shape
        shear_ratio = (f2Size * self.simParams.dt2) / (f1Size * self.simParams.dt1)
        middle = f1Size // 2
        if direction == "clockwise":
            for i in range(self.spectrum.shape[0]):
                distance_from_middle = i - middle
                self.spectrum[i,:] = np.roll(self.spectrum[i,:], round(distance_from_middle * shear_ratio))
        elif direction == "anticlockwise":
            for i in range(self.spectrum.shape[0]):
                distance_from_middle = i - middle
                self.spectrum[i,:] = np.roll(self.spectrum[i,:], round(-distance_from_middle * shear_ratio))
            
    def simulate(self, plotter):
        if self.simParams.noiseLevel > 0.0:
            normal = self.signal_to_noise('Phase twist:', self.simParams.posNoise)
            self.post_process()
            processed = self.signal_to_noise('After post processing:', self.simParams.posNoise)
            percent_improvement = 100*(processed/normal - 1.0)
            print("Signal to noise ratio improved: %.2f%%" % percent_improvement)
        else:
            self.post_process()
        if self.simParams.resolutionEnhance == ResolutionEnhance.Late:
            self.late_resolution_enhance()
        if plotter.plotParams.plotChoiceFunction:
            self.spectrum = plotter.plotParams.plotChoiceFunction(self.spectrum)
        if plotter.plotParams.doPlot:
            plotter.plot_spectrum(self)
        return self.spectrum


class Plotter(object):
    def __init__(self, plotParams):
        self.plotParams = plotParams
    
        
    def plot_spectrum(self, nmrData):  
        #plt.style.use('_mpl-gallery')
        output = nmrData.spectrum.real
        shape = output.shape
        f1_points = shape[0]
        f2_points = shape[1]
        f1_axis_pos = f1_points/2.0
        show_zoom = False
        zoom = self.plotParams.zoom
        innerBox = self.plotParams.innerBox
        show_axis = self.plotParams.showAxis
        showBoxes = self.plotParams.showBoxes
        shiftRef = self.plotParams.shiftRef
        if showBoxes:
            boxes = Boxes(self.plotParams.boxesFilename,
                          self.plotParams.boxesProjFilename,
                          output,
                          self.plotParams.doZoom,
                          zoom,
                          self.plotParams.mirrorBoxes)
            
        if self.plotParams.maxPlotValue:
            maxValue = self.plotParams.maxPlotValue
        else:
            maxValue = np.max(np.abs(output))
            
        if self.plotParams.doZoom:
            output = output[zoom[0]:zoom[2], zoom[1]:zoom[3]]
            f2_points = zoom[3] - zoom[1]
            if self.plotParams.showAxis:
                zoomed_f1_points = zoom[2] - zoom[0]
                #scaling = zoomed_f1_points/f1_points
                shift = zoom[0]
                f1_axis_pos = f1_axis_pos - shift
                if f1_axis_pos < 0 or f1_axis_pos > (f1_points-1):
                    show_axis = False          
        elif self.plotParams.showZoom:
            show_zoom = True
        
        colours = []
        low_level_contour = self.plotParams.lowContourLevel
        num_levels = self.plotParams.numContourLevels
        if self.plotParams.contourMultiplier:
            next_contour = low_level_contour * maxValue
            log_contour_levels = []
            for i in range(num_levels):
                log_contour_levels.append(next_contour)
                next_contour = next_contour * self.plotParams.contourMultiplier
            negative_contour_levels = np.flip(log_contour_levels) * -1.0
        else:
            log_contour_levels = np.logspace(np.log10(low_level_contour),0.0, num_levels) * maxValue
            negative_contour_levels = np.flip(log_contour_levels) * -1.0
        levels = np.concatenate((negative_contour_levels, log_contour_levels))

        for i in levels:
            if i < 0:
                colours.append('red')
            else:
                colours.append('black')

        fig = plt.figure()
        ax = fig.subplots()
        cs = plt.contour(output, levels=levels, colors=colours)
        cs.cmap.set_under('red')
        cs.axes.set_yticks([])
        if show_zoom:
            # draw a blue rectangle
            plt.plot([zoom[1], zoom[1], zoom[3], zoom[3], zoom[1]], [zoom[0], zoom[2], zoom[2], zoom[0], zoom[0]], 'b-')
        elif innerBox:
            # draw a blue rectangle
            plt.plot([innerBox[1], innerBox[1], innerBox[3], innerBox[3], innerBox[1]], [innerBox[0], innerBox[2], innerBox[2], innerBox[0], innerBox[0]], 'b-')
            # create smaller matrix deescribed by inner box
            small = output[innerBox[0]:innerBox[2], innerBox[1]:innerBox[3]]
            # print maximum value in small matrix
            print("MaxValue = %f" % np.max(small))
        if showBoxes:
            boxes.plot_boxes(plt)
        if show_axis:
            # draw a black horizontal line at f1_axis_pos
            plt.plot([0, f2_points-1], [f1_axis_pos, f1_axis_pos], 'k-')
        if self.plotParams.plotLabel:
            plt.text(self.plotParams.plotLabelOffset[0],
                     self.plotParams.plotLabelOffset[1],
                     self.plotParams.plotLabel,
                     size=self.plotParams.labelSize,
                     color='black')

        if shiftRef:
            shape = nmrData.spectrum.shape
            sw = 1.0/nmrData.simParams.dt2
            if self.plotParams.doZoom:
                firstPoint = zoom[1]
            else:
                firstPoint = 0
            ref = ShiftRef(shiftRef[0], shiftRef[1], shiftRef[2], sw, firstPoint, shape[1])   
            axis = plt.gca()
            secax = axis.secondary_xaxis('bottom', functions=(ref.point_to_ppm, ref.ppm_to_point))
            axis.tick_params(axis='x', which='both', bottom=False, labelbottom=False)
        else:
            cs.axes.set_xticks([])
            
        plt.tight_layout()
        if self.plotParams.plotFileName:
            plt.savefig(self.plotParams.plotFileName)
        else:
            if showBoxes:
                set_up_cursors(plt, ax, fig, boxes)          
            plt.show()
        plt.close()