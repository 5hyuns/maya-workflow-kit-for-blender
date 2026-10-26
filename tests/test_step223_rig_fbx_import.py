"""Step 223 (Issue #133, ATTACH_PLAN L12, decision 4 D): a rig FBX exported from Maya 2026 imports with the same
pose at every frame as in Maya — joint world positions within 1e-3 cm — with Euler rotation keys at Maya's own key
frames (each Maya rotate curve = one Blender rotation_euler curve with the same values, sign / axis per bone axes),
no conversion on the skeleton, the skinned mesh outside it and the Time Slider = the file's range.
Maya truth: tests/maya223_rig_data.py + tests/maya223/*.fbx (research/scripts/maya_rig223/make.py, mayapy 2026)."""

import math
import os
from importlib import import_module

import bpy
from mathutils import Vector

import kit

import maya223_rig_data as truth

compat = import_module(kit.MODULE + ".compat")
units = import_module(kit.MODULE + ".operators.units")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "tmp", "test_step223")
JOINTS = ("root", "spine", "head", "arm", "hand")


def _scene():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    scene = bpy.context.scene
    scene.unit_settings.system, scene.unit_settings.length_unit = 'METRIC', 'CENTIMETERS'   # the kit template
    scene.frame_start, scene.frame_end = 1, 250
    return scene


def _import(name):
    scene = _scene()
    path = os.path.join(HERE, "maya223", name)
    res = bpy.ops.allset.file_import('EXEC_DEFAULT', filepath=path)
    assert res == {'FINISHED'}, res
    arm = next(o for o in scene.objects if o.type == 'ARMATURE')
    return scene, arm


def _bl(p):
    return Vector((p[0], -p[2], p[1])) * 0.01        # Maya (x, y, z) cm -> Blender (x, -z, y), 1 cm = 0.01 BU


def _world_err(scene, arm, frames):
    worst, where = 0.0, None
    for f, d in frames.items():
        scene.frame_set(int(f))
        for j, p in d["world"].items():
            w = arm.matrix_world @ arm.pose.bones[j].head
            e = (w - _bl(p)).length / 0.01
            if e > worst:
                worst, where = e, (j, f)
    return worst, where


def test_maya_rig_pose_every_frame():
    scene, arm = _import("rig223_default.fbx")
    worst, where = _world_err(scene, arm, truth.FBX["default"])
    print("joint world error cm", worst, where)
    assert worst < 1e-3, (worst, where)


def test_skeleton_mesh_and_range_like_maya():
    scene, arm = _import("rig223_default.fbx")
    assert arm.name.startswith("skeleton"), arm.name
    assert arm.matrix_world == arm.matrix_world.Identity(4), arm.matrix_world
    body = scene.objects["body"]
    assert body.parent is None
    assert any(m.type == 'ARMATURE' and m.object == arm for m in body.modifiers)
    assert all(abs(x) < 1e-6 for x in body.rotation_euler) and all(abs(x - 1) < 1e-6 for x in body.scale)
    assert (scene.frame_start, scene.frame_end) == tuple(int(x) for x in truth.FBX["range"])
    for j in JOINTS:
        assert arm.pose.bones[j].rotation_mode not in ('QUATERNION', 'AXIS_ANGLE'), j
    # the skin follows its joints like Maya's skinCluster (every 7th vertex, Maya vertex order)
    worst = 0.0
    for f, pts in truth.VERTS.items():
        scene.frame_set(int(f))
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        for i, p in enumerate(pts):
            worst = max(worst, ((ev.matrix_world @ ev.data.vertices[7 * i].co) - _bl(p)).length / 0.01)
    print("skin vertex error cm", worst)
    assert worst < 0.02, worst            # measured 0.0101 cm on the 10 cm body (joints themselves 1e-5)


def _curve_values(arm, pb, index, frames):
    path = f'pose.bones["{pb.name}"].rotation_euler'
    fc = next((c for c in compat.id_fcurves(arm) if c.data_path == path and c.array_index == index), None)
    return fc, ([math.degrees(fc.evaluate(f)) for f in frames] if fc else None)


def test_euler_keys_equal_maya_per_frame():
    scene, arm = _import("rig223_default.fbx")
    frames = [int(f) for f in truth.FBX["default"]]
    maya_keys = truth.FBX["maya_import_curves"]["rig223_default"]
    for plug, key_times in maya_keys.items():
        j, attr = plug.split(".")
        i = "XYZ".index(attr[-1])
        want = [truth.FBX["default"][str(f)]["rotate"][j][i] for f in frames]
        pb = arm.pose.bones[j]
        found = None
        for index in range(3):
            fc, got = _curve_values(arm, pb, index, frames)
            if fc is None:
                continue
            for sign in (1.0, -1.0):
                if max(abs(sign * g - w) for g, w in zip(got, want)) < 1e-3:
                    found = (fc, sign)
        assert found is not None, plug
        fc = found[0]
        times = [round(k.co.x, 4) for k in fc.keyframe_points]
        assert times == [round(t, 4) for t in key_times], (plug, times, key_times)


def test_quaternion_curves_resampled_to_euler():
    """Maya writes quaternion-interpolated rotations resampled (24 keys); they import as Euler with the pose."""
    scene, arm = _import("rig223_quat.fbx")
    worst, where = _world_err(scene, arm, truth.FBX["quat"])
    assert worst < 1e-3, (worst, where)
    assert arm.pose.bones["spine"].rotation_mode != 'QUATERNION'


def test_blender_reader_alone_is_off():
    """Why: Blender's FBX reader samples linearly between keys (the [U] of DECISIONS7 §3)."""
    scene = _scene()
    bpy.ops.import_scene.fbx(filepath=os.path.join(HERE, "maya223", "rig223_default.fbx"))
    arm = next(o for o in scene.objects if o.type == 'ARMATURE')
    worst, _where = _world_err(scene, arm, truth.FBX["default"])
    print("Blender reader alone, joint world error cm", worst)
    assert worst > 0.5


# --- step 222 round trip: the kit's own Maya rig FBX comes back exactly ------------------------------------------

def _kit_rig(scene):
    k = units.maya_unit(scene)
    arm = bpy.data.armatures.new("skeleton1")
    rig = bpy.data.objects.new("skeleton1", arm)
    scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    pts = ((0, 0, 0), (0, 5, 2), (0, 10, 0))
    prev = None
    for i, (name, p) in enumerate(zip(("root", "spine", "head"), pts)):
        eb = arm.edit_bones.new(name)
        eb.head = _bl(p) * (k / 0.01)
        eb.tail = (_bl(pts[i + 1]) if i + 1 < 3 else _bl(p) + Vector((0, 0, 0.02))) * (k / 0.01)
        if prev is not None:
            eb.parent, eb.use_connect = prev, True
        prev = eb
    bpy.ops.object.mode_set(mode='POSE')
    for name, keys in (("root", ((1, 0.0), (10, 90.0))), ("spine", ((1, 0.0), (6, 50.0), (10, -30.0)))):
        pb = rig.pose.bones[name]
        pb.rotation_mode = 'XYZ'
        for f, deg in keys:
            pb.rotation_euler = (math.radians(deg) * 0.3, math.radians(deg), 0.0)
            pb.keyframe_insert("rotation_euler", frame=f)
    bpy.ops.object.mode_set(mode='OBJECT')
    scene.frame_start, scene.frame_end = 1, 10
    return rig


def test_step222_round_trip_exact():
    scene = _scene()
    rig = _kit_rig(scene)
    want = {}
    for f in range(1, 11):
        scene.frame_set(f)
        want[f] = {pb.name: (rig.matrix_world @ pb.head).copy() for pb in rig.pose.bones}
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "round_trip.fbx")
    for ob in scene.objects:
        ob.select_set(True)
    res = bpy.ops.allset.file_export_all('EXEC_DEFAULT', export_type='FBX', filepath=path, animation=True)
    assert res == {'FINISHED'}, res
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    res = bpy.ops.allset.file_import('EXEC_DEFAULT', filepath=path)
    assert res == {'FINISHED'}, res
    arm = next(o for o in scene.objects if o.type == 'ARMATURE')
    worst = 0.0
    for f in range(1, 11):
        scene.frame_set(f)
        for name, p in want[f].items():
            worst = max(worst, ((arm.matrix_world @ arm.pose.bones[name].head) - p).length / 0.01)
    print("kit round trip joint error cm", worst)
    assert worst < 1e-3, worst
