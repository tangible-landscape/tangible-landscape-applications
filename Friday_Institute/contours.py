import grass.script as gs
from activities import updateProfile


def run_contours(real_elev, scanned_elev, eventHandler, env, **kwargs):
    gs.run_command("r.colors", map=scanned_elev, raster="topography", env=env)
    info = gs.raster_info(scanned_elev)
    interval = (info["max"] - info["min"]) / 20.0
    # alternatively set fixed interval
    interval = 5
    gs.run_command(
        "r.contour",
        input=scanned_elev,
        output="contours",
        step=interval,
        flags="t",
        env=env,
    )
    # update profile
    event = updateProfile(points=points(real_elev))
    eventHandler.postEvent(receiver=eventHandler.activities_panel, event=event)


def points(real_elev):
    info = gs.raster_info(real_elev)
    y1 = y2 = (info["north"] + info["south"]) / 2
    x1 = info["west"] + 1 * (info["east"] - info["west"]) / 10.0
    x2 = info["west"] + 9 * (info["east"] - info["west"]) / 10.0
    return ((x1, y1), (x2, y2))


def calib_topography(real_elev, scanned_elev, env, **kwargs):
    p1, p2 = points(real_elev)
    x1, y1 = p1
    x2, y2 = p2
    gs.write_command(
        "v.in.ascii",
        input="-",
        stdin="{x1}|{y1}\n{x2}|{y2}".format(x1=x1, x2=x2, y1=y1, y2=y2),
        output="freeplay_points",
        env=env,
    )
    line = "L 2 1\n"
    line += f"{x1} {y1}\n"
    line += f"{x2} {y2}\n"
    line += "1 1"
    gs.write_command(
        "v.in.ascii",
        input="-",
        stdin=line,
        output="freeplay_line",
        format="standard",
        flags="n",
        env=env,
    )

    info = gs.raster_info(real_elev)
    gs.mapcalc(f"topography = rand({info['min']},{1*info['max']})", seed=1, env=env)
    colors = [
        "0% 50:121:70",
        "20% 90:148:80",
        "40% 148:174:92",
        "60% 224:205:103",
        "80% 186:151:74",
        "100% 159:100:44",
        f"{3*info['max']} black",
    ]
    gs.write_command(
        "r.colors", map="topography", stdin="\n".join(colors), rules="-", env=env
    )
