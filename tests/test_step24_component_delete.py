"""Delete / Backspace on components deletes right away, the Maya way (#565).

Faces -> faces (and their unused edges/vertices) gone; edges -> non-border edges dissolved, every vertex stays;
vertices -> only those with two edges go (their edges become one), the rest stay; the selection is cleared.
Edit Mesh > Delete Edge/Vertex (Ctrl+Delete) also cleans up two-edge vertices and deletes vertices with their edges.
"""

from importlib import import_module

import bmesh
import bpy

import kit

component = import_module(kit.MODULE + ".operators.component")


def _cube(mode):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type=mode)
    bpy.ops.mesh.select_all(action='DESELECT')
    return bpy.context.active_object


def _counts(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return len(bm.verts), len(bm.edges), len(bm.faces)


def _select(ob, kind, indices):
    bm = bmesh.from_edit_mesh(ob.data)
    seq = {"VERT": bm.verts, "EDGE": bm.edges, "FACE": bm.faces}[kind]
    seq.ensure_lookup_table()
    for i in indices:
        seq[i].select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def test_keymap_binds_delete_and_backspace():
    km = kit.maya_kc().keymaps["Mesh"]
    for key in ('DEL', 'BACK_SPACE'):
        plain = [k.idname for k in km.keymap_items if k.active and k.type == key and k.value == 'PRESS'
                 and not (k.ctrl or k.shift or k.alt or k.oskey)]
        assert plain == ["allset.delete_components"], (key, plain)
        ctrl = [k.idname for k in km.keymap_items if k.active and k.type == key and k.ctrl]
        assert ctrl == ["allset.delete_edge_vertex"], (key, ctrl)
    obj = kit.maya_kc().keymaps["Object Mode"]
    assert any(k.type == 'DEL' and k.idname.startswith("object.delete") for k in obj.keymap_items), \
        "object mode Delete unchanged"


def test_delete_all_faces():
    ob = _cube('FACE')
    bpy.ops.mesh.select_all(action='SELECT')
    assert bpy.ops.allset.delete_components() == {'FINISHED'}
    assert _counts(ob) == (0, 0, 0), _counts(ob)


def test_delete_one_face_keeps_the_rest():
    ob = _cube('FACE')
    _select(ob, "FACE", [0])
    bpy.ops.allset.delete_components()
    assert _counts(ob) == (8, 12, 5), _counts(ob)
    bm = bmesh.from_edit_mesh(ob.data)
    assert not any(el.select for el in bm.verts), "nothing selected afterwards"


def test_delete_edge_keeps_its_vertices():
    ob = _cube('EDGE')
    _select(ob, "EDGE", [0])
    assert bpy.ops.allset.delete_components() == {'FINISHED'}
    # two quads merge into one six-sided face; the edge's end vertices stay
    bm = bmesh.from_edit_mesh(ob.data)
    assert _counts(ob) == (8, 11, 5) and sorted(len(f.verts) for f in bm.faces) == [4, 4, 4, 4, 6], _counts(ob)


def test_delete_edge_vertex_cleans_up():
    """Edit Mesh > Delete Edge/Vertex (Ctrl+Delete): the vertices left with two edges go too."""
    ob = _cube('EDGE')
    _select(ob, "EDGE", [0])
    assert bpy.ops.mesh.dissolve_mode() == {'FINISHED'}
    assert _counts(ob) == (6, 9, 5), _counts(ob)


def test_border_edge_is_kept():
    ob = _cube('FACE')
    _select(ob, "FACE", [0])
    bpy.ops.allset.delete_components()        # open box: border edges now
    bpy.ops.mesh.select_mode(type='EDGE')
    bm = bmesh.from_edit_mesh(ob.data)
    border = next(e for e in bm.edges if len(e.link_faces) == 1)
    border.select = True
    bmesh.update_edit_mesh(ob.data)
    before = _counts(ob)
    assert bpy.ops.allset.delete_components() == {'FINISHED'}
    assert _counts(ob) == before
    assert not any(e.select for e in bmesh.from_edit_mesh(ob.data).edges), "the selection is cleared, like Maya"


def test_delete_vertex_with_three_edges_stays():
    ob = _cube('VERT')
    _select(ob, "VERT", [0])
    assert bpy.ops.allset.delete_components() == {'FINISHED'}
    assert _counts(ob) == (8, 12, 6), _counts(ob)
    assert not any(v.select for v in bmesh.from_edit_mesh(ob.data).verts)


def _grid():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=3, y_subdivisions=3, size=3)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    return bpy.context.active_object


def test_delete_two_edge_vertices_only():
    """A grid corner (two edges) goes and its quad becomes a triangle; inner and border vertices stay."""
    for edges, want in ((2, (15, 23, 9)), (3, (16, 24, 9)), (4, (16, 24, 9))):
        ob = _grid()
        bm = bmesh.from_edit_mesh(ob.data)
        next(v for v in bm.verts if len(v.link_edges) == edges).select = True
        bm.select_flush_mode()
        bmesh.update_edit_mesh(ob.data)
        assert bpy.ops.allset.delete_components() == {'FINISHED'}
        assert _counts(ob) == want, (edges, _counts(ob))


def test_delete_edge_vertex_deletes_vertices_with_their_edges():
    ob = _cube('VERT')
    _select(ob, "VERT", [0])
    assert bpy.ops.mesh.dissolve_mode() == {'FINISHED'}
    # corner vertex and its 3 edges go; the 3 faces around it merge into one
    assert _counts(ob) == (7, 9, 4), _counts(ob)


def test_nothing_selected_cancels():
    ob = _cube('FACE')
    assert bpy.ops.allset.delete_components() == {'CANCELLED'}
    assert _counts(ob) == (8, 12, 6)
    bpy.ops.object.mode_set(mode='OBJECT')
