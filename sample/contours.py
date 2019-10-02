import grass.script as gscript

def run_aspect(real_elev, scanned_elev, env, **kwargs):
    info = gscript.raster_info(scanned_elev)
    interval = (info['max'] - info['min']) / 20.
    gscript.run_command('r.contour', input=scanned_elev, output='contours_main', step=interval * 5, flags='t', env=env)
    gscript.run_command('r.contour', input=scanned_elev, output='contours', step=interval, flags='t', env=env)

