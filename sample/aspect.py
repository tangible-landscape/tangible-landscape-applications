# -*- coding: utf-8 -*-

import grass.script as gscript
from tangible_utils import get_environment


def run_aspect(real_elev, scanned_elev, env, **kwargs):
    gscript.run_command('r.slope.aspect', elevation=scanned_elev, aspect='aspect', env=env)
    info = gscript.raster_info(scanned_elev)
    interval = (info['max'] - info['min']) / 10.
    gscript.run_command('r.contour', input=scanned_elev, output='contours', step=interval, flags='t', env=env)

