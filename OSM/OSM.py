# -*- coding: utf-8 -*-
"""
@brief OSM routinh

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author: Anna Petrasova (akratoc@ncsu.edu)
"""

import os
import numpy as np
from datetime import datetime
from analyses import get_environment, match_scan
import grass.script as gscript
from grass.exceptions import CalledModuleError
import time


def run_osm(scanned_elev, scanned_color, eventHandler, env, **kwargs):
    # change these to calibrate:
    color_threshold = 140
    size_threshold = 20
    block_threshold = 10

    superpixels = 'superpixels'
    superpixels_filled = 'superpixels_filled'
    mean_color = 'mean_color'
    treatments = 'treatments'
    treatments_old = 'treatments_old'
    treatments_masked = 'treatments_masked'
    cross_test = 'cross_test'
    clump = 'clump'
    centroids = 'centroids'
    cost = 'cost'
    outdir = 'outdir'
    drain = 'drain'
    diff = 'diff'
    masked = 'masked'

    cost_layer = 'OSM_roads_speed_region_converted'
    before = 'scan_saved'
    regressed = 'regressed'
    match_scan(base=before, scan=scanned_elev, matched=regressed, env=env)
    gscript.mapcalc('{diff} = if ({a} - {b} > {t}, 1, null())'.format(a=regressed, b=before, t=block_threshold, diff=diff), env=env)


    gscript.run_command('i.superpixels.slic', input=scanned_color, output=superpixels,
                        num_pixels=100, step=10, compactness=2, minsize=30, memory=1000, env=env)
                        
    gscript.run_command('r.fill.stats', flags='k', input=superpixels, output=superpixels_filled,
                        distance=3, mode='mode', cells=6, env=env)
#                        
    gscript.mapcalc('{c} = ({r} + {g} + {b}) / 3.'.format(c=mean_color, r=scanned_color + '_r', g=scanned_color + '_g', b=scanned_color + '_b'), env=env)
#    
    data = gscript.read_command('r.univar', flags='gt', separator='comma', map=mean_color, zones=superpixels_filled, env=env).strip().splitlines()
#    
    data = np.genfromtxt(data, delimiter=',', skip_header=1)
#    
    zones = list(data[(data[:, 7] < color_threshold) & (data[:, 2] > size_threshold)][:, 0])
#    
    condition = " || ".join(['{c} == {n}'.format(c=superpixels, n=int(z)) for z in zones])
    if condition:
        gscript.mapcalc("{n} = if ({c}, 1, null()) ".format(n=treatments, c=condition), env=env)
        gscript.run_command('r.clump', flags='d', input=treatments, output=clump, env=env)
        gscript.run_command('r.volume', input=clump, clump=clump, centroids=centroids, env=env)
        points = gscript.read_command('v.out.ascii', input=centroids, format='point', env=env).strip().splitlines()
        if len(points) == 2:
            x, y, c = points[0].split('|')
            xx, yy, cc = points[-1].split('|')
            env2 = get_environment(raster=cost_layer)
            gscript.mapcalc('{m} = if(isnull({d}), {c}, null())'.format(m=masked, d=diff, c=cost_layer), env=env2)
            gscript.run_command('r.cost', input=masked, output=cost, outdir=outdir, start_coordinates=(x, y),
                                stop_coordinates=(xx, yy), flags='k', memory=1000, env=env2)
            gscript.run_command('r.drain', input=cost, output=drain, direction=outdir, flags='d', start_coordinates=(xx, yy), drain=drain, env=env2)
        else:
            print "incorrect number of felt pieces detected"
            gscript.run_command('v.edit', map=drain, tool='create', env=env)
    else:
        pass
        #gscript.run_command('v.edit', map=drain, tool='create', env=env)



   


