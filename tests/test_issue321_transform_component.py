"""#321: Edit Mesh > Transform (Transform Component) leaves a polyMoveFace / polyMoveEdge / polyMoveVertex node on the
selected component type, like Maya: the mesh stays as it is, the node's values move the components - pivot = the
centre of the selection's bounding box, Local Translate Z along the normals (a vertex of several selected faces by
their mean), Translate / Rotate / Scale in world space, Local Scale in the selection's frame; Random alone moves
nothing. The manipulator, In-View Editor and Channel Box INPUTS edit it like an extrusion."""

from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit

extrude = import_module(kit.MODULE + ".operators.extrude")
mc = import_module(kit.MODULE + ".operators.move_component")
in_view = import_module(kit.MODULE + ".ui.in_view")
menu_map = import_module(kit.MODULE + ".ui.menu_map")

S = 0.5773502691896258     # 1 / sqrt(3)
H = 0.7071067811865476     # 1 / sqrt(2)


def _cube(select):
    """A 2 x 2 x 2 cube at the origin in edit mode with ``select(bm, mode)`` choosing the components."""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    extrude.clear()
    for k in [k for k in bpy.context.scene.keys() if k.startswith("allset_poly")]:
        del bpy.context.scene[k]
    bpy.ops.mesh.primitive_cube_add(size=2)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    mode = select(bm)
    bpy.context.scene.tool_settings.mesh_select_mode = (mode == 'VERTEX', mode == 'EDGE', mode == 'FACE')
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    return ob


def _faces(*normals):
    def pick(bm):
        bm.normal_update()
        for f in bm.faces:
            if any((f.normal - Vector(n)).length < 1e-6 for n in normals):
                f.select_set(True)
        return 'FACE'
    return pick


def _verts(*cos):
    def pick(bm):
        for v in bm.verts:
            if any((v.co - Vector(c)).length < 1e-6 for c in cos):
                v.select_set(True)
        return 'VERTEX'
    return pick


def _edge(a, b):
    def pick(bm):
        for e in bm.edges:
            if {tuple(round(c, 6) for c in v.co) for v in e.verts} == {a, b}:
                e.select_set(True)
        return 'EDGE'
    return pick


def _coords(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return sorted(tuple(round(c, 4) for c in v.co) for v in bm.verts)


def _has(ob, *points):
    have = _coords(ob)
    for p in points:
        assert tuple(round(c, 4) for c in p) in have, (p, have)


def _run(ob, **changes):
    assert bpy.ops.allset.transform_component() == {'FINISHED'}
    rec = extrude.current(ob)
    assert rec is not None
    if changes:
        assert extrude.set_params(bpy.context, **changes) == {'FINISHED'}
    return extrude.current(ob)


def test_menu_item():
    assert menu_map.MAP["Edit Mesh/Transform"][1] == "allset.transform_component"


def test_node_per_component_and_nothing_moves():
    for pick, node in ((_faces((0, 0, 1)), "polyMoveFace1"), (_edge((1, -1, 1), (1, 1, 1)), "polyMoveEdge1"),
                       (_verts((1, 1, 1)), "polyMoveVertex1")):
        ob = _cube(pick)
        before = _coords(ob)
        rec = _run(ob)
        assert rec.name == node, rec.name
        assert _coords(ob) == before, "the menu item leaves the mesh as it is"
        assert extrude.caps_selected(ob, rec), "the selection stays: manipulator and In-View Editor show"
    ob = _cube(_faces((0, 0, 1)))
    before = _coords(ob)
    assert bpy.ops.allset.transform_component(random=0.5) == {'FINISHED'}
    assert extrude.current(ob).params["random"] == 0.5
    assert _coords(ob) == before, "Random alone moves nothing"


def test_top_face_translate_scale_rotate():
    ob = _cube(_faces((0, 0, 1)))
    _run(ob, local_translate_z=1.0)
    _has(ob, (1, 1, 2), (-1, -1, 2), (1, 1, -1))
    ob = _cube(_faces((0, 0, 1)))
    _run(ob, translate_z=1.0)
    _has(ob, (1, 1, 2), (-1, -1, 2))
    ob = _cube(_faces((0, 0, 1)))
    _run(ob, local_scale_x=2.0)
    _has(ob, (2, 1, 1), (-2, -1, 1), (1, 1, -1))
    ob = _cube(_faces((0, 0, 1)))
    _run(ob, scale_x=2.0)
    _has(ob, (2, 1, 1), (-2, -1, 1))
    ob = _cube(_faces((0, 0, 1)))
    _run(ob, rotate_z=45.0)          # about the pivot = the face centre (0, 0, 1)
    _has(ob, (0, 2 ** 0.5, 1), (2 ** 0.5, 0, 1), (1, 1, -1))


def test_two_faces_share_the_mean_normal():
    ob = _cube(_faces((0, 0, 1), (1, 0, 0)))
    _run(ob, local_translate_z=1.0)
    _has(ob, (1.5, 1, 1.5), (1.5, -1, 1.5), (-1, 1, 2), (2, 1, -1))


def test_vertices_and_edges_follow_their_normals():
    ob = _cube(_verts((1, 1, 1), (-1, 1, 1)))
    _run(ob, local_translate_z=1.0)
    _has(ob, (1 + S, 1 + S, 1 + S), (-1 - S, 1 + S, 1 + S))
    ob = _cube(_edge((1, -1, 1), (1, 1, 1)))
    _run(ob, local_translate_z=1.0)
    _has(ob, (1 + H, 1, 1 + H), (1 + H, -1, 1 + H))


def test_manipulator_and_in_view_rows():
    ob = _cube(_faces((0, 0, 1)))
    rec = _run(ob)
    assert rec.spec.view_fields == ("local_translate_x", "local_translate_y", "local_translate_z", "random")
    assert in_view.handle_fields(rec, "SX") == ("local_scale_x",)
    assert in_view.handle_fields(rec, "PXY") == ("local_translate_x", "local_translate_y")
    centre, axes, _k = in_view.manip_frame(ob, rec)
    assert (Vector(centre) - Vector((0, 0, 1))).length < 1e-6
    assert (axes.col[2] - Vector((0, 0, 1))).length < 1e-6, "Z = the face normal"
    ob = _cube(_verts((1, 1, 1)))
    rec = _run(ob)
    assert in_view.handle_fields(rec, "SX") == (), "polyMoveVertex has no Local Scale"
    assert in_view.handle_fields(rec, "TZ") == ("local_translate_z",)
    assert "local_scale_x" not in rec.params


def test_edit_again_and_object_mode():
    ob = _cube(_faces((0, 0, 1)))
    _run(ob, local_translate_z=1.0)
    assert extrude.set_params(bpy.context, local_translate_z=0.5) == {'FINISHED'}
    _has(ob, (1, 1, 1.5))
    assert extrude.current(ob).params["local_translate_z"] == 0.5
    bpy.ops.object.mode_set(mode='OBJECT')
    assert bpy.ops.allset.transform_component() == {'CANCELLED'}, "needs components"
