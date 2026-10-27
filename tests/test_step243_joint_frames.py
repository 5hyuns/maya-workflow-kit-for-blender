"""Step 243 (Issue #160): moving a joint keeps every Maya frame; Preserve Children; Edit-mode Channel Box Translate.

Maya 2026 (research/maya/re/joint_rig_2026_joint_math.md §3; numbers tests/maya2026_rig_data.py JOINT_MATH
"move_joint_156"): chain j1 (0,0,0) j2 (3,1,0) j3 (6,0,-1) j4 (8,1,1) oriented, j2 moved +2 Maya Y:
- plain move: j3 / j4 follow (+2 Y), every jointOrient unchanged (j1's X no longer aims at j2), j2.t (3.7947, 1.8974, 0);
- Preserve Children: j3 / j4 stay, j3.t (3.9196, -1.9069, 0), every jointOrient unchanged.
Kit: operators/joint_edit.py (process / keep_frames / set_joint_translate), joint_selection pick shape, hold D / Insert.
"""

from importlib import import_module

import bpy
from mathutils import Vector

import kit
import maya2026_rig as rig
import maya2026_rig_data as data

joint_edit = import_module(kit.MODULE + ".operators.joint_edit")
js = import_module(kit.MODULE + ".operators.joint_selection")
hold = import_module(kit.MODULE + ".operators.hold")
cb = import_module(kit.MODULE + ".ui.channel_box")

CASE = data.JOINT_MATH["move_joint_156"]
PARENTS = {"j1": None, "j2": "j1", "j3": "j2", "j4": "j3"}
NAMES = tuple(PARENTS)


def _skel(case="start"):
    c = CASE[case]
    return {n: dict(c["attrs"][n], parent=PARENTS[n], w=c["world"][n]) for n in NAMES}


def _reset():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.context.scene.tool_settings.use_transform_skip_children = False
    joint_edit.rebase()


def _build(unit=1.0):
    _reset()
    ob = rig.build_skeleton(_skel(), unit=unit, name="skeleton1")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    return ob


def _pick(ob, name):
    js.select_edit(bpy.context, ob, name)
    joint_edit.process(bpy.context)          # the watch's snapshot before the move


def _frames(ob, unit=1.0):
    return {n: rig.joint_world(ob, n, unit) for n in NAMES}


def _err(a, b):
    return max((a.col[i] - b.col[i]).length for i in range(3))


def _maya_frames(case):
    attrs = {n: dict(CASE[case]["attrs"][n], parent=PARENTS[n]) for n in NAMES}
    return {n: m.to_3x3().normalized() for n, m in rig.world_matrices(attrs).items()}


def _move_maya_y(amount, unit):
    bpy.ops.transform.translate(value=tuple(rig.to_blender((0.0, amount, 0.0), unit)))


def test_plain_move_keeps_every_maya_frame_children_follow():
    for unit in (1.0, 0.01):
        ob = _build(unit)
        before = _frames(ob, unit)
        _pick(ob, "j2")
        _move_maya_y(2.0, unit)
        assert joint_edit.process(bpy.context) == ["j1"], "only j1's bone re-aimed"
        after = _frames(ob, unit)
        maya = CASE["move_ws_j2"]["world"]
        want_frames = _maya_frames("move_ws_j2")
        for n in NAMES:
            pos, axes = after[n]
            assert (pos - Vector(maya[n])).length < 2e-3, (unit, n, pos, maya[n])
            assert _err(axes, before[n][1]) < 1e-6, (unit, n, "Maya frame turned", _err(axes, before[n][1]))
            assert _err(axes, want_frames[n]) < 1e-3, (unit, n, "vs Maya jointOrient")
        # j1's bone still reaches j2 (Maya draws the bone to the child); its Maya X no longer aims there
        eb1 = ob.data.edit_bones["j1"]
        assert (eb1.tail - ob.data.edit_bones["j2"].head).length < 1e-6
        x = after["j1"][1].col[0]
        aim = (after["j2"][0] - after["j1"][0]).normalized()
        assert x.dot(aim) < 0.99, "Maya: j1's X keeps its old direction"
        assert {eb.name for eb in ob.data.edit_bones if rig.MAYA_FRAME in eb} == {"j1"}
        t = joint_edit.joint_translate(ob.data.edit_bones["j2"]) / unit
        assert (t - Vector(CASE["move_ws_j2"]["attrs"]["j2"]["t"])).length < 1e-3, t
    _reset()


def test_preserve_children_moves_only_the_joint():
    ob = _build()
    ts = bpy.context.scene.tool_settings
    ts.use_transform_skip_children = True
    before = _frames(ob)
    _pick(ob, "j2")
    ebs = ob.data.edit_bones
    assert ebs["j2"].select_head and not ebs["j2"].select_tail and not ebs["j3"].select_head
    _move_maya_y(2.0, 1.0)
    fixed = joint_edit.process(bpy.context)
    assert set(fixed) == {"j1", "j2"}, fixed
    after = _frames(ob)
    maya = CASE["move_ws_j2_preserveChildPosition"]
    for n in NAMES:
        assert (after[n][0] - Vector(maya["world"][n])).length < 2e-3, (n, after[n][0])
        assert _err(after[n][1], before[n][1]) < 1e-6, n
    t3 = joint_edit.joint_translate(ebs["j3"])
    assert (t3 - Vector(maya["attrs"]["j3"]["t"])).length < 1e-3, t3
    _reset()


def test_channel_box_translate_entry_moves_like_w():
    ob = _build()
    before = _frames(ob)
    js.select_edit(bpy.context, ob, "j2")
    scene = bpy.context.scene
    assert scene.allset_joint_tx == "3.162" and scene.allset_joint_ty == "0", (scene.allset_joint_tx, scene.allset_joint_ty)
    want = CASE["move_ws_j2"]["attrs"]["j2"]["t"]
    scene.allset_joint_tx = f"{want[0]}"
    scene.allset_joint_ty = "+=" + f"{want[1]}"
    after = _frames(ob)
    for n in NAMES:
        assert (after[n][0] - Vector(CASE["move_ws_j2"]["world"][n])).length < 2e-3, (n, after[n][0])
        assert _err(after[n][1], before[n][1]) < 1e-6, n
    # with Preserve Children the children stay
    scene.tool_settings.use_transform_skip_children = True
    js.select_edit(bpy.context, ob, "j2")
    scene.allset_joint_tx = "+=1"
    assert (rig.joint_world(ob, "j3")[0] - Vector(CASE["move_ws_j2"]["world"]["j3"])).length < 2e-3
    assert (rig.joint_world(ob, "j2")[0] - after["j2"][0]).length > 0.9
    # a top joint's Translate is its position in Maya world axes
    js.select_edit(bpy.context, ob, "j1")
    scene.allset_joint_tz = "-1"
    assert (rig.joint_world(ob, "j1")[0] - Vector((0, 0, -1))).length < 1e-5
    _reset()


def test_channel_box_draws_translate_in_edit_mode():
    ob = _build()
    js.select_edit(bpy.context, ob, "j2")
    from test_step55_pose_cb import _draw_cb
    rec = _draw_cb()
    labels = rec.texts("label")
    assert "j2" in labels and "Translate X" in labels and "Translate Z" in labels, labels
    assert "Editing joints: W / E / R move them," in labels
    _reset()


def test_undo_and_redo_keep_the_frames():
    ob = _build()
    before = _frames(ob)
    bpy.ops.ed.undo_push(message="start")
    _pick(ob, "j2")
    bpy.ops.transform.translate('EXEC_DEFAULT', True, value=(0.0, 0.0, 2.0))
    joint_edit.process(bpy.context)
    moved = _frames(ob)
    bpy.ops.ed.undo()
    ob = bpy.context.object
    joint_edit.process(bpy.context)
    back = _frames(ob)
    for n in NAMES:
        assert (back[n][0] - before[n][0]).length < 1e-5 and _err(back[n][1], before[n][1]) < 1e-6, n
    bpy.ops.ed.redo()
    ob = bpy.context.object
    joint_edit.process(bpy.context)
    again = _frames(ob)
    for n in NAMES:
        assert (again[n][0] - moved[n][0]).length < 1e-5, n
        assert _err(again[n][1], before[n][1]) < 1e-6, (n, "redo lost the Maya frame")
    _reset()


def test_orient_change_is_not_reverted_and_pose_mode_keeps_frames():
    ob = _build()
    _pick(ob, "j2")
    _move_maya_y(2.0, 1.0)
    joint_edit.process(bpy.context)
    kept = _frames(ob)
    eb = ob.data.edit_bones["j3"]
    eb.roll += 0.3                       # an orient: the roll changes on purpose
    joint_edit.process(bpy.context)
    assert _err(_frames(ob)["j3"][1], kept["j3"][1]) > 0.1, "an orient change must stay"
    eb = ob.data.edit_bones["j4"]        # a kit command that writes the Maya frame itself (Mirror, Orient end joints)
    eb.head = eb.head + Vector((0.0, 0.0, 0.5))
    eb[rig.MAYA_FRAME] = [0.0, 1.0, 0.0, 0.0]
    joint_edit.process(bpy.context)
    assert list(eb[rig.MAYA_FRAME]) == [0.0, 1.0, 0.0, 0.0]
    bpy.ops.object.mode_set(mode='POSE')
    after = _frames(ob)
    assert _err(after["j1"][1], kept["j1"][1]) < 1e-6, "the kept frame survives leaving edit mode"
    _reset()


def test_d_hold_and_insert_toggle_preserve_children():
    ob = _build()
    ts = bpy.context.scene.tool_settings
    js.select_edit(bpy.context, ob, "j2")
    ebs = ob.data.edit_bones
    assert ebs["j3"].select and ebs["j4"].select
    hold.begin(ts, "preserve_children")
    assert ts.use_transform_skip_children
    assert ebs["j2"].select_head and not ebs["j3"].select and not ebs["j4"].select
    assert ebs.active.name == "j2"
    hold.end(ts, "preserve_children")
    assert not ts.use_transform_skip_children and ebs["j3"].select and ebs["j4"].select
    bpy.ops.allset.pivot_toggle()
    assert ts.use_transform_skip_children and not ebs["j3"].select
    bpy.ops.allset.pivot_toggle()
    assert not ts.use_transform_skip_children and ebs["j3"].select
    # the Tool Settings check box: the watch re-shapes the pick
    joint_edit.process(bpy.context)
    ts.use_transform_skip_children = True
    joint_edit.process(bpy.context)
    assert not ebs["j3"].select and ebs["j2"].select_head
    _reset()


def test_keys():
    kc = kit.maya_kc()
    km = kc.keymaps["Armature"]
    d = [i for i in km.keymap_items if i.type == 'D' and not (i.ctrl or i.shift or i.alt) and i.active]
    assert [i.idname for i in d] == ["allset.hold"] and d[0].properties.name == "preserve_children", \
        [i.idname for i in d]
    ins = [i for i in km.keymap_items if i.type == 'INSERT' and i.active]
    assert [i.idname for i in ins] == ["allset.pivot_toggle"], [i.idname for i in ins]
