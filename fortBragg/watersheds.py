# -*- coding: utf-8 -*-
"""
@brief experiment_flow

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author: Anna Petrasova (akratoc@ncsu.edu)
"""
from tangible_utils import get_environment
from activities import updateDisplay
from analyses import change_detection
import grass.script as gscript


def run_contours(scanned_calib_elev, env, **kwargs):
    info = gs.raster_info(scanned_calib_elev)
    interval = (info["max"] - info["min"]) / 20.0
    gs.run_command(
        "r.contour",
        input=scanned_calib_elev,
        output="contours",
        step=interval,
        flags="t",
        env=env,
    )


def run_flow(real_elev, scanned_elev, scanned_calib_elev, env, **kwargs):
    threshold = 30
    flowacc = 'flowacc'
    drain = 'drainage'
    stream = 'stream'
    basin = 'basin'

    env2 = get_environment(raster=scanned_calib_elev)
    change_detection(before=scanned_calib_elev, after=scanned_elev,
                              change='change', height_threshold=[150, 1000], cells_threshold=[20, 140], add=True, max_detected=10, debug=True, env=env)
    # detected points
    points = gscript.read_command('v.out.ascii', input='change',
                                      type='point', format='point').strip().splitlines()
    if points:
        x, y, cat = points[0].split('|')
        gscript.run_command('r.stream.snap', input='change', output='outlet',
                            stream_rast=stream, accumulation=flowacc, radius=10, env=env2)
        outlets = gscript.read_command('v.out.ascii', input='outlet',
                                       type='point', format='point').strip().splitlines()
        x2, y2, cat2 = outlets[0].split('|')
        gscript.run_command('r.water.outlet', input=drain, output=basin, coordinates=(x2, y2), env=env2)
        gscript.write_command('r.colors', map=basin, rules='-', stdin='0% indigo\n100% indigo', env=env2)
        # drain
        gscript.run_command('r.drain', input="hydrodem", output="drain", drain="drain",
                            start_coordinates=(x2, y2), env=env2)
    else:
        gscript.mapcalc('basin = null()', env=env)
        gscript.run_command('v.edit', tool='create', map='drain', env=env)
        gscript.run_command('r.watershed', elevation=scanned_elev, accumulation=flowacc,
                            stream=stream,  drainage=drain, threshold=threshold, env=env)
        gscript.run_command('r.hydrodem', input=scanned_elev, output="hydrodem", mod=30, env=env)
        gs.run_command("g.copy", raster=[scanned_elev, scanned_calib_elev], env=env)

