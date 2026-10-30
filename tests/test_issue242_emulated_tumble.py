"""Issue #242: with Emulate 3 Button Mouse on, Blender hands Alt+LMB on as a plain middle drag; the kit tumbles on
it while the Alt key is held. GUI: tests/gui/gui_step267_emulate.py, tests/gui/gui_issue242_alt_tumble.py."""

from importlib import import_module

import bpy

import kit

view = import_module(kit.MODULE + ".operators.view")
keystate = import_module(kit.MODULE + ".operators.keystate")


def _with(emulate, modifier, held):
    inputs = bpy.context.preferences.inputs     # factory prefs of the test process, never saved
    old = (inputs.use_mouse_emulate_3_button, inputs.mouse_emulate_3_button_modifier, keystate.is_down)
    try:
        inputs.use_mouse_emulate_3_button = emulate
        inputs.mouse_emulate_3_button_modifier = modifier
        keystate.is_down = lambda t: held if t in ("LEFT_ALT", "RIGHT_ALT") else None
        return view.emulated_alt_drag(bpy.context)
    finally:
        inputs.use_mouse_emulate_3_button, inputs.mouse_emulate_3_button_modifier, keystate.is_down = old


def test_emulated_alt_drag():
    assert _with(True, 'ALT', True) is True
    assert _with(True, 'ALT', False) is False
    assert _with(True, 'ALT', None) is False        # OS can't tell: a real middle drag is never taken
    assert _with(False, 'ALT', True) is False
    try:
        bpy.context.preferences.inputs.mouse_emulate_3_button_modifier = 'OSKEY'
        oskey = bpy.context.preferences.inputs.mouse_emulate_3_button_modifier == 'OSKEY'
    finally:
        bpy.context.preferences.inputs.mouse_emulate_3_button_modifier = 'ALT'
    if oskey:      # the OS key choice isn't offered everywhere
        assert _with(True, 'OSKEY', True) is False


def test_alt_virtual_keys():
    assert keystate.vk_code("LEFT_ALT") == 0xA4 and keystate.vk_code("RIGHT_ALT") == 0xA5


def test_keymap_item_first_and_passes_through():
    maya_patches = import_module(kit.MODULE + ".keymap.maya_patches")
    ic_data = import_module(kit.MODULE + ".keymap.ic_data")
    patch = import_module(kit.MODULE + ".keymap.patch")
    kd = patch.KeyconfigData(maya_patches.apply(ic_data.generate()))
    for km in maya_patches.EMULATED_TUMBLE_KEYMAPS:
        mmb = [it[0] for it in kd.items(km) if it[1].get("type") == "MIDDLEMOUSE"]
        assert mmb and mmb[0] == "allset.emulated_tumble", (km, mmb)
    assert "allset.emulated_tumble" in maya_patches.PASS_THROUGH_FIRST
