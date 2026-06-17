# read a json file containing a 1d spectrum and plot it in matplotlib

import numpy as np
import matplotlib.pyplot as plt
import json
import os
from pathlib import Path
import sys
from shift_ref import ShiftRef
import argparse


curr_dir = Path(__file__).resolve().parents[0]

def here(fileName):
    return os.path.join(curr_dir, fileName)


def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', '--expand', help='scale multiplication factor', type=float, default=1.0)
    parser.add_argument('-z', '--zoom', help='zoom window', type=int, nargs=2)
    parser.add_argument('-s', '--scale_zoom', help='scale zoom window', type=float, nargs=2)   
    parser.add_argument('filename', help='name of file to display', nargs='?', default='shift_only.json')
    args = parser.parse_args()
    filename = here(args.filename)
    expand = args.expand
    scale_zoom = args.scale_zoom
    zoom = args.zoom
    
    if zoom and scale_zoom:
        raise ValueError('cannot specify both zoom and scale_zoom')

    with open(filename, 'r') as f:
        data = json.load(f)
    params = data['params']
    spectrum = np.array(data['spectrum'])
    max_val = np.max(spectrum)
    max_val = max_val / expand
    min_val = -0.1 * max_val
    
    sw = 1.0/params['dt2']
    spectrum = np.array(spectrum)
    numPoints = len(spectrum)
    if params['shiftRef']:
        sr = params['shiftRef']
        shiftRef = ShiftRef(sr[0], sr[1], sr[2], sw=1.0/params['dt2'], firstPoint=0, numPoints=params['shape'][1])
    else:
        if scale_zoom and params['direction'] == 1:
            raise ValueError('cannot specify scale_zoom without shiftRef')
        shiftRef = None 
        
    ppm = None
    if params['direction'] == 0:
        if shiftRef:
            ppm = shiftRef.point_to_ppm(params['pos'])
        shiftRef = ShiftRef(1, 0.0, numPoints/2, sw=1.0/params['dt1'], firstPoint=0, numPoints=params['shape'][0]) 
        
        
    plt.ylim([min_val, max_val])
    if zoom:
        plt.xlim(zoom)
    elif scale_zoom:
        plt.xlim(shiftRef.ppm_to_point(scale_zoom[0]), shiftRef.ppm_to_point(scale_zoom[1]))
    xvals = range(len(spectrum))
    plt.plot(xvals, spectrum)
    if shiftRef:
        axis = plt.gca()
        secax = axis.secondary_xaxis('bottom', functions=(shiftRef.point_to_ppm, shiftRef.point_to_ppm))
        axis.tick_params(axis='x', which='both', bottom=False, labelbottom=False)
    else:
        plt.plot(xvals, spectrum)
    if ppm!=None:
        plt.text(0, 0.8*min_val, f'{ppm:.2f} ppm', size=10, color='black')
        
    plt.show()
    
    
if __name__ == '__main__':
    main()