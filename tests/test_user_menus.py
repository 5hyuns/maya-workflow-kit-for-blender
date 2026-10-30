"""the data behind the Marking Menu Editor (marking/user_menus.py), on the document alone.

Maya's Marking Menu Editor edits the factory marking menus (Restore Default puts one back) and makes new ones. A changed
kit menu keeps its untouched entries as references to the kit's entries, so kit fixes still reach them; the factory
objects (``menus.FACTORY``) are never changed, only ``menus.MENUS`` gets rebuilt copies."""

import json
import os
import tempfile
from importlib import import_module

import kit

um = import_module(kit.MODULE + ".marking.user_menus")
mm = import_module(kit.MODULE + ".marking.menus")


def _fresh():
    um._data.clear()
    um.apply()


def _snapshot(sub):
    """Comparable plain data of a factory Sub (labels, action reprs, options), depth first."""
    def act(a):
        return _snapshot(a) if isinstance(a, mm.Sub) else repr(a)
    return ({p: (l, act(a)) for p, (l, a) in sub.radial.items()},
            [e if e == mm.DIVIDER else (e[0], act(e[1])) for e in sub.items], sorted(sub.options))


def _same_menu(built, factory):
    """``built`` shows and runs what ``factory`` does (factory submenus are reused as they are)."""
    assert built.radial.keys() == factory.radial.keys(), (built.radial.keys(), factory.radial.keys())
    for pos, (label, action) in factory.radial.items():
        assert built.radial[pos][0] == label and built.radial[pos][1] == action, (pos, built.radial[pos], label)
    assert len(built.items) == len(factory.items)
    for b, f in zip(built.items, factory.items):
        assert b == f or (b[0] == f[0] and b[1] == f[1]), (b, f)
    assert built.options == factory.options


def test_factory_tree_rebuilds_every_kit_menu():
    _fresh()
    for name, menu in mm.FACTORY.items():
        built = um.build_menu(name, um.factory_tree(name), menu.label, menu.source)
        _same_menu(built, menu)


def test_override_applied_and_restored_factory_unchanged():
    _fresh()
    before = {n: _snapshot(m) for n, m in mm.FACTORY.items()}
    factory_face = mm.MENUS["SHIFT_FACE"]
    assert um.set_entry("SHIFT_FACE", "NE", {"label": "Bevel", "type": "op", "op": "mesh.bevel",
                                             "props": {"affect": 'EDGES'}})
    um.apply()
    menu = mm.MENUS["SHIFT_FACE"]
    assert menu is not factory_face and menu.name == "SHIFT_FACE" and menu.label == factory_face.label
    assert menu.radial["NE"] == ("Bevel", ("mesh.bevel", {"affect": 'EDGES'}))
    for pos in set(factory_face.radial) - {"NE"}:           # the other slots are still the kit's
        assert menu.radial[pos] == factory_face.radial[pos], pos
    assert mm.FACTORY["SHIFT_FACE"] is factory_face and mm.SHIFT_FACE is factory_face
    assert {n: _snapshot(m) for n, m in mm.FACTORY.items()} == before
    assert um.is_changed("SHIFT_FACE") and um.restore("SHIFT_FACE")
    um.apply()
    assert mm.MENUS["SHIFT_FACE"] is factory_face
    assert not um.restore("SHIFT_FACE")


def test_shared_factory_submenu_edit_stays_in_its_menu():
    """Maya's Symmetry submenu is one object in the Move / Rotate / Scale option menus: an edit in OPT_MOVE's copy
    never reaches the others (nor the factory object)."""
    _fresh()
    pos = next(p for p, (l, a) in mm.OPT_MOVE.radial.items() if l == "Symmetry")
    sym = mm.OPT_MOVE.radial[pos][1]
    assert um.set_entry("OPT_MOVE", f"{pos}/W", {"label": "Mine", "type": "item", "path": "Edit/Undo"})
    um.apply()
    assert mm.MENUS["OPT_MOVE"].radial[pos][1].radial["W"] == ("Mine", ("item", "Edit/Undo"))
    assert sym.radial["W"][0] == "World"
    rot_pos = next(p for p, (l, a) in mm.OPT_ROTATE.radial.items() if l == "Symmetry")
    assert mm.MENUS["OPT_ROTATE"].radial[rot_pos][1] is mm.OPT_ROTATE.radial[rot_pos][1]
    # the untouched entries of the edited submenu are still the kit's
    assert mm.MENUS["OPT_MOVE"].radial[pos][1].radial["E"] == sym.radial["E"]
    _fresh()


def test_list_rows_add_move_remove_and_dividers():
    _fresh()
    n = len(mm.RMB_EMPTY.items)
    path = um.add_item("RMB_EMPTY", "", {"label": "Hello", "type": "python", "code": "print('hi')"})
    assert path == f"#{n}"
    assert um.add_item("RMB_EMPTY", "", mm.DIVIDER, index=0) == "#0"
    assert um.move_item("RMB_EMPTY", f"#{n + 1}", -1) == f"#{n}"
    assert um.move_item("RMB_EMPTY", "#0", -1) is None            # already first
    assert um.move_item("RMB_EMPTY", "#-1", 1) is None            # never Python's negative index
    um.apply()
    items = mm.MENUS["RMB_EMPTY"].items
    assert items[0] == mm.DIVIDER
    assert items[n] == ("Hello", (um.PYTHON_OP, {"code": "print('hi')"}))
    assert um.set_entry("RMB_EMPTY", f"#{n}", None)
    assert not um.set_entry("RMB_EMPTY", "#99", None) and not um.set_entry("RMB_EMPTY", "#x", None)
    um.apply()
    assert len(mm.MENUS["RMB_EMPTY"].items) == n + 1
    _fresh()


def test_rename_keeps_option_box_and_kit_label_follows():
    _fresh()
    assert "Select Similar" in mm.RMB_MESH.options
    i = next(i for i, e in enumerate(mm.RMB_MESH.items) if e != mm.DIVIDER and e[0] == "Select Similar")
    assert um.has_option("RMB_MESH", f"#{i}")
    assert um.update_entry("RMB_MESH", f"#{i}", label="Similar")
    j = um.add_item("RMB_EMPTY", "", {"label": "Item", "type": "item", "path": "Edit/Undo"})
    assert um.update_entry("RMB_EMPTY", j, path="Edit/Redo")          # an item's own "path" field
    assert um.entry_at("RMB_EMPTY", j)["path"] == "Edit/Redo"
    um.apply()
    menu = mm.MENUS["RMB_MESH"]
    assert menu.items[i][0] == "Similar" and "Similar" in menu.options and "Select Similar" not in menu.options
    assert menu.items[i][1] == mm.RMB_MESH.items[i][1]                 # still the kit's command
    assert um.set_option("RMB_MESH", f"#{i}", False)
    um.apply()
    assert "Similar" not in mm.MENUS["RMB_MESH"].options
    # an untouched reference shows the kit's current label (a kit rename reaches it)
    e = um.ref("RMB_MESH", "N")
    e["factory_label"] = e["label"] = "Old Edge"
    assert um.entry_label(e) == "Edge"
    _fresh()


def test_reference_follows_a_moved_kit_entry_or_greys():
    _fresh()
    moved = {"label": "Face", "type": "factory", "menu": "RMB_MESH", "path": "NW", "factory_label": "Face"}
    assert um.entry_action(moved) == mm.RMB_MESH.radial["S"][1]        # found by label in the same submenu
    gone = {"label": "Gone", "type": "factory", "menu": "RMB_MESH", "path": "NW", "factory_label": "Gone"}
    assert um.entry_action(gone) is None
    assert um.describe(gone) == "Kit default (not found in this version)"
    assert um.entry_action({"type": "factory", "menu": "NOPE", "path": "N"}) is None


def test_custom_menu_new_copy_rename_delete():
    _fresh()
    name = um.new_custom("My Tools")
    assert name == "USER_MY_TOOLS" and um.is_custom(name)
    assert um.new_custom("My Tools") == "USER_MY_TOOLS_2" and um.delete_custom("USER_MY_TOOLS_2")
    um.set_entry(name, "N", {"label": "Cube", "type": "item", "path": "Create/Polygon Primitives/Cube"})
    um.add_item(name, "", {"label": "Sub", "type": "sub", "radial": {}, "items": [], "options": []})
    assert um.add_item(name, "#0", {"label": "Inner", "type": "op", "op": "mesh.select_all"}) == "#0/#0"
    copy = um.new_custom("Copy", from_menu="SHIFT_FACE")
    um.apply()
    menu = mm.MENUS[name]
    assert isinstance(menu, mm.MarkingMenu) and menu.label == "My Tools" and menu.source == "user"
    assert menu.radial["N"] == ("Cube", ("item", "Create/Polygon Primitives/Cube"))
    assert menu.items[0][1].items == [("Inner", "mesh.select_all")]
    _same_menu(mm.MENUS[copy], mm.SHIFT_FACE)
    assert um.menu_names()[:len(mm.FACTORY)] == list(mm.FACTORY)
    assert um.rename_custom(name, "Tools") and um.menu_label(name) == "Tools"
    assert not um.rename_custom(name, "  ")
    assert um.delete_custom(name) and um.delete_custom(copy)
    um.apply()
    assert name not in mm.MENUS and copy not in mm.MENUS
    assert list(mm.MENUS) == list(mm.FACTORY)


def test_editing_a_kit_submenu_makes_it_editable():
    _fresh()
    pos = next(p for p, (l, a) in mm.RMB_MESH.radial.items() if l == "UV")
    assert um.entry_at("RMB_MESH", f"{pos}/S")["type"] == "factory"
    assert um.tree_of("RMB_MESH") is None                       # reading never creates a change
    assert um.set_entry("RMB_MESH", f"{pos}/N", {"label": "New", "type": "op", "op": "uv.unwrap"})
    sub = um.tree_of("RMB_MESH")["radial"][pos]
    assert sub["type"] == "sub" and sub["radial"]["S"]["type"] == "factory"
    um.apply()
    built = mm.MENUS["RMB_MESH"].radial[pos][1]
    assert built.radial["N"] == ("New", "uv.unwrap") and built.radial["S"] == mm.RMB_MESH.radial[pos][1].radial["S"]
    # submenus filled when the menu opens can't be edited (Maya builds them from the object)
    i = next(i for i, e in enumerate(mm.RMB_MESH.items) if e != mm.DIVIDER and isinstance(e[1], mm.NodeList))
    assert not um.set_entry("RMB_MESH", f"#{i}/#0", {"label": "x", "type": "op", "op": "mesh.select_all"})
    assert um.add_item("RMB_MESH", f"#{i}", mm.DIVIDER) is None
    _fresh()


def test_swap_radial_and_empty_slot():
    _fresh()
    n, w = mm.RMB_MESH.radial["N"], mm.RMB_MESH.radial["W"]
    assert um.swap_radial("RMB_MESH", "N", "W")
    assert um.swap_radial("RMB_MESH", "NE", "NW")                # into an empty slot
    um.apply()
    menu = mm.MENUS["RMB_MESH"]
    assert menu.radial["N"] == w and menu.radial["W"] == n
    assert "NE" not in menu.radial and menu.radial["NW"] == mm.RMB_MESH.radial["NE"]
    assert not um.swap_radial("RMB_MESH", "N", "XX")
    _fresh()


def test_hotkeys_one_menu_per_key():
    _fresh()
    a, b = um.new_custom("A"), um.new_custom("B")
    assert um.set_hotkey(a, {"key": "Y", "shift": True})
    assert um.hotkeys() == [(a, {"key": "Y", "ctrl": False, "alt": False, "shift": True, "oskey": False})]
    assert um.set_hotkey(b, {"key": "Y", "shift": True})          # Maya: the key moves to the new command
    assert [n for n, _h in um.hotkeys()] == [b]
    assert um.set_hotkey(b, None) and um.hotkeys() == []
    assert not um.set_hotkey("RMB_MESH", {"key": "Y"})            # kit menus open from the kit's own triggers
    _fresh()


def test_file_round_trip_and_bad_files():
    _fresh()
    um.set_entry("SHIFT_FACE", "NE", {"label": "Bevel", "type": "op", "op": "mesh.bevel"})
    name = um.new_custom("Round Trip")
    um.set_hotkey(name, {"key": "F7", "ctrl": True})
    um.set_entry(name, "S", {"label": "Py", "type": "python", "code": "import maya.cmds as cmds\ncmds.ls()"})
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sub", um.FILE_NAME)
        um.save(path)
        saved = json.loads(open(path, encoding="utf-8").read())
        assert saved["version"] == um.VERSION and set(saved) == {"version", "menus", "custom"}
        doc = json.loads(json.dumps(um.document()))
        um._data.clear()
        assert um.load(path) == doc
        um.apply()
        assert mm.MENUS["SHIFT_FACE"].radial["NE"] == ("Bevel", "mesh.bevel")
        assert mm.MENUS[name].radial["S"][1] == (um.PYTHON_OP, {"code": "import maya.cmds as cmds\ncmds.ls()"})
        # broken / foreign files: nothing edited, never an exception
        for text in ("{not json", "[]", json.dumps({"menus": {"NOPE": {}, "RMB_MESH": "x"},
                                                    "custom": {"bad name!": {}, "RMB_MESH": {}, "OK": 3}})):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            assert um.load(path) == um.empty(), text
        assert um.load(os.path.join(tmp, "missing.json")) == um.empty()
    # bad entries are skipped, the rest kept
    doc = um.normalized({"menus": {"RMB_EMPTY": {"radial": {"N": {"type": "op", "op": "a.b"}, "Q": {"type": "op"},
                                                            "S": {"type": "nope"}},
                                                 "items": ["-", 3, {"type": "item", "path": "Edit/Undo"}]}}})
    tree = doc["menus"]["RMB_EMPTY"]
    assert list(tree["radial"]) == ["N"] and len(tree["items"]) == 2
    _fresh()


def test_entry_actions_are_validated():
    assert um.entry_action({"type": "op", "op": "mesh.bevel", "props": {"offset": 0.1}}) == ("mesh.bevel",
                                                                                            {"offset": 0.1})
    assert um.entry_action({"type": "op", "op": "not an op"}) is None
    assert um.entry_action({"type": "op", "op": "mesh.bevel", "props": "x"}) == "mesh.bevel"
    assert um.entry_action({"type": "python", "code": "  "}) is None
    assert um.entry_action({"type": "item", "path": ""}) is None
    assert um.entry_action({"type": "shelf", "shelf": "Polygons", "button": "Delete By Type: History"}) == (
        um.SHELF_OP, {"shelf": "Polygons", "button": "Delete By Type: History"})
    assert um.entry_action({"type": "shelf", "shelf": "Polygons", "button": ""}) is None
    assert um.describe({"type": "shelf", "shelf": "USER:Custom", "button": "Mine"}) == "Shelf button: Custom / Mine"
    assert um.entry_action({"type": "kit", "action": ["tool", "builtin.move", True]}) == ("tool", "builtin.move", True)
    assert um.entry_action({"type": "kit", "action": ["mesh.bevel", {"offset_type": 'OFFSET'}]}) == (
        "mesh.bevel", {"offset_type": 'OFFSET'})
    assert um.entry_action({"type": "kit", "action": ["rm -rf", {}]}) is None
    assert um.entry_action({"type": "kit", "action": 3}) is None
    for action in (mm.MULTI_CUT, mm.MERGE_CENTER, mm.PRESERVE_UVS, ("item", "Edit Mesh/Bevel"), "mesh.bevel"):
        assert um.action_from_json(json.loads(json.dumps(um.action_to_json(action)))) == action, action
