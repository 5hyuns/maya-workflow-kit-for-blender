"""Issue #399: in Paint Skin Weights (Select mode, some vertices selected) F frames the selected vertices like Maya,
where the posed mesh shows them, not the whole skeleton and not the rest shape."""

import os
import sys
from importlib import import_module
from math import radians

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, tap, win  # noqa: E402

GUI_TIMEOUT = 200
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


def hover():
    _a, r = main_view()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


def selected_posed():
    """World positions of the selected vertices on the posed (evaluated) mesh."""
    c = cyl()
    ev_ob = c.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev_ob.data
    mw = c.matrix_world
    return [mw @ me.vertices[v.index].co for v in c.data.vertices if v.select]


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
        # bend the top half well away from its rest place
        sk.pose.bones["joint2"].rotation_mode = 'XYZ'
        sk.pose.bones["joint2"].rotation_euler = (radians(80), 0, 0)
        bpy.ops.object.select_all(action='DESELECT')
        c.select_set(True)
        bpy.context.view_layer.objects.active = c
        bpy.ops.allset.frame(selected=False)
        mod(".ui.tool_dock").set_docked(True)
        bpy.ops.allset.paint_skin_weights()                    # the Rigging shelf's Paint Skin Weights
        bpy.ops.allset.skin_paint_mode(mode='SELECT')
    wp = mod(".operators.weight_paint")
    c = cyl()
    top = [v.index for v in c.data.vertices if v.co.z > 0.7 * k]
    wp.show_vertex_selection(c)
    wp.set_vertex_selection(c, top)
    c.data.update()
    check(f"painting in Select mode ({bpy.context.mode}, {wp.paint_mode(bpy.context)}, {len(top)} vertices)",
          bpy.context.mode == 'PAINT_WEIGHT' and wp.paint_mode(bpy.context) == 'SELECT' and top)
    _a, r = main_view()
    r.data.view_location = (5 * k, -6 * k, -4 * k)
    r.data.view_distance = 40 * k
    C["before"] = r.data.view_distance
    hover()


@step
def s_press():
    tap('F')


@step
def s_redraw():
    main_view()[0].tag_redraw()


@step
def s_framed():
    area, r = main_view()
    rv = r.data
    pts = selected_posed()
    rect = mod(".operators.view_frame").visible_bounds(area, r)
    # Maya aims the view at the centre of the box around the selection and fits the box into the view
    corners = mod(".operators.framing").box_corners(pts)
    xy = [location_3d_to_region_2d(r, rv, p) for p in corners]
    check(f"F zooms in on the selection ({C['before']:.3f} -> {rv.view_distance:.3f})",
          rv.view_distance < C["before"] * 0.5)
    ok = all(p is not None for p in xy)
    check("the selection's box is in the view", ok and all(rect[0] - 2 <= p.x <= rect[2] + 2
                                                           and rect[1] - 2 <= p.y <= rect[3] + 2 for p in xy))
    mid = location_3d_to_region_2d(r, rv, sum(corners, Vector()) / 8.0)
    cx, cy = (rect[0] + rect[2]) * .5, (rect[1] + rect[3]) * .5
    check(f"the posed selection is in the middle ({tuple(mid) if mid else None} vs ({cx:.1f}, {cy:.1f}))",
          mid is not None and abs(mid.x - cx) < 2 and abs(mid.y - cy) < 2)
    if ok:
        span_x = max(p.x for p in xy) - min(p.x for p in xy)
        span_y = max(p.y for p in xy) - min(p.y for p in xy)
        fill = max(span_x / (rect[2] - rect[0]), span_y / (rect[3] - rect[1]))
        check(f"the selection fills the view ({fill:.2f})", fill > 0.6)
    check(f"still painting ({bpy.context.mode})", bpy.context.mode == 'PAINT_WEIGHT')


run()
