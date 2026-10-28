"""Live labels with the native restriction columns from the user's Maya layout."""
import os
import sys
from importlib import import_module

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, view3d, win, screenshot

C = {}


def outliner():
    area = next(a for a in win().screen.areas if a.type == 'OUTLINER')
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def inspect(name):
    area, region = outliner()
    labels = import_module(MODULE+'.ui.outliner_joints')
    seen = {ob for ob, _label in labels.SEEN.get(region.as_pointer(), ())}
    check(name+': both actual pCube names are identified', seen == C['names'])
    path = os.path.join(os.environ.get('ALLSET_GUI_SHOTS', bpy.app.tempdir), name+'.png')
    screenshot(path)
    image = bpy.data.images.load(path, check_existing=False)
    w, h = image.size
    data = np.empty(w*h*4, dtype=np.float32)
    image.pixels.foreach_get(data)
    bpy.data.images.remove(image)
    crop = data.reshape(h, w, 4)[region.y:region.y+region.height, region.x:region.x+region.width, :3]
    green = ((crop[..., 0] < .09) & (np.abs(crop[..., 1]-.6) < .08)
             & (np.abs(crop[..., 2]-84/255) < .08))
    check(name+': visible native Outliner names render dark green', int(green.sum()) > 30)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_live():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        for i in range(2):
            bpy.ops.mesh.primitive_cube_add(location=(i*3, 0, 0))
            bpy.context.object.name = 'pCube'+str(i+1)
        refs = [bpy.data.objects['pCube1'], bpy.data.objects['pCube2']]
        for ob in bpy.context.selected_objects:
            ob.select_set(False)
        for ob in refs:
            ob.select_set(True)
        bpy.context.view_layer.objects.active = refs[-1]
        bpy.ops.allset.make_live('EXEC_DEFAULT', True)
    C['names'] = {ob.name for ob in refs}
    live = import_module(MODULE+'.operators.live')
    check('multi-object Make Live registers both references', set(live.objects(bpy.context.scene)) == set(refs))
    space = outliner()[0].spaces.active
    space.show_restrict_column_viewport = True


@step
def s_monitor_column():
    inspect('live_with_monitor_column')
    space = outliner()[0].spaces.active
    for prop in ('show_restrict_column_select', 'show_restrict_column_hide', 'show_restrict_column_render'):
        setattr(space, prop, True)


@step
def s_all_columns():
    inspect('live_with_all_restriction_columns')
    space = outliner()[0].spaces.active
    for prop in ('show_restrict_column_select', 'show_restrict_column_hide', 'show_restrict_column_render', 'show_restrict_column_viewport'):
        setattr(space, prop, False)


@step
def s_without_columns():
    inspect('live_without_restriction_columns')


run()
