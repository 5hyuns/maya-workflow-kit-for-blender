"""#542: Edit Mesh > Duplicate works like Maya's Duplicate Face: each selected face is copied in place as a piece of
its own, Separate duplicated faces (on by default) makes every piece an object under a group with the mesh's name
and selects the copies with the Move Tool; off, the copies stay in the mesh, selected, with the node's manipulator
(Local Translate Z moves each copy along its own normal). Offset moves the copy's edges inward."""

from importlib import import_module

import bmesh
import bpy

import kit


def m(name):
    return import_module(f"{kit.MODULE}.{name}")


def _cube(faces=(5,), name="pCube1"):
    """A 2 x 2 x 2 cube at x = 2 (Blender's cube), the given faces selected in face mode."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(2.0, 0.0, 0.0))
    ob = bpy.context.active_object
    ob.name = name
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select_set(f.index in faces)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    return ob


def _top_face_index(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return max(bm.faces, key=lambda f: f.calc_center_median().z).index


def _selected_faces(ob):
    """The selected faces; the BMesh is kept on the function so the faces stay valid."""
    bm = _selected_faces.bm = bmesh.from_edit_mesh(ob.data)
    return [f for f in bm.faces if f.select]


def _corners(f, mw):
    return sorted(tuple(round(c, 4) for c in (mw @ v.co)) for v in f.verts)


def test_duplicate_without_separate_keeps_the_copy_in_the_mesh():
    ob = _cube()
    top = _top_face_index(ob)
    _cube((top,))
    ob = bpy.data.objects["pCube1"]
    assert bpy.ops.allset.duplicate_face(separate=False) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    assert len(bm.faces) == 7 and len(bm.verts) == 12, (len(bm.faces), len(bm.verts))
    sel = _selected_faces(ob)
    assert len(sel) == 1 and sel[0].index == 6, [f.index for f in sel]
    bm.faces.ensure_lookup_table()
    assert _corners(sel[0], ob.matrix_world) == _corners(bm.faces[top], ob.matrix_world)
    rec = m("operators.extrude").RECORDS.get(ob.name)
    assert rec is not None and rec.spec.node == "polyChipOff", rec


def test_local_translate_z_moves_each_copy_along_its_normal():
    ob = _cube()
    bm = bmesh.from_edit_mesh(ob.data)
    top = max(bm.faces, key=lambda f: f.calc_center_median().z).index
    bottom = min(bm.faces, key=lambda f: f.calc_center_median().z).index
    ob = _cube((top, bottom))
    assert bpy.ops.allset.duplicate_face(separate=False) == {'FINISHED'}
    unit = m("operators.units").maya_unit(bpy.context.scene)
    assert bpy.ops.allset.duplicate_face_edit(local_translate_z=0.5) == {'FINISHED'}
    zs = sorted(round(f.calc_center_median().z, 4) for f in _selected_faces(ob))
    assert zs == [round(-1.0 - 0.5 * unit, 4), round(1.0 + 0.5 * unit, 4)], zs


def test_offset_moves_the_edges_inward():
    ob = _cube()
    top = _top_face_index(ob)
    ob = _cube((top,))
    unit = m("operators.units").maya_unit(bpy.context.scene)
    off = 0.25 / unit           # 0.25 Blender units
    assert bpy.ops.allset.duplicate_face(separate=False, offset=off) == {'FINISHED'}
    f = _selected_faces(ob)[0]
    xs = sorted({round((ob.matrix_world @ v.co).x, 4) for v in f.verts})
    ys = sorted({round((ob.matrix_world @ v.co).y, 4) for v in f.verts})
    assert xs == [1.25, 2.75] and ys == [-0.75, 0.75], (xs, ys)


def test_separate_makes_objects_and_selects_the_copies():
    ob = _cube()
    bm = bmesh.from_edit_mesh(ob.data)
    picked = sorted(f.index for f in bm.faces if f.calc_center_median().z > 0.5 or f.calc_center_median().z < -0.5)
    _cube(tuple(picked))
    assert bpy.ops.allset.duplicate_face() == {'FINISHED'}       # Separate duplicated faces: on by default
    assert bpy.context.mode == 'OBJECT'
    grp = bpy.data.objects.get("pCube1")
    assert grp is not None and grp.type == 'EMPTY', grp
    kids = sorted(o.name for o in grp.children)
    assert len(kids) == 3 and all(k.startswith("polySurface") for k in kids), kids
    faces = sorted(len(o.data.polygons) for o in grp.children)
    assert faces == [1, 1, 6], faces
    sel = sorted(o.name for o in bpy.context.selected_objects)
    assert len(sel) == 2 and all(len(bpy.data.objects[n].data.polygons) == 1 for n in sel), sel
    assert all("allset_duplicate_copy" not in o.data.attributes for o in grp.children)


def test_menu_and_marking_menu_run_it():
    menu_map = m("ui.menu_map")
    assert menu_map.MAP["Edit Mesh/Duplicate"][1] == "allset.duplicate_face"
    ob = _cube()
    top = _top_face_index(ob)
    _cube((top,))
    assert bpy.ops.allset.menu_item(item="Edit Mesh/Duplicate") == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT' and len(bpy.context.selected_objects) == 1


def test_object_mode_warns():
    _cube()
    bpy.ops.object.mode_set(mode='OBJECT')
    assert bpy.ops.allset.duplicate_face() == {'CANCELLED'}
