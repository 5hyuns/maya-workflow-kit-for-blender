"""Issue #399 follow-up: while painting skin weights with vertices selected, Alt+LMB still tumbles the view like Maya
(Alt+MMB tracks, Alt+RMB dollies): Select (Box / Lasso), Paint and Paint Select mode, vertices set or box-selected,
after F, from empty space, the mesh or the selection, Orbit Around Selection on or off, Emulate 3 Button Mouse,
F9 vertex component mode (Select and Move tool), and a view looking through the persp camera. No vertices selected
is the control."""

import os
import sys
from importlib import import_module
from math import radians

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, tap, win  # noqa: E402

GUI_TIMEOUT = 300
C = {}


def mod(name):
    return import_module(MODULE + name)


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def cyl():
    return bpy.data.objects["pCylinder1"]


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    joints = mod(".operators.joints")
    k = mod(".operators.units").maya_unit()
    area, r = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        bpy.ops.allset.create(kind='CYLINDER')
        c = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(c.data)
        vertical = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-9]
        bmesh.ops.subdivide_edges(bm, edges=vertical, cuts=7, use_grid_fill=True)
        bm.to_mesh(c.data)
        bm.free()
        bpy.ops.object.select_all(action='DESELECT')
        sk = joints.new_skeleton(bpy.context)
        parent = None
        for z in (-1.0, 0.0, 1.0):
            parent = joints.add_joint(sk, Vector((0, 0, z * k)), parent, length=k)
        joints.finish(bpy.context, sk, ["joint1", "joint2", "joint3"])
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        sk.select_set(True)
        c.select_set(True)
        bpy.context.view_layer.objects.active = c
        bpy.ops.allset.bind_skin()
        sk.pose.bones["joint2"].rotation_mode = 'XYZ'
        sk.pose.bones["joint2"].rotation_euler = (radians(60), 0, 0)
        bpy.ops.object.select_all(action='DESELECT')
        c.select_set(True)
        bpy.context.view_layer.objects.active = c
        bpy.ops.allset.frame(selected=False)
        mod(".ui.tool_dock").set_docked(True)
        bpy.ops.allset.paint_skin_weights()                    # the Rigging shelf's Paint Skin Weights
    check(f"painting skin weights ({bpy.context.mode})", bpy.context.mode == 'PAINT_WEIGHT')
    _a, r = main_view()


def set_paint_mode(mode):
    area, r = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        if mode == 'LASSO':
            bpy.ops.allset.skin_paint_mode(mode='SELECT', shape='LASSO')
        else:
            bpy.ops.allset.skin_paint_mode(mode=mode, shape='BOX' if mode == 'SELECT' else 'KEEP')


def select_top(on):
    wp = mod(".operators.weight_paint")
    c = cyl()
    k = mod(".operators.units").maya_unit()
    wp.show_vertex_selection(c)
    wp.set_vertex_selection(c, [v.index for v in c.data.vertices if v.co.z > 0.7 * k] if on else [])
    c.data.update()


# (label, Skin Paint mode, vertices selected, Orbit Around Selection, mouse buttons, what must change, F first)
CASES = [
    ("Select mode, vertices selected, emulated 3 button tumble", 'SELECT', True, False, 'EMULATED', 'ROT'),
    ("Paint mode, vertices selected, emulated 3 button tumble", 'PAINT', True, False, 'EMULATED', 'ROT'),
    ("Select mode, nothing selected, emulated 3 button tumble", 'SELECT', False, False, 'EMULATED', 'ROT'),
    ("Select mode, vertices selected, tumble from the selection", 'SELECT', True, False, 'LEFTMOUSE', 'ROT', False,
     'SEL'),
    ("Select mode (Lasso), vertices selected, tumble", 'LASSO', True, False, 'LEFTMOUSE', 'ROT'),
    ("Select mode (Lasso), vertices selected, tumble from the mesh", 'LASSO', True, False, 'LEFTMOUSE', 'ROT', False,
     (0.5, 0.5)),
    ("Select mode (Lasso), vertices selected, F, orbit around selection", 'LASSO', True, True, 'LEFTMOUSE', 'ROT', True),
    ("Select mode, vertices selected, tumble from the mesh", 'SELECT', True, False, 'LEFTMOUSE', 'ROT', False, (0.5, 0.5)),
    ("Paint mode, vertices selected, tumble from the mesh", 'PAINT', True, False, 'LEFTMOUSE', 'ROT', False, (0.5, 0.5)),
    ("Select mode, box-selected, F, tumble from the mesh", 'SELECT', 'BOX', True, 'LEFTMOUSE', 'ROT', True, (0.5, 0.5)),
    ("Select mode, box-selected vertices, tumble", 'SELECT', 'BOX', False, 'LEFTMOUSE', 'ROT'),
    ("Select mode, box-selected vertices, F, tumble", 'SELECT', 'BOX', False, 'LEFTMOUSE', 'ROT', True),
    ("Select mode, vertices selected, F, tumble", 'SELECT', True, False, 'LEFTMOUSE', 'ROT', True),
    ("Select mode, vertices selected, F, orbit around selection", 'SELECT', True, True, 'LEFTMOUSE', 'ROT', True),
    ("Select mode, vertices selected, F, track", 'SELECT', True, False, 'MIDDLEMOUSE', 'LOC', True),
    ("Select mode, vertices selected, tumble", 'SELECT', True, False, 'LEFTMOUSE', 'ROT'),
    ("Select mode, vertices selected, orbit around selection", 'SELECT', True, True, 'LEFTMOUSE', 'ROT'),
    ("Select mode, nothing selected, tumble", 'SELECT', False, False, 'LEFTMOUSE', 'ROT'),
    ("Paint mode, vertices selected, tumble", 'PAINT', True, False, 'LEFTMOUSE', 'ROT'),
    ("Paint Select mode, vertices selected, tumble", 'PAINT_SELECT', True, False, 'LEFTMOUSE', 'ROT'),
    ("Select mode, vertices selected, track", 'SELECT', True, False, 'MIDDLEMOUSE', 'LOC'),
    ("Select mode, vertices selected, dolly", 'SELECT', True, False, 'RIGHTMOUSE', 'DIST'),
]


def add_case(label, paint_mode, selected, around, button, what, frame=False, at=(0.3, 0.4)):
    def prepare():
        if paint_mode.startswith('F9'):
            bpy.context.preferences.inputs.use_rotate_around_active = around
            _a, r = main_view()
            ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
            if paint_mode != 'F9':
                tap(paint_mode[3:])          # F9:W = the Move tool, F9:Q = the Select tool
            return
        set_paint_mode(paint_mode)
        select_top(selected is True)
        bpy.context.preferences.inputs.use_rotate_around_active = around
        _a, r = main_view()
        ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)

    def box_at(fx, fy):
        _a, r = main_view()
        return r.x + int(r.width * fx), r.y + int(r.height * fy)

    def box1():
        if selected == 'BOX':
            ev('LEFTMOUSE', 'PRESS', x=box_at(0.1, 0.1)[0], y=box_at(0.1, 0.1)[1])

    def box2():
        if selected == 'BOX':
            ev('MOUSEMOVE', 'NOTHING', x=box_at(0.5, 0.5)[0], y=box_at(0.5, 0.5)[1])

    def box3():
        if selected == 'BOX':
            x, y = box_at(0.9, 0.9)
            ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
            ev('LEFTMOUSE', 'RELEASE', x=x, y=y)

    def box_check():
        if selected == 'BOX':
            sel = sum(1 for v in cyl().data.vertices if v.select)
            check(f"{label}: the box selected vertices ({sel})", sel > 0)

    def frame_f():
        if frame:
            tap('F')

    def store():
        _a, r = main_view()
        rv = r.data
        C["rot0"], C["loc0"], C["dist0"] = rv.view_rotation.copy(), rv.view_location.copy(), rv.view_distance
        C["cam0"] = C["cam"].matrix_world.copy() if C.get("cam") else None
        if at == 'SEL':          # the projected centre of the selection (the manipulator)
            from bpy_extras.view3d_utils import location_3d_to_region_2d
            c = cyl()
            ev_me = c.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
            if c.mode == 'EDIT':
                import bmesh as _bm
                idx = [v.index for v in _bm.from_edit_mesh(c.data).verts if v.select]
            else:
                idx = [v.index for v in c.data.vertices if v.select]
            mid = sum((c.matrix_world @ ev_me.vertices[i].co for i in idx), Vector()) / max(len(idx), 1)
            p2 = location_3d_to_region_2d(r, rv, mid)
            x, y = r.x + int(p2.x), r.y + int(p2.y)
        else:
            x, y = r.x + int(r.width * at[0]), r.y + int(r.height * at[1])
        C["xy"] = (x, y)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)

    # 'EMULATED': Emulate 3 Button Mouse turns Alt+LMB into a plain middle drag while the Alt key stays held
    emu = button == 'EMULATED'
    btn = 'MIDDLEMOUSE' if emu else button

    def press():
        x, y = C["xy"]
        ev('LEFT_ALT', 'PRESS', alt=True, x=x, y=y)
        if emu:
            import sim
            bpy.context.preferences.inputs.use_mouse_emulate_3_button = True
            sim._down.add('LEFT_ALT')

    def drag1():
        x, y = C["xy"]
        ev(btn, 'PRESS', alt=not emu, x=x, y=y)

    def drag2():
        x, y = C["xy"]
        ev('MOUSEMOVE', 'NOTHING', alt=not emu, x=x + 60, y=y + 20)

    def drag3():
        x, y = C["xy"]
        ev('MOUSEMOVE', 'NOTHING', alt=not emu, x=x + 120, y=y + 40)

    def release():
        x, y = C["xy"]
        ev(btn, 'RELEASE', alt=not emu, x=x + 120, y=y + 40)
        ev('LEFT_ALT', 'RELEASE', x=x + 120, y=y + 40)
        if emu:
            import sim
            sim._down.discard('LEFT_ALT')
            bpy.context.preferences.inputs.use_mouse_emulate_3_button = False

    def verify():
        _a, r = main_view()
        rv = r.data
        turned = C["rot0"].rotation_difference(rv.view_rotation).angle
        moved = (rv.view_location - C["loc0"]).length
        dolly = abs(rv.view_distance - C["dist0"])
        cam_moved = 0.0
        if what == 'CAM':
            cam_moved = max(abs(a - b) for ra, rb in zip(C["cam0"], C["cam"].matrix_world) for a, b in zip(ra, rb))
            turned = max(turned, cam_moved)
        changed = {'CAM': cam_moved > 1e-3, 'ROT': turned > 0.05, 'LOC': moved > 1e-4 or dolly > 1e-4, 'DIST': dolly > 1e-4 or moved > 1e-4}
        check(f"{label} (turned {turned:.3f} rad, moved {moved:.4f}, dolly {dolly:.4f})", changed[what])
        if what in {'ROT', 'CAM'} and selected:
            if paint_mode.startswith('F9'):
                import bmesh as _bm
                sel = sum(1 for v in _bm.from_edit_mesh(cyl().data).verts if v.select)
            else:
                sel = sum(1 for v in cyl().data.vertices if v.select)
            check(f"{label}: the selection stays ({sel} vertices)", sel > 0)
        want = 'EDIT_MESH' if paint_mode.startswith('F9') else 'PAINT_WEIGHT'
        check(f"{label}: still in {want} ({bpy.context.mode})", bpy.context.mode == want)

    for fn in (prepare, box1, box2, box3, box_check, frame_f, store, press, drag1, drag2, drag3, release, verify):
        step(fn)


for case in CASES:
    add_case(*case)


# F9 while painting: vertex component mode on the posed skin (#397), the Select mode vertices still selected
F9_CASES = [
    ("F9 component mode, vertices selected, tumble", 'F9', True, False, 'LEFTMOUSE', 'ROT'),
    ("F9 component mode, vertices selected, orbit around selection", 'F9', True, True, 'LEFTMOUSE', 'ROT'),
    ("F9 component mode, vertices selected, F, tumble", 'F9', True, False, 'LEFTMOUSE', 'ROT', True),
    ("F9 component mode, vertices selected, track", 'F9', True, False, 'MIDDLEMOUSE', 'LOC'),
    ("F9 component mode, vertices selected, dolly", 'F9', True, False, 'RIGHTMOUSE', 'DIST'),
    ("F9 component mode, vertices selected, tumble from the selection", 'F9', True, False, 'LEFTMOUSE', 'ROT', False,
     'SEL'),
    ("F9 component mode, Move tool, tumble from the manipulator", 'F9:W', True, False, 'LEFTMOUSE', 'ROT', False,
     'SEL'),
    ("F9 component mode, Move tool, orbit around selection", 'F9:W', True, True, 'LEFTMOUSE', 'ROT'),
    ("F9 component mode, Move tool, track from the manipulator", 'F9:W', True, False, 'MIDDLEMOUSE', 'LOC', False,
     'SEL'),
    ("F9 component mode, Select tool, tumble from the selection", 'F9:Q', True, True, 'LEFTMOUSE', 'ROT', False,
     'SEL'),
]


@step
def s_f9_prepare():
    set_paint_mode('SELECT')
    select_top(True)
    _a, r = main_view()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


@step
def s_f9():
    tap('F9')


@step
def s_f9_mode():
    check(f"F9: vertex component mode ({bpy.context.mode})", bpy.context.mode == 'EDIT_MESH')


for case in F9_CASES:
    add_case(*case)


# The view looks through the Maya persp camera (Panels > Perspective > persp): navigating moves that camera
@step
def s_cam_back():
    if bpy.context.mode == 'EDIT_MESH':
        tap('F8')                                   # back to object mode / painting


@step
def s_cam_paint():
    if bpy.context.mode != 'PAINT_WEIGHT':
        c = cyl()
        area, r = main_view()
        with bpy.context.temp_override(window=win(), area=area, region=r):
            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            c.select_set(True)
            bpy.context.view_layer.objects.active = c
            bpy.ops.allset.paint_skin_weights()
    area, r = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=r, space_data=area.spaces.active):
        cam = mod(".ui.panel_cameras")._look_through_panel_camera(bpy.context, area.spaces.active)
    C["cam"] = cam
    check(f"looking through {cam.name if cam else None} ({r.data.view_perspective}, {bpy.context.mode})",
          cam is not None and r.data.view_perspective == 'CAMERA' and bpy.context.mode == 'PAINT_WEIGHT')


CAM_CASES = [
    ("persp camera, Select mode, vertices selected, tumble", 'SELECT', True, False, 'LEFTMOUSE', 'CAM'),
    ("persp camera, Select mode, vertices selected, F, tumble", 'SELECT', True, False, 'LEFTMOUSE', 'CAM', True),
    ("persp camera, Select mode, nothing selected, tumble", 'SELECT', False, False, 'LEFTMOUSE', 'CAM'),
    ("persp camera, Paint mode, vertices selected, tumble", 'PAINT', True, False, 'LEFTMOUSE', 'CAM'),
    ("persp camera, Select mode, vertices selected, orbit around selection", 'SELECT', True, True, 'LEFTMOUSE', 'CAM'),
    ("persp camera, Select mode, vertices selected, track", 'SELECT', True, False, 'MIDDLEMOUSE', 'CAM'),
]
for case in CAM_CASES:
    add_case(*case)


@step
def s_restore():
    bpy.context.preferences.inputs.use_rotate_around_active = False


run()
