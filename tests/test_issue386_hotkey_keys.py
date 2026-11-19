"""#386: the kit Hotkey Editor (and the Marking Menu Editor's hotkey field) take every keyboard key Blender has,
like Blender's own keymap editor: the "<" key of German / Nordic keyboards (Blender's GRLESS), the "+" key (PLUS),
the Menu key, the media keys. Modifier keys stay modifiers. The list shows "<" / "+" for them."""

from importlib import import_module

import bpy

import kit

# Event types Blender lists among the keyboard items that are not keys a hotkey can be (window / area events, XR)
NOT_KEYS = {"NONE", "MOUSESMARTZOOM", "WINDOW_DEACTIVATE", "ACTIONZONE_AREA", "ACTIONZONE_REGION",
            "ACTIONZONE_REGION_QUAD", "ACTIONZONE_FULLSCREEN", "XR_ACTION"}
MODIFIERS = {"LEFT_CTRL", "RIGHT_CTRL", "LEFT_SHIFT", "RIGHT_SHIFT", "LEFT_ALT", "RIGHT_ALT", "OSKEY", "HYPER"}


def m(name):
    return import_module(f"{kit.MODULE}.{name}")


def blender_keyboard_keys():
    """Every event type a keymap item reports as a keyboard key (Blender's own keymap editor takes them all)."""
    kc = bpy.context.window_manager.keyconfigs.new("issue386_probe")
    try:
        km = kc.keymaps.new("issue386", space_type='EMPTY', region_type='WINDOW')
        out = set()
        for it in bpy.types.Event.bl_rna.properties['type'].enum_items:
            kmi = km.keymap_items.new("wm.call_menu", it.identifier, 'PRESS')
            if kmi.map_type == 'KEYBOARD':
                out.add(it.identifier)
        return out - NOT_KEYS - MODIFIERS
    finally:
        bpy.context.window_manager.keyconfigs.remove(kc)


def test_every_blender_keyboard_key_can_be_captured():
    rows = m("keymap.hotkey_rows")
    keys = blender_keyboard_keys()
    assert "GRLESS" in keys and "A" in keys and "F24" in keys, sorted(keys)
    missing = sorted(keys - rows.KEYBOARD)
    assert not missing, f"keys the Hotkey Editor ignores: {missing}"


def test_modifier_keys_are_not_hotkeys():
    rows = m("keymap.hotkey_rows")
    assert not (MODIFIERS & rows.KEYBOARD), sorted(MODIFIERS & rows.KEYBOARD)


def test_special_keys_show_their_character():
    rows = m("keymap.hotkey_rows")
    assert rows.key_text("GRLESS") == "<", rows.key_text("GRLESS")
    assert rows.key_text("PLUS") == "+", rows.key_text("PLUS")
    assert rows.event_text({"type": "GRLESS", "shift": True}) == "Shift+<"
    # typing "<" in Search by Hotkey still finds Maya's "<" hotkey (Shift + comma on a US keyboard)
    assert rows.parse_hotkey("<") == {"type": "COMMA", "shift": True}, rows.parse_hotkey("<")


def test_a_held_less_key_is_known_to_the_os_check():
    """Hold keys end on the OS key state when a transform drag ate their release: "<" has its key code."""
    keystate = m("operators.keystate")
    assert keystate.vk_code("GRLESS") == 0xE2, keystate.vk_code("GRLESS")


def test_the_less_key_binds_a_kit_command():
    """The reporter's case: SnapToPointPress (Maya's v hold) on the "<" key."""
    from rt60_dump import populate
    populate()
    keymap = m("keymap")
    keymap.deactivate()
    keymap.activate()
    he = m("ui.hotkey_editor")
    row = next(r for r in he.rows() if r["command"] == "SnapToPointPress" and r["number"] == 1)
    ok, _taken = he.assign(bpy.context, row, {"type": "GRLESS", "ctrl": False, "alt": False, "shift": False,
                                              "oskey": False})
    assert ok
    text = he.kit_text(bpy.context, row)
    assert text == "< *", text
