# -*- coding: utf-8 -*-
"""
@brief experiment_cutfill2

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author: Anna Petrasova (akratoc@ncsu.edu)
"""

import os
import numpy as np
from datetime import datetime
from analyses import get_environment
import grass.script as gscript
from grass.exceptions import CalledModuleError
import time
from pops_gui import updateDisplay



def run_felt(scanned_elev, scanned_color, pops, eventHandler, env, **kwargs):
##############################
    color_threshold = 60
###############################
    size_threshold = 10
    superpixels = 'superpixels'
    superpixels_filled = 'superpixels_filled'
    mean_color = 'mean_color'
    treatments = 'treatments'
    treatments_old = 'treatments_old'
    treatments_masked = 'treatments_masked'
    cross_test = 'cross_test'

    env = get_environment(raster=scanned_elev, n='n-200')
    gscript.run_command('i.superpixels.slic', input=scanned_color, output=superpixels,
                        step=8, perturb=10, compactness=1, minsize=10, memory=1000, env=env)
    gscript.run_command('r.fill.stats', flags='k', input=superpixels, output=superpixels_filled,
                        distance=3, mode='mode', cells=6, env=env)
    gscript.mapcalc('{c} = ({r} + {g} + {b}) / 3.'.format(c=mean_color, r=scanned_color + '_r', g=scanned_color + '_g', b=scanned_color + '_b'), env=env)
    data = gscript.read_command('r.univar', flags='egt', separator='comma', map=mean_color, zones=superpixels_filled, env=env).strip().splitlines()
    data = np.genfromtxt(data, delimiter=',', skip_header=1)
    #zones = list(data[(data[:, 7] < color_threshold) & (data[:, 2] > size_threshold)][:, 0])
    zones = list(data[(data[:, 15] < color_threshold) & (data[:, 2] > size_threshold)][:, 0])
    #print "detected zones:", zones
    if not zones:
        gscript.mapcalc('{t} = null()'.format(t=treatments), env=env)
        
    condition = " || ".join(['{c} == {n}'.format(c=superpixels_filled, n=int(z)) for z in zones])
    if not condition:
        event = updateDisplay(area=0)
        eventHandler.postEvent(receiver=eventHandler.pops_panel, event=event)
        return
    #gscript.mapcalc("{n} = if (({lide} > 0 || {inf} > 0) && ({c}), 1, null()) ".format(lide=lide, inf=inf, n=treatments, c=condition), env=env)
    gscript.mapcalc("{n} = if ({c}, 1, null()) ".format(n=treatments, c=condition), env=env)
    
    try:
        # is treatments_old doesn't exist, ignore this
        gscript.run_command('r.cross', input=[treatments, treatments_old], output=cross_test, env=env)
        
        stats = gscript.read_command('r.stats', flags='cn', input=cross_test, env=env).strip().splitlines()
        changed_cells = total_cells = 0
        for line in stats:
            cat, ncells = line.split(' ')
            if cat in ('0', '1'):
                changed_cells += int(ncells)
            else:
                total_cells = int(ncells)

        if total_cells > 0:
            changed_ratio = changed_cells / float(total_cells)
            #print changed_ratio
            if changed_ratio < 0.2:
                return

    except CalledModuleError:
        gscript.mapcalc('{t} = null()'.format(t=treatments), env=env)
        gscript.mapcalc('{t} = null()'.format(t=treatments_old), env=env)
        event = updateDisplay(area=0)
        eventHandler.postEvent(receiver=eventHandler.pops_panel, event=event)
        
#    print 'changed cells:' + str(changed_cells)
#    print 'total cells:' + str(total_cells)
   
    gscript.run_command('g.copy', raster=[treatments, treatments_old], env=env)
            
    # price
    gscript.mapcalc("{n} = if ({host} > 0, {t}, null())".format(host=pops['model']['host'], t=treatments, n=treatments + '_exclude_host_tmp'), env=env)
    univar = gscript.parse_command('r.univar', map=treatments + '_exclude_host_tmp', flags='g', env=env)
    if univar and 'n' in univar:
        ncells = int(univar['n'])
        info = gscript.raster_info(treatments)
        res = (info['nsres'] + info['ewres'] ) / 2.
        area = ncells * res * res
    else:
        area = 0
    event = updateDisplay(area=area)
    eventHandler.postEvent(receiver=eventHandler.pops_panel, event=event)


