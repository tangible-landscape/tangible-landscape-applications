# -*- coding: utf-8 -*-
"""
Created on Tue Mar 28 17:32:38 2017

@author: tangible
"""

import os
import shutil
import glob
from math import sqrt
from os.path import expanduser
import grass.script as gscript
from grass.exceptions import CalledModuleError
from activities import updateDisplay, updateProfile
from TSP import solve_tsp_numpy
from tangible_utils import get_environment

import analyses

PATH = '/run/user/1000/gvfs/smb-share:server=192.168.0.2,share=coupling/Watch/'


def dist(points, i, j):
    x2 = (points[i][0] - points[j][0]) * (points[i][0] - points[j][0])
    y2 = (points[i][1] - points[j][1]) * (points[i][1] - points[j][1])
    return sqrt(x2 + y2)


def run_trails(real_elev, scanned_elev, eventHandler, env, **kwargs):
    env2 = get_environment(raster=scanned_elev, n='n-100', s='s+100', e='e-100', w='w+100')
    resulting = 'trail'
    trail = 'trail'
    before = 'scan_saved'
    topo_saved = 'topo_saved'
    #env_crop = get_environment(raster=real_elev, n='n-100', s='s+100', e='e-100', w='w+100')
    analyses.change_detection(before=before, after=scanned_elev,
                              change='change', height_threshold=[15, 100], cells_threshold=[5, 100], add=True, max_detected=13, debug=True, env=env2)
    points = {}
    # start and end
    data = gscript.read_command('v.out.ascii', input='trail_points', type='point', format='point', env=env).strip()
    c1, c2 = data.splitlines()
    c1 = c1.split('|')
    c2 = c2.split('|')
    points[0] = (float(c1[0]), float(c1[1]))
    points[1] = (float(c2[0]), float(c2[1]))

    gscript.run_command('v.edit', tool='create', map=trail, env=env)
    # detected points
    points_raw = gscript.read_command('v.out.ascii', input='change',
                                      type='point', format='point').strip().split()
    i = 2
    for point in points_raw:
        point = point.split('|')
        point = (float(point[0]), float(point[1]))
        points[i] = point
        i += 1
    length = len(points)
    if length == 2:
        gscript.mapcalc("{} = null()".format(resulting), env=env)
        event = updateProfile(points=[])
        eventHandler.postEvent(receiver=eventHandler.activities_panel, event=event)
        return

    # distance matrix
    D = []
    for i in range(length):
        D.append([0] * length)
    for p1 in range(0, length - 1):
        for p2 in range(p1 + 1, length):
            d = dist(points, p1, p2)
            D[p1][p2] = d
            D[p2][p1] = d
    # 0 distance for start and end to make sure it's always connected
    D[0][1] = 0
    D[1][0] = 0

    # solve
    solution = solve_tsp_numpy(D, optim_steps=10)
    # rearange solutions to start in start point
    ind1 = solution.index(0)
    ind2 = solution.index(1)
    if ind2 > ind1:
        solution = solution[::-1]
    ind = solution.index(0)
    solution = solution[ind :] + solution[:ind ]
    profile_points = []
    for i in solution:
        profile_points.append(points[i])
    #return
    # friction
    friction = 'friction'
    #gscript.mapcalc('{} = if(isnull(water), 0, null())'.format(friction), env=env)
    gscript.mapcalc('{} = 0'.format(friction), env=env)
    tmp_dir = 'tmp_dir'
    tmp_cost = 'tmp_cost'
    tmp_drain = 'tmp_drain'
    
    gscript.run_command('v.edit', tool='create', map=trail, env=env)
    for i in range(len(solution) - 1):
        gscript.run_command('r.walk', elevation=topo_saved, friction=friction, output=tmp_cost, outdir=tmp_dir,
                            start_coordinates=points[solution[i]], stop_coordinates=points[solution[i+1]], flags='k',
                            env=env)
        gscript.run_command('r.drain', input=tmp_cost, direction=tmp_dir, output=tmp_drain,
                            drain=tmp_drain, start_coordinates=points[solution[i+1]], flags='d', env=env)
        gscript.run_command('v.patch', input=tmp_drain, output=trail, flags='a', env=env)


    env2 = get_environment(raster=topo_saved)
    # slope along line
    gscript.run_command('v.to.rast', input=trail, type='line', output='trail_dir', use='dir', env=env2)
    gscript.run_command('r.slope.aspect', elevation=topo_saved, slope='saved_slope', aspect='saved_aspect', env=env2)
    gscript.mapcalc("slope_dir = abs(atan(tan({slope}) * cos({aspect} - {trail_dir})))".format(slope='saved_slope', aspect='saved_aspect',
                    trail_dir='trail_dir'), env=env2)
    # set new color table
    colors = ['0 green', '5 green', '5 yellow', '15 yellow', '15 red', '90 red']
    gscript.write_command('r.colors', map='slope_dir', rules='-', stdin='\n'.join(colors), env=env2)
    # increase thickness
    gscript.run_command('r.grow', input='slope_dir', radius=1.1, output=resulting, env=env2)
    

    # update profile
    event = updateProfile(points=profile_points)
    eventHandler.postEvent(receiver=eventHandler.activities_panel, event=event)
    
    gscript.mapcalc('toponds = if ( isnull(ponds), {t}, ponds + {t})'.format(t=topo_saved), env=env)
    gscript.run_command('v.generalize', input=trail, type='line', output=trail + 'gen', method='snakes', threshold=100, env=env)
    gscript.run_command('g.rename', vector=[trail + 'gen', trail], env=env)
    gscript.run_command('v.drape', input=trail, output=trail + '3d', elevation='toponds', env=env)
    export_shp(trail + '3d', trail, env)


def export_shp(vector, name, env):
    tmp_directory = '/tmp/trail'
    try:
        shutil.rmtree(tmp_directory)
    except:
        pass  
    if not os.path.exists(tmp_directory):
        os.mkdir(tmp_directory)

    try:
        gscript.run_command('v.out.ogr', input=vector, lco="SHPT=ARCZ",
                            output=tmp_directory + '/' + name + '.shp', env=env)
    except CalledModuleError, e:
        print e
        return
    for each in glob.glob(tmp_directory + '/' + name + '.*'):
        ext = each.split('.')[-1]
        try:
            shutil.copyfile(each,  PATH + name + '.' + ext)
        except OSError as e:
            if e.errno == 95:
                pass
