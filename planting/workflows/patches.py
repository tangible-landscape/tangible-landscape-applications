# -*- coding: utf-8 -*-
"""
Created on Tue Mar 28 17:32:38 2017

@author: tangible
"""

import os
import shutil
import glob
from os.path import expanduser
import analyses
from tangible_utils import get_environment
from blender import blender_export_vector, blender_send_file
from activities import updateDisplay
import grass.script as gscript
from grass.exceptions import CalledModuleError

trees = {1: "class1",
         2: "class2",
         3: "mixed",
         4: "class3",
         5: "class4",
         7: "water"}


def run_patches(real_elev, scanned_elev, scanned_color, blender_path, eventHandler, env, **kwargs):
    topo = 'topo_saved'

    # detect patches
    patches = 'patches'
    analyses.classify_colors(new=patches, group=scanned_color, compactness=2,
                             threshold=0.3, minsize=10, useSuperPixels=True, env=env)
    gscript.run_command('r.to.vect', flags='svt', input=patches, output=patches, type='area', env=env)
    
    base_cat = [3, 6, 7]
    #
    # r.liPATH = '/run/user/1000/gvfs/smb-share:server=192.168.0.2,share=coupling/Watch/'
    #
    indices = 'index_'
    # write config file if it doesn't exist
    rlipath = os.path.join(expanduser("~"), ".grass7", "r.li")
    if not os.path.exists(rlipath):
        os.makedirs(rlipath)
    configpath = os.path.join(rlipath, "patches")
    outputpath = os.path.join(rlipath, "output")    

    if not os.path.exists(configpath):
        with open(configpath, 'w') as f:
            f.write('SAMPLINGFRAME 0|0|1|1\n')
            f.write('SAMPLEAREA 0.0|0.0|1|1')
    
    results = {}
    results_list = []
    # TODO: scaling values
    gscript.mapcalc('{p2} = if({p} != {cl1} && {p} != {cl2} && {p} != {cl3}, int({p}), null())'.format(p2=patches + '2', p=patches,
                    cl1=base_cat[0], cl2=base_cat[1], cl3=base_cat[2]), env=env)
    rliindices = ['patchnum', 'richness', 'mps', 'shannon', 'shape']
    for index in rliindices:
        gscript.run_command('r.li.' + index, input=patches + '2', output=indices + index, config=configpath, env=env)
        with open(os.path.join(outputpath, indices + index), 'r') as f:
            r = f.readlines()[0].strip().split('|')[-1]
            if index == 'patchnum' and float(r) == 0:
                results_list = [0] * len(rliindices)
                break

            results[index] = float(r)
            if index == 'mps':
                results[index] *= 10
            results_list.append(results[index])
    
    # remediation
    gscript.run_command('r.grow', flags='m', input='waterall', output='waterallg', radius=30, new=1, env=env)
    
    gscript.mapcalc('{new} = if({w} && {p} == 5, 1, null())'.format(new='remed', w='waterallg', p=patches + '2'), env=env)
    univar = gscript.parse_command('r.univar', map='remed', flags='g', env=env)
    remed_size = waterall = 0
    if univar and 'n' in univar:
        remed_size = float(univar['n'])
    univar = gscript.parse_command('r.univar', map='waterall', flags='g', env=env)
    if univar and 'n' in univar:
        waterall = int(univar['n'])
        
    perc = 0
    if waterall:
        perc = 100* remed_size/waterall
    results_list.insert(0, perc)
    
    # update dashboard
    event = updateDisplay(value=results_list)
    eventHandler.postEvent(receiver=eventHandler.activities_panel, event=event)        
    
    # export patches
    gscript.mapcalc('scanned_scan_int = int({})'.format(topo), env=env)
    
    # set color for patches
    gscript.run_command('r.to.vect', flags='svt', input=patches + '2', output=patches + '2', type='area', env=env)
    gscript.run_command('v.generalize', input=patches + '2', type='area', output=patches + '2gen', method='snakes', threshold=100, env=env)
    
    # creates color table as temporary file
    # this is the training map from where the colors are taken
    training = 'training_areas'
    color_path = '/tmp/patch_colors.txt'
    if not os.path.exists(color_path):
        color_table = gscript.read_command('r.colors.out', map=training, env=env).strip()
        with open(color_path, 'w') as f:
            for line in color_table.splitlines():
                if line.startswith('nv') or line.startswith('default'):
                    continue
                elif int(line.split(' ')[0]) in base_cat:
                    continue
                else:
                    f.write(line)
                    f.write('\n')
    try:
        gscript.run_command('v.colors', map=patches + '2gen', rules=color_path, env=env)
    except CalledModuleError:
        return

    env2 = get_environment(raster=patches, res=10)
    try:
        gscript.run_command('r.mask', flags='r', env=env)
    except:
        pass
    cats = gscript.read_command('r.describe', flags='1ni', map=patches, env=env).strip()
    cats = [int(cat) for cat in cats.splitlines()]
    toexport = []   
    for cat in cats:
        if cat in base_cat:
            continue
        gscript.run_command('r.mask', raster=patches, maskcats=cat, env=env)
        gscript.run_command('r.to.vect', flags='svt', input='scanned_scan_int', output=patches + '_2d', type='area', env=env2)
        gscript.run_command('r.mask', flags='r', env=env)
        gscript.run_command('v.drape', input=patches + '_2d', output='patch_' + trees[cat], elevation='scanned_scan_int', env=env2)
        
        toexport.append('patch_' + trees[cat])
    blender_send_file('empty.txt', path=blender_path)

    for vector in toexport:
        blender_export_vector(vector, vtype='area', z=True, time_suffix=True, path=blender_path, env=env)




