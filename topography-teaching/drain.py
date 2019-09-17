# -*- coding: utf-8 -*-
"""
@brief experiment_drain

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author: Anna Petrasova (akratoc@ncsu.edu)
"""

from datetime import datetime
from math import sqrt
import analyses
from tangible_utils import get_environment
import grass.script as gscript


solution = [(316715, 251545, 1134.5),
            (317045, 251065, 1166.9),
            (317485, 252475, 1005.0),
            (316765, 250475, 1271.5),
            (317055, 250705, 1189.9),
            (315725, 251855, 929.2),
            (317705, 252645, 940.2)]


def run_drain(real_elev, scanned_elev, eventHandler, env, subTask, **kwargs):
    before = 'scan_saved'
    analyses.change_detection(before=before, after=scanned_elev,
                              change='change', height_threshold=[60, 220], cells_threshold=[4, 80], add=True, max_detected=1, debug=True, env=env)
    point = gscript.read_command('v.out.ascii', input='change',
                                 type='point', format='point', env=env).strip()
    drain = 'drain_line'
    env2 = get_environment(raster=real_elev)
    if point:
        x, y, cat = point.split('|')
        gscript.run_command('r.drain', input=real_elev, output=drain, drain=drain, start_coordinates='{},{}'.format(x, y), env=env2)
    else:
        gscript.run_command('v.edit', map=drain, tool='create', env=env)

    # copy results
    if point:
        postfix = datetime.now().strftime('%H_%M_%S')
        prefix = 'drain'
        gscript.run_command('g.copy', vector=['change', '{}_change_{}_{}'.format(prefix, subTask, postfix)], env=env)

