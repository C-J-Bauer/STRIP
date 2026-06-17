import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path

# Try to use CuPy if available - otherwise use Numpy
try:
    import cupy as cp
    from strip_cupy import STRIP, STRIP_quick_and_dirty
except ImportError:
    from strip import STRIP, STRIP_quick_and_dirty


NOISE_LEVEL = 100  # alter this to change noise amplitude

SIGNAL_SQUARE = (1000, 1250)  # where in data set to look for largest peak
NOISE_SQUARE = (250, 500)    # where in data set to sample noise

curr_dir = Path(__file__).resolve().parents[0]

def here(fileName):
    return os.path.join(curr_dir, fileName)

class NMRData(object):
    def __init__(self):
        self.inventData()

    def inventData(self):
        self.t1Size = 1024
        self.t2Size = 1024
        
        
        noiseLevel = NOISE_LEVEL
        Fid2d = np.zeros((self.t1Size, self.t2Size), dtype=complex)
        for i in range(self.t1Size):
            noise = np.random.normal(0, noiseLevel, self.t2Size) + 1j * np.random.normal(0, noiseLevel, self.t2Size)
            if i == 0:
                Fid2d[i] = 0.5 * noise
            else:
                Fid2d[i] =  noise
             
        after_f2_transform = np.fft.fft(Fid2d, n=self.t2Size*2, axis=-1)
        raw_spectrum = np.fft.fft(after_f2_transform, n=self.t1Size*2, axis=-2)
        self.spectrum = np.fft.fftshift(raw_spectrum)
                
        self.spectrum = raw_spectrum      
        shape = self.spectrum.shape
        self.f1Size = shape[0]
        self.f2Size = shape[1]
            
                        
def calc_noise(row):
    sample_data = row.flatten()
    mean = np.mean(sample_data)
    positive_data = sample_data[sample_data > mean] - mean
    noise_positive = np.std(positive_data, mean = 0.0)
    negative_data = sample_data[sample_data < mean] - mean
    noise_negative = np.std(negative_data, mean = 0.0)
    return noise_positive, noise_negative, mean

def create_plot(plot_ref, data, id, maxValue, minValue, noise_dict, highText=True):
    x =  np.arange(len(data))
    y = data
    plot_ref.plot(x, y)
    plot_ref.set_xticks([])
    plot_ref.set_yticks([])
    plot_ref.set_ylim([minValue, maxValue])
    if highText:
        plot_ref.text(10, 0.8*maxValue, f'{id}', size=40, color='black')
    else:
        plot_ref.text(10, 0.9*minValue, f'{id}', size=40, color='black')
    noise_positive, noise_negative, mean = noise_dict[id][2], noise_dict[id][3], noise_dict[id][4]
    plot_ref.hlines(y=[mean], xmin=0, xmax=len(data), colors=['w'])
    plot_ref.hlines(y=[mean+noise_positive, 0, mean-noise_negative], xmin=0, xmax=len(data), colors=['r', 'k', 'r'])


def plot_spectrum(originalRow, improvedRow, quick_improvedRow, abs_valueRow, noise_dict):  
    plt.style.use('_mpl-gallery')
    plt.rcParams["figure.figsize"] = (18, 10)


    maxOriginal = np.max(np.abs(originalRow))
    maxImproved = np.max(np.abs(improvedRow))
    maxQuick = np.max(np.abs(quick_improvedRow))
    maxAbs = np.max(np.abs(abs_valueRow))
    maxValue = np.max([maxOriginal, maxImproved, maxQuick, maxAbs])

    minOriginal = np.min(originalRow)
    minImproved = np.min(improvedRow)
    minQuick = np.min(quick_improvedRow)
    minAbs = np.min(abs_valueRow)
    minValue = np.min([minOriginal, minImproved, minQuick, minAbs])
    
    
    fig = plt.figure(layout="constrained")
    ax_array = fig.subplots(2, 2, squeeze=False)
    create_plot(ax_array[0][0], originalRow, "Untreated", maxValue, minValue, noise_dict)
    create_plot(ax_array[0][1], abs_valueRow, "Absolute value", maxValue, minValue, noise_dict)
    create_plot(ax_array[1][0], improvedRow, "STRIP", maxValue, minValue, noise_dict, False)
    create_plot(ax_array[1][1], quick_improvedRow, "STRIP QD", maxValue, minValue, noise_dict, False)
  
    fig.savefig(here("Figure_6.png"))

    plt.show()


def noise_calc(spectrum, title):    
    print("\n\nNoise calculations for %s" % title)
    as_1d = spectrum.flatten()
    mean = np.mean(as_1d)
    noise_mean_0 = np.std(as_1d, mean = 0.0)
    noise = np.std(as_1d)
    positive_sided = as_1d[as_1d > mean] - mean
    negative_sided = as_1d[as_1d < mean] - mean
    
    noise_positive_sided = np.std(positive_sided, mean = 0.0)
    noise_negative_sided = np.std(negative_sided, mean = 0.0)
    print("Noise = %.3f" % noise)
    print("Noise mean at zero = %.3f" % noise_mean_0)
    print("Noise positive side = %.3f" % noise_positive_sided)
    print("Noise negative side = %.3f" % noise_negative_sided)
    print("Mean = %.3f" % mean)
    return noise, noise_mean_0, noise_positive_sided, noise_negative_sided, mean


def noise_compare(noise_data, title, baseline_noise_data):
    print("%s: Noise = %.3f" % (title, noise_data[0]/baseline_noise_data[0]))
    print("%s: Noise mean at zero = %.3f" % (title, noise_data[1]/baseline_noise_data[1]))
    print("%s: Noise positive side = %.3f" % (title, noise_data[2]/baseline_noise_data[2]))
    print("%s: Noise negative side = %.3f" % (title, noise_data[3]/baseline_noise_data[3]))

def main():
    nmrData = NMRData()
    real = nmrData.spectrum.real
    abs_value = np.abs(nmrData.spectrum)
    improved = STRIP(real, loops=15) 
    improved_quick = STRIP_quick_and_dirty(real, loops=15)

    real_noise= noise_calc(real, "phase_twist")
    improved_noise = noise_calc(improved, "improved")
    improved_quick_noise = noise_calc(improved_quick, "improved_quick")
    abs_value_noise = noise_calc(abs_value, "abs_value")

    noise_dict = {
        "Untreated": real_noise,
        "Absolute value": abs_value_noise,
        "STRIP": improved_noise,
        "STRIP QD": improved_quick_noise,
    }

    print("\n\nNoise compared to phase twist:")
    noise_compare(real_noise, "phase_twist", real_noise)
    noise_compare(improved_noise, "improved", real_noise)
    noise_compare(improved_quick_noise, "improved_quick", real_noise)
    noise_compare(abs_value_noise, "abs_value", real_noise)

    print("\n\nNoise compared to STRIP:")
    noise_compare(real_noise, "phase_twist", improved_noise)
    noise_compare(improved_noise, "improved", improved_noise)
    noise_compare(improved_quick_noise, "improved_quick", improved_noise)            
    noise_compare(abs_value_noise, "abs_value", improved_noise)

    print("\n\nNoise compared to abs_value:")
    noise_compare(real_noise, "phase_twist", abs_value_noise)
    noise_compare(improved_noise, "improved", abs_value_noise)
    noise_compare(improved_quick_noise, "improved_quick", abs_value_noise)            
    noise_compare(abs_value_noise, "abs_value", abs_value_noise)


    shape = improved.shape
    # pick a randon row
    row = np.random.randint(0, shape[0])
    plot_spectrum(real[row], improved[row], improved_quick[row], abs_value[row], noise_dict)


if __name__ == '__main__':
    main()