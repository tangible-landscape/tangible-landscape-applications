import grass.script as gs
import analyses
from tangible_utils import get_environment


def run_cutfill(real_elev, scanned_elev, zexag, env, **kwargs):
    analyses.difference(
        real_elev=real_elev, scanned_elev=scanned_elev, new="diff", zexag=zexag, env=env
    )


def calib_cutfill(real_elev, scanned_elev, env, **kwargs):
    dem_env = get_environment(raster=real_elev)
    gs.run_command(
        "r.contour",
        input=real_elev,
        output="contours_dem",
        step=5,
        flags="t",
        env=dem_env,
    )
