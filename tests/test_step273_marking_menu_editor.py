"""Step 273: Maya's Marking Menu Editor in the kit (marking/menu_editor.py, marking/user_menus.py).

Windows > Settings/Preferences > Marking Menu Editor opens the kit window (it was a notice); the user's file is put
into the marking menus at register and taken out at unregister; a custom menu's hotkey is Maya's "hold the key + LMB"
(``allset.tap_hold``) and comes in front of the Maya key of the same event; the Blender Pies style draws the edited
menus; a Python item runs like a shelf button; the editor's operators edit, save and apply at once."""

import json
import os
import types
from importlib import import_module

import bpy

import kit


def m(name):
    return import_module(f"{kit.MODULE}.{name}")


def _mods():
    return (m("marking"), m("marking.menus"), m("marking.user_menus"), m("marking.menu_editor"))


def _reset():
    marking, _mm, um, _me = _mods()
    um._data.clear()
    marking.apply_user_menus()
    path = um.store_path()
    if os.path.isfile(path):
        os.remove(path)


class _Rec:
    """A layout that records what a draw() puts in it."""

    def __init__(self):
        self.log = []

    def operator(self, idname, text="", **kw):
        props = types.SimpleNamespace()
        self.log.append(("op", idname, text, props))
        return props

    def label(self, text="", **kw):
        self.log.append(("label", text))

    def prop(self, data, name, text="", **kw):
        self.log.append(("prop", name))

    def menu(self, idname, text="", **kw):
        self.log.append(("menu", idname, text))

    def __getattr__(self, name):        # row / column / box / split / menu_pie / separator ...: the same recorder
        return lambda *a, **k: self

    def texts(self):
        return [e[2] if e[0] in ("op", "menu") else e[1] for e in self.log if e[0] in ("op", "menu", "label")]


def _draw(cls):
    rec = _Rec()
    cls.draw(types.SimpleNamespace(layout=rec), bpy.context)
    return rec


def test_menu_item_opens_the_editor():
    menu_map, notices, marked_window = m("ui.menu_map"), m("ui.notices"), m("ui.marked_window")
    path = "Windows/Settings/Preferences/Marking Menu Editor"
    assert menu_map.MAP[path] == "allset.marking_menu_editor"
    assert path not in notices.NOTICES
    assert hasattr(bpy.types, "ALLSET_OT_marking_menu_editor") and hasattr(bpy.types, "ALLSET_PT_marking_menu_editor")
    kinds = marked_window.KINDS
    assert kinds["MARKING_MENU_EDITOR"] and len(set(kinds.values())) == len(kinds)    # its own flag pair


def test_python_item_runs_like_a_shelf_button():
    _marking, _mm, um, _me = _mods()
    scene = bpy.context.scene
    assert um.PYTHON_OP == "allset.mm_python"
    r = bpy.ops.allset.mm_python(code="import bpy\nbpy.context.scene['mm273'] = 7")
    assert r == {'FINISHED'} and scene["mm273"] == 7
    try:
        bpy.ops.allset.mm_python(code="raise ValueError('nope')")
    except RuntimeError as ex:          # the ERROR report of a script error
        assert "nope" in str(ex), ex
    else:
        raise AssertionError("a failing script must report an error")
    del scene["mm273"]


def test_custom_hotkey_is_hold_key_plus_lmb_and_wins():
    marking, mm, um, _me = _mods()
    keymap, taphold, modal = m("keymap"), m("operators.taphold"), m("marking.modal")
    _reset()
    name = um.new_custom("Hold W")
    um.set_entry(name, "N", {"label": "Cube", "type": "item", "path": "Create/Polygon Primitives/Cube"})
    um.set_hotkey(name, {"key": "W"})
    marking.apply_user_menus()
    try:
        assert name in mm.MENUS
        items = keymap.overlay_items(marking.HOTKEY_OWNER)
        assert sorted(k.idname for k in items) == ["allset.tap_hold"] * len(marking.HOTKEY_KEYMAPS)
        assert {k.properties.binding for k in items} == {marking.binding_name(name)}
        assert all(k.type == 'W' and k.value == 'PRESS' and not k.ctrl and not k.shift for k in items)
        # Maya: the new assignment replaces the old one -> first in Object Mode, before the Move tool's W
        km = kit.maya_kc().keymaps["Object Mode"]
        first = next(k for k in km.keymap_items if k.type == 'W' and not (k.ctrl or k.alt or k.shift))
        assert first.idname == "allset.tap_hold" and first.properties.binding == marking.binding_name(name)
        # hold W + LMB opens the custom menu (engine or pie per the style), a tap does nothing
        binding = taphold.get_binding(marking.binding_name(name))
        calls = []
        real = modal.open_menu
        modal.open_menu = lambda *a: calls.append(a)
        try:
            binding.click(bpy.context, types.SimpleNamespace(mouse_region_x=10, mouse_region_y=20))
            binding.tap(bpy.context)
        finally:
            modal.open_menu = real
        assert calls == [(name, 'LEFTMOUSE', (10, 20))], calls
        # the editor names what the key takes over (the merged user keymap; background Blender fills it first)
        from rt60_dump import populate
        populate()
        bpy.context.window_manager.keyconfigs.update()
        clash = m("marking.menu_editor").conflicts(bpy.context, name, um.document()["custom"][name]["hotkey"])
        assert ("Object Mode", "Move Tool / Options") in clash, clash
        # no hotkey -> the Maya W again, the binding gone
        um.set_hotkey(name, None)
        marking.apply_user_menus()
        assert keymap.overlay_items(marking.HOTKEY_OWNER) == []
        assert marking.binding_name(name) not in taphold.binding_names()
        km = kit.maya_kc().keymaps["Object Mode"]
        first = next(k for k in km.keymap_items if k.type == 'W' and not (k.ctrl or k.alt or k.shift))
        assert first.properties.binding == "tool_move"
    finally:
        _reset()
    assert name not in mm.MENUS


def test_pie_style_draws_the_edited_menu():
    marking, mm, um, _me = _mods()
    _reset()
    try:
        um.update_entry("SHIFT_FACE", "N", label="Mine!")
        name = um.new_custom("Pies")
        um.set_entry(name, "E", {"label": "More", "type": "sub", "radial": {"N": {"label": "Inner", "type": "op",
                                                                                  "op": "mesh.select_all"}},
                                 "items": [], "options": []})
        marking.apply_user_menus()
        pid = marking.pie_idname("SHIFT_FACE")
        assert pid != marking.idname("SHIFT_FACE") and hasattr(bpy.types, pid)
        assert "Mine!" in _draw(getattr(bpy.types, pid)).texts()
        assert "Mine!" not in _draw(getattr(bpy.types, marking.idname("SHIFT_FACE"))).texts()   # the factory class
        sub = mm.MENUS[name].radial["E"][1]
        sub_id, is_pie = marking._sub_ids[id(sub)]
        assert is_pie and hasattr(bpy.types, sub_id) and "Inner" in _draw(getattr(bpy.types, sub_id)).texts()
        rec = _draw(getattr(bpy.types, marking.pie_idname(name)))
        assert ("op", "wm.call_menu_pie") in [(e[0], e[1]) for e in rec.log] and "More ▸" in rec.texts()
        um.restore("SHIFT_FACE")
        um.delete_custom(name)
        marking.apply_user_menus()
        assert marking.pie_idname("SHIFT_FACE") == marking.idname("SHIFT_FACE") and not hasattr(bpy.types, pid)
        assert not hasattr(bpy.types, sub_id)
    finally:
        _reset()


def test_editor_edits_save_and_apply():
    marking, mm, um, me = _mods()
    wm = bpy.context.window_manager
    _reset()
    try:
        me.refresh(bpy.context)
        wm.allset_mme_menu = "RMB_MESH"
        assert bpy.ops.allset.mme_select(slot="N") == {'FINISHED'}
        assert wm.allset_mme_label == "Edge" and wm.allset_mme_type == "factory"
        assert not um.is_changed("RMB_MESH")              # selecting never changes anything
        wm.allset_mme_label = "Edges!"
        assert um.is_changed("RMB_MESH") and os.path.isfile(um.store_path())
        assert mm.MENUS["RMB_MESH"].radial["N"] == ("Edges!", mm.RMB_MESH.radial["N"][1])
        saved = json.loads(open(um.store_path(), encoding="utf-8").read())
        assert saved["menus"]["RMB_MESH"]["radial"]["N"]["label"] == "Edges!"
        wm.allset_mme_type = "op"
        wm.allset_mme_op = "mesh.select_all"
        wm.allset_mme_props = '{"action": "SELECT"}'
        assert mm.MENUS["RMB_MESH"].radial["N"] == ("Edges!", ("mesh.select_all", {"action": "SELECT"}))
        wm.allset_mme_props = "{nope"
        assert "JSON" in wm.allset_mme_message
        assert mm.MENUS["RMB_MESH"].radial["N"][1] == ("mesh.select_all", {"action": "SELECT"})
        assert wm.allset_mme_props == '{"action": "SELECT"}'          # the field shows what is stored
        assert any("N: Edges!" in t for t in _draw(me.ALLSET_PT_marking_menu_editor).texts())
        wm.allset_mme_type = "factory"                                 # Kit Default again
        assert mm.MENUS["RMB_MESH"].radial["N"] == mm.RMB_MESH.radial["N"]
        assert bpy.ops.allset.mme_menu(action="RESTORE") == {'FINISHED'} and not um.is_changed("RMB_MESH")
        assert mm.MENUS["RMB_MESH"] is mm.RMB_MESH

        # a custom menu made in the editor
        assert bpy.ops.allset.mme_menu(action="NEW", label="Mine") == {'FINISHED'}
        name = wm.allset_mme_menu
        assert um.is_custom(name) and um.menu_label(name) == "Mine" and name in mm.MENUS
        bpy.ops.allset.mme_select(slot="N")
        assert bpy.ops.allset.mme_slot(action="SET") == {'FINISHED'}
        wm.allset_mme_type = "item"
        wm.allset_mme_item = "Create/Polygon Primitives/Cube"
        wm.allset_mme_label = "Cube"
        assert mm.MENUS[name].radial["N"] == ("Cube", ("item", "Create/Polygon Primitives/Cube"))
        assert bpy.ops.allset.mme_slot(action="SWAP", pos="S") == {'FINISHED'} and wm.allset_mme_slot == "S"
        assert "N" not in mm.MENUS[name].radial and mm.MENUS[name].radial["S"][0] == "Cube"
        assert bpy.ops.allset.mme_slot(action="OPTION") == {'FINISHED'} and "Cube" in mm.MENUS[name].options
        for _ in range(2):
            bpy.ops.allset.mme_slot(action="ADD_ITEM")
        assert wm.allset_mme_slot == "#1" and len(mm.MENUS[name].items) == 2
        wm.allset_mme_type = "python"
        wm.allset_mme_code = "print(1)"
        assert bpy.ops.allset.mme_slot(action="UP") == {'FINISHED'} and wm.allset_mme_slot == "#0"
        assert mm.MENUS[name].items[0][1] == (um.PYTHON_OP, {"code": "print(1)"})
        bpy.ops.allset.mme_slot(action="ADD_DIVIDER")
        assert mm.MENUS[name].items[1] == mm.DIVIDER
        bpy.ops.allset.mme_select(slot="#2")
        wm.allset_mme_type = "sub"
        assert bpy.ops.allset.mme_open(path="#2") == {'FINISHED'} and wm.allset_mme_path == "#2"
        bpy.ops.allset.mme_select(slot="NE")
        bpy.ops.allset.mme_slot(action="SET")
        assert isinstance(mm.MENUS[name].items[2][1], mm.Sub) and "NE" in mm.MENUS[name].items[2][1].radial
        bpy.ops.allset.mme_open(path="")
        # every kind of slot draws (the window's panel, with each selection)
        for slot in ("", "N", "S", "#0", "#1", "#2"):
            bpy.ops.allset.mme_select(slot=slot)
            texts = _draw(me.ALLSET_PT_marking_menu_editor).texts()
            assert any("S: Cube" in t for t in texts), texts
        # hotkey: assigned, then cleared
        assert bpy.ops.allset.mme_hotkey(key="F8", shift=True) == {'FINISHED'}
        assert um.hotkeys() == [(name, {"key": "F8", "ctrl": False, "alt": False, "shift": True, "oskey": False})]
        assert len(m("keymap").overlay_items(marking.HOTKEY_OWNER)) == len(marking.HOTKEY_KEYMAPS)
        assert any("Shift+F8" in t for t in _draw(me.ALLSET_PT_marking_menu_editor).texts())
        assert bpy.ops.allset.mme_hotkey(clear=True) == {'FINISHED'} and um.hotkeys() == []
        assert bpy.ops.allset.mme_menu(action="DELETE") == {'FINISHED'}
        assert name not in mm.MENUS and wm.allset_mme_menu in mm.FACTORY
        # a kit submenu opens in place; one filled when the menu opens can't
        wm.allset_mme_menu = "RMB_MESH"
        pos = next(p for p, (l, a) in mm.RMB_MESH.radial.items() if l == "UV")
        assert bpy.ops.allset.mme_open(path=pos) == {'FINISHED'}
        i = next(i for i, e in enumerate(mm.RMB_MESH.items) if e != mm.DIVIDER and isinstance(e[1], mm.NodeList))
        bpy.ops.allset.mme_open(path="")
        try:
            bpy.ops.allset.mme_open(path=f"#{i}")
        except RuntimeError:
            pass
        assert wm.allset_mme_path == ""
        for slot in ("", "N", "E", "NW", "#0", f"#{i}"):
            bpy.ops.allset.mme_select(slot=slot)
            _draw(me.ALLSET_PT_marking_menu_editor)
    finally:
        _reset()


def test_file_applied_at_register_and_taken_back_at_unregister():
    """The file is read when the kit registers (it outlives kit updates in the extension's user folder); disabling
    leaves Blender as it was, the factory menus included."""
    _marking, _mm, um, _me = _mods()
    _reset()
    path = um.store_path()
    doc = um.empty()
    doc["menus"]["SHIFT_FACE"] = um.factory_tree("SHIFT_FACE")
    doc["menus"]["SHIFT_FACE"]["radial"]["NE"] = {"label": "Bevel", "type": "op", "op": "mesh.bevel"}
    doc["custom"]["USER_KEYS"] = {"label": "Keys", "hotkey": {"key": "F7", "ctrl": True},
                                  "radial": {"N": {"label": "Undo", "type": "item", "path": "Edit/Undo"}},
                                  "items": [], "options": []}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    try:
        kit.disable()
        before = kit.snapshot()
        kit.enable()
        marking, mm, um, _me = _mods()
        assert mm.MENUS["SHIFT_FACE"].radial["NE"] == ("Bevel", "mesh.bevel")
        assert mm.MENUS["USER_KEYS"].radial["N"] == ("Undo", ("item", "Edit/Undo"))
        items = m("keymap").overlay_items(marking.HOTKEY_OWNER)
        assert len(items) == len(marking.HOTKEY_KEYMAPS) and all(k.type == 'F7' and k.ctrl for k in items)
        kit.disable()
        assert not [k for km in bpy.context.window_manager.keyconfigs.addon.keymaps for k in km.keymap_items
                    if k.idname == "allset.tap_hold" and k.properties.binding.startswith("user_mm_")]
        assert list(mm.MENUS) == list(mm.FACTORY) and all(mm.MENUS[n] is mm.FACTORY[n] for n in mm.FACTORY)
        d = kit.diff(before, kit.snapshot())
        assert not d, "state leaked after disable:\n" + "\n".join(d)
    finally:
        if not kit.is_enabled():
            kit.enable()
        _reset()
