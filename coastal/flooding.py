import uuid

import analyses
import grass.script as gscript
from grass.exceptions import CalledModuleError

from tangible_utils import updateGUIEvt

def run_flooding(real_elev, scanned_elev, env, **kwargs):
    seed = [703758.79476,11471.6200873]
    lake = "lake"
    buildings = 'buildings'
    analyses.rlake(scanned_elev, new=lake, base=real_elev, env=env, seed=seed, level=3)
    lines = gscript.read_command('r.univar', flags='t', quiet=True, map=lake, zones=buildings, env=env).strip()
    cats = []
    if lines:
        lines = lines.splitlines()
        for line in lines[1:]:
            cats.append(line.split('|')[0])
    name = 'flooded'
    gscript.run_command('v.extract', input=buildings, output=name, flags='t', cats=','.join(cats), env=env)
    max_rounds = 5
    before = gscript.read_command('v.db.select', flags='c', map='score', columns='score', env=env).strip()
    num_rounds = len(before.split()) + 1
    if num_rounds > max_rounds:
        num_rounds = 1
        before = ' '
        gscript.run_command('v.db.update', map='score', layer=1, column='score', value=' ', env=env)
    gscript.run_command('v.db.update', map='score', layer=1, column='score',
                        value=before + ' ' + str(num_rounds) + ':' + str(len(cats)), env=env)

def button_breach(eventHandler, env, **kwargs):
    gscript.run_command('v.extract', input="ridge_points", output="breach", layer=1, random=1, flags='t', env=env)
    event = updateGUIEvt(eventHandler.GetId())
    eventHandler.postEvent(receiver=eventHandler, event=event)
