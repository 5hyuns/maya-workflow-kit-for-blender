"""#351 follow-up in a real UI: a pivot edit latched with a short D tap in component mode ends with its file. After
File > Open the next file's component mode has no pivot edit: W + a middle drag moves the components, not the 3D
cursor, and the next file gets the user's pivot point, not the edit's 3D cursor."""

import os
import sys
from importlib import import_module

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win  # noqa: E402

C = {}
OTHER = os.path.join(bpy.app.tempdir or os.environ.get("TEMP", "."), "gui_issue351_other.blend")


def mod(name):
    return import_module(MODULE + "." + name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def ts():
    return bpy.context.scene.tool_settings


def mesh_ob():
    return next(o for o in bpy.context.scene.objects if o.type == 'MESH')


def verts():
    o = bpy.context.edit_object
    return [o.matrix_world @ v.co for v in bmesh.from_edit_mesh(o.data).verts]


def edit_top():
    o = mesh_ob()
    for other in bpy.context.view_layer.objects:
        other.select_set(other == o)
    bpy.context.view_layer.objects.active = o
    with override():
        if bpy.context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
    bm = bmesh.from_edit_mesh(o.data)
    for v in bm.verts:
        v.select = v.co.z > 0
    bm.select_flush(True)
    bmesh.update_edit_mesh(o.data)


@step
def s_setup():
    C["mouse"] = setup()
    with override():
        bpy.ops.wm.save_as_mainfile(filepath=OTHER, copy=True)     # the next file: the same start scene
    bpy.context.scene.cursor.matrix = Matrix.Identity(4)
    ts().transform_pivot_point = 'BOUNDING_BOX_CENTER'
    edit_top()
    ev('MOUSEMOVE', 'NOTHING', x=C["mouse"][0], y=C["mouse"][1])
    tap('W')


@step
def s_tap_d():
    tap('D')                     # a short, unused press latches the pivot edit


@step
def s_latched():
    hold = mod("operators.hold")
    check(f"short D tap: the pivot edit stays on ({hold.COMPONENT.on}, {hold.COMPONENT.toggled})",
          hold.COMPONENT.on and hold.COMPONENT.toggled)
    with override():
        bpy.ops.wm.open_mainfile(filepath=OTHER)


@step
def s_opened():
    hold = mod("operators.hold")
    check(f"File > Open: no pivot edit in the next file ({hold.COMPONENT.on}), its pivot point is the user's "
          f"({ts().transform_pivot_point})", not hold.COMPONENT.on and ts().transform_pivot_point != 'CURSOR')
    bpy.context.scene.cursor.matrix = Matrix.Identity(4)
    edit_top()


@step
def s_w():       # a step after the mode change: the kit gives the new mode its tool from a 0 s timer first
    ev('MOUSEMOVE', 'NOTHING', x=C["mouse"][0], y=C["mouse"][1])
    tap('W')


@step
def s_before_mmb():
    with override():
        on = mod("ui.manipulator").pivot_edit(bpy.context)
    with override():
        t = bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH', create=False)
    check(f"W in the next file: the Move tool ({t.idname if t else None}) with the plain manipulator ({on})",
          t is not None and t.idname == "builtin.move" and not on)
    C["verts"] = verts()
    C["cursor"] = bpy.context.scene.cursor.location.copy()
    area, region = view3d()
    C["at"] = (region.x + int(region.width * 0.8), region.y + int(region.height * 0.3))
    ev('MOUSEMOVE', 'NOTHING', x=C["at"][0], y=C["at"][1])


@step
def s_mmb_press():
    with override():
        t = bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH', create=False)
    C["tool"] = t.idname if t else None
    ev('MIDDLEMOUSE', 'PRESS', x=C["at"][0], y=C["at"][1])


@step
def s_mmb_running():
    C["modal"] = [op.bl_idname for op in win().modal_operators]


for _i in range(1, 7):
    @step
    def s_mmb_move(i=_i):
        ev('MOUSEMOVE', 'NOTHING', x=C["at"][0] + 10 * i, y=C["at"][1] + 4 * i)


@step
def s_mmb_release():
    ev('MIDDLEMOUSE', 'RELEASE', x=C["at"][0] + 60, y=C["at"][1] + 24)


@step
def s_wait():
    pass


@step
def s_moved():
    moved = any((a - b).length > 1e-4 for a, b in zip(C["verts"], verts()))
    check(f"a middle drag moves the components (tool {C.get('tool')}, modal {C.get('modal')})", moved)
    check(f"... not the 3D cursor ({tuple(round(v, 3) for v in bpy.context.scene.cursor.location)})",
          (bpy.context.scene.cursor.location - C["cursor"]).length < 1e-6)


run()
