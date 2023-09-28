import grass.script as gs
from tangible_utils import get_environment


def run_slope(real_elev, scanned_elev, env, **kwargs):
    gs.run_command("r.slope.aspect", elevation=scanned_elev, slope="slope", env=env)
    info = gs.raster_info(scanned_elev)
    interval = (info["max"] - info["min"]) / 20.0
    gs.run_command(
        "r.contour",
        input=scanned_elev,
        output="contours",
        step=5,
        flags="t",
        env=env,
    )
    gs.run_command("r.colors", map="slope", raster="max_slope", env=env)


def calib_slope(real_elev, scanned_elev, env, **kwargs):
    dem_env = get_environment(raster=real_elev)
    gs.mapcalc("max_slope = float(rand(0, 91))", seed=1, env=env)
    gs.run_command("r.colors", map="max_slope", color="slope", env=env)
