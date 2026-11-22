"""#438 in a real UI, mesh edit mode with edge selection: a marquee picks every edge it touches (inside it or across
its border), like Maya; Shift toggles, Ctrl removes; without selecting through, only edges seen in front count.
The clipping helper itself: tests/test_issue438_edge_marquee.py."""
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, view3d, win, MODULE  # noqa: E402

C = {}


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def bm():
    return bmesh.from_edit_mesh(bpy.context.edit_object.data)


def selected():
    with override():
        return {e.index for e in bm().edges if e.select}


def touched(rect):
    """Edges with a sampled point inside the window rect (an independent check of the kit's clipping)."""
    _area, region = view3d()
    x0, y0, x1, y1 = rect
    out = set()
    with override():
        mw = bpy.context.edit_object.matrix_world
        for e in bm().edges:
            a, b = mw @ e.verts[0].co, mw @ e.verts[1].co
            for k in range(201):
                p = location_3d_to_region_2d(region, region.data, a.lerp(b, k / 200))
                if p is not None and x0 <= region.x + p.x <= x1 and y0 <= region.y + p.y <= y1:
                    out.add(e.index)
                    break
    return out


def inside(rect):
    """Edges wholly inside the window rect."""
    _area, region = view3d()
    x0, y0, x1, y1 = rect
    out = set()
    with override():
        mw = bpy.context.edit_object.matrix_world
        for e in bm().edges:
            ps = [location_3d_to_region_2d(region, region.data, mw @ v.co) for v in e.verts]
            if all(p is not None and x0 <= region.x + p.x <= x1 and y0 <= region.y + p.y <= y1 for p in ps):
                out.add(e.index)
    return out


def drag(prefix, rect_of, shift=False, ctrl=False):
    def start():
        x0, y0, x1, y1 = C[prefix] = rect_of()
        ev('MOUSEMOVE', 'NOTHING', x=x0, y=y0)
        if ctrl:
            ev('LEFT_CTRL', 'PRESS', ctrl=True)
        if shift:
            ev('LEFT_SHIFT', 'PRESS', ctrl=ctrl, shift=True)
        ev('LEFTMOUSE', 'PRESS', x=x0, y=y0, ctrl=ctrl, shift=shift)

    def move():
        x0, y0, x1, y1 = C[prefix]
        for k in range(1, 6):
            ev('MOUSEMOVE', 'NOTHING', x=x0 + (x1 - x0) * k // 5, y=y0 + (y1 - y0) * k // 5, ctrl=ctrl, shift=shift)

    def release():
        x0, y0, x1, y1 = C[prefix]
        C[prefix + '_running'] = any(op.bl_idname == 'ALLSET_OT_edge_box' for op in win().modal_operators)
        ev('LEFTMOUSE', 'RELEASE', x=x1, y=y1, ctrl=ctrl, shift=shift)
        if shift:
            ev('LEFT_SHIFT', 'RELEASE', ctrl=ctrl)
        if ctrl:
            ev('LEFT_CTRL', 'RELEASE')

    for f in (start, move, release):
        f.__name__ = f"s_{prefix}_{f.__name__}"
        step(f)


def screen(world):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, world)
    return Vector((region.x + p.x, region.y + p.y))


def strip_rect():
    """A box across the middle of the grid's second row of faces: it crosses the edges across the row and holds
    the edges along it only partly."""
    a, b = screen(Vector((-1.5, -0.6, 0))), screen(Vector((1.5, 0.6, 0)))
    return int(min(a.x, b.x)), int(min(a.y, b.y)), int(max(a.x, b.x)), int(max(a.y, b.y))


def cube_rect():
    """A box round the whole cube."""
    pts = [screen(Vector((x, y, z))) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    return (int(min(p.x for p in pts)) - 20, int(min(p.y for p in pts)) - 20,
            int(max(p.x for p in pts)) + 20, int(max(p.y for p in pts)) + 20)


def mesh_setup(kind):
    with override():
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob)
        if kind == 'GRID':
            bpy.ops.mesh.primitive_grid_add(x_subdivisions=4, y_subdivisions=4, size=4)
        else:
            bpy.ops.mesh.primitive_cube_add()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.wm.tool_set_by_id(name='builtin.select_box')
        region = view3d()[1]
        if kind == 'GRID':
            region.data.view_rotation = Quaternion((1, 0, 0, 0))
            region.data.view_perspective = 'ORTHO'
        else:
            region.data.view_rotation = Quaternion((0.82, 0.42, 0.17, 0.34))
            region.data.view_perspective = 'PERSP'
        region.data.view_location = (0, 0, 0)
        region.data.view_distance = 9
        shading = view3d()[0].spaces.active.shading
        shading.type = 'SOLID'
        shading.show_xray = False
        bpy.ops.ed.undo_push(message="Test Setup")       # the state an undo of the marquee lands on


@step
def s_setup():
    C['mouse'] = setup()
    mesh_setup('GRID')


drag('plain', strip_rect)


@step
def s_check_plain():
    want, fully, got = touched(C['plain']), inside(C['plain']), selected()
    check(f"a plain edge marquee runs the kit's box ({C.get('plain_running')})", C.get('plain_running'))
    check(f"it picks the edges inside the box and the ones across its border ({len(got)} of {len(want)}; "
          f"{len(fully)} wholly inside)", got == want and len(want) > len(fully) > 0)
    C['after_plain'] = got


@step
def s_undo():
    with override():
        bpy.ops.ed.undo()
    check(f"one Ctrl+Z takes the marquee back ({len(selected())} selected)", not selected())
    with override():
        bpy.ops.ed.redo()
    check("redo brings it back", selected() == C['after_plain'])


drag('ctrl', strip_rect, ctrl=True)


@step
def s_check_ctrl():
    check(f"Ctrl+marquee removes the touched edges ({len(selected())} left)", not selected())


@step
def s_cube():
    mesh_setup('CUBE')
    import_module(MODULE + ".preferences").get().select_through = False


drag('front', cube_rect)


@step
def s_check_front():
    got = selected()
    check(f"without selecting through, the edges hidden behind the cube stay unpicked ({len(got)} of 12, 9 in front)",
          len(got) == 9)
    with override():
        bpy.ops.mesh.select_all(action='DESELECT')
    import_module(MODULE + ".preferences").get().select_through = True


drag('through', cube_rect)


@step
def s_check_through():
    check(f"selecting through, every edge in the box is picked ({len(selected())} of 12)", len(selected()) == 12)


drag('toggle', strip_rect, shift=True)


@step
def s_check_toggle():
    want = set(range(12)) - touched(C['toggle'])
    check(f"Shift+marquee toggles the touched edges ({len(selected())} selected, {len(want)} expected)",
          selected() == want)


run()
