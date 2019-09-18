# -*- coding: utf-8 -*-
"""
@brief transfer1

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author: Anna Petrasova (akratoc@ncsu.edu)
"""
from datetime import datetime
import analyses
from tangible_utils import get_environment
from activities import updateDisplay, updateProfile
from grass.pygrass.vector import VectorTopo
import grass.script as gscript


def run_road(real_elev, scanned_elev, eventHandler, env, **kwargs):
    env2 = get_environment(raster=real_elev)
    before = 'scan_saved'
    analyses.change_detection(before=before, after=scanned_elev,
                              change='change', height_threshold=[12, 80], cells_threshold=[3, 70], add=True, max_detected=1, debug=True, env=env)
    point = gscript.read_command('v.out.ascii', input='change',
                                 type='point', format='point', env=env).strip()

    conn = 'transfer_connection'
    drain = 'transfer_drain'
    resulting = "transfer_slopedir"
    if point:
        x, y, cat = point.split('|')
        gscript.run_command('r.drain', input='transfer_cost', direction='transfer_costdir', output=conn,
                            start_points='change', drain=conn, flags='d', env=env2)

        gscript.run_command('v.to.rast', input=conn, type='line', output=conn + '_dir', use='dir', env=env2)
        gscript.mapcalc("slope_dir = abs(atan(tan({slope}) * cos({aspect} - {line_dir})))".format(slope='transfer_slope',
                        aspect='transfer_aspect', line_dir=conn + '_dir'), env=env2)
        # set new color table
        colors = ['0 green', '5 green', '5 yellow', '12 yellow', '12 red', '90 red']
        gscript.write_command('r.colors', map='slope_dir', rules='-', stdin='\n'.join(colors), env=env2)
        # increase thickness

        gscript.run_command('r.grow', input='slope_dir', radius=1.8, output=resulting, env=env2)

        # drain
        gscript.run_command('r.drain', input=real_elev, output=drain,
                            start_points='change', drain=drain, env=env2)

        gscript.run_command('r.viewshed', input=real_elev, output='transfer_viewshed', observer_elevation=67,
                            coordinates=[x, y], flags='b', env=env2)
        gscript.write_command('r.colors', map='transfer_viewshed', rules='-', stdin='0 black', env=env2)

        env3 = get_environment(raster='transfer_road')
        gscript.mapcalc('visible_road = if(transfer_viewshed == 1 && ! isnull(transfer_road), 1, null())', env=env3)
        #road_full = float(gscript.parse_command('r.univar', map='transfer_road', flags='g', env=env3)['n'])
        road_full = 500  # number of road cells
        try:
            road_v = float(gscript.parse_command('r.univar', map='visible_road', flags='g', env=env3)['n'])
        except KeyError:
            road_v = 0
        event = updateDisplay(value=int(100 * road_v / road_full))

        with VectorTopo(conn, mode='r') as v:
            try:
                line = v.read(1)
                event2 = updateProfile(points=[(line[0].x, line[0].y), (line[-1].x, line[-1].y)])
            except IndexError:
                 event2 = updateProfile(points=[])
    else:
        gscript.run_command('v.edit', map=conn, tool='create', env=env)
        gscript.run_command('v.edit', map=drain, tool='create', env=env)
        gscript.mapcalc('{} = null()'.format(resulting), env=env)
        gscript.mapcalc('{} = null()'.format('transfer_viewshed'), env=env)
        event = updateDisplay(value=None)
        event2 = updateProfile(points=[])

    # update viewshed score
    eventHandler.postEvent(receiver=eventHandler.activities_panel, event=event)
    eventHandler.postEvent(receiver=eventHandler.activities_panel, event=event2)

    # copy results
    if point:
        postfix = datetime.now().strftime('%H_%M_%S')
        prefix = 'transfer1'
        gscript.run_command('g.copy', vector=['change', '{}_change_{}'.format(prefix, postfix)],
                            raster=['visible_road', '{}_visible_road_{}'.format(prefix, postfix)], env=env)
        gscript.run_command('g.copy', raster=['slope_dir', '{}_slope_dir_{}'.format(prefix, postfix)], env=env)
