import grass.script as gs
from tangible_utils import get_environment


def run_aspect(real_elev, scanned_elev, env, **kwargs):
    gs.run_command("r.slope.aspect", elevation=scanned_elev, aspect="aspect", env=env)
    # reclassify using rules passed as a string to standard input
    # 0:45:2 means reclassify interval 0 to 45 degrees to category 2
    # rules = ['225:315:3', '315:360:2', '0:45:2', '45:135:1', '135:225:4']
    # gs.write_command('r.recode', input='aspect', output='aspect_class',
    #                  rules='-', stdin='\n'.join(rules), env=env)
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
