"""#490: Extrude of faces along a curve that bends in more than one plane: every step turns the faces on from the
previous step's direction (the turns add up along the path), not straight from their first normal."""

from importlib import import_module

import bmesh
import bpy
from mathutils import Matrix, Vector

import kit

extrude = import_module(kit.MODULE + ".operators.extrude")
cmaya = import_module(kit.MODULE + ".operators.curves_maya")


def _scene(path):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    extrude.clear()
    c = cmaya.make_cv_curve(bpy.context, list(path), 1)
    c.name = "crv"
    c.select_set(True)
    me = bpy.data.meshes.new("m")
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(p) for p in ((-0.5, -0.2, 0), (0.5, -0.2, 0), (0.5, 0.2, 0), (-0.5, 0.2, 0))])
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("mesh", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(True)
    bmesh.update_edit_mesh(ob.data)
    return ob


def test_face_turns_add_up():
    # up, then +X, then +Y: three straight chords, one per step
    path = [(0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1)]
    ob = _scene(path)
    assert bpy.ops.allset.extrude(divisions=3, curve='SELECTED') == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    last = [v.co.copy() for f in bm.faces if f.select for v in f.verts]
    assert len(last) == 4, last
    # the chain of the three smallest turns, applied to the first corners about the faces' centre
    turn, heading, prev = Matrix.Identity(3), Vector((0, 0, 1)), Vector((0, 0, 0))
    for p in path[1:]:
        d = Vector(p) - prev
        turn = heading.rotation_difference(d.normalized()).to_matrix() @ turn
        heading, prev = d.normalized(), Vector(p)
    corners = [Vector(c) for c in ((-0.5, -0.2, 0), (0.5, -0.2, 0), (0.5, 0.2, 0), (-0.5, 0.2, 0))]
    want = [prev + turn @ c for c in corners]
    for w in want:
        assert min((w - p).length for p in last) < 1e-4, (w, last)
