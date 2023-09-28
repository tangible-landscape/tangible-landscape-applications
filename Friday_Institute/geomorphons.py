import grass.script as gs

import analyses


def run_geomorphons(real_elev, scanned_elev, env, **kwargs):
    analyses.geomorphon(
        scanned_elev, new="geomorphon", search=15, skip=6, flat=1, dist=0, env=env
    )
    rules = """
    1:3:1:3
    4:4:3
    5:7:6
    8:9:9
    10:10:10
    """
    gs.write_command(
        "r.recode",
        input="geomorphon",
        output="geomorphon_recoded",
        stdin=rules,
        rules="-",
        env=env,
    )
    gs.run_command("r.colors", map="geomorphon_recoded", raster="geomorphon", env=env)
    gs.run_command("r.category", map="geomorphon_recoded", raster="geomorphon", env=env)
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
        step=5,
        flags="t",
        env=env,
    )
