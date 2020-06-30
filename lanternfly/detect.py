# -*- coding: utf-8 -*-
"""
@brief detect felt

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author: Anna Petrasova (akratoc@ncsu.edu)
"""

import os
import numpy as np
from datetime import datetime
from tangible_utils import get_environment
import grass.script as gscript
from grass.exceptions import CalledModuleError
import analyses
from pops_gui import updateDisplay



def run_felt(real_elev, scanned_elev, scanned_color, eventHandler, env, **kwargs):
    print('aaaa')
    
    
    compute_zoomed_region(real_elev, scanned_elev, kwargs['zoom_name'], env=env)
    
##############################
    color_threshold = 90
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
    data = gscript.read_command('r.univar', flags='gt', separator='comma', map=mean_color, zones=superpixels_filled, env=env).strip().splitlines()
    data = np.genfromtxt(data, delimiter=',', skip_header=1)
    zones = list(data[(data[:, 7] < color_threshold) & (data[:, 2] > size_threshold)][:, 0])
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
    pops = kwargs['pops']
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


def adjust_coordinates(points, real_elev):
    info = gscript.raster_info(real_elev)
    orig_width =  info['east'] - info['west'] 
    orig_height = info['north'] - info['south']
    orig_ratio = orig_width / orig_height
    
    width = abs(points[0][0] - points[1][0])
    height = abs(points[0][1] - points[1][1])
    ratio = width / height

    minx = min(points[0][0], points[1][0])
    miny = min(points[0][1], points[1][1])
    
    if orig_ratio > ratio:
        new_height = height
        new_width = new_height * orig_ratio
        minx = minx - (new_width - width) / 2
    else:
        new_width = width
        new_height = new_width / orig_ratio
        miny = miny - (new_height - height) / 2

    maxx = minx + new_width
    maxy = miny + new_height
    return ((minx, miny), (maxx, maxy))


def get_points(vector):
    points_raw = gscript.read_command('v.out.ascii', input=vector,
                                      type='point', format='point').strip().split()
    points = []
    for p in points_raw:
        x, y, cat = p.split('|')
        points.append((float(x), float(y)))
    return points

def compare_points(new, old, real_elev, env):
    res = gscript.read_command('v.distance', flags='p', from_=new, from_type='point',
                               to=old, to_type='point', upload='dist', separator='comma', env=env).strip()
    print(res)
    res = res.splitlines()[1:]
    total = 0
    for line in res:
        cat, dist = line.split(',')
        total += float(dist)
    
    info = gscript.raster_info(real_elev)
    width =  info['east'] - info['west'] 
    print('compare')
    print(total / width)
    if total / width > 0.1:
        return False
    return True
    

def compute_zoomed_region(real_elev, scanned_elev, zoom_name, env):
    if not zoom_name:
        return

    new_change = 'new_change'
    old_change = 'old_change'
    analyses.change_detection(before='scan_saved', after=scanned_elev,
                              change=new_change, height_threshold=[10000, 30000], cells_threshold=[5, 100],
                              add=True, max_detected=5, debug=True, env=env)
    new_points = get_points(new_change)
    if len(new_points) == 2:
        try:
            if compare_points(new_change, old_change, real_elev, env):
                minp, maxp = adjust_coordinates(new_points, real_elev)
                gscript.run_command('g.region', flags='u', n=maxp[1], s=minp[1], e=maxp[0], w=minp[0],
                                    save=zoom_name, env=env)
                gscript.run_command('g.remove', type='vector', flags='f', name=old_change, env=env)
            else:
                gscript.run_command('g.copy', vector=[new_change, old_change], env=env)
        except CalledModuleError as e:
            print(e)
            gscript.run_command('g.copy', vector=[new_change, old_change], env=env)
            #gscript.run_command('v.edit', map=tmp_adjusted, tool='create', env=env)
            
    else:
        pass
        #gscript.run_command('v.edit', map=tmp_adjusted, tool='create', env=env)
