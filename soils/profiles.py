import analyses
import grass.script as gs
from tangible_utils import get_environment

voxel = 'interp_2002_08_25@tdr_observ'

#d.rast map=slice
#d.vect map=axes width=1 attribute_column=label label_color=black label_size=12 yref=bottom
#d.vect map=axes@scanning layer=2 width=1 icon=basic/cross1 size=10

def xrun_crossection(scanned_elev, env, **kwargs):
    env3d = get_environment(raster_3d=voxel)
    analyses.cross_section(scanned_elev=scanned_elev, voxel=voxel, new='cross', env=env3d)
    analyses.contours(scanned_elev=scanned_elev, new='contours_scanned', step=20., maxlevel=0, env=env)


def run_slice(scanned_elev, env, **kwargs):
    env3d = get_environment(raster_3d=voxel)
    data = gs.read_command('v.out.ascii', input='change', type='point', format='point', separator='comma').strip().split()
    points = [point.split(',')[:2] for point in data]
    if len(points) == 2:
        gs.run_command('r3.slice', input=voxel, output='slice', axes='axes',
                       coordinates=[points[0][0], points[0][1], points[1][0], points[1][1]],
                       slice_line='slice_line', offset=[0,0], units=['m', 'cm'], overwrite=True, quiet=True, env=env3d)


def run_trail_points(scanned_elev, env, **kwargs):
    analyses.change_detection('scan_saved', scanned_elev, 'change',
                              height_threshold=[35, 70], cells_threshold=[5, 50],
                              add=True, max_detected=2, debug=True, env=env)
