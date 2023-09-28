import grass.script as gs
from grass.exceptions import CalledModuleError
from tangible_utils import get_environment

import analyses


def run_contours(scanned_elev, env, **kwargs):
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


def run_water(scanned_elev, env, **kwargs):
    # simwe
    analyses.simwe(
        scanned_elev=scanned_elev, depth="depth", rain_value=300, niterations=5, env=env
    )
    #    gs.write_command(
    #        "r.colors",
    #        map="depth",
    #        rules="-",
    #        stdin="0.001 0:128:0\n0.05 0:255:255\n0.1 0:127:255\n0.5 0:0:255\n10 0:0:0",
    #        env=env,
    #    )

    # ponds
    try:
        analyses.depression(
            scanned_elev=scanned_elev, new="ponds", repeat=3, filter_depth=0, env=env
        )
    except CalledModuleError:
        return
