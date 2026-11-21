"""Issue #416: File > Import (Maya Units and Axes) of a rig whose joints point Y down the bone and
hang without an armature node: Blender's reader connects a child whose head sits at its parent's tail, and moving
the axis / unit conversion into the bones must still move every bone exactly once. The rest skeleton equals
Blender's own reading of the file, the pose channels stay 0 at the bind pose (also under a joint whose PreRotation is
a fraction of a degree), and a skinned mesh keeps its place.
"""

import math
import os
from importlib import import_module

import bpy
from mathutils import Matrix, Vector

import kit

units = import_module(kit.MODULE + ".operators.units")
fbx_rig = import_module(kit.MODULE + ".operators.fbx_rig")
fbx_rig_import = import_module(kit.MODULE + ".operators.fbx_rig_import")

OUT = os.path.join(os.environ.get("ALLSET_TEST_OUT", bpy.app.tempdir), "fbx_connected")

# (name, parent, head, tail) in cm, Blender Z up; spine1 / spine2 / arm / forearm / leg / foot are connected chains,
# hips has three children (not connected), the arm chain bends and rolls
BONES = (
    ("Hips", None, (0, 0, 100), (0, 0, 110)),
    ("Spine", "Hips", (0, 0, 110), (0, 1, 122)),
    ("Spine1", "Spine", (0, 1, 122), (0, 2, 135)),
    ("Spine2", "Spine1", (0, 2, 135), (0, 2, 145)),
    ("LeftArm", "Spine2", (17, 3, 143), (40, 5, 140)),
    ("LeftForeArm", "LeftArm", (40, 5, 140), (62, 12, 139)),
    ("LeftHand", "LeftForeArm", (62, 12, 139), (70, 14, 139)),
    ("LeftUpLeg", "Hips", (10, 0, 95), (11, 1, 52)),
    ("LeftLeg", "LeftUpLeg", (11, 1, 52), (12, 4, 11)),
    ("LeftFoot", "LeftLeg", (12, 4, 11), (12, -10, 2)),
    ("RightUpLeg", "Hips", (-10, 0, 95), (-11, 1, 52)),
)
CONNECTED = {"Spine", "Spine1", "Spine2", "LeftForeArm", "LeftHand", "LeftLeg", "LeftFoot"}
ROLL = {"LeftArm": 30.0, "LeftForeArm": -20.0, "LeftFoot": 45.0}


def _clear():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions):
        for d in list(coll):
            coll.remove(d)
    sc = bpy.context.scene
    sc.unit_settings.system, sc.unit_settings.length_unit = 'METRIC', 'CENTIMETERS'
    sc.frame_start, sc.frame_end = 1, 20
    return sc, units.maya_unit(sc)


def _armature(k, name="rig"):
    arm = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    for bname, parent, head, tail in BONES:
        eb = arm.edit_bones.new(bname)
        eb.head, eb.tail = Vector(head) * k, Vector(tail) * k
        eb.roll = math.radians(ROLL.get(bname, 0.0))
        if parent is not None:
            eb.parent = arm.edit_bones[parent]
            eb.use_connect = bname in CONNECTED
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def _export_mixamo_style(path, k):
    """A Y-down-the-bone rig without an armature node: Blender's writer (bone Y = joint Y), the Null folded."""
    rig = _armature(k)
    bpy.ops.mesh.primitive_cube_add(size=20 * k, location=(0, 0, 120 * k))
    body = bpy.context.active_object
    body.name = "Body"
    for bname, *_rest in BONES:
        body.vertex_groups.new(name=bname)
    body.vertex_groups["Spine1"].add([v.index for v in body.data.vertices], 1.0, 'REPLACE')
    body.modifiers.new("skinCluster1", 'ARMATURE').object = rig
    body.parent = rig
    os.makedirs(OUT, exist_ok=True)
    for o in bpy.context.view_layer.objects:
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=False, add_leaf_bones=False, bake_anim=False,
                             apply_unit_scale=True)
    folded = fbx_rig.rewrite(path, path)[1]
    assert folded == 1, folded
    tree, _v = fbx_rig.load(path)
    index = fbx_rig.Index(tree)
    assert not any(m.props[2] == b"Null" for m in index.models.values())
    assert len(index.limbs()) == len(BONES)


def _native_rest(path):
    """{bone: world rest matrix (unit axes)} from Blender's own reader, in cm."""
    sc, k = _clear()
    bpy.ops.import_scene.fbx(filepath=path)
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    out = {}
    for b in arm.data.bones:
        m = arm.matrix_world @ b.matrix_local
        tail = (arm.matrix_world @ b.tail_local.to_4d()).to_3d() / k
        out[b.name] = (m.translation / k, m.to_3x3().normalized(), b.use_connect, tail)
    return out


def _kit_import(path):
    sc, k = _clear()
    assert bpy.ops.allset.file_import('EXEC_DEFAULT', filepath=path) == {'FINISHED'}
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    return sc, k, arm


def test_connected_bones_keep_the_rest_of_the_file():
    sc, k = _clear()
    path = os.path.join(OUT, "connected416.fbx")
    _export_mixamo_style(path, k)
    native = _native_rest(path)
    connected = {n for n, (_h, _r, c, _t) in native.items() if c}
    assert connected >= {"Spine1", "Spine2", "LeftForeArm", "LeftLeg"}, connected   # the reader connects them
    sc, k, arm = _kit_import(path)
    assert arm.matrix_world == Matrix.Identity(4)
    worst_head = worst_axis = worst_tail = 0.0
    for b in arm.data.bones:
        head, rot, _c, tail = native[b.name]
        worst_head = max(worst_head, (b.head_local / k - head).length)
        worst_axis = max(worst_axis, max((b.matrix_local.to_3x3().normalized().col[i] - rot.col[i]).length
                                         for i in range(3)))
        worst_tail = max(worst_tail, (b.tail_local / k - tail).length)
    print(f"fbx connected: {len(connected)} connected, head {worst_head:.2e} cm, axes {worst_axis:.2e}, "
          f"tails {worst_tail:.2e} cm")
    assert worst_head < 1e-3, worst_head
    assert worst_axis < 1e-4, worst_axis
    assert worst_tail < 1e-3, worst_tail


def test_connected_bones_rest_pose_channels_zero():
    sc, k = _clear()
    path = os.path.join(OUT, "connected416b.fbx")
    _export_mixamo_style(path, k)
    sc, k, arm = _kit_import(path)
    worst = 0.0
    for pb in arm.pose.bones:
        vals = list(pb.location) + [a for a in (pb.rotation_euler if pb.rotation_mode != 'QUATERNION'
                                                 else pb.rotation_quaternion[1:])]
        worst = max(worst, max(abs(v) for v in vals), max(abs(s - 1.0) for s in pb.scale))
    mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    centre = sum((ev.matrix_world @ v.co for v in ev.data.vertices), Vector()) / len(ev.data.vertices) / k
    print(f"fbx connected: largest pose channel {worst:.2e}, mesh centre {tuple(round(c, 4) for c in centre)}")
    assert worst < 1e-5, worst          # a joint turned by a fraction of a degree (Spine1) keeps its offset too
    assert (centre - Vector((0, 0, 120))).length < 1e-3, centre


def test_apply_conversion_moves_every_bone_once():
    """Directly: an armature object's matrix moved into its bones leaves every bone's world rest where it was."""
    sc, k = _clear()
    rig = _armature(1.0, "conv")
    g = Matrix.Translation((0.3, -0.2, 0.1)) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Scale(0.01, 4)
    rig.matrix_world = g
    before = {b.name: (rig.matrix_world @ b.matrix_local, (rig.matrix_world @ b.tail_local.to_4d()).to_3d())
              for b in rig.data.bones}
    connected_before = {b.name for b in rig.data.bones if b.use_connect}
    fbx_rig_import._apply_conversion(bpy.context, rig, g.copy())
    assert rig.matrix_world == Matrix.Identity(4)
    worst_m = worst_t = 0.0
    for b in rig.data.bones:
        m, tail = before[b.name]
        got = b.matrix_local
        worst_m = max(worst_m, (got.translation - m.translation).length,
                      max((got.to_3x3().normalized().col[i] - m.to_3x3().normalized().col[i]).length
                          for i in range(3)))
        worst_t = max(worst_t, (b.tail_local - tail).length)
    assert {b.name for b in rig.data.bones if b.use_connect} == connected_before
    assert worst_m < 1e-5, worst_m
    assert worst_t < 1e-6, worst_t
