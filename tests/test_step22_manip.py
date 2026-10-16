"""Step 22: Shift+drag a manipulator = Maya Smart Duplicate.

The Maya keyconfig puts ``maya_kit.manip_duplicate`` (Shift+LMB press, PASS_THROUGH)
in front of the gizmo's own tweak; the operator duplicates only in object mode with a
selection, the option on and the transform gizmo shown. The drag itself is checked in
tests/gui/gui_step22_manip_duplicate.py. Plan: docs/steps/step_22.md 「계획」.
"""

from importlib import import_module

import bpy

import kit

manip = import_module(kit.MODULE + ".operators.manip")
patches = import_module(kit.MODULE + ".keymap.maya_patches")
preferences = import_module(kit.MODULE + ".preferences")
mm = import_module(kit.MODULE + ".marking.menus")


def _fresh():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.view_layer.objects.active
    ob.name, ob.data.name = "pCube1", "pCubeShape1"
    return ob


def test_gizmo_keymaps_run_smart_duplicate_first():
    kc = bpy.context.window_manager.keyconfigs["Maya"]
    for name in patches.GIZMO_KEYMAPS:
        items = [k for k in kc.keymaps[name].keymap_items if k.active]
        ids = [k.idname for k in items]
        dup = items[ids.index("maya_kit.manip_duplicate")]
        assert (dup.type, dup.value, dup.shift, dup.ctrl, dup.alt) == \
            ('LEFTMOUSE', 'PRESS', True, False, False), name
        # step 28 puts manip_press (plain LMB) in front too; both before the gizmo's tweak
        assert ids.index("maya_kit.manip_duplicate") < ids.index("gizmogroup.gizmo_tweak"), (name, ids)
    assert "maya_kit.manip_duplicate" in patches.PASS_THROUGH_FIRST


def test_shift_precision_kept():
    # Measured (GUI): Shift held when the drag starts doesn't turn precision on, so Blender's
    # Shift precision during a drag stays (docs/steps/step_22.md 「계획」 3).
    km = bpy.context.window_manager.keyconfigs["Maya"].keymaps["Transform Modal Map"]
    assert {k.type for k in km.keymap_items if k.propvalue == 'PRECISION'} == {'LEFT_SHIFT', 'RIGHT_SHIFT'}


def _run():
    n = len(bpy.data.objects)
    res = bpy.ops.maya_kit.manip_duplicate()
    assert res == {'PASS_THROUGH'}, res
    return len(bpy.data.objects) - n


def test_duplicates_only_when_it_applies():
    shown = manip.from_xform_gizmo
    manip.from_xform_gizmo = lambda _context: True
    prefs = preferences.get()
    try:
        ob = _fresh()
        assert _run() == 1
        copy = bpy.context.view_layer.objects.active
        assert copy.name == "pCube2" and copy.data.name == "pCubeShape2" and not ob.select_get()
        assert (copy.matrix_world.translation - ob.matrix_world.translation).length < 1e-6

        prefs.smart_duplicate = False
        assert _run() == 0, "option off"
        prefs.smart_duplicate = True

        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        assert _run() == 0, "nothing selected"

        copy.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        assert _run() == 0, "edit mode: Smart Extrude, no new object (step 26)"
        bpy.ops.object.mode_set(mode='OBJECT')

        manip.from_xform_gizmo = lambda _context: False
        assert _run() == 0, "not the transform manipulator (light gizmo, ...)"
    finally:
        manip.from_xform_gizmo = shown
        prefs.smart_duplicate = True


def test_hold_menus_toggle_smart_duplicate():
    for menu in (mm.OPT_MOVE, mm.OPT_ROTATE, mm.OPT_SCALE):
        items = dict(i for i in menu.items if i != mm.DIVIDER)
        assert items["Smart Duplicate"] == ("maya_kit.manip_option", {"option": 'SMART_DUPLICATE'}), menu
        assert items["Smart Extrude"] == ("maya_kit.manip_option", {"option": 'SMART_EXTRUDE'}), menu
    prefs = preferences.get()
    assert prefs.smart_duplicate is True, "Maya default on (PREF:371-374)"
    bpy.ops.maya_kit.manip_option(option='SMART_DUPLICATE')
    assert prefs.smart_duplicate is False
    bpy.ops.maya_kit.manip_option(option='SMART_DUPLICATE')
    assert prefs.smart_duplicate is True
