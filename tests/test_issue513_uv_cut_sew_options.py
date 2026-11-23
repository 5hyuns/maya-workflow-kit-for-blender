"""#513: the UV Editor Cut and Sew tools have Maya's Steady Stroke (with its Distance), Cut Open Ratio (Cut) and
Display All Shell Borders. A cut opens a gap of Cut Open Ratio times the cut edges' length between the split UVs (0 =
they stay on each other), the ends of a cut inside a shell stay joined; with Steady Stroke the stroke point trails
the mouse by the Distance; Display All Shell Borders lists every shell border and open edge."""

from importlib import import_module

import bmesh
import bpy
import numpy as np

import kit

brush = import_module(kit.MODULE + ".operators.uv_brush")


def _grid(n=10):
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=n, y_subdivisions=n, size=2, calc_uvs=True)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_all(action='SELECT')
    return ob


def _column_edges(bm, x, y0, y1):
    return [e for e in bm.edges if all(abs(v.co.x - x) < 1e-6 for v in e.verts)
            and all(y0 - 1e-6 <= v.co.y <= y1 + 1e-6 for v in e.verts)]


def _uvs_at(bm, uv, co):
    return {tuple(round(c, 6) for c in l[uv].uv) for v in bm.verts if (v.co.xy - co).length < 1e-6
            for l in v.link_loops}


def test_settings():
    s = bpy.context.scene.allset_uv_brush
    assert (s.cut_steady, round(s.cut_steady_distance, 6), round(s.cut_open_ratio, 6), s.show_shell_borders) == \
        (False, 0.1, 0.1, False)


def test_cut_opens_by_the_ratio():
    for ratio in (0.1, 0.5, 0.0):
        ob = _grid()
        bm = bmesh.from_edit_mesh(ob.data)
        uv = bm.loops.layers.uv.active
        edges = _column_edges(bm, 0.0, -0.6, 0.6)            # a slit inside the shell, UV u = 0.5, v 0.2 - 0.8
        assert brush.open_cut(bm, uv, edges, ratio) == len(edges)
        from mathutils import Vector
        mid = _uvs_at(bm, uv, Vector((0.0, 0.0)))
        end = _uvs_at(bm, uv, Vector((0.0, 0.6)))
        edge_len = 0.1
        if ratio == 0.0:
            assert len(mid) == 1, mid
        else:
            assert len(mid) == 2, mid
            us = sorted(p[0] for p in mid)
            assert abs((us[1] - us[0]) - ratio * edge_len) < 1e-5, (ratio, us)
            assert all(abs(p[1] - 0.5) < 1e-6 for p in mid), "the UVs open across the cut, not along it"
        assert len(end) == 1, f"the end of the cut stays joined {end}"
        assert all(e.seam for e in edges)


def test_steady_stroke():
    s = bpy.context.scene.allset_uv_brush
    s.cut_steady, s.cut_steady_distance = True, 0.1
    op = type("Op", (), {"_uv": (0.5, 0.5), "_area": 1, "_mode": lambda self: "CUT"})()
    steady = brush.ALLSET_OT_uv_brush_stroke._steady
    assert steady(op, bpy.context, (0.55, 0.5)) == (0.5, 0.5), "inside the distance the stroke waits"
    p = steady(op, bpy.context, (0.8, 0.5))
    assert abs(p[0] - 0.7) < 1e-6 and abs(p[1] - 0.5) < 1e-6, p
    s.cut_steady = False
    assert steady(op, bpy.context, (0.8, 0.5)) == (0.8, 0.5)
    brush._stroke["lazy"] = None


def test_shell_borders():
    ob = _grid(4)
    m = brush.MeshUVs(ob, True)
    segs = brush.shell_border_segments([m])
    assert len(segs) == 16, f"a 4 x 4 grid's outline = 16 edges ({len(segs)})"
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    brush.open_cut(bm, uv, _column_edges(bm, 0.0, -1.0, 1.0), 0.1)     # right through: two shells
    bmesh.update_edit_mesh(ob.data)
    m = brush.MeshUVs(ob, True)
    segs = brush.shell_border_segments([m])
    assert len(segs) == 16 + 8, len(segs)
    pts = np.array([p for seg in segs for p in seg])
    assert pts[:, 0].min() < 1e-6 and pts[:, 0].max() > 1 - 1e-6
