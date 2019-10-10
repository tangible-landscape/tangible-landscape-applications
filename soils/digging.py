import analyses
from tangible_utils import get_environment
import grass.script as gs

voxel = 'interp_2002_08_25'

def run_crossection(scanned_elev, env, **kwargs):    
    env3d = get_environment(raster_3d=voxel)
    analyses.cross_section(scanned_elev=scanned_elev, voxel=voxel, new='cross', env=env3d)
    analyses.contours(scanned_elev=scanned_elev, new='contours_scanned', step=20., maxlevel=0, env=env)

