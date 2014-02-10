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

BASE64_HTML_IMG = '''
    <html>
        <body>
            <img src="data:image/png;base64,{}" />
        </body>
    </html>
    ''' 

def shot_chart_matplotlib(made_x, made_y, miss_x, miss_y):
    # Need to correct for native coordinate system
    fig = plt.figure()
    plt.scatter(miss_y, map(lambda x: 51-x, miss_x), marker='x')
    plt.scatter(made_y, map(lambda x: 51-x, made_x), marker='o')
    plt.xlim(0,96)   
    
    # Encode image to png in base64
    # Source: http://pythonwise.blogspot.com/2013/04/serving-dynamic-images-with-matplotlib.html
    io = StringIO()
    fig.savefig(io, format='png')
    data = io.getvalue().encode('base64')
    return BASE64_HTML_IMG.format(data)

def shot_freq_map_matplotlib(x, y, freq, label=False):
    x, y, z = map(np.array, [x, y, freq])
    res = 250
    
    X_MIN = 0
    X_MAX = 50
    Y_MIN = 0
    Y_MAX = 48
    
    # Increase resolution
    xi, yi = np.linspace(x.min(), x.max(), res), np.linspace(y.min(), y.max(), res)
    xi, yi = np.meshgrid(xi, yi)
    
    # Use radial basis functions to do interpolation
    rbf = scipy.interpolate.Rbf(x, y, z, function='linear')
    zi = rbf(xi, yi)
    
    # Plot freq map
    fig = plt.figure()
    plt.imshow(zi, extent=[x.min(), x.max(), y.min(), y.max()], origin='lower', vmin=z.min(), vmax=z.max(), cmap=plt.cm.get_cmap('Reds'))

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
    plt.xlim(0,50)
    plt.ylim(1,48)
    plt.colorbar()
    
    if label:
        for X, Y, Z in zip(x, y, z):
            plt.annotate('{}'.format(Z), xy=(X,Y))
    
    # Encode image to png in base64
    # Source: http://pythonwise.blogspot.com/2013/04/serving-dynamic-images-with-matplotlib.html
    io = StringIO()
    fig.savefig(io, format='png')
    data = io.getvalue().encode('base64')
    return BASE64_HTML_IMG.format(data)
    
    