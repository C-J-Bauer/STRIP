import numpy as np
from scipy.signal import hilbert

# An algorithm to reduce the double dispersive component from phase modulated 2d NMR data 
# Inputs: 
#   input_spectrum: the 2d NMR spectrum data to be processed in a numpy array of complex numbers
#   loops: the number of iterations to run the algorithm. 15 should be sufficient for low-dynamic rage spectra
# Output: the processed 2d NMR data as a numpy array of real numbers
def STRIP(input_spectrum, loops=15):         
    real_input_spectrum = input_spectrum.real
    spectrum_guess = input_spectrum
        
    for _k in range(loops):
         # Only on 1st iteration is data in the spectrum_guess input to np.abs complex.
         # It is real for all following iterations.
        initial_spectrum_guess = np.abs(spectrum_guess)
        initial_dispersive_guess = B_transform(initial_spectrum_guess)
        new_spectrum_guess = real_input_spectrum - initial_dispersive_guess
        new_dispersive_guess = B_transform(new_spectrum_guess)
        average_dispersive_guess = 0.5 * (new_dispersive_guess + initial_dispersive_guess)
        spectrum_guess = real_input_spectrum - average_dispersive_guess
            
    return spectrum_guess

# This function converts a double absorbtion into a negative double dispersion and vice versa                
def B_transform(spectrum):
    h = hilbert(spectrum, axis = 0).imag
    return -hilbert(h, axis = 1).imag


# This is a quick and dirty algorithm to reduce the double dispersive component from phase modulated 2d NMR data  
# Peak shapes are improved but noise is made worse.
# Inputs: 
#   input_spectrum: the 2d NMR spectrum data to be processed in a numpy array of complex numbers
#   loops: the number of iterations to run the algorithm. 15 should be sufficient for low-dynamic rage spectra
# Output: the processed 2d NMR data as a numpy array of real numbers 
def STRIP_quick_and_dirty(input_spectrum, loops=15):          
    real_input_spectrum = input_spectrum.real
    spectrum_guess = np.abs(input_spectrum)
        
    for _k in range(loops): 
        dispersive_guess = B_transform(spectrum_guess)
        new_spectrum_guess = real_input_spectrum - dispersive_guess
        new_spectrum_guess = np.abs(new_spectrum_guess)  
        spectrum_guess = 0.5 * (new_spectrum_guess + spectrum_guess)
    return spectrum_guess
