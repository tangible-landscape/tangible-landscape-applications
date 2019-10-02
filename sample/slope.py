import grass.script as gscript


def run_slope(real_elev, scanned_elev, env, **kwargs):
    gscript.run_command('r.slope.aspect', elevation=scanned_elev, slope='slope', env=env)
    info = gscript.raster_info(scanned_elev)
    interval = (info['max'] - info['min']) / 20.
    gscript.run_command('r.contour', input=scanned_elev, output='contours', step=interval, flags='t', env=env)

