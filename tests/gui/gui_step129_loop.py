"""Step 129, issue #22, in the Maya Workflow Kit layout: Maya double-click component selection.
Event simulation can't send DOUBLE_CLICK (step 73), so the double-click's operator (``allset.loop_pick``, the
"Mesh" LEFTMOUSE DOUBLE_CLICK item) is invoked at the simulated mouse; the picks before it are real select-tool
clicks (click, Shift+click), so the select history is the one a user makes."""

import os
import sys

import bmesh
import bpy
from bpy_extras import view3d_utils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, view3d, win  # noqa: E402

C = {}


def edit():
    ob = bpy.context.edit_object
    return ob, bmesh.from_edit_mesh(ob.data)


def screen_of(ob, co):
    area, region = view3d()
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, ob.matrix_world @ co)
    return region.x + int(p.x), region.y + int(p.y)


def front_row():
    """Edges of the cube's front face (-Y) on the middle horizontal row, sorted by x (3 after 2 cuts)."""
    ob, bm = edit()
    zs = sorted({round(v.co.z, 6) for v in bm.verts})
    z, y = zs[1], min(v.co.y for v in bm.verts)
    tol = (zs[1] - zs[0]) * 0.01
    es = [e for e in bm.edges if all(abs(v.co.y - y) < tol and abs(v.co.z - z) < tol for v in e.verts)]
    return ob, sorted(es, key=lambda e: sum(v.co.x for v in e.verts))


def mid(e):
    return (e.verts[0].co + e.verts[1].co) / 2


def invoke(between):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return bpy.ops.allset.loop_pick('INVOKE_DEFAULT', between=between)


@step
def s_setup():
    setup()
    bpy.ops.allset.layout_install()
    bpy.ops.wm.read_homefile(app_template="Maya_Workflow_Kit")


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
        ob = bpy.context.active_object
        ob.scale = (4, 4, 4)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=2)
        bpy.context.tool_settings.mesh_select_mode = (False, True, False)
        bpy.ops.mesh.select_all(action='DESELECT')
        rv3d = area.spaces.active.region_3d
        rv3d.view_perspective = 'ORTHO'
        rv3d.view_rotation = (0.7071068, 0.7071068, 0.0, 0.0)      # front view: -Y faces the camera
        bpy.ops.view3d.view_selected()


@step
def s_hover_edge():
    ob, row = front_row()
    C["x"], C["y"] = screen_of(ob, mid(row[1]))
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])


@step
def s_double_click():
    got = invoke(False)
    _ob, bm = edit()
    n = sum(1 for e in bm.edges if e.select)
    check(f"#22: double-click on an edge selects its edge loop ({got}, {n} edges, a loop round the cube = 12)",
          n == 12)
    bpy.ops.mesh.select_all(action='DESELECT')


@step
def s_pick_first():
    ob, row = front_row()
    x, y = screen_of(ob, mid(row[0]))
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_click_first():
    ev('LEFTMOUSE', 'PRESS')
    ev('LEFTMOUSE', 'RELEASE')


@step
def s_pick_second():
    _ob, bm = edit()
    check("the first pick selected one edge", sum(1 for e in bm.edges if e.select) == 1)
    ob, row = front_row()
    x, y = screen_of(ob, mid(row[2]))
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_shift_click_second():
    ev('LEFTMOUSE', 'PRESS', shift=True)
    ev('LEFTMOUSE', 'RELEASE', shift=True)


@step
def s_between():
    _ob, bm = edit()
    check("Shift+click added the second edge", sum(1 for e in bm.edges if e.select) == 2)
    got = invoke(True)
    ob, row = front_row()
    sel = [e for e in bmesh.from_edit_mesh(ob.data).edges if e.select]
    check(f"#22: Shift+double-click the second edge selects the run between ({got}, {len(sel)} edges)",
          len(sel) == 3 and all(e.select for e in row))


run()
