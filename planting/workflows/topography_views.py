# -*- coding: utf-8 -*-
"""
Created on Tue Mar 28 17:32:38 2017

@author: tangible
"""

from math import sqrt
import grass.script as gscript
from blender import blender_export_vector


def dist(p1, p2):
    x2 = (p1[0] - p2[0]) * (p1[0] - p2[0])
    y2 = (p1[1] - p2[1]) * (p1[1] - p2[1])
    return sqrt(x2 + y2)


def run_view(scanned_elev, blender_path, env, **kwargs):
    # regression
    group = 'color'
    before = 'topo_saved'
    elev_threshold = 20
    color_threshold = 100
    dist_threshold = 30
    change = 'change'
    arrow = 'arrow'
    arrow3d = 'arrow3d'
    arrow_final = 'arrow_final'

    ff = gscript.find_file(name=arrow_final, element='vector')
    old_points = []
    if ff and ff['fullname']:
        old_p = gscript.read_command('v.out.ascii', input=ff['fullname'], format='standard', type='line', env=env).strip().splitlines()
        for op in old_p:
            line = op.strip().split()
            if line == ['1', '1']:
                continue
            try:
                x = float(line[0])
                y = float(line[1])
                z = float(line[2])
                old_points.append((x, y, z))
            except ValueError:
                continue
            except IndexError, e:
                print line
                print e
                continue
    
    reg_params = gscript.parse_command('r.regression.line', flags='g', mapx=before, mapy=scanned_elev, env=env)
    gscript.mapcalc(exp='{new} = if(({a} + {b} * {after}) - {before} > {thr}, 1, null())'.format(a=reg_params['a'],
                    b=reg_params['b'], after=scanned_elev, before=before, thr=elev_threshold, new=change), env=env)
    #gscript.parse_command('r.univar', map=[group + '_r', group + '_g', group + '_b'], output=, flags='t', zones=, env=env)
    gscript.mapcalc(exp='{new} = if({change} && ({r} + {g} + {b}) / 3. >= {th}, 1, 2)'.format(new=arrow, change=change, th=color_threshold,
                    r=group + '_r', g=group + '_g', b=group + '_b'), env=env)
    gscript.run_command('r.volume', input=arrow, clump=arrow, centroids=arrow, env=env)
    gscript.run_command('v.drape', input=arrow, output=arrow3d, elevation=before, method='bilinear', env=env)
    points = gscript.read_command('v.out.ascii', input=arrow3d, env=env).strip()

    if points:
        new_points = []
        linetext = 'L 2 1\n' 
        for p in points.splitlines():
            x, y, z, c = p.split('|')
            new_points.append((float(x), float(y), float(z)))
            linetext += '{} {} {}\n'.format(x, y, z)
        linetext += '1 1\n'

        # compare old and new
        if not old_points or (dist(old_points[0], new_points[0]) > dist_threshold or dist(old_points[1], new_points[1]) > dist_threshold):
            print 'write'
            gscript.write_command('v.in.ascii', stdin=linetext, input='-', output=arrow_final, format='standard', flags='zn', env=env)
            blender_export_vector(vector=arrow_final, name='vantage', z=True, vtype='line', path=blender_path, time_suffix=False, env=env)
