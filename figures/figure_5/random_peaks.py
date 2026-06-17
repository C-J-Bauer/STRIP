import numpy as np
import json

def main():
    limits_x = (-100.0,+100.0)
    limits_y = (-14.0,+14.0)
    limits_relaxation = (1.0,5.0)
    limits_intensity = (0.4,1.0)
    
    peaks = []
    for i in range(100):
        
        peak = {}
        peak['id'] = i
        peak['x'] = round(np.random.uniform(limits_x[0],limits_x[1]),1) 
        peak['y'] = round(np.random.uniform(limits_y[0],limits_y[1]),1) 
        peak['relaxation'] = round(np.random.uniform(limits_relaxation[0],limits_relaxation[1]),1)
        peak['intensity'] = round(np.random.uniform(limits_intensity[0],limits_intensity[1]),1)
        peaks.append(peak)
 
    fileName = 'random_peaks.json'
    with open(fileName, 'w') as outfile:
        json.dump(peaks, outfile)       
  

if __name__ == '__main__':
    main()