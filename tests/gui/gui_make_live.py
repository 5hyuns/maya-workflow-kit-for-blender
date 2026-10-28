"""Live reference viewport picking, native Outliner colour/management and history/undo."""
import os
import sys
from importlib import import_module

import bpy
import numpy as np
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win, screenshot

C = {}


def mod(name):
    return import_module(MODULE+'.'+name)


def override():
    a, r = view3d()
    return bpy.context.temp_override(window=win(), area=a, region=r)


def reference():
    return bpy.data.objects[C.get('name', 'LiveReference')]


def outliner():
    area = next(a for a in win().screen.areas if a.type == 'OUTLINER')
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def shot(name):
    folder = os.environ.get('ALLSET_GUI_SHOTS', bpy.app.tempdir)
    path = os.path.join(folder, name+'.png')
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    pixels = np.empty(w*h*4, np.float32)
    img.pixels.foreach_get(pixels)
    bpy.data.images.remove(img)
    return pixels.reshape(h, w, 4)[..., :3]


def green(image):
    return ((image[..., 0] < .09) & (np.abs(image[..., 1]-.6) < .08)
            & (np.abs(image[..., 2]-84/255) < .08))


@step
def s_setup():
    mouse = setup()
    with override():
        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects['Cube']
        ob.name = 'LiveReference'
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.context.scene.unit_settings.system = 'NONE'
        bpy.context.tool_settings.use_snap = False
        bpy.context.tool_settings.snap_elements = {'INCREMENT'}
        a, r = view3d()
        a.spaces.active.overlay.show_wireframes = True
        r.data.view_rotation = Euler((.9, 0, .5)).to_quaternion()
        r.data.view_location = (0, 0, 0)
        r.data.view_distance = 8
        oa, _ = outliner()
        mod('ui.maya_outliner').setup(oa.spaces.active)
        C['matrix'] = ob.matrix_world.copy()
        bpy.ops.ed.undo_push(message='Before Make Live')
        bpy.ops.allset.make_live('EXEC_DEFAULT', True)
    ev('MOUSEMOVE', 'NOTHING', x=mouse[0], y=mouse[1])


@step
def s_wait():
    # A small Outliner at larger UI scales may scroll to the virtual camera rows.
    # Frame the reference before checking its visible label, without selecting it.
    oa, region = outliner()
    bpy.context.view_layer.objects.active = reference()
    with bpy.context.temp_override(window=win(), area=oa, region=region):
        bpy.ops.outliner.show_active()
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_live():
    check('Make Live locks and deselects the reference in the viewport', reference().hide_select and not reference().select_get())
    check('Make Live leaves snap preferences independent', not bpy.context.tool_settings.use_snap)
    check('status field displays the live object name', bpy.context.scene.allset_live_text == 'LiveReference')
    image = shot('make_live_wire_and_outliner')
    a, r = outliner()
    seen = mod('ui.outliner_joints').SEEN.get(r.as_pointer(), [])
    check('native Outliner row is identified without replacing its tree', ('LiveReference', 'LiveReference') in seen)
    crop = green(image[r.y:r.y+r.height, r.x:r.x+r.width])
    ys, xs = np.nonzero(crop)
    check('Outliner name renders the requested dark green', len(xs) > 12)
    if len(xs):
        C['row'] = (r.x+int(np.median(xs)), r.y+int(np.median(ys)))
    a, r = view3d()
    C['wire_count'] = int(green(image[r.y:r.y+r.height, r.x:r.x+r.width]).sum())
    check('wireframe on shaded draws the live mesh in #009954', C['wire_count'] > 150)
    p = location_3d_to_region_2d(r, r.data, Vector())
    C['centre'] = (r.x+round(p.x), r.y+round(p.y))
    ev('MOUSEMOVE', 'NOTHING', x=C['centre'][0], y=C['centre'][1])
    ev('LEFTMOUSE', 'PRESS', x=C['centre'][0], y=C['centre'][1])
    ev('LEFTMOUSE', 'RELEASE', x=C['centre'][0], y=C['centre'][1])


@step
def s_pick():
    check('viewport click cannot select the live reference', not reference().select_get())
    a, r = view3d()
    with override():
        bpy.ops.view3d.select_box(xmin=round(r.width/2-120), xmax=round(r.width/2+120),
                                 ymin=round(r.height/2-120), ymax=round(r.height/2+120), mode='SET')
    check('box selection also excludes live geometry', not reference().select_get())
    a.spaces.active.overlay.show_wireframes = False
    a.tag_redraw()


@step
def s_shaded():
    a, r = view3d()
    image = shot('make_live_shaded_only')
    count = int(green(image[r.y:r.y+r.height, r.x:r.x+r.width]).sum())
    check('shaded-only mode does not force a green wire overlay', count < max(15, C['wire_count']//10))
    a.spaces.active.shading.type = 'WIREFRAME'
    mod('preferences').get(bpy.context).maya_selection_wire = False
    a.tag_redraw()


@step
def s_wireframe():
    a, r = view3d()
    image = shot('make_live_wireframe')
    count = int(green(image[r.y:r.y+r.height, r.x:r.x+r.width]).sum())
    check('wireframe mode keeps Live green even with selection wire disabled', count > 150)
    a.spaces.active.shading.type = 'SOLID'
    a.spaces.active.overlay.show_wireframes = True
    mod('preferences').get(bpy.context).maya_selection_wire = True
    p = C.get('row')
    if p:
        ev('MOUSEMOVE', 'NOTHING', x=p[0], y=p[1])
        ev('LEFTMOUSE', 'PRESS', x=p[0], y=p[1])
        ev('LEFTMOUSE', 'RELEASE', x=p[0], y=p[1])


@step
def s_manage():
    check('restricted object remains addressable by native Outliner selection',
          reference() in mod('operators.live').selected(bpy.context, outliner=True))
    with override():
        bpy.ops.allset.live_list('EXEC_DEFAULT', True, action='REMOVE')
    check('Remove Selected operates on the Outliner-selected live reference',
          not mod('operators.live').objects(bpy.context.scene) and not reference().hide_select)


@step
def s_removed():
    image = shot('make_live_removed')
    a, r = outliner()
    count = int(green(image[r.y:r.y+r.height, r.x:r.x+r.width]).sum())
    check('turning Live off removes the green Outliner label', count < 8)
    with override():
        bpy.ops.allset.live_list('EXEC_DEFAULT', True, action='RECENT')


@step
def s_recalled():
    check('history recall restores the live target and its restriction',
          mod('operators.live').objects(bpy.context.scene) == [reference()] and reference().hide_select)
    with override():
        bpy.ops.ed.undo()


@step
def s_undo():
    check('Undo releases Live and restores selectability', not reference().hide_select and not mod('operators.live').objects(bpy.context.scene))
    with override():
        bpy.ops.ed.redo()


@step
def s_redo():
    check('Redo restores the live list and selection restriction', reference().hide_select and mod('operators.live').contains(bpy.context.scene, reference()))
    cls = mod('operators.live').ALLSET_MT_live_history
    original = cls.draw
    def spy(self, context):
        C['history_drawn'] = True
        original(self, context)
    cls.draw = spy
    with override():
        bpy.ops.allset.live_history('INVOKE_DEFAULT')


@step
def s_history():
    check('history arrow opens a surface-history menu', C.get('history_drawn', False))
    check('opening history does not change the live target', reference().hide_select)
    tap('ESC')
    check('reference transform remains unchanged', reference().matrix_world == C['matrix'])


@step
def s_middle_click():
    # Invoking the same operator with an MMB event exercises the arrow's toggle route.
    C['history_mouse'] = mod('operators.live').ALLSET_OT_live_history.invoke
    with override():
        from types import SimpleNamespace
        C['history_mouse'](SimpleNamespace(), bpy.context, SimpleNamespace(type='MIDDLEMOUSE'))
    check('middle-click history turns Live off', not reference().hide_select)


@step
def s_middle_undo():
    with override():
        bpy.ops.ed.undo()
    check('middle-click history has an undo step', reference().hide_select)
    reference().name = 'LiveRenamed'
    C['name'] = 'LiveRenamed'
    oa, _ = outliner()
    oa.spaces.active.filter_text = C['name']
    oa.tag_redraw()


@step
def s_search_rename():
    oa, region = outliner()
    image = shot('make_live_search_renamed')
    seen = mod('ui.outliner_joints').SEEN.get(region.as_pointer(), [])
    check('renamed live row keeps green while filtered in Outliner', (C['name'], C['name']) in seen and
          green(image[region.y:region.y+region.height, region.x:region.x+region.width]).sum() > 12)
    oa.spaces.active.filter_text = ''
    with override():
        for i in range(32):
            ob = bpy.data.objects.new(f'Filler {i:02}', None)
            bpy.context.scene.collection.objects.link(ob)
        parent = bpy.data.objects.new('Reference Parent', None)
        bpy.context.scene.collection.objects.link(parent)
        reference().parent = parent
    with bpy.context.temp_override(window=win(), area=oa, region=region):
        bpy.ops.outliner.show_hierarchy()


@step
def s_scroll():
    oa, region = outliner()
    x, y = region.x+region.width//2, region.y+region.height//2
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    for _ in range(35):
        ev('WHEELDOWNMOUSE', 'PRESS', x=x, y=y)


@step
def s_frame_live_after_scroll():
    oa, region = outliner()
    bpy.context.view_layer.objects.active = reference()
    with bpy.context.temp_override(window=win(), area=oa, region=region):
        bpy.ops.outliner.show_active()


@step
def s_scrolled():
    oa, region = outliner()
    image = shot('make_live_hierarchy_scrolled')
    seen = mod('ui.outliner_joints').SEEN.get(region.as_pointer(), [])
    check('live name keeps green after hierarchy expansion and scrolling', (C['name'], C['name']) in seen and
          green(image[region.y:region.y+region.height, region.x:region.x+region.width]).sum() > 12)


run()
