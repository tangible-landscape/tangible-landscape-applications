import grass.script as gscript

import analyses
from tangible_utils import get_environment


def run_cutfill(real_elev, scanned_elev, env, **kwargs):
    # this doesn't need to be computed on the fly
    dem_env = get_environment(raster=real_elev)
    gscript.run_command('r.contour', input=real_elev, output='contours_dem', step=5, flags='t', env=dem_env)
    gscript.mapcalc('diff = {r} - {s}'.format(r=real_elev, s=scanned_elev), env=env)
    
    rules = ['-300 black', '-20 red', '0 white', '20 blue', '300 black', 'default black']
    gscript.write_command('r.colors', map='diff', rules='-', stdin='\n'.join(rules), env=env)

