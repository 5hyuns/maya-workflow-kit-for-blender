"""Maya's HumanIK entries lead to Blender's Rigify (issue #319): Skeleton > HumanIK and Windows > Animation Editors >
HumanIK are one submenu — with Rigify off it offers to enable the add-on, with it on it lists Add Meta-Rig (Rigify's
own list), Generate Rig, Rig Settings / Bone Rig Type (a pinned Properties window) and Rig Controls (the sidebar's
Item tab); Quick Rig keeps working."""

import sys
from importlib import import_module

import bpy

import kit

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from test_step106_tool_settings_ae import Recorder  # noqa: E402

menu_map = import_module(kit.MODULE + ".ui.menu_map")
notices = import_module(kit.MODULE + ".ui.notices")
rigify_menu = import_module(kit.MODULE + ".ui.rigify_menu")
rig_tools = import_module(kit.MODULE + ".operators.rig_tools")
shelf_map = import_module(kit.MODULE + ".ui.shelf_map")


def _draw():
    rec = Recorder()
    rigify_menu.ALLSET_MT_rigify.draw(type("Menu", (), {"layout": rec})(), bpy.context)
    return rec


def _off():
    if rig_tools.rigify_enabled():
        import addon_utils
        addon_utils.disable("rigify", default_set=True)


def test_humanik_entries_lead_to_the_rigify_menu():
    for path in ("Skeleton/HumanIK", "Windows/Animation Editors/HumanIK"):
        assert menu_map.MAP[path] == ("menu", "ALLSET_MT_rigify"), path
        assert "Rigify" in notices.NOTICES[path][0] and "HumanIK" in notices.NOTICES[path][1], path
    action, _icon = shelf_map.lookup("Rigging", "Human IK", "HIKCharacterControlsTool")       # Rigging shelf
    assert action == ("menu", "ALLSET_MT_rigify"), action
    assert menu_map.MAP["Skeleton/Quick Rig"] == "allset.quick_rig"


def test_menu_offers_to_enable_rigify_then_lists_its_steps():
    _off()
    rec = _draw()
    assert rec.texts("operator") == ["Enable Rigify Add-on..."] and rec.texts("menu") == [], rec.log
    try:
        assert bpy.ops.allset.rigify_enable() == {'FINISHED'}
        assert rig_tools.rigify_enabled()
        rec = _draw()
        assert rec.texts("menu") == ["Add Meta-Rig"], rec.log
        assert rec.texts("operator") == ["Generate Rig", "Rig Settings...", "Bone Rig Type...", "Rig Controls"], rec.log
        assert [p.tab for p in rec.ops("allset.rigify_properties")] == ['DATA', 'BONE']
        assert getattr(bpy.types, rigify_menu.METARIG_MENU, None) is not None, "Rigify's meta-rig menu is registered"
        assert bpy.ops.allset.rigify_enable() == {'FINISHED'}       # already on: nothing to do
    finally:
        _off()


def test_properties_and_controls_need_an_armature():
    _off()
    try:
        bpy.ops.allset.rigify_enable()
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob)
        assert not bpy.ops.allset.rigify_controls.poll()
        assert not bpy.ops.allset.rigify_properties.poll()
        bpy.ops.object.armature_human_metarig_add()
        arm = bpy.context.active_object
        assert arm is not None and arm.type == 'ARMATURE' and arm.data.get("rig_id") is None
        # with a meta-rig the rows are available (the window ones are not run here: no UI); Generate Rig polls
        assert bpy.ops.allset.rigify_properties.poll() and bpy.ops.allset.rigify_controls.poll()
        assert bpy.ops.pose.rigify_generate.poll()
    finally:
        _off()


def test_quick_rig_still_enables_rigify_and_adds_a_metarig():
    _off()
    try:
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob)
        assert bpy.ops.allset.quick_rig() == {'FINISHED'}
        assert rig_tools.rigify_enabled()
        arm = bpy.context.active_object
        assert arm is not None and arm.type == 'ARMATURE' and len(arm.data.bones) > 20
    finally:
        _off()
