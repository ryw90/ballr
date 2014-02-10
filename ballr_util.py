# -*- coding: utf-8 -*-
"""
    Ballr-utilities
    ~~~~~~

    Utility functions for processing ballr data

    by Ryan Wang (2013)
"""

import matplotlib.pyplot as plt
from cStringIO import StringIO
import numpy as np
import scipy.interpolate
import matplotlib.patches

XMIN = 1
XMAX = 50
YMIN = 1
YMAX = 48

def gen_court():
    fig = plt.figure()
    
    # Add 3 Point Line
    plt.plot([47, 47], [0, 14], 'k-')
    plt.plot([3, 3], [0, 14], 'k-')
    plt.axes().add_patch(matplotlib.patches.Arc(xy=(25,14), width=44, height=31, angle=0, theta1=0, theta2=180))

    # Add free throw lane
    plt.plot([31, 31], [0, 19], 'k-')
    plt.plot([19, 19], [0, 19], 'k-')
    plt.plot([19, 31], [19, 19], 'k-')
    plt.axes().add_patch(plt.Circle(xy=(25,19), radius=6, fill=False))
    
    # Set axes
    plt.xlim(XMIN, XMAX)
    plt.ylim(YMIN, YMAX)
    
    return fig

def heat_map_hist(x, y, freq):
    '''
    TODO: Figure out what's going on with coordinates
    x, y, z = map(np.array, [x, y, freq])
    H, xedges, yedges = np.histogram2d(x=x, y=y, weights=freq, bins=15)
    
    fig = gen_court()
    plt.imshow(H, cmap=plt.cm.get_cmap('Oranges'), extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]])
    plt.colorbar()
    '''
    pass
    
def heat_map_rbf(x, y, freq, label=False):
    x, y, z = map(np.array, [x, y, freq])
    
    # TO DO: Include options for lower-resolution grid
    # agg = 3.0
    # x_g3 = np.ceil(shots.x/agg)*agg-agg/2
    # y_g3 = np.ceil(shots.y/agg)*agg-agg/2
    # z_g3 = ...
    
    # Create grid
    res = 100
    xi, yi = np.linspace(XMIN, XMAX, res), np.linspace(YMIN, YMAX, res)
    xi, yi = np.meshgrid(xi, yi)
    
    # Use radial basis functions to do interpolation
    rbf = scipy.interpolate.Rbf(x, y, z, function='linear')
    zi = rbf(xi, yi)
    
    # Plot freq map
    fig = gen_court()
    plt.imshow(zi, extent=[xi.min(), xi.max(), yi.min(), yi.max()], origin='lower', vmin=z.min(), vmax=z.max(), cmap=plt.cm.get_cmap('YlGn'))
    plt.colorbar()
    
    if label:
        for X, Y, Z in zip(x, y, z):
            plt.annotate('{}'.format(Z), xy=(X,Y))
    
    # Encode image to png in base64
    # Source: http://pythonwise.blogspot.com/2013/04/serving-dynamic-images-with-matplotlib.html    
    io = StringIO()
    fig.savefig(io, format='png')    
    return io.getvalue().encode('base64')
    