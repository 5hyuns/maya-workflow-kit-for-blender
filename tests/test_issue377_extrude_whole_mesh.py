"""#377 / #378: Edit Mesh > Extrude of every face of a mesh keeps the old faces, turned inside out, as the bottom, like
Maya: a plane with divisions becomes a closed slab (no inner edges or vertices left without faces), and Thickness on
an open shell (a tube, a box without a lid) gives a wall with both sides and rim faces. Faces that are only part of
the mesh move as before (no bottom), and their inner edges and vertices go with them."""

from importlib import import_module

import bmesh
import bpy

import kit

ex = import_module(kit.MODULE + ".operators.extrude")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    ex.clear()


def _edit_faces(ob, pick=None):
    """Edit Mode on ``ob`` in face mode with the faces ``pick`` (indices; None = all) selected."""
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select_set(False)
    for f in bm.faces:
        if pick is None or f.index in pick:
            f.select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _mesh(ob):
    if ob.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(ob.data)
    else:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
    return bm


def _counts(ob):
    bm = _mesh(ob)
    return len(bm.verts), len(bm.edges), len(bm.faces)


def _clean(ob, closed=True, outward=True):
    """No edge without a face, no vertex without an edge; ``closed``: every edge between exactly two faces
    (``outward``: and the faces point outwards)."""
    bm = _mesh(ob)
    wire = [e.index for e in bm.edges if not e.link_faces]
    loose = [v.index for v in bm.verts if not v.link_edges]
    assert not wire and not loose, (len(wire), len(loose))
    if closed:
        bad = [e.index for e in bm.edges if len(e.link_faces) != 2]
        assert not bad, len(bad)
        if outward:
            bm.normal_update()
            assert bm.calc_volume(signed=True) > 0, "faces point outwards"


def _plane():
    """Create > Polygon Primitives > Plane: 10 x 10 divisions."""
    _clear()
    assert bpy.ops.allset.create(kind='PLANE') == {'FINISHED'}
    ob = bpy.context.active_object
    assert _counts(ob) == (121, 220, 100)
    return ob


def _open_shell(drop):
    """A cube of size 1 without the faces whose normal is in ``drop`` ('Z' top and bottom: a tube; '+Z' the lid)."""
    _clear()
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob = bpy.context.active_object
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    gone = [f for f in bm.faces if (f.normal.z > 0.9) or (drop == 'Z' and f.normal.z < -0.9)]
    bmesh.ops.delete(bm, geom=gone, context='FACES_ONLY')
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def test_plane_faces_extrude_to_a_closed_slab():
    """#377: a plane with divisions, all faces selected, Ctrl+E, Local Translate Z 1."""
    ob = _plane()
    _edit_faces(ob)
    assert bpy.ops.allset.extrude(local_translate_z=1.0) == {'FINISHED'}
    assert _counts(ob) == (242, 480, 240), _counts(ob)
    _clean(ob)
    bm = _mesh(ob)
    caps = [f for f in bm.faces if f.select]
    assert len(caps) == 100 and all(f.normal.z > 0.99 for f in caps), "the moved faces stay selected"
    bottom = [f for f in bm.faces if f.normal.z < -0.99]
    assert len(bottom) == 100 and all(abs(v.co.z) < 1e-6 for f in bottom for v in f.verts), "the old faces stay"


def test_plane_object_extrude_from_the_menu():
    """#377: the plane selected as an object, Edit Mesh > Extrude, then Local Translate Z in Channel Box INPUTS."""
    ob = _plane()
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    assert bpy.ops.allset.menu_item(item="Edit Mesh/Extrude") == {'FINISHED'}
    assert ex.set_params(bpy.context, local_translate_z=0.5) == {'FINISHED'}
    assert _counts(ob) == (242, 480, 240), _counts(ob)
    _clean(ob)


def test_some_faces_of_a_plane_leave_nothing_behind():
    """#377: four inner faces of the plane: the faces move, no bottom, no edge or vertex left without a face."""
    ob = _plane()
    _edit_faces(ob, {44, 45, 54, 55})
    assert bpy.ops.allset.extrude(local_translate_z=1.0) == {'FINISHED'}
    assert _counts(ob) == (129, 236, 108), _counts(ob)
    _clean(ob, closed=False)


def test_divisions_and_faces_apart_on_a_whole_plane():
    ob = _plane()
    _edit_faces(ob)
    assert bpy.ops.allset.extrude(local_translate_z=1.0, divisions=2) == {'FINISHED'}
    assert _counts(ob) == (282, 560, 280), _counts(ob)
    _clean(ob)
    # Keep Faces Together off: every face its own extrusion, nothing kept below
    ob = _plane()
    _edit_faces(ob)
    assert bpy.ops.allset.extrude(local_translate_z=1.0, keep_faces_together=False) == {'FINISHED'}
    assert _counts(ob) == (521, 1020, 500), _counts(ob)
    _clean(ob, closed=False)
    # a one-face plane: the face apart is the whole mesh, a closed box
    _clear()
    bpy.ops.mesh.primitive_plane_add(size=1.0)
    ob = bpy.context.active_object
    _edit_faces(ob)
    assert bpy.ops.allset.extrude(local_translate_z=1.0, keep_faces_together=False) == {'FINISHED'}
    assert _counts(ob) == (8, 12, 6), _counts(ob)
    _clean(ob)


def _extents(ob):
    bm = _mesh(ob)
    return sorted({round(abs(v.co.x), 4) for v in bm.verts}), sorted({round(abs(v.co.y), 4) for v in bm.verts})


def test_thickness_on_a_tube_keeps_both_walls():
    """#378: a tube (a cube without top and bottom), all faces, Ctrl+E, then Thickness in the In-View Editor."""
    for thickness, walls in ((0.14, [0.5, 0.64]), (-0.12, [0.38, 0.5])):
        ob = _open_shell('Z')
        _edit_faces(ob)
        assert bpy.ops.allset.extrude() == {'FINISHED'}
        assert ex.set_params(bpy.context, thickness=thickness) == {'FINISHED'}
        assert _counts(ob) == (16, 32, 16), (thickness, _counts(ob))
        _clean(ob, outward=thickness > 0)
        xs, ys = _extents(ob)
        assert xs == walls and ys == walls, (thickness, xs, ys)
        bm = _mesh(ob)
        rims = [f for f in bm.faces if abs(f.normal.z) > 0.99]
        assert len(rims) == 8, "four rim faces at each open end"


def test_thickness_on_a_box_without_a_lid():
    ob = _open_shell('+Z')
    _edit_faces(ob)
    assert bpy.ops.allset.extrude(thickness=0.1) == {'FINISHED'}
    assert _counts(ob) == (16, 28, 14), _counts(ob)
    _clean(ob)


def test_whole_closed_mesh_keeps_its_inside():
    _clear()
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob = bpy.context.active_object
    _edit_faces(ob)
    assert bpy.ops.allset.extrude(thickness=0.1) == {'FINISHED'}
    assert _counts(ob) == (16, 24, 12), _counts(ob)


def _plane_and_cube():
    """One mesh: a 2 x 2 plane (faces 0-3) and a separate cube at x = 3 (faces 4-9)."""
    _clear()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=2, size=1.0)
    plane = bpy.context.active_object
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.0, 0.0, 0.0))
    cube = bpy.context.active_object
    plane.select_set(True)
    cube.select_set(True)
    bpy.context.view_layer.objects.active = plane
    bpy.ops.object.join()
    ob = bpy.context.active_object
    assert _counts(ob) == (17, 24, 10)
    return ob


def test_part_of_a_mesh_has_no_bottom():
    """The plane's faces of a mesh that also holds a cube: the plane moves (no bottom, no inner leftovers); the
    cube's faces alone (a closed shell) just move, nothing stays inside."""
    ob = _plane_and_cube()
    _edit_faces(ob, {0, 1, 2, 3})
    assert bpy.ops.allset.extrude(local_translate_z=1.0) == {'FINISHED'}
    assert _counts(ob) == (25, 40, 18), _counts(ob)
    _clean(ob, closed=False)
    ob = _plane_and_cube()
    _edit_faces(ob, {4, 5, 6, 7, 8, 9})
    assert bpy.ops.allset.extrude(thickness=0.1) == {'FINISHED'}
    assert _counts(ob) == (17, 24, 10), _counts(ob)
    bm = _mesh(ob)
    cube = [v for v in bm.verts if v.co.x > 1.5]
    assert len(cube) == 8 and all(abs(abs(v.co.y) - 0.6) < 1e-5 for v in cube), "the cube grew by the thickness"
    # every face of both: each part keeps its old faces
    ob = _plane_and_cube()
    _edit_faces(ob)
    assert bpy.ops.allset.extrude(local_translate_z=1.0) == {'FINISHED'}
    assert _counts(ob) == (34, 56, 28), _counts(ob)
    _clean(ob, closed=False)


def test_command_line_whole_plane():
    """``cmds.polyExtrudeFacet`` on every face: the moved faces keep their ids, the old faces come next (facing
    down), then the side faces."""
    cmds = import_module(kit.MODULE + ".command_line.cmds_shim")
    _clear()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=2, size=1.0)
    ob = bpy.context.active_object
    ob.name = "pPlane1"
    assert len(ob.data.polygons) == 4
    cmds.polyExtrudeFacet("pPlane1.f[0:3]", localTranslateZ=1.0)
    me = ob.data
    assert (len(me.vertices), len(me.edges), len(me.polygons)) == (18, 32, 16)
    zs = [p.normal.z for p in me.polygons]
    assert all(z > 0.99 for z in zs[:4]) and all(z < -0.99 for z in zs[4:8]), zs
    assert all(abs(z) < 1e-6 for z in zs[8:]), zs
