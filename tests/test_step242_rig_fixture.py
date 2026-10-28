"""Step 242 (Issue #159): Maya 2026 rig data fixture + Maya -> kit skeleton builder.

Fixture: tests/maya2026_rig_data.py (tools/gen_maya2026_rig_data.py from research/maya/re/joint_rig_2026_*.json and
the measured cross-checks, private notes). Builder / axis map: tests/maya2026_rig.py.
Checks: the fixture loads with the tables steps 243-252 use; the axis map round trip is <= 1e-12; the Maya joint
matrix rebuilt from t / jo / r / ra / s gives Maya's measured world positions; a built skeleton reads back its Maya
positions and axes and agrees with the kit's own joint frame (joints.joint_frame).
"""

import math
import random
from importlib import import_module

import bpy
from mathutils import Matrix, Vector

import kit
import maya2026_rig as rig
import maya2026_rig_data as data

joints = import_module(kit.MODULE + ".operators.joints")

TABLES = {
    "JOINT_MATH": ("attrs_defaults", "world_matrix_formula", "move_joint_156"),
    "SKELETON_MENU": ("skeleton", "skeleton2"),
    "IK": ("ik", "blender"),
    "SKINNING": ("skin", "dq"),
    "CONSTRAINTS_SDK": ("orient_blend", "parent_blend", "aim_up_types", "sdk_curve"),
    "SELECT_PICK": ("pickwalk", "pickwalk_controllers"),
    "MEASURED_IK_VERIFY": ("pv_length_vs_display_scale", "pv_farthest_joint_rule"),
    "MEASURED_DQ_SCALE": (),
    "MEASURED_SC_VERIFY": (),
    "MEASURED_SC_VERIFY2": (),
    "JOINT_TOOL": ("jointCtx", "front_clicks", "front_chain"),       # step 244
    "OJ_VERIFY": ("traditional_no_sao", "extremes", "siblings"),       # step 244 (measured)
}


def _skeletons(value, path="", out=None):
    """Every complete {joint: {"t", "jo", "w", "parent"}} dict in the fixture (each parent listed), by path."""
    out = {} if out is None else out
    if isinstance(value, dict):
        recs = [v for v in value.values() if isinstance(v, dict)]
        if recs and len(recs) == len(value) and all({"t", "jo", "w", "parent"} <= set(r) for r in recs)                 and all(r["parent"] is None or r["parent"] in value for r in recs):
            out[path] = value
            return out
        for k, v in value.items():
            _skeletons(v, f"{path}/{k}", out)
    return out


def _reset():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def test_fixture_loads_with_the_tables_later_steps_use():
    assert set(data.ALL) == set(TABLES), sorted(data.ALL)
    for name, keys in TABLES.items():
        table = data.ALL[name]
        assert table, name
        for k in keys:
            assert k in table, (name, k)
    assert len(data.IK["ik"]["rp_solve"]["rows"]) == 8
    assert data.JOINT_MATH["attrs_defaults"]["segmentScaleCompensate"] is True
    assert data.SKINNING["skin"]["prune_and_max"]["sum_after"] == 1.0
    pv = [r["pv_len"] for r in data.MEASURED_IK_VERIFY["pv_length_vs_display_scale"]]
    assert pv == [2.0, 4.0, 1.0], pv                       # pv length = 2 x jointDisplayScale (principles.md)
    assert len(_skeletons(data.ALL)) >= 10, sorted(_skeletons(data.ALL))


def test_fixture_holds_no_maya_script_text():
    text = open(data.__file__, encoding="utf-8").read()
    for bad in ("$", "`", "Traceback", "proc "):    # "proc " covers every MEL procedure header
        assert bad not in text, bad


def test_axis_map_round_trip_is_exact():
    rnd = random.Random(242)
    worst = 0.0
    for _ in range(2000):
        p = [rnd.uniform(-1e3, 1e3) for _ in range(3)]
        for unit in (1.0, 0.01, 0.1, 2.54):
            b = rig.to_blender_xyz(p, unit)
            back = rig.to_maya_xyz(b, unit)
            worst = max(worst, max(abs(a - c) / max(1.0, abs(a)) for a, c in zip(p, back)))
        axes = [[rnd.uniform(-1, 1) for _ in range(3)] for _ in range(3)]
        back = rig.frame_to_maya_rows(rig.frame_to_blender_rows(axes))
        worst = max(worst, max(abs(a - c) for ra, rb in zip(axes, back) for a, c in zip(ra, rb)))
    assert worst <= 1e-12, worst
    # direction: Maya +Y (up) = Blender +Z, Maya +Z (toward the viewer) = Blender -Y
    assert rig.to_blender_xyz((0, 1, 0)) == (0.0, -0.0, 1.0)
    assert rig.to_blender_xyz((0, 0, 1)) == (0.0, -1.0, 0.0)
    # the same convention as the kit's
    assert rig.MAYA_TO_BLENDER == joints.MAYA_WORLD
    assert rig.JOINT_AXES == joints.JOINT_AXES
    m = Matrix(rig.frame_to_blender_rows([[1, 2, 3], [4, 5, 6], [7, 8, 9]]))
    assert m == rig.frame_to_blender(Matrix(((1, 2, 3), (4, 5, 6), (7, 8, 9))))


def test_joint_matrix_gives_mayas_measured_world_positions():
    worst, n = 0.0, 0
    for path, skel in _skeletons(data.ALL).items():
        worlds = rig.world_matrices(skel)
        for name, rec in skel.items():
            if rec["w"] is None:
                continue
            err = (worlds[name].to_translation() - Vector(rec["w"])).length
            worst = max(worst, err)
            n += 1
            assert err < 2e-3, (path, name, err)          # fixture values are rounded to 4 decimals
    assert n >= 40, n
    print(f"  joints {n}, worst world error {worst:.2e}")


def test_built_skeleton_reads_back_maya_positions_and_axes():
    skels = _skeletons(data.ALL)
    for path in sorted(skels)[:6]:
        skel = skels[path]
        worlds = rig.world_matrices(skel)
        for unit in (1.0, 0.01):
            _reset()
            ob = rig.build_skeleton(skel, unit=unit, name="skeleton1")
            assert {b.name for b in ob.data.bones} == set(skel)
            for name in skel:
                pos, axes = rig.joint_world(ob, name, unit)
                want = worlds[name]
                assert (pos - want.to_translation()).length < 1e-4, (path, name, unit, pos)
                maya_axes = want.to_3x3().normalized()
                for i in range(2):                          # X (bone Y) and Y (bone Z); Z follows
                    err = (axes.col[i] - maya_axes.col[i]).length
                    assert err < 1e-5, (path, name, unit, i, err)
                # the kit reads the same frame from the bone
                bone = ob.data.bones[name]
                kit_axes = (ob.matrix_world.to_3x3() @ bone.matrix_local.to_3x3()).normalized() @ joints.JOINT_AXES
                assert (rig.frame_to_maya(kit_axes).col[0] - maya_axes.col[0]).length < 1e-5
                parent = skel[name].get("parent")
                if parent:
                    assert bone.parent is not None and bone.parent.name == parent
    _reset()


def test_build_without_orientation_aims_at_the_child():
    skel = data.JOINT_MATH["move_joint_156"]["start"]["attrs"]
    world = data.JOINT_MATH["move_joint_156"]["start"]["world"]
    skel = {n: dict(r, parent=p, w=world[n]) for (n, r), p in zip(skel.items(), (None, "j1", "j2", "j3"))}
    _reset()
    ob = rig.build_skeleton(skel, oriented=False)
    b1 = ob.data.bones["j1"]
    want = rig.to_blender(Vector(world["j2"]) - Vector(world["j1"])).normalized()
    assert (b1.y_axis - want).length < 1e-5
    assert ob.data.bones["j2"].use_connect
    _reset()
