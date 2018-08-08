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
from popss_gui import updateDisplay


price_per_m2 = 1.24
lide = 'treeofheaven'
inf = 'infestation_2017'

def run_felt(scanned_elev, scanned_color, pops, eventHandler, env, **kwargs):
##############################
    color_threshold = 70
###############################
    size_threshold = 15
    superpixels = 'superpixels'
    superpixels_filled = 'superpixels_filled'
    mean_color = 'mean_color'
    treatments = 'treatments'
    treatments_old = 'treatments_old'
    treatments_masked = 'treatments_masked'
    cross_test = 'cross_test'

    env = get_environment(raster=scanned_elev, n='n-200')
    gscript.run_command('i.superpixels.slic', input=scanned_color, output=superpixels,
                        num_pixels=300, step=20, compactness=1, minsize=5, memory=1000, env=env)
    gscript.run_command('r.fill.gaps', flags='p', input=superpixels, output=superpixels_filled,
                        distance=3, mode='mode', cells=6, env=env)
    gscript.mapcalc('{c} = ({r} + {g} + {b}) / 3.'.format(c=mean_color, r=scanned_color + '_r', g=scanned_color + '_g', b=scanned_color + '_b'), env=env)
    data = gscript.read_command('r.univar', flags='gt', separator='comma', map=mean_color, zones=superpixels_filled, env=env).strip().splitlines()
    data = np.genfromtxt(data, delimiter=',', skip_header=1)
    zones = list(data[(data[:, 7] < color_threshold) & (data[:, 2] > size_threshold)][:, 0])
    print "detected zones:", zones
    if not zones:
        gscript.mapcalc('{t} = null()'.format(t=treatments), env=env)
        
    condition = " || ".join(['{c} == {n}'.format(c=superpixels_filled, n=int(z)) for z in zones])
    if not condition:
        event = updateDisplay(value=[0, 0])
        eventHandler.postEvent(receiver=eventHandler.popss_panel, event=event)
        return
    gscript.mapcalc("{n} = if (({lide} > 0 || {inf} > 0) && ({c}), 1, null()) ".format(lide=lide, inf=inf, n=treatments, c=condition), env=env)
    
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
            print changed_ratio
            if changed_ratio < 0.1:
                return

    except CalledModuleError:
        gscript.mapcalc('{t} = null()'.format(t=treatments), env=env)
        pass
        
#    print 'changed cells:' + str(changed_cells)
#    print 'total cells:' + str(total_cells)
   
    gscript.run_command('g.copy', raster=[treatments, treatments_old], env=env)
            
    # price
    ncells = int(gscript.parse_command('r.univar', map=treatments, flags='g', env=env)['n'])
    info = gscript.raster_info(treatments)
    res = (info['nsres'] + info['ewres'] ) / 2.
    area = ncells * res * res
    price_per_m2 = eval(pops['price'].format(pops['treatment_efficacy']))
    price  = area * price_per_m2
#    print '$' + str(price)
#    print 'acres: '+str(area* 0.000247105)
    area_miles = area * 3.86102e-7
    event = updateDisplay(value=[int(area_miles), int(price / 1e6)])
    eventHandler.postEvent(receiver=eventHandler.popss_panel, event=event)
    


    
    # TODO: dashboard
#    print time.time() - a
#    print time.time()
    # resample
#    env2 = get_environment(raster=scanned_elev, align='lide_den_int')
#    gscript.run_command('r.resamp.stats', input=treatments, output=treatments_resampled, flags='w', method='count', env=env2)
#    maxvalue = gscript.raster_info(treatments_resampled)['max']
#    gscript.mapcalc("treated_lide = {l} - {l} * ({t} / {m})".format(t=treatments_resampled, m=maxvalue, l='lide_den_int'), env=env2)
    
    


   


