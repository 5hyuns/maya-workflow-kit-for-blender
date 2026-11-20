"""#391 in a real UI, Move tool in mesh edit mode: while Ctrl+Shift is held over a manipulator handle, a "slide"
label shows under the mouse, like Maya's slide cursor; it goes away when a key is let go, when the mouse leaves the
handle, and it never shows in object mode."""
import os
import sys
import tempfile
from importlib import import_module

import bmesh
import bpy
import numpy as np
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, px, run, screenshot, setup, step, view3d, win, MODULE  # noqa: E402

C = {}
SHOTS = os.environ.get('ALLSET_GUI_SHOTS') or tempfile.mkdtemp(prefix='allset_391_')


def mod(name):
    return import_module(MODULE + '.' + name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def hint_on():
    return bool(getattr(mod('operators.manip'), 'SLIDE_HINT', {}).get('region'))


def screen(world):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, world)
    return Vector((region.x + p.x, region.y + p.y))


def z_arrow():
    """Window point on the Move manipulator's Z arrow (half way) of the current selection."""
    with override():
        centre, frame, _otype = mod('ui.manipulator').pivot_frame(bpy.context, 'TRANSLATE')
        _area, region = view3d()
        size = region.data.view_distance * 0.02
        p0, p1 = screen(centre), screen(centre + frame.col[2].normalized() * size)
        n = mod('ui.manipulator').ARROW_PX * bpy.context.preferences.view.gizmo_size / 75.0 * \
            bpy.context.preferences.system.ui_scale
    return p0 + (p1 - p0).normalized() * n * 0.6


def bright_under_mouse(name):
    """Near-white pixels in a box just below the mouse, read from a window screenshot."""
    path = os.path.join(SHOTS, f'issue391_{name}.png')
    screenshot(path)
    img = bpy.data.images.load(path)
    w, h = img.size
    pix = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(pix)
    bpy.data.images.remove(img)
    pix = pix.reshape(h, w, 4)
    x0, y0 = int(C['a'].x), int(C['a'].y)
    box = pix[max(0, y0 - px(60)):max(0, y0 - px(4)), max(0, x0 - px(20)):min(w, x0 + px(80)), :3]
    return int((box > 0.85).all(axis=2).sum())


def hover():
    C['a'] = z_arrow()
    ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x), y=int(C['a'].y))
    ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x) + 1, y=int(C['a'].y))
    C['a'].x += 1


@step
def s_setup():
    setup()
    with override():
        ob = bpy.data.objects['Cube']
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.wm.tool_set_by_id(name='builtin.move')
        region = view3d()[1]
        region.data.view_rotation = Quaternion((0.82, 0.42, 0.17, 0.34))
        region.data.view_location = (0, 0, 0)
        region.data.view_distance = 9
        mod('preferences').get(bpy.context).transform_constraint = 'NONE'
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='DESELECT')
        b = bmesh.from_edit_mesh(bpy.context.edit_object.data)
        for e in b.edges:
            if all(abs(v.co.x - 1) < 1e-4 and abs(v.co.z - 1) < 1e-4 for v in e.verts):
                e.select_set(True)
        b.select_flush_mode()
        bmesh.update_edit_mesh(bpy.context.edit_object.data)


@step
def s_hover():
    hover()


@step
def s_plain():
    C['plain'] = bright_under_mouse('plain')
    check("hovering a handle without keys: no slide label", not hint_on())
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    ev('LEFT_SHIFT', 'PRESS', ctrl=True, shift=True)


@step
def s_held():
    shown = bright_under_mouse('ctrl_shift')
    check("Ctrl+Shift over a Move handle in edit mode: slide state on", hint_on())
    check(f"... a label is drawn under the mouse ({C['plain']} -> {shown} bright pixels)", shown >= C['plain'] + 15)
    ev('LEFT_SHIFT', 'RELEASE', ctrl=True)


@step
def s_shift_up():
    check("letting Shift go ends the slide label", not hint_on())
    ev('LEFT_SHIFT', 'PRESS', ctrl=True, shift=True)


@step
def s_again():
    check("pressing Shift again shows it again", hint_on())
    _a, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + int(r.width * 0.2), y=r.y + int(r.height * 0.2), ctrl=True, shift=True)


@step
def s_left():
    check("moving off the handle with Ctrl+Shift held ends the slide label", not hint_on())
    C['a'] = z_arrow()
    ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x), y=int(C['a'].y), ctrl=True, shift=True)
    ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x) + 1, y=int(C['a'].y), ctrl=True, shift=True)
    C['a'].x += 1


@step
def s_back():
    shown = bright_under_mouse('back')
    check("coming back onto the handle with Ctrl+Shift still held shows the label again", hint_on())
    check(f"... drawn under the mouse ({shown} bright pixels)", shown >= C['plain'] + 15)
    ev('LEFT_SHIFT', 'RELEASE', ctrl=True)
    ev('LEFT_SHIFT', 'PRESS', ctrl=True, shift=True)


@step
def s_mmb():
    check("label on before the middle-drag", hint_on())
    ev('MIDDLEMOUSE', 'PRESS', x=int(C['a'].x), y=int(C['a'].y), ctrl=True, shift=True)
    ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x), y=int(C['a'].y) - 20, ctrl=True, shift=True)


@step
def s_mmb_drag():
    running = [op.bl_idname for op in win().modal_operators]
    check(f"a Ctrl+Shift+middle-drag ends the label ({running})", not hint_on())
    ev('MIDDLEMOUSE', 'RELEASE', ctrl=True, shift=True)


@step
def s_mmb_done():
    ev('LEFT_SHIFT', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


@step
def s_rehover():
    hover()


@step
def s_rekeys():
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    ev('LEFT_SHIFT', 'PRESS', ctrl=True, shift=True)


@step
def s_rmb():
    check("label on again before the marking menu", hint_on())
    ev('RIGHTMOUSE', 'PRESS', x=int(C['a'].x), y=int(C['a'].y), ctrl=True, shift=True)


@step
def s_rmb_open():
    running = [op.bl_idname for op in win().modal_operators]
    check(f"while the Ctrl+Shift+right-button marking menu is open the label is off ({running})", not hint_on())
    ev('ESC', 'PRESS', ctrl=True, shift=True)
    ev('ESC', 'RELEASE', ctrl=True, shift=True)
    ev('RIGHTMOUSE', 'RELEASE', ctrl=True, shift=True)


@step
def s_rmb_done():
    ev('LEFT_SHIFT', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')
    with override():
        bpy.ops.object.mode_set(mode='OBJECT')


@step
def s_object_hover():
    hover()


@step
def s_object_keys():
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    ev('LEFT_SHIFT', 'PRESS', ctrl=True, shift=True)


@step
def s_object_check():
    check("object mode: Ctrl+Shift over a handle shows no slide label", not hint_on())
    ev('LEFT_SHIFT', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


run()
