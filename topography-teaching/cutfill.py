# -*- coding: utf-8 -*-
"""
@brief cutfill1

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author: Anna Petrasova (akratoc@ncsu.edu)
"""

from datetime import datetime
import grass.script as gscript
from activities import updateDisplay


def run_cutfill(real_elev, scanned_elev, eventHandler, env, **kwargs):
    before_resampled = 'resamp'
    masked = 'masked'
    resulting = 'cutfill1_diff'
    gscript.run_command('r.resamp.interp', input=real_elev, output=before_resampled, env=env)
    gscript.mapcalc('{} = if(cutfill1_masking, {}, null())'.format(masked, before_resampled), env=env)
    coeff = gscript.parse_command('r.regression.line', mapx=scanned_elev, mapy=masked, flags='g', env=env)
    gscript.mapcalc(exp="{diff} = ({a} + {b} * {scan}) - {before}".format(diff=resulting, before=before_resampled, scan=scanned_elev,
                                                                          a=coeff['a'], b=coeff['b']), env=env)
    threshold = 1.5
    gscript.mapcalc(exp="abs_diff = if({diff} >= {thr}, {diff}, if({diff} <= -{thr}, abs({diff}), null()) )".format(diff=resulting, thr=threshold), env=env)

    abs_sum = float(gscript.parse_command('r.univar', map='abs_diff', flags='g', env=env)['sum'])
    event = updateDisplay(value=abs_sum / 100)
    eventHandler.postEvent(receiver=eventHandler.activities_panel, event=event)

    # copy scan
    postfix = datetime.now().strftime('%H_%M_%S')
    prefix = 'cutfill'
    gscript.run_command('g.copy', raster=[scanned_elev, '{}_scan_{}'.format(prefix, postfix)], env=env)
    gscript.run_command('g.copy', raster=[resulting, '{}_diff_{}'.format(prefix, postfix)], env=env)
