"""#380 in the UV Editor: with UV Sync Selection on or off and in vertex, edge or face mode, a vertex / edge / face is
extruded with Ctrl+E and the manipulator's arrow is dragged out (the kit rebuilds the mesh while it is dragged), then
a click in the UV Editor on a UV vertex / edge / face of another face selects that element (UV Sync Selection: the
mesh element), and the mesh keeps its component mode."""

import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, view3d, win  # noqa: E402

C = {}
CASES = [(sync, mode) for sync in (True, False) for mode in ('VERT', 'EDGE', 'FACE')]


def mod(name):
    return import_module(MODULE + name)


def cube():
    return bpy.data.objects["Cube"]


def v3d_ctx():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def uv_region():
    return C["uv_area"], next(r for r in C["uv_area"].regions if r.type == 'WINDOW')


def click(x, y):
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x + 1, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x + 1, y=y)


def park():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"] - 300, y=C["y"] - 200)


def arrow_point(frac=0.35):
    """Window point on the extrude manipulator's Z arrow and the arrow's screen direction."""
    area, region = view3d()
    in_view = mod(".ui.in_view")
    with v3d_ctx():
        ob, r = in_view.record(bpy.context)
        c, axes, _k = in_view.manip_frame(ob, r)
        upx = in_view.unit_px(bpy.context)
    rv3d = area.spaces.active.region_3d
    p0 = view3d_utils.location_3d_to_region_2d(region, rv3d, c)
    w = view3d_utils.region_2d_to_location_3d(region, rv3d, p0 + Vector((1, 0)), c) - c
    p = view3d_utils.location_3d_to_region_2d(region, rv3d, c + axes.col[2] * upx * w.length * frac)
    return region.x + round(p.x), region.y + round(p.y), (p - p0).normalized()


def target(mode):
    """(index, UV point) of an element on the lowest face: its centre, its first edge's middle, or just inside its
    first corner."""
    bm = bmesh.from_edit_mesh(cube().data)
    uv = bm.loops.layers.uv.active
    face = min(bm.faces, key=lambda f: f.calc_center_median().z)
    lp = face.loops[0]
    if mode == 'FACE':
        return face.index, sum((x[uv].uv for x in face.loops), Vector((0, 0))) / len(face.loops)
    if mode == 'EDGE':
        return lp.edge.index, (lp[uv].uv + lp.link_loop_next[uv].uv) / 2
    inside = (lp.link_loop_next[uv].uv - lp[uv].uv + lp.link_loop_prev[uv].uv - lp[uv].uv) * 0.02
    return lp.vert.index, lp[uv].uv + inside


def picked(sync, mode, index):
    """True when the element ``index`` is selected: in the mesh with UV Sync Selection, in the UVs without."""
    bm = bmesh.from_edit_mesh(cube().data)
    if sync:
        seq = {'VERT': bm.verts, 'EDGE': bm.edges, 'FACE': bm.faces}[mode]
        seq.ensure_lookup_table()
        return seq[index].select
    loops = [lp for f in bm.faces for lp in f.loops]
    if mode == 'FACE':
        return any(f.index == index and all(lp.uv_select_vert for lp in f.loops) for f in bm.faces)
    if mode == 'EDGE':
        return any(lp.edge.index == index and lp.uv_select_edge for lp in loops)
    return any(lp.vert.index == index and lp.uv_select_vert for lp in loops)


def case(sync, mode):
    name = f"UV Sync Selection {'on' if sync else 'off'}, {mode.lower()} mode"

    @step
    def s_select():
        ts = bpy.context.scene.tool_settings
        with v3d_ctx():
            bpy.ops.mesh.select_all(action='DESELECT')
        ts.use_uv_select_sync = sync
        ts.mesh_select_mode = (mode == 'VERT', mode == 'EDGE', mode == 'FACE')
        if not sync:
            ts.uv_select_mode = {'VERT': 'VERTEX', 'EDGE': 'EDGE', 'FACE': 'FACE'}[mode]
        bm = bmesh.from_edit_mesh(cube().data)
        if mode == 'FACE':
            max(bm.faces, key=lambda f: f.calc_center_median().z).select_set(True)
        elif mode == 'EDGE':
            max(bm.edges, key=lambda e: sum(v.co.z - v.co.y for v in e.verts)).select_set(True)
        else:
            max(bm.verts, key=lambda v: v.co.z - v.co.y + v.co.x).select_set(True)
        bm.select_flush_mode()
        bmesh.update_edit_mesh(cube().data)
        park()
        ev('E', 'PRESS', ctrl=True)
        ev('E', 'RELEASE', ctrl=True)

    @step
    def s_hover():
        x, y, _d = C["arrow"] = arrow_point()
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y + 1)

    @step
    def s_press():
        x, y, _d = C["arrow"]
        ev('LEFTMOUSE', 'PRESS', x=x, y=y + 1)

    @step
    def s_moves():
        x, y, d = C["arrow"]
        for i in range(1, 9):
            ev('MOUSEMOVE', 'NOTHING', x=x + round(d.x * 60 * i / 8), y=y + 1 + round(d.y * 60 * i / 8))

    @step
    def s_release():
        x, y, d = C["arrow"]
        ev('LEFTMOUSE', 'RELEASE', x=x + round(d.x * 60), y=y + 1 + round(d.y * 60))
        park()

    @step
    def s_click():
        bm = bmesh.from_edit_mesh(cube().data)
        C["mode_kept"] = sorted(bm.select_mode) == [mode]
        if not sync:      # every face selected in the mesh so its UVs show, no UV selected (the mode untouched)
            for f in bm.faces:
                f.select = True
                for lp in f.loops:
                    lp.uv_select_vert = False
                    lp.uv_select_edge = False
            bmesh.update_edit_mesh(cube().data)
        C["target"], co = target(mode)
        _area, region = uv_region()
        x, y = region.view2d.view_to_region(co.x, co.y, clip=False)
        click(region.x + int(x), region.y + int(y))

    @step
    def s_check():
        check(f"{name}: after the extrusion was dragged out the mesh keeps its component mode", C["mode_kept"])
        check(f"{name}: a click in the UV Editor selects the clicked {mode.lower()}",
              picked(sync, mode, C["target"]))
        park()


@step
def s_setup():
    C["x"], C["y"] = setup()
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    with v3d_ctx():
        bpy.ops.object.mode_set('EXEC_DEFAULT', True, mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide(number_cuts=1)
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
    # the Properties editor on the right becomes a UV Editor
    area = max((a for a in win().screen.areas if a.type == 'PROPERTIES'), key=lambda a: a.height)
    area.type = 'IMAGE_EDITOR'
    area.ui_type = 'UV'
    C["uv_area"] = area
    park()


@step
def s_uv_view():
    area, region = uv_region()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.image.view_all(fit_view=True)


for _sync, _mode in CASES:
    case(_sync, _mode)


run()
