"""Step 30: selection feel — marquee select-through keymap items, the X-ray watch, the
pre-selection gizmo group, Maya undo queue (256 steps) through prefs_preset.

Box/lasso through hidden vertices and the highlight are checked in tests/gui/gui_step30_selection.py.

"""

import types
from importlib import import_module

import bpy

import kit

patches = import_module(kit.MODULE + ".keymap.maya_patches")
marquee = import_module(kit.MODULE + ".operators.marquee")
preselect = import_module(kit.MODULE + ".operators.preselect")
prefs_preset = import_module(kit.MODULE + ".prefs_preset")
preferences = import_module(kit.MODULE + ".preferences")


def test_select_through_items_lead_box_and_lasso():
    kc = bpy.context.window_manager.keyconfigs["Maya-style"]
    assert "allset.select_through" in patches.PASS_THROUGH_FIRST
    for km_name in patches.SELECT_DRAG_KEYMAPS:
        items = [k for k in kc.keymaps[km_name].keymap_items if k.active]
        target = "view3d.select_lasso" if "Lasso" in km_name else "view3d.select_box"
        for shift in (False, True):
            for ctrl in (False, True):
                same = [k.idname for k in items if k.type == 'LEFTMOUSE' and k.value == 'CLICK_DRAG'
                        and k.shift == shift and k.ctrl == ctrl and not k.alt]
                assert same[:2] == ["allset.select_through", target], (km_name, shift, ctrl, same)


def _fake_entry(running):
    shading = types.SimpleNamespace(show_xray=True, xray_alpha=1.0)
    space = types.SimpleNamespace(shading=shading)
    window = types.SimpleNamespace(modal_operators=[types.SimpleNamespace(bl_idname="VIEW3D_OT_select_box")]
                                   if running else [])
    return shading, window, [space, window, "show_xray", "xray_alpha", 0.5, False, 0.0]


def test_watch_restores_after_the_select_modal():
    shading, window, entry = _fake_entry(running=True)
    marquee._active.clear()
    marquee._active[1] = entry
    assert marquee._watch() is not None and shading.show_xray, "still dragging"
    window.modal_operators.clear()
    assert marquee._watch() is None, "nothing left to watch"
    assert shading.show_xray is False and shading.xray_alpha == 0.5
    # Never saw the modal (e.g. the drag was taken by something else): restore after a second.
    shading, window, entry = _fake_entry(running=False)
    marquee._active[2] = entry
    for _ in range(int(marquee._GIVE_UP / marquee._TICK) + 1):
        if marquee._watch() is None:
            break
    assert shading.show_xray is False and not marquee._active


def test_select_through_needs_edit_mesh_and_option():
    # Headless: no 3D View space; begin() must refuse quietly.
    assert marquee.begin(bpy.context) is False
    assert bpy.ops.allset.select_through.poll()


def test_preselect_group_registered_and_polls_off():
    assert "bl_rna" in preselect.ALLSET_GGT_preselect.__dict__, "registered"
    assert preferences.get().preselect_highlight is True
    assert preselect._enabled(bpy.context) is False, "object mode"


def test_undo_queue_is_maya_infinite():
    prefs = bpy.context.preferences
    ap = preferences.get()
    assert ap.use_maya_undo and prefs.edit.undo_steps == 256, prefs.edit.undo_steps
    assert ap.undo_backup, "the user's value is backed up"
    ap.use_maya_undo = False
    assert prefs.edit.undo_steps == 32 and ap.undo_backup == ""
    ap.use_maya_undo = True
    assert prefs.edit.undo_steps == 256
    # Navigation group untouched by the undo group.
    assert prefs_preset.read(prefs) == dict(prefs_preset.PRESET)
