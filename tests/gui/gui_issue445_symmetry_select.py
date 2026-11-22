"""#445 in a real UI: with Symmetry on, clicking, Shift / Ctrl / Ctrl+Shift clicking, a marquee, a lasso and a
double-clicked edge loop also take the mirror partners, like Maya; Grow doesn't, Symmetry off doesn't, World symmetry
on a mesh away from the world plane has no partners. One Ctrl+Z takes a symmetric click back.
Partner lookup and the modifier rule: tests/test_issue445_symmetry_select.py."""
import math
import os
import sys

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, view3d, win  # noqa: E402

C = {}
B = {'VERT': [(0.5, 0.5, 1)], 'EDGE': [(0.5, 0.5, 1), (0.5, 0.0, 1)], 'FACE': [(0.25, 0.25, 1)]}
A = {'VERT': [(-0.5, -0.5, 1)]}


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def bm():
    return bmesh.from_edit_mesh(bpy.context.edit_object.data)


def r(v):
    return tuple(round(x, 3) + 0.0 for x in v)


def centre(el):
    return r(el.co) if isinstance(el, bmesh.types.BMVert) else r(sum((v.co for v in el.verts), Vector()) / len(el.verts))


def seq(dom):
    b = bm()
    return b.verts if dom == 'VERT' else (b.edges if dom == 'EDGE' else b.faces)


def picked(dom):
    with override():
        return {centre(el) for el in seq(dom) if el.select}


def centre_of(pts):
    return r(sum((Vector(p) for p in pts), Vector()) / len(pts))


def mirror(c, axis=0):
    c = list(c)
    c[axis] = -c[axis] + 0.0
    return tuple(c)


def symmetric(got, axis=0):
    return bool(got) and all(mirror(c, axis) in got for c in got)


def screen(pts, t=0.6):
    _area, region = view3d()
    p = Vector(pts[0]) * (1 - t) + Vector(pts[1]) * t if len(pts) == 2 else Vector(pts[0])
    s = location_3d_to_region_2d(region, region.data, bpy.context.edit_object.matrix_world @ p)
    return int(region.x + s.x), int(region.y + s.y)


def build(loc=(0, 0, 0), mode="OBJECT_X"):
    with override():
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob)
        bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide(number_cuts=3)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.wm.tool_set_by_id(name='builtin.select_box')
        region = view3d()[1]
        region.data.view_rotation = Vector((1.0, 0.75, 1.2)).to_track_quat('Z', 'Y')
        region.data.view_perspective = 'PERSP'
        region.data.view_location = loc
        region.data.view_distance = 7
        shading = view3d()[0].spaces.active.shading
        shading.type = 'SOLID'
        shading.show_xray = False
        bpy.ops.allset.symmetry(mode=mode)
        bpy.ops.ed.undo_push(message="Test Setup")


def dom_mode(dom):
    with override():
        bpy.ops.mesh.select_mode(type=dom)
        bpy.ops.mesh.select_all(action='DESELECT')


def click(name, pts, shift=False, ctrl=False, t=0.6):
    def move():
        C[name] = screen(pts, t)
        ev('MOUSEMOVE', 'NOTHING', x=C[name][0], y=C[name][1])

    def press():
        if ctrl:
            ev('LEFT_CTRL', 'PRESS', ctrl=True)
        if shift:
            ev('LEFT_SHIFT', 'PRESS', ctrl=ctrl, shift=True)
        ev('LEFTMOUSE', 'PRESS', ctrl=ctrl, shift=shift)
        ev('LEFTMOUSE', 'RELEASE', ctrl=ctrl, shift=shift)
        if shift:
            ev('LEFT_SHIFT', 'RELEASE', ctrl=ctrl)
        if ctrl:
            ev('LEFT_CTRL', 'RELEASE')

    def gap():
        pass                         # past the double-click time before the next press
    for f in (move, press, gap, gap):
        step(f)


def drag(name, pts, lasso=False):
    def start():
        if lasso:
            with override():
                bpy.ops.wm.tool_set_by_id(name='builtin.select_lasso')
        x, y = screen(pts)
        C[name] = ([(x, y - 18), (x + 18, y), (x, y + 18), (x - 18, y), (x, y - 17)] if lasso
                   else [(x - 14, y - 14), (x + 14, y + 14)])
        a = C[name][0]
        ev('MOUSEMOVE', 'NOTHING', x=a[0], y=a[1])
        ev('LEFTMOUSE', 'PRESS', x=a[0], y=a[1])

    def move():
        path = C[name]
        for a, b in zip(path, path[1:]):
            for k in range(1, 6):
                ev('MOUSEMOVE', 'NOTHING', x=int(a[0] + (b[0] - a[0]) * k / 5), y=int(a[1] + (b[1] - a[1]) * k / 5))

    def release():
        C[name + '_running'] = any(op.bl_idname == 'ALLSET_OT_symmetry_drag' for op in win().modal_operators)
        b = C[name][-1]
        ev('LEFTMOUSE', 'RELEASE', x=b[0], y=b[1])

    def back():
        with override():
            bpy.ops.wm.tool_set_by_id(name='builtin.select_box')
    for f in (start, move, release, back):
        step(f)


@step
def s_setup():
    C['mouse'] = setup()
    build()


click('plain', B['VERT'])


@step
def s_check_plain():
    got = picked('VERT')
    check(f"a click selects the vertex and its mirror partner ({sorted(got)})",
          got == {r(B['VERT'][0]), mirror(r(B['VERT'][0]))})
    with override():
        bpy.ops.ed.undo()
    check(f"one Ctrl+Z takes the symmetric click back ({len(picked('VERT'))} left)", not picked('VERT'))


click('a', A['VERT'])
click('add', B['VERT'], shift=True, ctrl=True)


@step
def s_check_add():
    got = picked('VERT')
    want = {r(A['VERT'][0]), mirror(r(A['VERT'][0])), r(B['VERT'][0]), mirror(r(B['VERT'][0]))}
    check(f"Ctrl+Shift+click after a click adds the vertex and its partner, no path between ({sorted(got)})",
          got == want)


click('toggle', B['VERT'], shift=True)


@step
def s_check_toggle():
    got = picked('VERT')
    check(f"Shift+click on a selected vertex takes it and its partner out ({sorted(got)})",
          got == {r(A['VERT'][0]), mirror(r(A['VERT'][0]))})


click('remove', A['VERT'], ctrl=True)


@step
def s_check_remove():
    check(f"Ctrl+click removes the vertex and its partner ({sorted(picked('VERT'))})", not picked('VERT'))


drag('box', B['VERT'])


@step
def s_check_box():
    got = picked('VERT')
    check(f"a vertex marquee runs the kit's symmetric drag ({C.get('box_running')})", C.get('box_running'))
    check(f"it selects what is inside and the mirror partners ({len(got)})",
          r(B['VERT'][0]) in got and symmetric(got))
    dom_mode('FACE')


drag('lasso', B['FACE'], lasso=True)


@step
def s_check_lasso():
    got = picked('FACE')
    check(f"a face lasso selects the face and its partner ({sorted(got)})",
          r(B['FACE'][0]) in got and symmetric(got))
    dom_mode('EDGE')


drag('edges', B['EDGE'])


@step
def s_check_edges():
    got = picked('EDGE')
    check(f"an edge marquee also takes the partners of the edges it touches ({len(got)})",
          centre_of(B['EDGE'][0:2]) in got and symmetric(got))
    dom_mode('EDGE')


click('loop_first', B['EDGE'])


@step
def s_loop():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.loop_pick('INVOKE_DEFAULT', between=False)     # the double-click's operator


@step
def s_check_loop():
    got = picked('EDGE')
    check(f"a double-clicked edge selects its loop and the mirrored loop ({len(got)})",
          len(got) == 32 and symmetric(got) and centre_of(B['EDGE']) in got)
    dom_mode('VERT')
    with override():
        b = bm()
        for v in b.verts:
            if centre(v) == r(B['VERT'][0]):
                v.select_set(True)
        bmesh.update_edit_mesh(bpy.context.edit_object.data)
        bpy.ops.mesh.select_more()
    got = picked('VERT')
    check(f"Grow adds no partners ({len(got)})", len(got) == 9 and all(c[0] >= 0 for c in got))
    with override():
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.allset.symmetry(mode="OFF")


click('off', B['VERT'])


@step
def s_check_off():
    check(f"with Symmetry off a click selects one vertex ({sorted(picked('VERT'))})",
          picked('VERT') == {r(B['VERT'][0])})
    build(loc=(3, 0, 0), mode="WORLD_X")


click('world_off_plane', B['VERT'])


@step
def s_check_world():
    check(f"World X on a mesh away from the world plane: only the clicked vertex ({sorted(picked('VERT'))})",
          picked('VERT') == {r(B['VERT'][0])})
    build(mode="TOPOLOGY")


click('topology', B['VERT'])


@step
def s_check_topology():
    got = picked('VERT')
    check(f"Topology symmetry on a cut cube: the vertex and its partner ({sorted(got)})",
          got == {r(B['VERT'][0]), mirror(r(B['VERT'][0]))})
    with override():
        bpy.ops.allset.symmetry(mode="OFF")


run()
