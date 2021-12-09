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


color_threshold = 80
size_threshold = 150
change_cfactor = 0.01
base_cfactor = 0.5

def contours(scanned_elev, env,):
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
def cfactor(scanned_color, env):
    gs.run_command('i.superpixels.slic', input=scanned_color, output="superpixels",
                   step=8, perturb=10, compactness=2, minsize=150, memory=1000, env=env)
    gs.run_command('r.fill.stats', flags='k', input="superpixels", output="superpixels_filled",
                   distance=7, mode='mode', cells=4, env=env)
    gs.mapcalc('{c} = ({r} + {g} + {b}) / 3.'.format(c="mean", r=scanned_color + '_r', g=scanned_color + '_g', b=scanned_color + '_b'), env=env)
    data = gs.read_command('r.univar', flags='egt', separator='comma', map="mean", zones="superpixels_filled", env=env).strip().splitlines()
    data = np.genfromtxt(data, delimiter=',', skip_header=1)
    zones = list(data[(data[:, 15] < color_threshold) & (data[:, 2] > size_threshold)][:, 0])
    if not zones:
        return False
    condition = " || ".join(['{c} == {n}'.format(c="superpixels_filled", n=int(z)) for z in zones])
    gs.mapcalc(f"cfactor = if ({condition}, {change_cfactor}, {base_cfactor})", env=env)
    return True

def run_usped(scanned_elev, scanned_color, scanned_calib_elev, env, **kwargs):
    filled = "scan_filled"
    gs.run_command("r.fill.stats", flags="k", input=scanned_elev, output=filled, distance=7, mode="wmean", power=2, cells=4, env=env)

    if not cfactor(scanned_color, env):
        print ("no c factor detected")
        elev = filled
        gs.run_command("g.copy", raster=[filled, scanned_calib_elev], env=env)
        contours(elev, env)
    else:
        elev = scanned_calib_elev
    gs.run_command("r.slope.aspect", elevation=elev, slope="slope", aspect="aspect", env=env)
    analyses.usped(elev, k_factor=0.2, c_factor="cfactor", flowacc="flowacc", slope="slope", aspect="aspect", new="usped", env=env)

