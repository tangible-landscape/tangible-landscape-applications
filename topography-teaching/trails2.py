# -*- coding: utf-8 -*-
"""
@brief experiment_trailsB

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author: Anna Petrasova (akratoc@ncsu.edu)
"""
from datetime import datetime
from math import sqrt
import analyses
from tangible_utils import get_environment
from activities import updateProfile
import grass.script as gscript
from TSP import solve_tsp_numpy


def dist(points, i, j):
    x2 = (points[i][0] - points[j][0]) * (points[i][0] - points[j][0])
    y2 = (points[i][1] - points[j][1]) * (points[i][1] - points[j][1])
    return sqrt(x2 + y2)


def run_trails(real_elev, scanned_elev, eventHandler, env, **kwargs):
    resulting = "trails2_slopedir"
    before = 'scan_saved'
    #env_crop = get_environment(raster=real_elev, n='n-100', s='s+100', e='e-100', w='w+100')
    analyses.change_detection(before=before, after=scanned_elev,
                              change='change', height_threshold=[60, 335], cells_threshold=[3, 100], add=True, max_detected=10, debug=True, env=env)
    points = {}
    # start and end
    data = gscript.read_command('v.out.ascii', input='trails2_points', type='point', format='point', env=env).strip()
    c1, c2 = data.splitlines()
    c1 = c1.split('|')
    c2 = c2.split('|')
    points[0] = (float(c1[0]), float(c1[1]))
    points[1] = (float(c2[0]), float(c2[1]))

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

    # export line
    profile_points = []
    line = 'L {} 1\n'.format(len(solution))
    for i in solution:
        line += '{} {}\n'.format(points[i][0], points[i][1])
        profile_points.append(points[i])
    line += '1 1'
    gscript.write_command('v.in.ascii', input='-', stdin=line, output='line', format='standard', flags='n', env=env)

    env2 = get_environment(raster=before)
    # slope along line
    gscript.run_command('v.to.rast', input='line', type='line', output='line_dir', use='dir', env=env2)
    gscript.run_command('r.slope.aspect', elevation=before, slope='saved_slope', aspect='saved_aspect', env=env2)
    gscript.mapcalc("slope_dir = abs(atan(tan({slope}) * cos({aspect} - {line_dir})))".format(slope='saved_slope', aspect='saved_aspect',
                    line_dir='line_dir'), env=env2)
    # set new color table
    colors = ['0 green', '7 green', '7 yellow', '15 yellow', '15 red', '90 red']
    gscript.write_command('r.colors', map='slope_dir', rules='-', stdin='\n'.join(colors), env=env2)
    # increase thickness
    gscript.run_command('r.grow', input='slope_dir', radius=2.1, output=resulting, env=env2)

    # update profile
    event = updateProfile(points=profile_points)
    eventHandler.postEvent(receiver=eventHandler.activities_panel, event=event)
    # copy results
    postfix = datetime.now().strftime('%H_%M_%S')
    prefix = 'trails2'
    gscript.run_command('g.copy', raster=['slope_dir', '{}_slope_dir_{}'.format(prefix, postfix)],
                        vector=['line', '{}_line_{}'.format(prefix, postfix)], env=env)
        