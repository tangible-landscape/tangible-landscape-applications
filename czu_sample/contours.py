import grass.script as gs


def run_aspect(real_elev, scanned_elev, env, **kwargs):
    info = gs.raster_info(scanned_elev)
    interval = (info["max"] - info["min"]) / 20.0
    # alternatively set fixed interval
    # interval = 10
    gs.run_command(
        "r.contour",
        input=scanned_elev,
        output="contours_main",
        step=interval * 5,
        flags="t",
        env=env,
    )
    gs.run_command(
        "r.contour",
        input=scanned_elev,
        output="contours",
        step=interval,
        flags="t",
        env=env,
    )
