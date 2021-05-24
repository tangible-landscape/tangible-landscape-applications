import grass.script as gs
import analyses
from tangible_utils import get_environment


def run_cutfill(real_elev, scanned_elev, zexag, env, **kwargs):
    tmp = 'tmp_resampled'
    new = 'diff'
    gs.run_command('r.resamp.interp', input=real_elev, output=tmp,
                   method='bilinear', env=env)
    gs.mapcalc(f"{new} = {tmp} - {scanned_elev}", env=env)
    univar = gs.parse_command("r.univar", flags="g", map=real_elev, env=env)
    std1 = zexag * float(univar["stddev"])
    std2 = zexag * 2 * std1
    std3 = zexag * 3 * std1
    rules = [
        f"-1000000 black",
        f"-{std3} black",
        f"-{std2} 202:000:032",
        f"-{std1} 244:165:130",
        "0 247:247:247",
        f"{std1} 146:197:222",
        f"{std2} 5:113:176",
        f"{std3} black",
        f"1000000 black",
    ]
    gs.write_command("r.colors", map=new, rules="-", stdin="\n".join(rules), env=env)
    # analyses.difference(real_elev=real_elev, scanned_elev=scanned_elev,
    #                     new='diff', zexag=zexag, env=env)

