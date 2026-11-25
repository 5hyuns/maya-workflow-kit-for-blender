"""Unfold keeps the direction of a shell whose UVs were laid out facing the right way (like Maya): a bent strip laid
out along U stays along U, and one laid out along V stays along V; its UV area and the mean of its UVs stay too."""

import math
from importlib import import_module

import bmesh
import bpy

import kit

uvt = import_module(kit.MODULE + ".operators.uv_tools")


def _strip(along_v=False, turn_deg=0.0):
    """A 12 x 1 face strip bent into a quarter arc in 3D, its UVs a straight band (0..1 x 0..0.08), turned by
    ``turn_deg`` (or laid along V)."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("strip")
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    n = 12
    rows = []
    for j in range(2):
        row = []
        for i in range(n + 1):
            t = (math.pi / 2) * i / n
            row.append(bm.verts.new((2 * math.sin(t), 2 - 2 * math.cos(t), 0.16 * j)))
        rows.append(row)
    a = math.radians(90.0 if along_v else turn_deg)
    for i in range(n):
        f = bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
        for loop, (u, v) in zip(f.loops, ((i / n, 0.0), ((i + 1) / n, 0.0), ((i + 1) / n, 0.08), (i / n, 0.08))):
            loop[uv].uv = (0.5 + (u - 0.5) * math.cos(a) - (v - 0.04) * math.sin(a),
                           0.5 + (u - 0.5) * math.sin(a) + (v - 0.04) * math.cos(a))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("strip", me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_all(action='SELECT')
    return ob


def _uvs(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    pts = [l[uv].uv.copy() for f in bm.faces for l in f.loops]
    return pts, sum(uvt._uv_area(f, uv) for f in bm.faces)


def _long_axis_deg(pts):
    """Direction (0..180) of the band's long axis: from the first to the last row of its UVs."""
    cu = sum(p.x for p in pts) / len(pts)
    cv = sum(p.y for p in pts) / len(pts)
    sxx = sum((p.x - cu) ** 2 for p in pts)
    syy = sum((p.y - cv) ** 2 for p in pts)
    sxy = sum((p.x - cu) * (p.y - cv) for p in pts)
    return math.degrees(0.5 * math.atan2(2 * sxy, sxx - syy)) % 180.0


def _angle_gap(a, b):
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def test_unfold_keeps_the_direction_of_a_laid_out_strip():
    for along_v, turn in ((False, 0.0), (True, 0.0), (False, 30.0)):
        ob = _strip(along_v, turn)
        before, area0 = _uvs(ob)
        assert bpy.ops.allset.uv_unfold() == {'FINISHED'}
        after, area1 = _uvs(ob)
        gap = _angle_gap(_long_axis_deg(before), _long_axis_deg(after))
        assert gap < 3.0, (along_v, turn, _long_axis_deg(before), _long_axis_deg(after))
        assert abs(area1 - area0) < 1e-4 * max(area0, 1e-9) + 1e-7, (area0, area1)
        c0 = sum(before, before[0] * 0) / len(before)
        c1 = sum(after, after[0] * 0) / len(after)
        assert (c1 - c0).length < 0.02, (c0, c1)
