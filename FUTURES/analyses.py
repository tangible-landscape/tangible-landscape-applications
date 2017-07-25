# -*- coding: utf-8 -*-
"""
This file serves as a control file with analyses
which are running in real-time. The name of the analyses
must start with 'run_'. The file has to be saved so that the change is applied.
"""
import os
import subprocess
import uuid
import math
import wx

import analyses
from tangible_utils import get_environment
import grass.script as gscript
from grass.exceptions import CalledModuleError


def xdrawing_roads(draw_vector_append_name, env,  update, giface, **kwargs):
    gscript.run_command('v.generalize', input=draw_vector_append_name, output='smooth', threshold=10, method='snakes', env=env)
    env2 = get_environment(raster='buncombe')
    gscript.run_command('v.to.rast', input='smooth', output='road', type='line', use='val', env=env2)
    #gscript.mapcalc('roads_patch = if(isnull(road), roads, road)', env=env2)
    #gscript.run_command('r.neighbors', flags='c', input='roads_patch', output='road_dens_edit', size=25, method='average', env=env2)
    #gscript.mapcalc('road_dens_perc_edit = 100 * road_dens_edit', env=env2)
    #gscript.run_command('r.colors', map='road_dens_perc_edit,road_dens_perc', color='byr', env=env2)
    
    gscript.run_command('r.grow.distance', input='road', distance='buffer', env=env2)
    gscript.mapcalc('stimulus_roads = if(buffer > 500, 0, graph(buffer, 0, 0.7, 200,0.5, 500,0.3))', env=env2)
    gscript.run_command('r.colors', map='stimulus_roads', color='reds', env=env)

    params = []
    ff = gscript.find_file(name='appended', element='vector')
    if ff and ff['fullname'] and gscript.vector_info_topo('appended')['lines'] > 0:
        params.append('stimulus=stimulus_roads')
    
    futures(params, giface, update)

    

def onFuturesDone(event):
    event.userData['update']()
    env = event.userData['env']
    #gscript.write_command('r.colors', map='final', rules='-', stdin='-1 104:200:104\n0 200:200:200\n1 250:100:50\n24 250:100:50', quiet=True)
    gscript.write_command('r.colors', map='final', rules='-', stdin='-1 104:200:104\n0 221:201:201\n1 165:42:42\n24 165:42:42', quiet=True, env=env)
    steps = gscript.read_command('g.list', type='raster', pattern='step_*', separator=',', quiet=True, env=env).strip()
    gscript.run_command('t.register', maps=steps, input='futures_series', start=2012, unit='years', increment=1, overwrite=True, quiet=True, env=env)
    gscript.write_command('t.rast.colors', input='futures_series', stdin='1 165:42:42', rules='-', env=env)


def run_futures(scanned_elev, env, update, giface, **kwargs):
    analyses.match_scan(base='scan_saved', scan=scanned_elev, matched='matched', env=env)
    threshold = 180
    params = list()
    gscript.mapcalc(exp="{change} = if({new} - {old} > {thres}, {new} - {old}, null())".format(
                    change='change', thres=threshold, new='matched', old='scan_saved'), env=env)
    change_info = gscript.raster_info('change')
    if not math.isnan(change_info['min']):
        max_change = change_info['max']
        gscript.mapcalc(exp="{change} = if(change, 1, null())".format(
                        change='change_bin'), env=env)
        gscript.run_command('r.clump', input='change_bin', output='clump', env=env)
        gscript.run_command('r.stats.zonal', base='clump', cover='color_r', output='red_mean', method='average', env=env)
        gscript.run_command('r.stats.zonal', base='clump', cover='color_g', output='green_mean', method='average', env=env)
        gscript.mapcalc('stimulus = if(isnull(red_mean), 0, if(red_mean > green_mean, graph(change, 0,0, {}, 0.9), 0))'.format(max_change), env=env)
        gscript.mapcalc('constrain = if(isnull(green_mean), 1, if(green_mean > red_mean, graph(change, 0,1, {},0.1), 1))'.format(max_change), env=env)
        gscript.mapcalc('stimulus_flat = if(red_mean > green_mean, 1, null())', env=env)
        gscript.mapcalc('constrain_flat = if(green_mean > red_mean, 1, null())', env=env)
#        try:
#            gscript.run_command('g.remove', flags='f',  type='vector', name='constrain,stimulus', env=env)
#        except:
#            pass
        gscript.run_command('r.to.vect', input='stimulus_flat', output='stimulus', type='area', flags='s', env=env)
        gscript.run_command('r.to.vect', input='constrain_flat', output='constrain', type='area', flags='s', env=env)
        gscript.run_command('r.colors', map='stimulus', color='greens', env=env)
        gscript.run_command('r.colors', map='constrain', color='red', flags='n', env=env)
#        params['stimulus'] = 'stimulus'
#        params['constrain'] = 'constrain'
        params.append('constrain=constrain')        
        params.append('stimulus=stimulus')
    else:
        gscript.run_command('v.edit', tool='create', map='stimulus', env=env)
        gscript.run_command('v.edit', tool='create', map='constrain', env=env)
    update()    

#    ff = gscript.find_file(name='appended', element='vector')
#    if ff and ff['fullname'] and gscript.vector_info_topo('appended')['lines'] > 0:
        #roads = 'road_dens_perc_edit'
#        gscript.mapcalc('stimulus2 = stimulus + stimulus_roads', env=env2)
#        params[-1] = 'stimulus=stimulus2'
    futures(params, giface, update)
 
    #gscript.run_command('r.futures.pga', subregions='buncombe', developed='urban_2011_buncombe',
#                        predictors=['road_dens_perc', 'forest_smooth_perc', 'dist_to_water_km', 'dist_to_protected_km'],
#                        devpot_params='potential.csv', development_pressure='devpressure_0_5', n_dev_neighbourhood=30,
#                        development_pressure_approach='gravity', gamma=0.5, scaling_factor=0.1, demand='demand_TL_high.csv',
#                        discount_factor=0.4, compactness_mean=0.1, compactness_range=0.05, patch_sizes='patches.txt',
#                        num_neighbors=4, seed_search=2, random_seed=1, output='final', output_series='step',
#                        env=env2, quiet=False,**params)
                             
def futures(params, giface, update):
    os.chdir('/home/tangible/Documents/asheville_TL')
    env2 = get_environment(raster='buncombe')

    cmd = ['r.futures.pga', 'subregions=buncombe', 'developed=urban_2011_buncombe',
           'predictors=road_dens_perc,forest_smooth_perc,dist_to_water_km,dist_to_protected_km',
           'devpot_params=potential.csv', 'development_pressure=devpressure_0_5', 'n_dev_neighbourhood=30',
           'development_pressure_approach=gravity', 'gamma=0.5', 'scaling_factor=0.1', 'demand=demand_TL_high.csv',
           'discount_factor=0.8', 'compactness_mean=0.1', 'compactness_range=0.05', 'patch_sizes=patches.txt',
           'num_neighbors=4', 'seed_search=2', 'random_seed=1', 'output=final', 'output_series=step'] + params
    userData = {}
    userData['update'] = update
    userData['env'] = env2
    giface.RunCmd(cmd, env=env2, onDone=onFuturesDone, userData=userData)
