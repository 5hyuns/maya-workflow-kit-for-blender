"""#337: Mesh > Fill Hole and Edit Mesh > Bridge with Maya's selection rules. Fill Hole closes every hole whose
border edges are selected with one face whatever the number of edges around it (a cylinder rim), and every hole
of the mesh when nothing is selected; Bridge with exactly one closed loop of border edges fills it with a single
face (no divisions), two loops still bridge, and a selection that is neither warns and changes nothing. The
Shift+RMB menus, the shelf button, the Modeling Toolkit and the option window run the same two commands."""

from importlib import import_module

import bmesh
import bpy

import kit

fb = import_module(kit.MODULE + ".operators.fill_bridge")
ow = import_module(kit.MODULE + ".operators.option_windows")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
shelf_map = import_module(kit.MODULE + ".ui.shelf_map")
toolkit = import_module(kit.MODULE + ".ui.modeling_toolkit")
mm = import_module(kit.MODULE + ".marking.menus")
SEGMENTS = 32


def _fresh():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.wm.read_homefile(use_empty=True)


def _link(bm, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob


def _open_cylinder():
    """A tube without caps: both rims are border loops of 32 edges."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=SEGMENTS, radius1=1.0, radius2=1.0, depth=2.0)
    return _link(bm, "tube")


def _cube_side_open(cuts=2):
    """A cube divided into 3 x 3 per side with the +X side's faces deleted: one border loop of 12 edges."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.x > 0.5], context='FACES')
    return _link(bm, "cube")


def _two_circles():
    """Two concentric circles of 32 edges, no faces: two loops with nothing between them."""
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=False, segments=SEGMENTS, radius=1.0)
    bmesh.ops.create_circle(bm, cap_ends=False, segments=SEGMENTS, radius=2.0)
    return _link(bm, "circles")


def _edit(ob, mode='EDGE'):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type=mode)
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    bm.select_flush_mode()
    return bm


def _select(ob, bm, test):
    for e in bm.edges:
        e.select = bool(test(e))
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _faces(ob):
    bm = bmesh.from_edit_mesh(ob.data) if ob.mode == 'EDIT' else None
    return [f for f in bm.faces] if bm is not None else list(ob.data.polygons)


def _big_faces(ob):
    """(vertex count, normal) of every face with more than four corners."""
    bm = bmesh.from_edit_mesh(ob.data)
    bm.normal_update()
    return [(len(f.verts), f.normal.copy()) for f in bm.faces if len(f.verts) > 4]


def _top_rim(e):
    return e.is_boundary and all(v.co.z > 0 for v in e.verts)


def test_fill_hole_closes_a_selected_rim():
    # the report: an open cylinder, its rim selected, Fill Hole did nothing (the hole has more than four edges)
    _fresh()
    ob = _open_cylinder()
    bm = _edit(ob)
    _select(ob, bm, _top_rim)
    n = len(_faces(ob))
    assert bpy.ops.allset.menu_item(item="Mesh/Fill Hole") == {'FINISHED'}
    assert len(_faces(ob)) == n + 1, len(_faces(ob))
    big = _big_faces(ob)
    assert len(big) == 1 and big[0][0] == SEGMENTS and big[0][1].z > 0.99, big     # one n-gon, facing out
    assert sum(1 for e in bmesh.from_edit_mesh(ob.data).edges if e.is_boundary) == SEGMENTS   # the other rim stays


def test_fill_hole_with_nothing_selected_fills_every_hole():
    _fresh()
    ob = _open_cylinder()
    _edit(ob)
    n = len(_faces(ob))
    assert bpy.ops.allset.menu_item(item="Mesh/Fill Hole") == {'FINISHED'}
    assert len(_faces(ob)) == n + 2, len(_faces(ob))
    normals = sorted(round(nm.z) for _c, nm in _big_faces(ob))
    assert normals == [-1, 1], normals
    # and again on the object (the Mesh menu / Shift+RMB object menu in object mode): back in object mode after
    bpy.ops.object.mode_set(mode='OBJECT')
    _fresh()
    ob = _open_cylinder()
    assert bpy.ops.allset.menu_item(item="Mesh/Fill Hole") == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT' and len(ob.data.polygons) == n + 2, len(ob.data.polygons)


def test_fill_hole_without_a_hole_warns_and_changes_nothing():
    _fresh()
    ob = _open_cylinder()
    bm = _edit(ob)
    _select(ob, bm, lambda e: not e.is_boundary)        # the side edges only
    n = len(_faces(ob))
    assert bpy.ops.allset.fill_hole() == {'CANCELLED'}
    assert len(_faces(ob)) == n
    bm = bmesh.from_edit_mesh(ob.data)
    _select(ob, bm, lambda e: _top_rim(e) and e.verts[0].co.x > 0)      # an open chain of border edges
    assert bpy.ops.allset.fill_hole() == {'CANCELLED'}
    assert len(_faces(ob)) == n


def test_bridge_fills_one_closed_border_loop_with_one_face():
    # the report: a divided cube with one side deleted, its border loop selected, Bridge did nothing
    _fresh()
    ob = _cube_side_open()
    bm = _edit(ob)
    _select(ob, bm, lambda e: e.is_boundary)
    assert sum(1 for e in bm.edges if e.select) == 12
    n = len(_faces(ob))
    assert bpy.ops.allset.menu_item(item="Edit Mesh/Bridge") == {'FINISHED'}
    assert len(_faces(ob)) == n + 1, len(_faces(ob))
    big = _big_faces(ob)
    assert len(big) == 1 and big[0][0] == 12 and big[0][1].x > 0.99, big      # one 12-gon, no divisions


def test_bridge_option_values_do_not_divide_a_filled_loop():
    _fresh()
    ob = _cube_side_open()
    bm = _edit(ob)
    _select(ob, bm, lambda e: e.is_boundary)
    n = len(_faces(ob))
    assert ow.run(ow._BY_KEY["bridge"], bpy.context, {"divisions": 4, "twist": 0}) == {'FINISHED'}
    assert len(_faces(ob)) == n + 1 and len(_big_faces(ob)) == 1


def test_bridge_still_bridges_two_loops():
    _fresh()
    ob = _two_circles()
    bm = _edit(ob)
    _select(ob, bm, lambda e: True)
    assert bpy.ops.allset.menu_item(item="Edit Mesh/Bridge") == {'FINISHED'}
    assert len(_faces(ob)) == SEGMENTS, len(_faces(ob))
    assert all(len(f.verts) == 4 for f in bmesh.from_edit_mesh(ob.data).faces)
    # the option window's Divisions make rows of faces
    bpy.ops.object.mode_set(mode='OBJECT')
    _fresh()
    ob = _two_circles()
    bm = _edit(ob)
    _select(ob, bm, lambda e: True)
    assert ow.run(ow._BY_KEY["bridge"], bpy.context, {"divisions": 2, "twist": 0}) == {'FINISHED'}
    assert len(_faces(ob)) == SEGMENTS * 3, len(_faces(ob))


def test_bridge_with_another_selection_warns_and_changes_nothing():
    _fresh()
    ob = _open_cylinder()
    bm = _edit(ob)
    _select(ob, bm, lambda e: not e.is_boundary and e.verts[0].co.x > 0.9)     # one side edge
    n = len(_faces(ob))
    assert bpy.ops.allset.bridge() == {'CANCELLED'}
    assert len(_faces(ob)) == n
    bm = bmesh.from_edit_mesh(ob.data)
    _select(ob, bm, lambda e: False)                                           # nothing
    assert bpy.ops.allset.bridge() == {'CANCELLED'}
    assert len(_faces(ob)) == n
    # Bridge on an object (object mode) still warns like Maya and leaves the mesh alone
    bpy.ops.object.mode_set(mode='OBJECT')
    assert bpy.ops.allset.menu_item(item="Edit Mesh/Bridge") == {'CANCELLED'}
    assert len(ob.data.polygons) == n


def test_every_caller_runs_the_same_commands():
    assert menu_map.spec("Mesh/Fill Hole") == ("op", "allset.fill_hole", {})
    assert menu_map.spec("Edit Mesh/Bridge") == ("op", "allset.bridge", {})
    entries = {p: a for name, menu in mm.MENUS.items() for p, _l, a in mm.label_walk(menu, name)}
    bridges = {p: a for p, a in entries.items() if p.rsplit("/", 1)[-1] in ("Bridge", "Bridge Faces", "Fill Hole",
                                                                              "Fill Holes")}
    assert bridges, "no marking-menu Bridge / Fill Hole entries"
    for path, action in bridges.items():
        assert action in (("item", "Edit Mesh/Bridge"), ("item", "Mesh/Fill Hole")), (path, action)
    assert shelf_map.BY_COMMAND["BridgeOrFill"][0] == ("item", "Edit Mesh/Bridge")
    assert ("Bridge", "Edit Mesh/Bridge", 'MOD_LATTICE') in toolkit.COMPONENTS
    assert ow._BY_KEY["bridge"].paths == ("Edit Mesh/Bridge",)
