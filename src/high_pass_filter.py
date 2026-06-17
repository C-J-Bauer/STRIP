# see: Dominique Marion, Mitsuhiko Ikura, Ad Bax
# Improved solvent suppression in one- and two-dimensional NMR spectra by convolution of time-domain data
# Journal of Magnetic Resonance, 2006
# http://dx.doi.org/10.1016/j.jmr.2005.11.040
# https://spin.niddk.nih.gov/bax/lit/508/115b.pdf

import numpy as np

FILTER_K = 8
FILTER_M = 16

class HighPassFilter(object):
    def __init__(self, K=FILTER_K, M=FILTER_M):
        self.K = K
        self.M = M
        self.f_k = [0.0] * (2*K + 1)
        K2 = K * K
        A = 0.0
        for k in range(-K, K):
            self.f_k[k + K] = np.exp(-4 * k * k/K2)
            A += self.f_k[k + K]
        for k in range(-K, K):
            self.f_k[k + K] /= A

    def filter_component(self, fid):
            len = fid.shape[0]
            if self.K*2 > len:
                return fid
            K = self.K
            M = self.M
            filtered = np.zeros(len)
            for i in range(K, len - K):
                sum = 0.0
                for k in range(-K, K):
                    filtered[i] += self.f_k[k + K] * fid[i + k]
            # fill in the edges with linear extrapolation using gradients
            front_gradient = (filtered[K] - filtered[K+M])/M
            back_gradient = (filtered[-(K+1)] - filtered[-(K+M+1)])/M
            for i in range(1,K+1):
                filtered[K-i] = filtered[K] + front_gradient * i
            for i in range(K):
                filtered[-(K-i)] = filtered[-(K+1)] + back_gradient * i
                
            return filtered
        
    def filter(self, fid):
        real = self.filter_component(fid.real)
        imag = self.filter_component(fid.imag)
        return fid - (real + 1j * imag)