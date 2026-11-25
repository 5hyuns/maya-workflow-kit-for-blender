"""#548: with soft select on, a real drag on the Scale tool's centre handle (R) moves the points around the
selection with the falloff, like Move and Rotate; one Undo puts every point back."""
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, tap, view3d, win, MODULE  # noqa: E402

C = {}


def mod(name):
    return import_module(MODULE + '.' + name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def bm():
    return bmesh.from_edit_mesh(bpy.context.edit_object.data)


def coords():
    return [v.co.copy() for v in bm().verts]


def move(p):
    ev('MOUSEMOVE', 'NOTHING', x=round(p[0]), y=round(p[1]))


def handle_drag():
    return any(op.bl_idname == 'ALLSET_OT_manip_scale' for op in win().modal_operators)


@step
def s_setup():
    C['mouse'] = setup()
    ui = mod('ui.manipulator')
    original = ui.ALLSET_GGT_xform.draw_prepare

    def spy(self, context):
        original(self, context)
        C['group'] = self
    ui.ALLSET_GGT_xform.draw_prepare = spy
    with override():
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob)
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=10, y_subdivisions=10, size=4.0)
        ob = bpy.context.object
        ts = bpy.context.tool_settings
        ts.use_snap = False
        ts.transform_pivot_point = 'MEDIAN_POINT'
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        b = bm()
        for v in b.verts:
            v.select_set(abs(v.co.x) < 0.5 and abs(v.co.y) < 0.5)
        b.select_flush(True)
        bmesh.update_edit_mesh(ob.data)
        C['sel'] = [v.select for v in bm().verts]
        ts.proportional_size = 1.5
        ts.proportional_edit_falloff = 'SMOOTH'
        region = view3d()[1]
        region.data.view_rotation = Quaternion((1, 0, 0, 0))
        region.data.view_location = (0, 0, 0)
        region.data.view_distance = 7
        C['before'] = coords()
        bpy.ops.ed.undo_push(message='Soft scale fixture')
    move(C['mouse'])
    tap('B')        # soft select on (Maya key)


@step
def s_scale_tool():
    check('B turns soft select on', bpy.context.tool_settings.use_proportional_edit)
    tap('R')        # Scale tool (Maya key)


@step
def s_wait_tool():
    tool = bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH')
    check('R picks the Scale tool', tool is not None and tool.idname == 'builtin.scale')
    mod('ui.manipulator').ensure_tools(patched=True)
    view3d()[0].tag_redraw()


@step
def s_wait_draw():
    view3d()[0].tag_redraw()


@step
def s_hover():
    gz = next(g for g, role, _axis in C['group'].handles if role == 'CENTER')
    _area, region = view3d()
    xy = location_3d_to_region_2d(region, region.data, gz.matrix_world.translation)
    C['start'] = Vector((round(region.x + xy.x), round(region.y + xy.y)))
    move(C['start'])


@step
def s_press():
    ev('LEFTMOUSE', 'PRESS', x=round(C['start'].x), y=round(C['start'].y))


@step
def s_drag_start():
    move(C['start'] - Vector((8, 0)))


@step
def s_drag():
    check('the centre handle starts the Maya scale drag', handle_drag())
    C['end'] = C['start'] - Vector((60, 0))
    move(C['end'])


@step
def s_release():
    ev('LEFTMOUSE', 'RELEASE', x=round(C['end'].x), y=round(C['end'].y))


@step
def s_result():
    after = coords()
    before, sel = C['before'], C['sel']
    check('the selected points shrank toward the centre',
          all(a.length < b.length - 1e-4 for a, b, s in zip(after, before, sel) if s and b.length > 1e-6))
    near = [i for i, b in enumerate(before) if not sel[i] and b.length < 1.2]
    far = [i for i, b in enumerate(before) if b.length > 0.75 + 1.5 + 0.1]
    check('points inside the soft radius follow the scale',
          near and all((after[i] - before[i]).length > 1e-4 for i in near))
    check('points beyond the soft radius stay', far and all((after[i] - before[i]).length < 1e-6 for i in far))
    with override():
        bpy.ops.ed.undo()


@step
def s_undo():
    check('one Undo puts every point back',
          all((a - b).length < 1e-5 for a, b in zip(coords(), C['before'])))
    tap('B')


run()
