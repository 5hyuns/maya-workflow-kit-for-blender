"""#410 in a real UI, Move tool in mesh edit mode: a Ctrl+Shift+drag on a manipulator handle slides the selected
edges, and the "slide" label stays under the mouse for the whole drag, following it, like Maya's slide cursor; it
goes away when the drag ends and the keys are let go."""
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
SHOTS = os.environ.get('ALLSET_GUI_SHOTS') or tempfile.mkdtemp(prefix='allset_410_')


def mod(name):
    return import_module(MODULE + '.' + name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def hint():
    return getattr(mod('operators.manip'), 'SLIDE_HINT', {})


def hint_on():
    return bool(hint().get('region'))


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
    path = os.path.join(SHOTS, f'issue410_{name}.png')
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


def edge_co():
    ob = bpy.data.objects['Cube']
    return [v.co.copy() for v in bmesh.from_edit_mesh(ob.data).verts if v.select]


def running():
    return [op.bl_idname for op in win().modal_operators]


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
    C['co0'] = edge_co()


@step
def s_hover():
    C['a'] = z_arrow()
    ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x), y=int(C['a'].y))
    ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x) + 1, y=int(C['a'].y))
    C['a'].x += 1


@step
def s_plain():
    C['plain'] = bright_under_mouse('plain')
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    ev('LEFT_SHIFT', 'PRESS', ctrl=True, shift=True)


@step
def s_held():
    check("Ctrl+Shift over a Move handle: slide label on before the drag", hint_on())
    x, y = int(C['a'].x), int(C['a'].y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y, ctrl=True, shift=True)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y + 15, ctrl=True, shift=True)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y + 30, ctrl=True, shift=True)
    C['a'] = Vector((x, y + 30))


@step
def s_drag():
    ops = running()
    check(f"the drag is a slide ({ops})", any('slide' in o.lower() for o in ops))
    shown = bright_under_mouse('drag')
    check("during the slide drag the slide label stays on", hint_on())
    check(f"... drawn under the mouse ({C['plain']} -> {shown} bright pixels)", shown >= C['plain'] + 60)
    x, y = int(C['a'].x), int(C['a'].y)
    ev('MOUSEMOVE', 'NOTHING', x=x + 20, y=y + 15, ctrl=True, shift=True)
    C['a'] = Vector((x + 20, y + 15))


@step
def s_follow():
    _area, region = view3d()
    want = (int(C['a'].x) - region.x, int(C['a'].y) - region.y)
    pos = tuple(hint().get('pos', (0, 0)))
    check(f"... and follows the mouse ({pos} ~ {want})", hint_on() and abs(pos[0] - want[0]) <= 2
          and abs(pos[1] - want[1]) <= 2)
    shown = bright_under_mouse('follow')
    check(f"... drawn at the new mouse position ({shown} bright pixels)", shown >= C['plain'] + 60)
    ev('LEFTMOUSE', 'RELEASE', x=int(C['a'].x), y=int(C['a'].y), ctrl=True, shift=True)


@step
def s_released():
    check(f"the slide ended ({running()})", not any('slide' in o.lower() for o in running()))
    moved = max((a - b).length for a, b in zip(edge_co(), C['co0']))
    check(f"... and moved the edge ({moved:.3f})", moved > 1e-3)
    ev('LEFT_SHIFT', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


@step
def s_keys_up():
    check("with the drag over and the keys let go the label is off", not hint_on())


run()
