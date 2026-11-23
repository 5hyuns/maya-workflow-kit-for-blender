"""#503: UV Editor > Cut/Sew > Stitch Together stitches the selected border edges at once (no interactive step), with
the Stitch Together option (Smallest to Largest / Largest to Smallest) in its option window.

Like Maya: the moving shell is moved, turned and scaled so its copy of the edge lands on the other shell's copy with
the two faces on opposite sides; then the edges are sewn. A pair joined first moves on as one shell. Faces alone are
not a selection Stitch Together works on."""

import math
from importlib import import_module

import bmesh
import bpy

import kit

ow = import_module(kit.MODULE + ".operators.option_windows")
box = import_module(kit.MODULE + ".ui.menu_option_box")
uvt = import_module(kit.MODULE + ".operators.uv_tools")
emap = import_module(kit.MODULE + ".ui.editor_menu_map")

ITEM = "UV Editor/Cut/Sew/Stitch Together"


def _strip(n, layouts):
    """A strip of ``n`` unit quads along X; face i gets the UV corners ``layouts[i]`` (4 (u, v) in face order)."""
    ow.store("uv_stitch_together", None)
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("strip")
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, 0.0)) for y in (0, 1) for x in range(n + 1)]
    uv = bm.loops.layers.uv.new("UVMap")
    for i in range(n):
        f = bm.faces.new((vs[i], vs[i + 1], vs[n + 2 + i], vs[n + 1 + i]))
        for loop, p in zip(f.loops, layouts[i]):
            loop[uv].uv = p
    bm.to_mesh(me)
    ob = bpy.data.objects.new("strip", me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_mode(type='EDGE')
    return ob


def _square(u0, w=1.0 / 3):
    return [(u0, 0.0), (u0 + w, 0.0), (u0 + w, 1.0), (u0, 1.0)]


def _moved(points, deg, k, t, centre=(0.5, 0.5)):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    out = []
    for u, v in points:
        x, y = u - centre[0], v - centre[1]
        out.append((centre[0] + k * (c * x - s * y) + t[0], centre[1] + k * (s * x + c * y) + t[1]))
    return out


def _bm(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.ensure_lookup_table()
    return bm, bm.loops.layers.uv.active


def _select_edges(ob, pairs):
    bm, _uv = _bm(ob)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    for a, b in pairs:
        e = next(e for e in bm.edges if {v.index for v in e.verts} == {a, b})
        e.select = True
        for v in e.verts:
            v.select = True
    bmesh.update_edit_mesh(ob.data)


def _face_uvs(ob, i):
    bm, uv = _bm(ob)
    return [tuple(l[uv].uv) for l in bm.faces[i].loops]


def _close(got, want, tol=1e-5):
    assert all(abs(g[0] - w[0]) < tol and abs(g[1] - w[1]) < tol for g, w in zip(got, want)), (got, want)


def test_menu_item_and_window():
    assert emap.MAP[ITEM] == "allset.uv_stitch_together", "no interactive Blender Stitch"
    w = ow.find_path(ITEM)
    assert w is not None and w.key == "uv_stitch_together" and box.option_kind(ITEM) == "window"
    assert w.defaults() == {"order": "Smallest to Largest"}
    assert w.action == "Apply and Close" and not w.missing


def test_smaller_shell_moves_onto_the_larger_one():
    left = _square(0.0)
    right = _square(1.0 / 3)
    ob = _strip(2, [left, _moved(right, 30, 0.5, (0.3, 0.2))])
    _select_edges(ob, [(1, 4)])
    assert bpy.ops.allset.uv_stitch_together() == {'FINISHED'}
    _close(_face_uvs(ob, 0), left)
    _close(_face_uvs(ob, 1), right)       # back where it fits: moved, turned and scaled onto the left face's edge
    bm, uv = _bm(ob)
    assert len(uvt.islands(bm, uv)) == 1


def test_largest_to_smallest_moves_the_larger_shell():
    left = _square(0.0)
    right = _square(1.0 / 3)
    moved = _moved(right, 30, 0.5, (0.3, 0.2))
    ob = _strip(2, [left, moved])
    _select_edges(ob, [(1, 4)])
    assert bpy.ops.allset.opt_uv_stitch_together('EXEC_DEFAULT', order="Largest to Smallest") == {'FINISHED'}
    _close(_face_uvs(ob, 1), moved)       # the smaller shell stays
    _close(_face_uvs(ob, 0), _moved(left, 30, 0.5, (0.3, 0.2)))
    assert ow.saved("uv_stitch_together") == {"order": "Largest to Smallest"}
    # the saved option drives the menu item
    ob = _strip(2, [left, moved])
    ow.store("uv_stitch_together", {"order": "Largest to Smallest"})
    _select_edges(ob, [(1, 4)])
    assert bpy.ops.allset.menu_item(item=ITEM) == {'FINISHED'}
    _close(_face_uvs(ob, 1), moved)


def test_joined_pair_moves_on_as_one_shell():
    a, b, c = _square(0.0), _square(1.0 / 3), _square(2.0 / 3)
    ob = _strip(3, [a, _moved(b, 40, 0.8, (0.1, 0.5)), _moved(c, -70, 1.3, (0.2, -0.6))])
    _select_edges(ob, [(1, 5), (2, 6)])
    assert bpy.ops.allset.uv_stitch_together() == {'FINISHED'}
    # first edge: the middle face (smaller) goes onto the first; then that pair (the first face's area) is smaller
    # than the last face, so both go onto it: the last face stays and the strip lines up with it
    want = [_moved(p, -70, 1.3, (0.2, -0.6)) for p in (a, b, c)]
    for i in range(3):
        _close(_face_uvs(ob, i), want[i])
    bm, uv = _bm(ob)
    assert len(uvt.islands(bm, uv)) == 1


def test_faces_alone_are_refused_and_nothing_moves():
    left, right = _square(0.0), _moved(_square(1.0 / 3), 30, 0.5, (0.3, 0.2))
    ob = _strip(2, [left, right])
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='SELECT')
    assert bpy.ops.allset.uv_stitch_together() == {'CANCELLED'}
    _close(_face_uvs(ob, 1), right)
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='DESELECT')
    assert bpy.ops.allset.uv_stitch_together() == {'CANCELLED'}, "nothing selected"
