"""
This file serves as a control file with analyses
which are running in real-time. The name of the analyses
must start with 'run_'. The file has to be saved so that the change is applied.
"""

import subprocess
import uuid
import numpy as np

import analyses
from tangible_utils import get_environment
import grass.script as gs
from grass.exceptions import CalledModuleError


def contours(scanned_elev, env):
    info = gs.raster_info(scanned_elev)
    interval = (info["max"] - info["min"]) / 20.0
    gs.run_command(
        "r.contour",
        input=scanned_elev,
        output="contours",
        step=interval,
        flags="t",
        env=env,
    )


def run_water(scanned_elev, env, **kwargs):
    filled = "scan_filled"
    gs.run_command("r.fill.stats", flags="k", input=scanned_elev, output=filled, distance=7, mode="wmean", power=2, cells=4, env=env)
    # contours
    contours(filled, env)
    # simwe
    gs.run_command("r.slope.aspect", elevation=filled, dx="dx", dy="dy", env=env)
    gs.run_command("r.sim.water", elevation=filled, dx="dx", dy="dy", rain_value=150, hmax=0.1, depth="depth", niterations=20, nprocs=1, env=env)
    color='0 255:255:255\n0.001 255:255:0\n0.05 0:255:255\n0.1 0:127:255\n0.5 0:0:255\n10 0:0:0'
    gs.write_command(
        "r.colors",
        map="depth",
        rules="-",
        stdin="0.001 0:128:0\n0.07 0:255:255\n0.1 0:127:255\n0.5 0:0:255\n10 0:0:0",
        env=env,
    )
    # ponds
    analyses.depression(scanned_elev=filled, new="ponds", repeat=3, filter_depth=0, env=env)


#def run_difference(real_elev, scanned_elev, env, **kwargs):
#    analyses.difference(real_elev=real_elev, scanned_elev=scanned_elev,
#                         env=env, new='diff', color_coeff=1)
#
#
#def run_contours(scanned_elev, env, **kwargs):
#    analyses.contours(scanned_elev=scanned_elev, new='contours_scanned', env=env, step=2)


#def run_ponds(scanned_elev, env, **kwargs):
#    analyses.depression(scanned_elev=scanned_elev, new="ponds", repeat=2, filter_depth=0.5, env=env)

#def run_rlake(real_elev, scanned_elev, env, **kwargs):
#    seed = [635773.7234042553,220978.60182370822]
#    analyses.rlake(scanned_elev, new='lake', base=real_elev, env=env, seed=seed, level=700)


#def run_simwe(scanned_elev, env, **kwargs):
#    analyses.simwe(scanned_elev=scanned_elev, depth='depth', rain_value=700, niterations=4, env=env)

#
#def run_erosion(scanned_elev, env, **kwargs):
#    analyses.erosion(scanned_elev=scanned_elev, rain_value=200, depth='depth', detachment_coeff=0.001, transport_coeff=0.01, shear_stress=0, sediment_flux='flux', erosion_deposition='erdep', niterations=4, env=env)

#def run_geomorphon(scanned_elev, env, **kwargs):
#    analyses.geomorphon(scanned_elev, new='geomorphon', search=22, skip=12, flat=1, dist=0, env=env)

#def run_slope_aspect(scanned_elev, env, **kwargs):
#    analyses.slope_aspect(scanned_elev=scanned_elev, slope='slope', aspect='aspect', env=env)

#
#def run_usped(scanned_elev, env, **kwargs):
#    analyses.flowacc(scanned_elev, new='flowacc', env=env)
#    analyses.usped(scanned_elev, k_factor='soils_Kfactor', c_factor='cfactorbare_1m', flowacc='flowacc', slope='slope', aspect='aspect', new='erdep', env=env)

#def run_change_detection(scanned_elev, env, **kwargs):
#    trim to avoid detecting differences on the edge
#    env = get_environment(rast=scanned_elev, n='n-20', s='s+20', e='e-20', w='w+20')
#    analyses.change_detection(before='scan_saved', after=scanned_elev,
#                              change='change', height_threshold=[10, 30], cells_threshold=[7, 100], add=True, max_detected=6, debug=False, env=env)
#
#def run_trail(real_elev, scanned_elev, env, **kwargs):
#    analyses.trails_combinations(real_elev,friction='friction', walk_coeff=[0.72, 6.0, 1.9998, -1.9998],
#                                 _lambda=.5, slope_factor=-.8125, walk='walk_result',
#                                 walking_dir='walkdir_result', points='change', raster_route='route_result',
#                                 vector_routes='route_result', mask=None, env=env)
#    analyses.trail_salesman(trails='route_result', points='change', output='route_salesman', env=env)

#def run_viewshed(real_elev, scanned_elev, env, **kwargs):
#    analyses.viewshed(real_elev, output='viewshed', obs_elev=1.75, vector='change', visible_color='green', invisible_color='red', env=env)

#def run_colors(scanned_elev, scanned_color, env, **kwargs):
#    if scanned_color:
#        # need training phase, see Analyses tab
#        analyses.classify_colors(new='patches', group=scanned_color, compactness=2, threshold=0.3, minsize=10, useSuperPixels=False, env=env)
