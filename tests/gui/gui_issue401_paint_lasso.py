"""Issue #401: Paint Skin Weights' Select mode also selects vertices with a lasso: Tool Settings' Select row picks
Box or Lasso, a lasso drag in the view selects the vertices inside it, the choice stays for the next Select mode
(Ctrl+. / Ctrl+, cycle the three Maya modes as before), and Box is still the first choice."""

import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402

GUI_TIMEOUT = 200
C = {}
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")


def mod(name):
    return import_module(MODULE + name)


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def override():
    area, r = main_view()
    return bpy.context.temp_override(window=win(), area=area, region=r)


def cyl():
    return bpy.data.objects["pCylinder1"]


def tool():
    t = bpy.context.workspace.tools.from_space_view3d_mode('PAINT_WEIGHT', create=False)
    return t.idname if t is not None else ''


def mode():
    return mod(".operators.weight_paint").paint_mode(bpy.context)


def lasso_points():
    """A triangle (window pixels) over the left half of the view's middle."""
    _a, r = main_view()
    cx, cy = r.x + r.width // 2, r.y + r.height // 2
    s = min(r.width, r.height) // 3
    return [(cx - s, cy - s), (cx + s // 4, cy), (cx - s, cy + s)]


def inside(p, poly):
    x, y = p
    hit = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            hit = not hit
    return hit


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    joints = mod(".operators.joints")
    k = mod(".operators.units").maya_unit()
    with override():
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
        bpy.ops.object.select_all(action='DESELECT')
        c.select_set(True)
        bpy.context.view_layer.objects.active = c
        bpy.ops.allset.frame(selected=False)
        mod(".ui.tool_dock").set_docked(True)
        bpy.ops.allset.paint_skin_weights()
        bpy.ops.allset.skin_paint_mode(mode='SELECT')
    check(f"Select mode starts with Box ({tool()})", tool() == 'builtin.select_box' and mode() == 'SELECT')
    with override():
        bpy.ops.allset.skin_paint_mode(mode='SELECT', shape='LASSO')
    check(f"Select with Lasso ({tool()}, {mode()})", tool() == 'builtin.select_lasso' and mode() == 'SELECT')
    mod(".operators.weight_paint").set_vertex_selection(cyl(), ())
    cyl().data.update()


@step
def s_press():
    pts = lasso_points()
    ev('MOUSEMOVE', 'NOTHING', x=pts[0][0], y=pts[0][1])
    ev('LEFTMOUSE', 'PRESS', x=pts[0][0], y=pts[0][1])


def _move(i):
    @step
    def s_move():
        pts = lasso_points() + [lasso_points()[0]]
        a, b = pts[i], pts[i + 1]
        for t in (0.25, 0.5, 0.75, 1.0):
            ev('MOUSEMOVE', 'NOTHING', x=int(a[0] + (b[0] - a[0]) * t), y=int(a[1] + (b[1] - a[1]) * t))
    s_move.__name__ = f"s_move{i}"


for _i in range(3):
    _move(_i)


@step
def s_release():
    pts = lasso_points()
    ev('LEFTMOUSE', 'RELEASE', x=pts[0][0], y=pts[0][1])


@step
def s_lassoed():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue401_lasso.png"))
    area, r = main_view()
    c = cyl()
    poly = [(x - r.x, y - r.y) for x, y in lasso_points()]
    sel = [v for v in c.data.vertices if v.select]
    xy = [location_3d_to_region_2d(r, r.data, c.matrix_world @ v.co) for v in sel]
    check(f"the lasso selected vertices ({len(sel)} of {len(c.data.vertices)})", 5 <= len(sel) < len(c.data.vertices))
    # 2 px of slack: Blender rounds the lasso path to whole pixels
    outside = [p for p in xy if p is None or not any(inside((p.x + dx, p.y + dy), poly)
                                                       for dx in (-2, 0, 2) for dy in (-2, 0, 2))]
    check(f"only vertices inside the lasso ({len(outside)} outside)", not outside)
    check(f"still painting ({bpy.context.mode})", bpy.context.mode == 'PAINT_WEIGHT')
    with override():
        bpy.ops.allset.skin_paint_mode(step=1)
        C["next"] = mode()
        bpy.ops.allset.skin_paint_mode(step=1)
        C["paint"] = mode()
        bpy.ops.allset.skin_paint_mode(mode='SELECT')
    check(f"Ctrl+. still cycles the three modes ({C['next']}, {C['paint']}); Select comes back with Lasso "
          f"({tool()})", (C["next"], C["paint"]) == ('PAINT_SELECT', 'PAINT') and tool() == 'builtin.select_lasso')
    with override():
        bpy.ops.allset.skin_paint_mode(mode='SELECT', shape='BOX')
    check(f"... and Box again ({tool()})", tool() == 'builtin.select_box' and mode() == 'SELECT')


run()
