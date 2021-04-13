import grass.script as gs
import analyses
from tangible_utils import get_environment


def run_cutfill(real_elev, scanned_elev, env, **kwargs):
    # this doesn't need to be computed on the fly
    dem_env = get_environment(raster=real_elev)
    gs.run_command(
        "r.contour",
        input=real_elev,
        output="contours_dem",
        step=5,
        flags="t",
        env=dem_env,
    )

    # compute difference and set color table using standard deviations
    gs.mapcalc("diff = {r} - {s}".format(r=real_elev, s=scanned_elev), env=env)
    gs.mapcalc("absdiff = abs(diff)", env=env)
    univar = gs.parse_command("r.univar", flags="g", map="absdiff", env=env)
    std1 = float(univar["stddev"])
    std2 = 2 * std1
    maxv = float(univar["max"]) + 1
    rules = [
        f"-{maxv} black",
        f"-{std2} 202:000:032",
        f"-{std1} 244:165:130",
        "0 247:247:247",
        f"{std1} 146:197:222",
        f"{std2} 5:113:176",
        f"{maxv} black",
    ]
    gs.write_command("r.colors", map="diff", rules="-", stdin="\n".join(rules), env=env)
