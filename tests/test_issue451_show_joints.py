"""Issue #451: the panel's Show > Joints hides the joints only. Rig controls drawn as curve bone shapes stay; they
follow Show > NURBS Curves. A scene without shaped controls keeps the view's armature filter."""

from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

cc = import_module(kit.MODULE + ".ui.curve_controls")
pm = import_module(kit.MODULE + ".ui.panel_menus")
pmd = import_module(kit.MODULE + ".ui.panel_menu_data")
lj = import_module(kit.MODULE + ".ui.layer_joints")
compat = import_module(kit.MODULE + ".compat")


def _clear():
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _rig(with_control=True):
    """Armature `rig`: joints root / mid / tip, and (with_control) bone `ctrl` with a curve custom shape."""
    _clear()
    sc = bpy.context.scene
    arm = bpy.data.armatures.new("rig")
    rig = bpy.data.objects.new("rig", arm)
    sc.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    names = ["root", "mid", "tip"] + (["ctrl"] if with_control else [])
    for i, name in enumerate(names):
        eb = arm.edit_bones.new(name)
        eb.head, eb.tail = (0, 0, i), (0, 0, i + 1)
    bpy.ops.object.mode_set(mode='OBJECT')
    if with_control:
        circle = bpy.data.curves.new("ctrl_shape", 'CURVE')
        circle.splines.new('POLY').points.add(3)
        shape = bpy.data.objects.new("ctrl_shape", circle)
        rig.pose.bones["ctrl"].custom_shape = shape
    return rig


def _ctx():
    space = SimpleNamespace(type='VIEW_3D', show_object_viewport_armature=True, show_object_viewport_curve=True,
                            shading=None, overlay=SimpleNamespace(show_extras=True))
    return SimpleNamespace(space_data=space, scene=bpy.context.scene), space


def _hidden(rig):
    return {pb.name for pb in rig.pose.bones if compat.bone_hidden(pb)}


def test_joints_row_is_the_kit_switch():
    assert ("set", "SHOW_JOINTS", "Joints") in pmd.SHOW
    assert not any(r[0] == "prop" and r[-1] == "Joints" for r in pmd.SHOW)


def test_joints_off_keeps_curve_controls():
    rig = _rig()
    ctx, space = _ctx()
    assert pm.state(ctx, "SHOW_JOINTS") is True
    pm.apply(ctx, "SHOW_JOINTS")
    assert pm.state(ctx, "SHOW_JOINTS") is False
    assert space.show_object_viewport_armature is True, "the armature stays drawn: its controls are in it"
    assert _hidden(rig) == {"root", "mid", "tip"}
    # NURBS Curves off on top hides the control too; on again brings back only the control
    pm.apply(ctx, "SHOW_NURBS_CURVES")
    assert _hidden(rig) == {"root", "mid", "tip", "ctrl"}
    pm.apply(ctx, "SHOW_NURBS_CURVES")
    assert _hidden(rig) == {"root", "mid", "tip"}
    pm.apply(ctx, "SHOW_JOINTS")
    assert pm.state(ctx, "SHOW_JOINTS") is True and _hidden(rig) == set()
    assert not any(pb.get(cc.JOINT_MARK) for pb in rig.pose.bones)


def test_joints_on_keeps_a_joint_the_user_hid():
    rig = _rig()
    ctx, _space = _ctx()
    compat.set_bone_hidden(rig.pose.bones["mid"], True)
    pm.apply(ctx, "SHOW_JOINTS")
    pm.apply(ctx, "SHOW_JOINTS")
    assert _hidden(rig) == {"mid"}
    # the joint's own Visibility (Channel Box / layers) tells a Show-filter hide from the user's
    pm.apply(ctx, "SHOW_JOINTS")
    assert lj._own_hidden(rig, rig.data.bones, False) == ["mid"]
    pm.apply(ctx, "SHOW_JOINTS")


def test_no_controls_uses_the_view_filter():
    rig = _rig(with_control=False)
    ctx, space = _ctx()
    pm.apply(ctx, "SHOW_JOINTS")
    assert space.show_object_viewport_armature is False and _hidden(rig) == set()
    assert pm.state(ctx, "SHOW_JOINTS") is False
    pm.apply(ctx, "SHOW_JOINTS")
    assert space.show_object_viewport_armature is True and pm.state(ctx, "SHOW_JOINTS") is True


def test_show_all_and_disable_bring_joints_back():
    rig = _rig()
    ctx, _space = _ctx()
    pm.apply(ctx, "SHOW_JOINTS")
    pm.apply(ctx, "SHOW_ALL")
    assert _hidden(rig) == set() and pm.state(ctx, "SHOW_JOINTS") is True
    pm.apply(ctx, "SHOW_JOINTS")
    cc.release_all()
    assert _hidden(rig) == set()
