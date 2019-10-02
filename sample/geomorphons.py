import grass.script as gscript

import analyses

def run_geomorphons(real_elev, scanned_elev, env, **kwargs):
    try:
        analyses.geomorphon(scanned_elev, new='geomorphon', search=12, skip=4, flat=1, dist=0, env=env)
    except:
        print("r.geomorphon failed, please install it with g.extension")
    info = gscript.raster_info(scanned_elev)
    interval = (info['max'] - info['min']) / 20.
    gscript.run_command('r.contour', input=scanned_elev, output='contours', step=interval, flags='t', env=env)

