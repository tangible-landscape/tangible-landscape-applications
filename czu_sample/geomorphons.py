import grass.script as gs

import analyses


def run_geomorphons(real_elev, scanned_elev, env, **kwargs):
    analyses.geomorphon(
        scanned_elev, new="geomorphon", search=12, skip=4, flat=1, dist=0, env=env
    )
    # convert peaks to points
    gs.mapcalc("peaks = if(geomorphon == 2, 1, null())", env=env)
    gs.run_command("r.clump", input="peaks", output="clumped_peaks", env=env)
    gs.run_command(
        "r.volume",
        input="clumped_peaks",
        clump="clumped_peaks",
        centroids="peaks",
        errors="exit",
        env=env,
    )
    # contours
    info = gs.raster_info(scanned_elev)
    interval = (info["max"] - info["min"]) / 20.0
    gs.run_command(
        "r.contour",
        input=scanned_elev,
        output="contours",
        step=interval,
        flags="t",
        env=env,
    )
