# -*- coding: utf-8 -*-
"""
Created on Tue Mar 28 17:32:38 2017

@author: tangible
"""

import os
import shutil
import glob
from os.path import expanduser
from datetime import datetime
import analyses
from tangible_utils import get_environment
from activities import updateDisplay
import grass.script as gscript
from grass.exceptions import CalledModuleError

trees = {1: "class1",
         2: "class2",
         3: "mixed",
         4: "class3",
         5: "class4",
         7: "water"}

PATH = '/run/user/1000/gvfs/smb-share:server=192.168.0.2,share=coupling/Watch/'


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

def export_raster(raster, name, env):
    time = datetime.now()
    suffix = '_{}_{}_{}'.format(time.hour, time.minute, time.second)
    out = '/tmp/{}{}.tif'.format(name, suffix)
    gscript.run_command('r.out.gdal', flags='c', input=raster, type="Float32", create='TFW=YES', out=out, env=env)

    try:
        shutil.copyfile(out,  PATH + '{}{}.tif'.format(name, suffix))
    except OSError as e:
        if e.errno == 95:
            pass


def export_polygons(vectors, env):
    time = datetime.now()
    suffix = '_{}_{}_{}'.format(time.hour, time.minute, time.second)
    outdir = PATH
    tmp_outdir = '/tmp'
    for vector in vectors:
        try:
            gscript.run_command('v.out.ogr', input=vector, lco="SHPT=POLYGONZ",
                                output=tmp_outdir + '/' + vector + suffix + '.shp', env=env)
        except CalledModuleError, e:
            print e
            
            
    for vector in vectors:
        for each in glob.glob(tmp_outdir + '/' +  vector + suffix + '.*'):
            print each
            ext = each.split('.')[-1]
            try:
                shutil.copyfile(each,  outdir + '/' + vector + suffix + '.' + ext)
            except OSError as e:
                if e.errno == 95:
                    pass


def run_patches(real_elev, scanned_elev, eventHandler, env, **kwargs):
    group = 'color'
    before = 'scan_saved'
    threshold = 25
    change = 'change'
    arrow = 'arrow'
    arrow3d = 'arrow3d'
    arrow_final = 'arrow_final'
    topo = 'topo_saved'
   #before = topo

#     regression
#    reg_params = gscript.parse_command('r.regression.line', flags='g', mapx=before, mapy=scanned_elev, env=env)
#    gscript.mapcalc(exp='{new} = if(({a} + {b} * {after}) - {before} > {thr}, 1, null())'.format(a=reg_params['a'],
#                    b=reg_params['b'], after=scanned_elev, before=before, thr=threshold, new=change), env=env)
#    gscript.mapcalc(exp='{new} = if({change} &&  ({r} + {g} + {b}) / 3. >= 100, 1, 2)'.format(new=arrow, change=change, r=group + '_r', g=group + '_g', b=group + '_b'), env=env)
#    gscript.run_command('r.volume', input=arrow, clump=arrow, centroids=arrow, env=env)
#    gscript.run_command('v.drape', input=arrow, output=arrow3d, elevation=before, method='bilinear', env=env)
#    points = gscript.read_command('v.out.ascii', input=arrow3d, env=env).strip()
#    print points
#    if points:
#        new_points = []
#        linetext = 'L 2 1\n' 
#        for p in points.splitlines():
#            x, y, z, c = p.split('|')
#            new_points.append((float(x), float(y), float(z)))
#            linetext += '{} {} {}\n'.format(x, y, z)
#        linetext += '1 1\n'
#        gscript.write_command('v.in.ascii', stdin=linetext, input='-', output=arrow_final, format='standard', flags='zn', env=env)
#        export_shp(arrow_final, 'vantage', env)
#        return
    
    segment = 'segment'
    signature = 'signature'
    classification = 'classification'
    filtered_classification = 'fclassification'
    reject = 'reject'
    patches = 'patches'
    # detect patches
    gscript.run_command('i.superpixels.slic', group=group, output=segment, compactness=2,
                        minsize=10, env=env)
    gscript.run_command('i.smap', group=group, subgroup=group, signaturefile=signature,
                        output=classification, goodness=reject, env=env)
    percentile = float(gscript.parse_command('r.univar', flags='ge', map=reject, env=env)['percentile_90'])
    gscript.mapcalc('{new} = if({classif} < {thres}, {classif}, null())'.format(new=filtered_classification,
                                                                                classif=classification, thres=percentile), env=env)
    gscript.run_command('r.stats.quantile', base=segment, cover=filtered_classification, output=patches, env=env)
    gscript.mapcalc('{} = int({})'.format(patches + '_cell', patches), env=env)
    gscript.run_command('r.to.vect', flags='svt', input=patches + '_cell', output=patches, type='area', env=env)
    
    base_cat = [3, 6, 7]
    #
    # r.liPATH = '/run/user/1000/gvfs/smb-share:server=192.168.0.2,share=coupling/Watch/'
    #
    indices = 'index_'
    # write config file if it doesn't exist
    rlipath = os.path.join(expanduser("~"), ".grass7", "r.li")
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
    for index in ['patchnum', 'richness', 'mps', 'shannon', 'shape']:
        gscript.run_command('r.li.' + index, input=patches + '2', output=indices + index, config=configpath, env=env)
        with open(os.path.join(outputpath, indices + index), 'r') as f:
            results[index] = float(f.readlines()[0].strip().split('|')[-1])
            if index == 'mps':
                results[index] *= 10
            results_list.append(results[index])
    
    # remediation
    gscript.run_command('r.grow', flags='m', input='waterall', output='waterallg', radius=30, new=1, env=env)
    
    gscript.mapcalc('{} = if(waterallg && patches2 == 5, 1, null())'.format('remed'), env=env)
    univar = gscript.parse_command('r.univar', map='remed', flags='g', env=env)
    remed_size = waterall = 0
    if univar and 'n' in univar:
        remed_size = float(univar['n'])
        print remed_size
    univar = gscript.parse_command('r.univar', map='waterall', flags='g', env=env)
    if univar and 'n' in univar:
        waterall = int(univar['n'])
        print waterall
        
    perc = 0
    if waterall:
        perc = 100* remed_size/waterall
    results_list.insert(0, perc)
    
    # update dashboard
    event = updateDisplay(value=results_list)
    print results_list
    eventHandler.postEvent(receiver=eventHandler.activities_panel, event=event)        
    
    # export patches
    gscript.mapcalc('scanned_scan_int = int({})'.format(topo), env=env)
    
    # set color for patches
    gscript.run_command('r.to.vect', flags='svt', input=patches + '2', output=patches + '2', type='area', env=env)
    gscript.run_command('v.generalize', input=patches + '2', type='area', output=patches + '2gen', method='snakes', threshold=100, env=env)
    gscript.run_command('v.colors', map=patches + '2gen', rules='/home/tangible/analyses/acadia/patch_colors.txt', env=env)
    

    #data = gscript.read_command('v.to.db', flags='p', map=patches + 2, option='area', columns='area', env=env)
    
    
    env2 = get_environment(raster=patches, res=10)
    try:
        gscript.run_command('r.mask', flags='r', env=env)
    except:
        pass
    cats = gscript.read_command('r.describe', flags='1ni', map=patches + '_cell', env=env).strip()
    cats = [int(cat) for cat in cats.splitlines()]
    toexport = []
    for cat in cats:
        if cat in base_cat:
            continue
        gscript.run_command('r.mask', raster=patches + '_cell', maskcats=cat, env=env)
        #gscript.run_command('r.clump', input='', output='')
#        univar = gscript.parse_command('r.univar', flags='g', map=patches + '_cell', env=env)
#        size = int(univar['n'])
        gscript.run_command('r.to.vect', flags='svt', input='scanned_scan_int', output=patches + '_2d', type='area', env=env2)
        gscript.run_command('r.mask', flags='r', env=env)
        gscript.run_command('v.drape', input=patches + '_2d', output='patch_' + trees[cat], elevation='scanned_scan_int', env=env2)
        
        toexport.append('patch_' + trees[cat])
    send_file('empty.txt')
    export_polygons(vectors=toexport, env=env)
#        gscript.run_command('r.mask', raster=patches + '_cell', maskcats=cat, env=env)#
#        gscript.mapcalc('patch_{} = {}'.format(trees[cat], topo), env=env)
#        #gscript.run_command('r.to.vect', flags='svt', input='scanned_scan_int', output=patches + '_2d', type='area', env=env2)
#        gscript.run_command('r.mask', flags='r', env=env)
#        #gscript.run_command('v.drape', input=patches + '_2d', output='patch_' + trees[cat], elevation='scanned_scan_int', env=env2)
#        toexport.append('patch_' + trees[cat])
#    send_file('empty.txt')
#    print 'export'
#    for each in toexport:
#        export_raster(raster=each, name=each, env=env)
#    #export_polygons(vectors=toexport, env=env)


def send_file(name):
    with open(os.path.join(PATH, name), 'w') as f:
        f.close()
