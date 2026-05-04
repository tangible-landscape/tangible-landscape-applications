"""
Created on April 20 2026
Updated May 4 2026
@author: Everett Tucker
@description Combined Terrain, Patch, Water (Depression),
and Point-of-Interest export activity to Blender.
Each of these channels should be interpretable by the 
current Blender model, but can be extended for different
applications. 
"""

import os
import time
import sys
import shutil
import glob
from os.path import expanduser
import analyses
from tangible_utils import get_environment
from blender import blender_export_PNG, blender_send_file, blender_export_DEM, blender_export_vector
from activities import updateDisplay
import grass.script as gscript
from grass.exceptions import CalledModuleError


classes = {
    1: "terrain",
    2: "class_1",
    3: "class_2",
    4: "class_3",
    5: "class_4",
}


def run_dem(real_elev, scanned_elev, scanned_color, blender_path, eventHandler, env, **kwargs):
    """
    Exports the basic depth model to Blender
    """
    if scanned_color is None:
        print("No color!")
    else:
        print("We have color")
    print(f"Exporting files to Blender with Raster: {scanned_elev}, and Blender Path: {blender_path}")
    blender_export_DEM(raster=scanned_elev, name='terrain', time_suffix=False, path=blender_path, env=None)


def run_patches(real_elev, scanned_elev, scanned_color, blender_path, eventHandler, env, **kwargs):
    """
    Exports patch masks to blender corresponding to colored patches on the terrain model
    Uses a support vector machine classifier with optional hs colorspace
    """
    patches = 'patches'
    print("Running Patches!")

    analyses.classify_colors_svm(new=patches, 
                                group=scanned_color, 
                                compactness=2,
                                minsize=10,
                                hs_colorspace=True,
                                env=env)
    gscript.run_command('r.to.vect', flags='svt', input=patches, output=patches, type='area', env=env)
    
    # Changing base_cat to what I expect based on my color_patches.txt
    base_cat = [1]  # Probably what it should be

    # creates color table as temporary file
    # this is the training map from where the colors are taken
    # training = 'training_areas'
    training = "classification"  # Changing the name of the color training raster
    color_path = '/tmp/patch_colors.txt'
    if not os.path.exists(color_path):
        color_table = gscript.read_command('r.colors.out', map=training, env=env).strip()
        with open(color_path, 'w') as f:
            for line in color_table.splitlines():
                if line.startswith('nv') or line.startswith('default'):
                    continue
                elif float(line.split(' ')[0]) in base_cat:
                    continue
                else:
                    f.write(line)
                    f.write('\n')
    try:
        # Changed input from patches + "2gen" because that was undefined
        gscript.run_command('v.colors', map=patches, rules=color_path, env=env)
    except CalledModuleError:
        return

    # We grab different categories of mask, based on the different categories inside the parsed color scan
    try:
        gscript.run_command('r.mask', flags='r', env=env)
    except:
        pass
    cats = gscript.read_command('r.describe', flags='1ni', map=patches, env=env).strip()
    cats = [int(cat) for cat in cats.splitlines()]
    toexport = []   
    for cat in cats:
        map_name = "patch_" + classes[cat]
        # For some reason 1 is black and 0 is white
        gscript.mapcalc(map_name + ' = if(isnull({p}), 1, if({p} == {c}, 0, 1))'.format(p=patches, c=cat), env=env)
        gscript.run_command('r.colors', map=map_name, color='grey', flags='n', env=env)
        toexport.append(map_name)
    blender_send_file('empty.txt', path=blender_path)

    # Exporting PNG files to the Blender watch directory
    for png in toexport:
        blender_export_PNG(png, name=png, time_suffix=False, path=blender_path, env=env)


def run_water(real_elev, scanned_elev, scanned_color, blender_path, eventHandler, env, **kwargs):
    """
    Exports water assets to Blender based on depression analysis of the terrain
    """
    try:
        analyses.depression(scanned_elev=scanned_elev, new="ponds", repeat=4, filter_depth=2, env=env)
    except Exception as e:
        print(f"Water failed! {str(e)}")
        return
    
    water_offset = 2  # Lowering ponds so it fits into the terrain
    grow_radius = 4.01  # Growing ponds so they line up more seamlessly with the terrain
    print(f"Exporting water with offset: {water_offset} and growth factor {grow_radius}")
    gscript.mapcalc("{} = if(ponds, int(ponds + {} - {}), 0)"
                    .format("ponds_export", scanned_elev, water_offset), overwrite=True, env=env)
    gscript.run_command("r.grow", input="ponds_export", output="ponds_grown", radius=grow_radius, 
                        metric="euclidean", overwrite=True, env=env)
    
    blender_export_DEM(raster="ponds_grown", name="water", time_suffix=False, path=blender_path, env=env)


def run_pois(real_elev, scanned_elev, scanned_color, blender_path, eventHandler, env, **kwargs):
    """
    Locates points of interest on the terrain model indicated by cork markers
    Requires a calibrated filter_file generated by calibrate_filter_file
    """

    # Running analysis to get the locations
    filter_file = "calibrated_kernel.txt"
    vector_positions = "points_of_interest"
    analyses.locate_pins(depth_scan=scanned_elev,
                         output=vector_positions,
                         filter_file=filter_file,
                         env=env)
    
    print(f"Running Point of interest")
    blender_export_vector(vector=vector_positions, 
                          path=blender_path,
                          vtype="point",
                          name=vector_positions, 
                          z=False,
                          tmp_path="/tmp",
                          time_suffix=False, 
                          env=env)

