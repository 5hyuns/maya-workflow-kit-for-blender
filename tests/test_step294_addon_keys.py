"""Maya keys win over other add-ons' keys that one press could also run (#218), and switching while
playback runs stops playback first. A Maya switch request while Maya mode is already on keeps the mode and
puts the Maya keys back."""

from importlib import import_module

import bpy

import kit

keymap = import_module(kit.MODULE + ".keymap")
switch = import_module(kit.MODULE + ".switch")


def _sig(type_='W', value='PRESS', any_=False, shift=0, ctrl=0, alt=0, oskey=0, keymod='NONE'):
    return (type_, value, any_, shift, ctrl, alt, oskey, keymod)


def test_same_press_rules():
    assert keymap.same_press(_sig(), _sig())
    assert keymap.same_press(_sig(value='ANY'), _sig())
    assert keymap.same_press(_sig(value='CLICK'), _sig())                 # the press item runs first
    assert keymap.same_press(_sig(value='PRESS'), _sig(value='CLICK_DRAG'))
    assert keymap.same_press(_sig(any_=True), _sig(shift=1))
    assert keymap.same_press(_sig(shift=-1), _sig(shift=1))
    assert not keymap.same_press(_sig(shift=1), _sig())                   # Shift+W is another press
    assert not keymap.same_press(_sig(type_='E'), _sig())
    assert not keymap.same_press(_sig(value='RELEASE'), _sig(value='CLICK'))
    assert not keymap.same_press(_sig(keymod='A'), _sig())


def _foreign(value, any_=False):
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new("Object Mode", space_type='EMPTY', region_type='WINDOW')
    item = km.keymap_items.new("wm.context_toggle", 'W', value, any=any_)
    return km, item


def _kit_w(k):
    return k.idname == "wm.tool_set_by_id" and k.type == 'W' and not (k.shift or k.ctrl or k.alt)


def test_a_later_addon_any_or_click_item_does_not_win():
    for value, any_ in (('ANY', False), ('CLICK', False), ('PRESS', True)):
        km, other = _foreign(value, any_)
        try:
            kit_items = [i for i, k in enumerate(km.keymap_items) if keymap._state["addon_items"].__contains__(k.as_pointer())
                         and k.type == 'W']
            assert kit_items, "the kit's Object Mode W"
            keymap._state["addon_count"] = -1
            assert keymap._keep_first() >= 1, (value, any_)
            pos_other = [i for i, k in enumerate(km.keymap_items) if k.idname == "wm.context_toggle"][0]
            pos_kit = [i for i, k in enumerate(km.keymap_items)
                       if k.as_pointer() in keymap._state["addon_items"] and k.type == 'W'][0]
            assert pos_kit > pos_other, (value, any_, pos_kit, pos_other)   # later in the list = runs first
        finally:
            for k in [k for k in km.keymap_items if k.idname == "wm.context_toggle"]:
                km.keymap_items.remove(k)


def test_activate_runs_keep_first():
    km, other = _foreign('ANY')
    try:
        keymap.deactivate()
        keymap.activate()
        pos_other = [i for i, k in enumerate(km.keymap_items) if k.idname == "wm.context_toggle"][0]
        pos_kit = [i for i, k in enumerate(km.keymap_items)
                   if k.as_pointer() in keymap._state["addon_items"] and k.type == 'W']
        assert pos_kit and min(pos_kit) > pos_other
    finally:
        for k in [k for k in km.keymap_items if k.idname == "wm.context_toggle"]:
            km.keymap_items.remove(k)


def test_maya_request_while_on_puts_the_keys_back():
    assert switch.is_on()
    keymap.deactivate()
    assert not keymap.is_applied()
    assert switch.set_mode(True, layout=False) is False      # already on: no switch ...
    assert switch.is_on() and keymap.is_applied()            # ... but the Maya keys are back


def test_stop_playback_is_safe_headless():
    assert switch.stop_playback() == 0
