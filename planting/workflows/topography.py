# -*- coding: utf-8 -*-
"""
Created on Tue Mar 28 17:32:38 2017

@author: tangible
"""

import os
import shutil
import grass.script as gscript
from grass.exceptions import CalledModuleError
from activities import updateDisplay
from tangible_utils import get_environment
from blender import blender_export_DEM

import analyses


def run_contours(real_elev, scanned_elev, eventHandler, env, **kwargs):
    gscript.run_command('r.contour', input=scanned_elev, output='contours', step=5, flags='t', env=env)


def run_dem(real_elev, scanned_elev, blender_path, eventHandler, env, **kwargs):
    gscript.run_command('g.copy', raster=[scanned_elev, 'topo_saved'], env=env)
    info = gscript.raster_info(map=scanned_elev)
    env2 = get_environment(raster=scanned_elev, res=(info['nsres'] + info['ewres']) / 4)
    gscript.run_command('r.resamp.interp', input=scanned_elev, output=scanned_elev + '_hires', method='bilinear', env=env2)
    blender_export_DEM(raster=scanned_elev + '_hires', name='terrain', time_suffix=False, path=blender_path, env=env2)

    
#==============================================================================
# Ponds
#==============================================================================
def run_water(scanned_elev, blender_path, env, eventHandler, **kwargs):
    # simwe
    gscript.mapcalc("{} = {} / 8.".format('scan10', scanned_elev), env=env)
    analyses.simwe(scanned_elev='scan10', depth='depth', rain_value=300, niterations=5, env=env)
    gscript.write_command('r.colors', map='depth', rules='-',
                          stdin='0.001 0:128:0\n0.05 0:255:255\n0.1 0:127:255\n0.5 0:0:255\n10 0:0:0', env=env)
    
    # ponds
    try:
        analyses.depression(scanned_elev=scanned_elev, new="ponds", repeat=4, filter_depth=1., env=env)
    except CalledModuleError:
        return
    gscript.mapcalc("{} = if(ponds, int(ponds + {} - 4.5), null())".format('ponds_export', scanned_elev), env=env)
    univar = gscript.read_command('r.univar', flags='t', map='ponds_export', zones='ponds_export', env=env).strip().splitlines()[1:]
    expr = 'ponds_export2 = if( '
    threshold = 40
    i = 0
    for line in univar:
        line = line.split('|')
        zone, cells = int(line[0]), int(line[2])

        if cells > threshold:
            if i > 0:
                expr += ' || '
            expr += '{} == {}'.format('ponds_export', zone)
            i += 1
    if i == 0:
        gscript.mapcalc('ponds_export2 = null()', env=env)
        blender_export_DEM(raster='ponds_export', name='water', time_suffix=False, path=blender_path, env=env)
        event = updateDisplay(value=[0, 0])
    else:
        expr += ', ponds_export, null())'
        gscript.mapcalc(expr, env=env)
        blender_export_DEM(raster='ponds_export', name='water', time_suffix=False, path=blender_path, env=env)
        info = gscript.raster_info(map='ponds_export2')
        univar = gscript.parse_command('r.univar', map='ponds_export2', flags='g', env=env)
        gscript.write_command('r.colors', map='ponds_export2', rules='-', stdin='0 149:233:232\n100 149:233:232', env=env)
     
        area = int(float(univar['n']) * info['nsres'] * info['ewres'])
        avg_depth = float(univar['mean'])
        # update dashboard
        event = updateDisplay(value=[area/10000., avg_depth])
        eventHandler.postEvent(receiver=eventHandler.activities_panel, event=event)
    
    gscript.mapcalc('water = if(!isnull(ponds_export2), ponds, null())', env=env)
    gscript.write_command('r.colors', map='water', rules='-',
                          stdin='0 0:255:255\n5 0:127:255\n20 0:0:255\n30 0:0:200\n100 0:0:100', env=env)
    gscript.mapcalc('waterall = if(!isnull(ponds_export2) || depth > 0.06, 1, null())', env=env)
    gscript.write_command('r.colors', map='waterall', rules='-',
                          stdin='1 30:144:255', env=env)                    
                           
    
