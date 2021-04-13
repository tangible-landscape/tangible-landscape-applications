from math import sqrt
import grass.script as gs
from activities import updateProfile
from TSP import solve_tsp_numpy
from tangible_utils import get_environment

import analyses


def dist(points, i, j):
    x2 = (points[i][0] - points[j][0]) * (points[i][0] - points[j][0])
    y2 = (points[i][1] - points[j][1]) * (points[i][1] - points[j][1])
    return sqrt(x2 + y2)


def create_end_points(env):
    info = gs.raster_info("scan")
    y1 = info["south"] + 2 * (info["north"] - info["south"]) / 10.0
    y2 = info["south"] + 8 * (info["north"] - info["south"]) / 10.0
    x1 = info["west"] + 2 * (info["east"] - info["west"]) / 10.0
    x2 = info["west"] + 8 * (info["east"] - info["west"]) / 10.0
    gs.write_command(
        "v.in.ascii",
        input="-",
        stdin="{x1}|{y1}\n{x2}|{y2}".format(x1=x1, x2=x2, y1=y1, y2=y2),
        output="trail_points",
        env=env,
    )
    return ((x1, y1), (x2, y2))


def run_trails(real_elev, scanned_elev, blender_path, eventHandler, env, **kwargs):
    resulting = "trail"
    trail = "trail"
    before = "scan_saved"
    # trim the edges to avoid noise being detected as markers
    info = gs.raster_info("scan")
    edge = (info["north"] - info["south"]) / 20
    env2 = get_environment(
        raster=scanned_elev,
        n="n-{}".format(edge),
        s="s+{}".format(edge),
        e="e-{}".format(edge),
        w="w+{}".format(edge),
    )
    analyses.change_detection(
        before=before,
        after=scanned_elev,
        change="change",
        height_threshold=[5, 30],
        cells_threshold=[5, 100],
        add=True,
        max_detected=5,
        debug=True,
        env=env2,
    )
    points = {}
    # if we have 'trail_points' vector, use this:
    # data = gs.read_command('v.out.ascii', input='trail_points', type='point', format='point', env=env).strip()
    # c1, c2 = data.splitlines()
    # c1 = c1.split('|')
    # c2 = c2.split('|')
    # points[0] = (float(c1[0]), float(c1[1]))
    # points[1] = (float(c2[0]), float(c2[1]))
    # otherwise we will generate them on the fly:
    points[0], points[1] = create_end_points(env)

    gs.run_command("v.edit", tool="create", map=trail, env=env)
    # detected points
    points_raw = (
        gs.read_command("v.out.ascii", input="change", type="point", format="point")
        .strip()
        .split()
    )
    i = 2
    for point in points_raw:
        point = point.split("|")
        point = (float(point[0]), float(point[1]))
        points[i] = point
        i += 1
    length = len(points)
    if length == 2:
        gs.mapcalc("{} = null()".format(resulting), env=env)
        event = updateProfile(points=[])
        eventHandler.postEvent(receiver=eventHandler.activities_panel, event=event)
        return

    # distance matrix
    D = []
    for i in range(length):
        D.append([0] * length)
    for p1 in range(0, length - 1):
        for p2 in range(p1 + 1, length):
            d = dist(points, p1, p2)
            D[p1][p2] = d
            D[p2][p1] = d
    # 0 distance for start and end to make sure it's always connected
    D[0][1] = 0
    D[1][0] = 0

    # solve
    solution = solve_tsp_numpy(D, optim_steps=10)
    # rearange solutions to start in start point
    ind1 = solution.index(0)
    ind2 = solution.index(1)
    if ind2 > ind1:
        solution = solution[::-1]
    ind = solution.index(0)
    solution = solution[ind:] + solution[:ind]
    profile_points = []
    for i in solution:
        profile_points.append(points[i])

    # friction
    friction = "friction"
    gs.mapcalc("{} = 0".format(friction), env=env)
    tmp_dir = "tmp_dir"
    tmp_cost = "tmp_cost"
    tmp_drain = "tmp_drain"

    gs.run_command("v.edit", tool="create", map=trail, env=env)
    for i in range(len(solution) - 1):
        gs.run_command(
            "r.walk",
            elevation=before,
            friction=friction,
            output=tmp_cost,
            outdir=tmp_dir,
            start_coordinates=points[solution[i]],
            stop_coordinates=points[solution[i + 1]],
            flags="k",
            env=env,
        )
        gs.run_command(
            "r.drain",
            input=tmp_cost,
            direction=tmp_dir,
            output=tmp_drain,
            drain=tmp_drain,
            start_coordinates=points[solution[i + 1]],
            flags="d",
            env=env,
        )
        gs.run_command("v.patch", input=tmp_drain, output=trail, flags="a", env=env)

    env2 = get_environment(raster=before)
    # slope along line
    gs.run_command(
        "v.to.rast", input=trail, type="line", output="trail_dir", use="dir", env=env2
    )
    gs.run_command(
        "r.slope.aspect",
        elevation=before,
        slope="saved_slope",
        aspect="saved_aspect",
        env=env2,
    )
    gs.mapcalc(
        "slope_dir = abs(atan(tan({slope}) * cos({aspect} - {trail_dir})))".format(
            slope="saved_slope", aspect="saved_aspect", trail_dir="trail_dir"
        ),
        env=env2,
    )
    # set new color table
    colors = ["0 green", "5 green", "5 yellow", "10 yellow", "10 red", "90 red"]
    gs.write_command(
        "r.colors", map="slope_dir", rules="-", stdin="\n".join(colors), env=env2
    )
    # increase thickness
    gs.run_command("r.grow", input="slope_dir", radius=1.1, output=resulting, env=env2)

    # update profile
    event = updateProfile(points=profile_points)
    eventHandler.postEvent(receiver=eventHandler.activities_panel, event=event)
