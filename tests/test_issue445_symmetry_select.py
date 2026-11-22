"""#445: with Symmetry on, a component pick also takes its mirror partner. Partner lookup per symmetry mode and the
modifier rule; the picks in a real viewport: tests/gui/gui_issue445_symmetry_select.py."""
import math
from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit

ss = import_module(kit.MODULE + ".operators.symmetry_select")
symmetry = import_module(kit.MODULE + ".operators.symmetry")


def _cube(rot=(0, 0, 0), loc=(0, 0, 0)):
    """A 2-unit cube cut into 4 x 4 per side, in edit mode, nothing selected."""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add(size=2)
    ob = bpy.context.active_object
    ob.rotation_euler = [math.radians(a) for a in rot]
    ob.location = loc
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=3)
    bpy.ops.mesh.select_all(action='DESELECT')
    return ob


def _index(ob, dom, centre):
    bm = bmesh.from_edit_mesh(ob.data)
    seq = {'VERT': bm.verts, 'EDGE': bm.edges, 'FACE': bm.faces}[dom]
    seq.ensure_lookup_table()
    for i, el in enumerate(seq):
        c = el.co if dom == 'VERT' else sum((v.co for v in el.verts), Vector()) / len(el.verts)
        if (c - Vector(centre)).length < 1e-4:
            return i
    raise LookupError(centre)


def _mode(mode):
    sym = bpy.context.scene.allset_symmetry
    symmetry.set_mode(sym, mode)
    symmetry.apply(sym, symmetry.edit_meshes(bpy.context.scene))


def _partner(ob, dom, centre):
    got = ss.partners(bpy.context, dom, {ob.name: {_index(ob, dom, centre)}})
    return got.get(ob.name, set())


def test_object_axes():
    ob = _cube()
    for mode, want in (("OBJECT_X", (-0.5, 0.5, 1)), ("OBJECT_Y", (0.5, -0.5, 1)), ("OBJECT_Z", (0.5, 0.5, -1))):
        _mode(mode)
        assert _partner(ob, 'VERT', (0.5, 0.5, 1)) == {_index(ob, 'VERT', want)}, mode
    _mode("OBJECT_X")
    assert _partner(ob, 'EDGE', (0.5, 0.25, 1)) == {_index(ob, 'EDGE', (-0.5, 0.25, 1))}
    assert _partner(ob, 'FACE', (0.25, 0.25, 1)) == {_index(ob, 'FACE', (-0.25, 0.25, 1))}
    # a component on the mirror plane is its own partner
    assert _partner(ob, 'VERT', (0, 0.5, 1)) == {_index(ob, 'VERT', (0, 0.5, 1))}
    _mode("OFF")


def test_world_axes_on_a_turned_mesh():
    # turned 90 degrees about Y: world X runs along the mesh's own Z
    ob = _cube(rot=(0, 90, 0))
    _mode("WORLD_X")
    assert _partner(ob, 'VERT', (0.5, 0.5, 1)) == {_index(ob, 'VERT', (0.5, 0.5, -1))}
    _mode("OBJECT_X")
    assert _partner(ob, 'VERT', (0.5, 0.5, 1)) == {_index(ob, 'VERT', (-0.5, 0.5, 1))}
    _mode("OFF")


def test_world_mesh_away_from_the_plane_has_no_partner():
    ob = _cube(loc=(3, 0, 0))
    _mode("WORLD_X")
    assert _partner(ob, 'VERT', (0.5, 0.5, 1)) == set()
    assert _partner(ob, 'FACE', (0.25, 0.25, 1)) == set()
    _mode("OFF")


def test_topology_on_a_mesh_topology_cannot_split():
    # every side of a cut cube looks the same to a topology mirror: the mirrored position decides
    ob = _cube()
    _mode("TOPOLOGY")
    assert _partner(ob, 'VERT', (0.5, 0.5, 1)) == {_index(ob, 'VERT', (-0.5, 0.5, 1))}
    _mode("OFF")


def test_modifier_rule():
    before = {1, 2}
    assert ss.combine(before, {3, 4}, 'SET') == {3, 4}
    assert ss.combine(before, {2, 3}, 'ADD') == {1, 2, 3}
    assert ss.combine(before, {2, 3}, 'SUB') == {1}
    assert ss.combine(before, {2, 3}, 'XOR') == {1, 3}
    assert [ss.pick_mode(s, c) for s, c in ((0, 0), (1, 0), (0, 1), (1, 1))] == ['SET', 'XOR', 'SUB', 'ADD']


def test_apply_takes_the_partners_with_the_pick():
    ob = _cube()
    _mode("OBJECT_X")
    b, m = _index(ob, 'VERT', (0.5, 0.5, 1)), _index(ob, 'VERT', (-0.5, 0.5, 1))
    a = _index(ob, 'VERT', (-0.5, -0.5, 1))
    ctx = bpy.context
    # Shift on a component whose partner alone is selected: the partner turns off, the component on
    before = {ob.name: ({m}, [])}
    assert ss.apply(ctx, 'VERT', before, {ob.name: {b}}, 'XOR')
    assert ss.selected(ctx, 'VERT')[ob.name] == {b}
    # Ctrl+Shift adds both, Ctrl removes both
    ss.apply(ctx, 'VERT', {ob.name: ({a}, [])}, {ob.name: {b}}, 'ADD')
    assert ss.selected(ctx, 'VERT')[ob.name] == {a, b, m}
    ss.apply(ctx, 'VERT', {ob.name: ({a, b, m}, [])}, {ob.name: {b}}, 'SUB')
    assert ss.selected(ctx, 'VERT')[ob.name] == {a}
    _mode("OFF")


def test_turning_on_mirrors_the_selection():
    ob = _cube()
    b, m = _index(ob, 'VERT', (0.5, 0.5, 1)), _index(ob, 'VERT', (-0.5, 0.5, 1))
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bm.verts[b].select_set(True)
    bmesh.update_edit_mesh(ob.data)
    bpy.ops.allset.symmetry(mode="OBJECT_X")
    assert ss.selected(bpy.context, 'VERT')[ob.name] == {b, m}
    bpy.ops.allset.symmetry(mode="OFF")
