# -*- coding: utf-8 -*-
"""
@brief flow

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author: Anna Petrasova (akratoc@ncsu.edu)
"""

from datetime import datetime
from tangible_utils import get_environment
import grass.script as gscript


def run_contours(real_elev, scanned_elev, eventHandler, env, **kwargs):
    gscript.run_command('r.contour', input=scanned_elev, output='flow_contours', step=5, flags='t', env=env)


def run_flow(real_elev, scanned_elev, eventHandler, env, **kwargs):
    gscript.run_command('r.slope.aspect', elevation=scanned_elev, dx='dx', dy='dy', env=env)
    gscript.run_command('r.sim.water', elevation=scanned_elev, dx='dx', dy='dy', rain_value=300,
                        depth='flow_flow', niterations=6, env=env)
    gscript.write_command('r.colors', map='flow_flow', rules='-',
                          stdin='0.001 0:128:0\n0.05 0:255:255\n0.1 0:127:255\n0.5 0:0:255\n10 0:0:0', env=env)
    # copy scan
    postfix = datetime.now().strftime('%H_%M_%S')
    prefix = 'flow'
    gscript.run_command('g.copy', raster=[scanned_elev, '{}_scan_{}'.format(prefix, postfix)], env=env)

