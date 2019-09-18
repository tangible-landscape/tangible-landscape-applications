# -*- coding: utf-8 -*-
"""
@brief cutfill2

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author: Anna Petrasova (akratoc@ncsu.edu)
"""

from datetime import datetime
import grass.script as gscript


def run_cutfill(real_elev, scanned_elev, eventHandler, env, **kwargs):
    before_resampled = 'resamp'
    masked = 'masked'
    resulting = 'cutfill2_diff'
    gscript.run_command('r.resamp.interp', input=real_elev, output=before_resampled, env=env)
    gscript.mapcalc('{} = if(cutfill2_masking, {}, null())'.format(masked, before_resampled), env=env)
    coeff = gscript.parse_command('r.regression.line', mapx=scanned_elev, mapy=masked, flags='g', env=env)
    gscript.mapcalc(exp="{diff} = ({a} + {b} * {scan}) - {before}".format(diff=resulting, before=before_resampled, scan=scanned_elev,
                                                                          a=coeff['a'], b=coeff['b']), env=env)

    colors = ['100 black',
              '20 black',
              '7 red',
              '1 white',
              '0 white',
              '-1 white',
              '-7 blue',
              '-20 black',
              '-100 black',
              'nv black']
    gscript.write_command('r.colors', map=resulting, rules='-', stdin='\n'.join(colors), env=env)

    # copy scan
    postfix = datetime.now().strftime('%H_%M_%S')
    prefix = 'cutfill2'
    gscript.run_command('g.copy', raster=[scanned_elev, '{}_scan_{}'.format(prefix, postfix)], env=env)
    gscript.run_command('g.copy', raster=[resulting, '{}_diff_{}'.format(prefix, postfix)], env=env)
