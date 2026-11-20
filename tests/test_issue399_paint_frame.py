"""Issue #399: F (Frame Selection) while painting skin weights frames what Maya frames: the selected vertices on the
posed mesh, or the whole posed mesh when no vertex is selected. GUI: tests/gui/gui_issue399_paint_frame.py."""

from importlib import import_module
from math import radians

import bpy
from mathutils import Vector

import kit

joints = import_module(kit.MODULE + ".operators.joints")
view_frame = import_module(kit.MODULE + ".operators.view_frame")
wp = import_module(kit.MODULE + ".operators.weight_paint")


def _scene():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    arm = joints.new_skeleton(bpy.context)
    parent = None
    for z in (0.0, 1.0, 2.0):
        parent = joints.add_joint(arm, Vector((0, 0, z)), parent, length=0.5)
    joints.finish(bpy.context, arm, ["joint1", "joint2", "joint3"])
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=2.0, location=(0, 0, 1.0), vertices=12)
    cyl = bpy.context.active_object
    with bpy.context.temp_override(object=cyl, active_object=cyl):
        cyl.modifiers.new("sub", 'SUBSURF').levels = 2
        bpy.ops.object.modifier_apply(modifier="sub")
    for ob in (arm, cyl):
        ob.select_set(True)
    bpy.context.view_layer.objects.active = cyl
    assert bpy.ops.allset.bind_skin() == {'FINISHED'}
    pb = arm.pose.bones["joint2"]
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (radians(90), 0, 0)              # the top half bends far from its rest place
    bpy.ops.object.select_all(action='DESELECT')
    cyl.select_set(True)
    bpy.context.view_layer.objects.active = cyl
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.context.view_layer.update()
    return arm, cyl


def _posed(cyl, indices):
    me = cyl.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    return [cyl.matrix_world @ me.vertices[i].co for i in indices]


def _same(a, b):
    return len(a) == len(b) and all((p - q).length < 1e-5 for p, q in zip(sorted(map(tuple, a)), sorted(map(tuple, b))))


def test_paint_frame_selected_vertices_posed():
    _arm, cyl = _scene()
    assert bpy.context.mode == 'PAINT_WEIGHT'
    top = [v.index for v in cyl.data.vertices if v.co.z > 0.8]
    wp.show_vertex_selection(cyl)
    wp.set_vertex_selection(cyl, top)
    cyl.data.update()
    pts = view_frame.frame_points(bpy.context, None, True, False)
    assert pts is not None, "F in Paint Skin Weights is left to Blender, which frames the selected joints"
    assert _same(pts, _posed(cyl, top)), "F frames the selected vertices where the posed mesh shows them"
    rest = [cyl.matrix_world @ cyl.data.vertices[i].co for i in top]
    assert not _same(pts, rest)


def test_paint_frame_face_mask_and_no_selection():
    _arm, cyl = _scene()
    faces = [p for p in cyl.data.polygons if p.center.z > 0.8]
    for p in cyl.data.polygons:
        p.select = p in faces
    cyl.data.use_paint_mask = True
    cyl.data.update()
    pts = view_frame.frame_points(bpy.context, None, True, False)
    want = sorted({i for p in faces for i in p.vertices})
    assert pts is not None and _same(pts, _posed(cyl, want)), "face mask: the selected faces' vertices"
    # nothing selected: the whole posed mesh (Maya F frames the painted object)
    for p in cyl.data.polygons:
        p.select = False
    cyl.data.update()
    pts = view_frame.frame_points(bpy.context, None, True, False)
    assert pts, "no selection: the painted mesh"
    posed = _posed(cyl, range(len(cyl.data.vertices)))
    lo = Vector(tuple(min(p[i] for p in posed) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in posed) for i in range(3)))
    for i in range(3):
        assert abs(min(p[i] for p in pts) - lo[i]) < 1e-4 and abs(max(p[i] for p in pts) - hi[i]) < 1e-4, i
    bpy.ops.object.mode_set(mode='OBJECT')
