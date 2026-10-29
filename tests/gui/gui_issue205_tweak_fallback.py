"""Issue #205 in a real UI: the Move / Rotate tool's Drag fallback is Blender's Tweak (the state a user startup file
or session can leave in the workspace). A drag off the manipulator is still Maya's marquee — with the tool already
active (no new W press), on the mesh in object mode and in empty space in edit mode, Ctrl+drag deselects — nothing
moves, and the workspace's fallback setting stays Tweak (the kit doesn't write it).

Test idea and first version of the drag steps: Kevorama (issue #205)."""

import os
import sys

import bmesh
import bpy
from bpy_extras import view3d_utils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, step, setup, view3d, win  # noqa: E402

C = {}
TWEAK = "builtin.select"


def cube():
    return bpy.data.objects["Cube"]


def to_screen(co):
    area, region = view3d()
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, co)
    return region.x + int(p.x), region.y + int(p.y)


def rect():
    pts = [to_screen(cube().matrix_world @ v.co) for v in cube().data.vertices]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    m = 25
    return min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m


def selected():
    return sum(v.select for v in bmesh.from_edit_mesh(cube().data).verts)


def coords():
    return [tuple(round(c, 4) for c in v.co) for v in bmesh.from_edit_mesh(cube().data).verts]


def tool_op(idname, as_fallback=False):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.tool_set_by_id(name=idname, as_fallback=as_fallback, space_type='VIEW_3D')


def tool(mode):
    return win().workspace.tools.from_space_view3d_mode(mode)


def drag(a, b, ctrl=False):
    """press / moves / release in separate ticks (a transform or gesture modal started on the press)."""
    def press():
        if ctrl:
            ev('LEFT_CTRL', 'PRESS', ctrl=True)    # a keyboard event carries the modifier into the window state
        ev('MOUSEMOVE', 'NOTHING', x=a[0], y=a[1], ctrl=ctrl)
        ev('LEFTMOUSE', 'PRESS', x=a[0], y=a[1], ctrl=ctrl)

    def move():
        ev('MOUSEMOVE', 'NOTHING', x=(a[0] + b[0]) // 2, y=(a[1] + b[1]) // 2, ctrl=ctrl)
        ev('MOUSEMOVE', 'NOTHING', x=b[0], y=b[1], ctrl=ctrl)

    def release():
        ev('LEFTMOUSE', 'RELEASE', x=b[0], y=b[1], ctrl=ctrl)
        if ctrl:
            ev('LEFT_CTRL', 'RELEASE')
    return press, move, release


def steps(*fns):
    for fn in fns:
        step(fn)


# --- object mode, Move already active, drag starting on the mesh --------------------------------------------------

@step
def s_setup():
    setup()
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = None
    tool_op("builtin.move")
    tool_op(TWEAK, as_fallback=True)            # the Drag fallback a user startup file can carry
    C["loc"] = tuple(cube().location)
    check(f"setup: Move tool with Tweak fallback ({tool('OBJECT').idname}, {tool('OBJECT').idname_fallback})",
          (tool('OBJECT').idname, tool('OBJECT').idname_fallback) == ("builtin.move", TWEAK))
    x0, y0, x1, y1 = rect()
    C["obj_drag"] = (to_screen(cube().matrix_world.translation), (x1 + 20, y1 + 20))


steps(lambda: drag(*C["obj_drag"])[0](), lambda: drag(*C["obj_drag"])[1](), lambda: drag(*C["obj_drag"])[2]())


@step
def s_settle_obj():
    pass


@step
def s_object_marquee():
    check(f"object mode: a drag from the mesh = marquee, Cube selected ({cube().select_get()})", cube().select_get())
    check(f"object mode: nothing moved ({tuple(cube().location)})", tuple(cube().location) == C["loc"])
    check(f"the workspace's fallback stays Tweak ({tool('OBJECT').idname_fallback})",
          tool('OBJECT').idname_fallback == TWEAK)
    # edit mode, Rotate, one vertex selected (a tweak-drag would rotate / move it)
    bpy.context.view_layer.objects.active = cube()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(cube().data)
    bm.verts.ensure_lookup_table()
    bm.verts[0].select = True
    bmesh.update_edit_mesh(cube().data)
    tool_op("builtin.rotate")
    tool_op(TWEAK, as_fallback=True)
    C["co"] = coords()
    x0, y0, x1, y1 = rect()
    C["edit_drag"] = ((x0, y0), (x1, y1))
    check(f"edit mode: Rotate tool with Tweak fallback ({tool('EDIT_MESH').idname}, "
          f"{tool('EDIT_MESH').idname_fallback})",
          (tool('EDIT_MESH').idname, tool('EDIT_MESH').idname_fallback) == ("builtin.rotate", TWEAK))


steps(lambda: drag(*C["edit_drag"])[0](), lambda: drag(*C["edit_drag"])[1](), lambda: drag(*C["edit_drag"])[2]())


@step
def s_settle_edit():
    pass


@step
def s_edit_marquee():
    check(f"edit mode: a drag in empty space = marquee, selects 8 ({selected()})", selected() == 8)
    check("edit mode: nothing moved", coords() == C["co"])


steps(lambda: drag(*C["edit_drag"], ctrl=True)[0](), lambda: drag(*C["edit_drag"], ctrl=True)[1](),
      lambda: drag(*C["edit_drag"], ctrl=True)[2]())


@step
def s_settle_ctrl():
    pass


@step
def s_ctrl_marquee():
    check(f"edit mode: Ctrl+drag = Maya deselect marquee ({selected()})", selected() == 0)
    check("edit mode: still nothing moved", coords() == C["co"])
    check(f"the edit-mode fallback stays Tweak ({tool('EDIT_MESH').idname_fallback})",
          tool('EDIT_MESH').idname_fallback == TWEAK)


run()
