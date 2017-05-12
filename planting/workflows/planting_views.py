# -*- coding: utf-8 -*-
"""
Created on Tue Mar 28 17:32:38 2017

@author: tangible
"""

import os
from math import sqrt
import shutil
import glob
import grass.script as gscript
from grass.exceptions import CalledModuleError

PATH = '/run/user/1000/gvfs/smb-share:server=192.168.0.2,share=coupling/Watch/'

   

def dist(p1, p2):
    x2 = (p1[0] - p2[0]) * (p1[0] - p2[0])
    y2 = (p1[1] - p2[1]) * (p1[1] - p2[1])
    return sqrt(x2 + y2)


def run_view(scanned_elev, env, **kwargs):
    # regression
    group = 'color'
    before = 'scan_saved'
    elev_threshold = 20
    color_threshold = 150
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
            export_shp(arrow_final, 'vantage', env)
            #export_line(new_points[0], new_points[1], name='vantage')


def export_shp(vector, name, env):
    tmp_directory = '/tmp/line'
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


def export_line(p1, p2, name):
    out = '/tmp/{}.txt'.format(name)
    with open(out, 'w') as f:
        f.write('{},{},{}\n'.format(*p1))
        f.write('{},{},{}\n'.format(*p2))
        f.close()
    try:
        shutil.copyfile(out, PATH + name + '.txt')
    except OSError as e:
        if e.errno == 95:   
            pass  