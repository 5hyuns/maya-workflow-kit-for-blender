"""#530: the kit Hotkey Editor lists Maya's menu item commands, not only the commands with a standard hotkey (Edit
Mesh > Merge to Center, Merge, Merge (Option), Collapse, Mesh > Combine, Mesh Tools > Target Weld ...), like Maya's
Hotkey Editor, and a key given to one of them runs the menu item. The key is a keymap item the kit adds to the user
keyconfig (Blender's Preferences > Keymap "Add New" does the same); Restore takes it away, Maya mode off / on keeps it,
the kit writes no file."""

import os
from importlib import import_module

import bmesh
import bpy

import kit
from rt60_dump import populate


def m(name):
    return import_module(f"{kit.MODULE}.{name}")


def _he():
    return m("ui.hotkey_editor")


def _cmd(command):
    return next(r for r in _he().rows() if r["command"] == command)


def _setup():
    populate()
    keymap = m("keymap")
    keymap.deactivate()
    keymap.activate()
    bpy.context.window_manager.keyconfigs.update()


def _window_items(idname="allset.menu_item"):
    km = bpy.context.window_manager.keyconfigs.user.keymaps["Window"]
    return [k for k in km.keymap_items if k.idname == idname and k.is_user_defined]


def _config_files():
    cfg = bpy.utils.user_resource('CONFIG')
    return sorted(os.listdir(cfg)) if os.path.isdir(cfg) else []


def test_merge_family_is_listed_and_found():
    hr = m("keymap.hotkey_rows")
    rows = _he().rows()
    by = {r["command"]: r for r in rows}
    for command, label, category in (
            ("MergeToCenter", "Merge to Center", "Menu items > Modeling > Edit Mesh"),
            ("PolyMerge", "Merge", "Menu items > Modeling > Edit Mesh"),
            ("PolyMergeOptions", "Merge (Option)", "Menu items > Modeling > Edit Mesh"),
            ("PolygonCollapse", "Collapse", "Menu items > Modeling > Edit Mesh"),
            ("CombinePolygons", "Combine", "Menu items > Modeling > Mesh"),
            ("MergeVertexTool", "Target Weld", "Menu items > Modeling > Mesh Tools")):
        r = by.get(command)
        assert r is not None, command
        assert (r["label"], r["category"]) == (label, category), r
        assert r["editable"] and r["status"] == "KIT" and r["maya_key"] == "" and r["event"] is None, r
    found = lambda text: {r["command"] for r in hr.search(rows, text)}     # noqa: E731
    assert {"PolyMerge", "PolyMergeOptions", "MergeToCenter"} <= found("merge"), found("merge")
    assert "MergeToCenter" in found("merge to center")
    assert "MergeVertexTool" in found("weld")          # Target Weld
    assert "CombinePolygons" in found("combine")
    assert "PolygonCollapse" in found("collapse")
    edit_mesh = {r["command"] for r in hr.search(rows, category="Menu items > Modeling > Edit Mesh")}
    assert {"PolyMerge", "MergeToCenter", "PolygonCollapse"} <= edit_mesh, edit_mesh
    f8 = hr.search(rows, "F8", by="HOTKEY")
    assert f8 and not [r for r in f8 if r.get("path")], "a row without a Maya key never matches the Maya key"


def test_every_kit_menu_command_can_be_bound():
    """The same cause for every menu: each main-menu item the kit runs is listed and bindable (its option box too),
    a command with a standard hotkey keeps its hotkey row only, and commands are listed once."""
    he = _he()
    rows = he.rows()
    menu_map, menu_tree = m("ui.menu_map"), m("ui.menu_tree")
    data = m("keymap.hotkey_data")
    commands = [r for r in rows if r.get("path")]
    names = [r["command"] for r in rows if r["context"] == "global" and r["command"]]
    hotkey_commands = {r["command"] for r in rows if not r.get("path")}
    assert len(commands) > 1000, len(commands)
    assert len([r for r in commands if r["editable"]]) > 700
    assert not [n for n in names if names.count(n) > 1 and n not in hotkey_commands]
    listed = {r["command"] for r in commands}
    missing = []
    for command, _label, _cat, path, option in data.COMMANDS:
        if command in hotkey_commands:
            continue
        runs = path in menu_map.MAP and (not option or path in menu_tree.OPTION_BOXES)
        if command not in listed or (runs and not next(r for r in commands if r["command"] == command)["editable"]):
            missing.append((command, path))
    assert not missing, missing[:20]
    for r in commands:
        if r["editable"]:
            km, idname, props = r["check"]
            assert km == "Window" and idname in ("allset.menu_item", "allset.menu_option_box"), r
            assert props["item"] in menu_map.MAP, r


def test_assign_runs_the_menu_item_and_restore_removes_it():
    _setup()
    he = _he()
    ctx = bpy.context
    files = _config_files()
    row = _cmd("MergeToCenter")
    assert he.kit_text(ctx, row) == "—"
    assert not _window_items()
    r = bpy.ops.allset.hotkey_assign(row=row["index"], key="M", ctrl=True, alt=True)
    assert r == {'FINISHED'}, r
    items = _window_items()
    assert len(items) == 1, items
    kmi = items[0]
    assert (kmi.type, kmi.ctrl, kmi.alt, kmi.shift) == ('M', True, True, False)
    assert kmi.properties.item == "Edit Mesh/Merge to Center" and kmi.properties.hotkey
    assert he.kit_text(ctx, row) == "Ctrl+Alt+M *", he.kit_text(ctx, row)
    assert row in he.changed_rows(ctx)
    hr = m("keymap.hotkey_rows")
    assert row in hr.search(he.rows(), "ctrl+alt+m", "HOTKEY", live={row["index"]: he.live_events(ctx, row)})
    # a second key replaces the first (one key per command row)
    he.assign(ctx, row, {"type": "M", "ctrl": True, "alt": True, "shift": True})
    assert [(k.type, k.shift) for k in _window_items()] == [('M', True)]
    # the bound item runs the menu item: two vertices merge at their centre
    me = bpy.data.meshes.new("i530")
    bm = bmesh.new()
    a, b = bm.verts.new((0.0, 0.0, 0.0)), bm.verts.new((2.0, 0.0, 0.0))
    bm.verts.new((0.0, 2.0, 0.0))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("i530", me)
    ctx.scene.collection.objects.link(ob)
    ctx.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me)
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        v.select_set(v.index in (0, 1))
    bm.select_flush_mode()
    bmesh.update_edit_mesh(me)
    kmi = _window_items()[0]
    bpy.ops.allset.menu_item(item=kmi.properties.item, hotkey=kmi.properties.hotkey)
    bpy.ops.object.mode_set(mode='OBJECT')
    xs = sorted(round(v.co.x, 4) for v in me.vertices)
    assert len(me.vertices) == 2 and 1.0 in xs, [tuple(v.co) for v in me.vertices]
    # Maya mode off / on keeps the key (keymap/user_keys)
    keymap = m("keymap")
    keymap.deactivate()
    assert not _window_items(), "the kit keys go out with the Maya keys"
    keymap.activate()
    bpy.context.window_manager.keyconfigs.update()
    assert he.kit_text(ctx, row) == "Ctrl+Alt+Shift+M *", he.kit_text(ctx, row)
    # the option box row gets its own item
    box = _cmd("PolyMergeOptions")
    ok, _taken = he.assign(ctx, box, {"type": "F6", "ctrl": True, "alt": True, "shift": True})
    assert ok and [k.properties.item for k in _window_items("allset.menu_option_box")] == ["Edit Mesh/Merge"]
    # Restore = Maya's: no hotkey
    assert bpy.ops.allset.hotkey_restore(row=row["index"]) == {'FINISHED'}
    assert he.kit_text(ctx, row) == "—" and not _window_items()
    assert he.restore_all(ctx) >= 1
    assert not _window_items("allset.menu_option_box") and not he.changed_rows(ctx)
    assert _config_files() == files, (files, _config_files())


def test_keys_move_between_commands_and_maya_keys():
    """Maya: a key belongs to one command; giving it to another takes it away (a menu command's key, a Maya key)."""
    _setup()
    he = _he()
    ctx = bpy.context
    merge = _cmd("MergeToCenter")
    collapse = _cmd("PolygonCollapse")
    he.assign(ctx, merge, {"type": "F6", "ctrl": True, "alt": True})
    assert he.conflicts(ctx, collapse, {"type": "F6", "ctrl": True, "alt": True}) == [("Window", "Merge to Center")]
    ok, taken = he.assign(ctx, collapse, {"type": "F6", "ctrl": True, "alt": True})
    assert ok and taken == [("Window", "Merge to Center")], taken
    assert he.kit_text(ctx, merge) == "—" and he.kit_text(ctx, collapse) == "Ctrl+Alt+F6 *"
    # a Maya hotkey row takes it back from the menu command
    sel = next(r for r in he.rows() if r["command"] == "SelectToggleMode" and r["context"] == "global")
    ok, taken = he.assign(ctx, sel, {"type": "F6", "ctrl": True, "alt": True})
    assert ok and ("Window", "Collapse") in taken, taken
    assert he.kit_text(ctx, collapse) == "—"
    # a menu command takes a Maya key (F8 = SelectToggleMode's own)
    he.restore(ctx, sel)
    ok, taken = he.assign(ctx, merge, {"type": "F8"})
    assert ok and any(label.startswith("SelectToggleMode") for _km, label in taken), taken
    assert he.kit_text(ctx, sel) == "— *", he.kit_text(ctx, sel)
    he.restore_all(ctx)
    assert he.kit_text(ctx, sel) == "F8" and he.kit_text(ctx, merge) == "—"
    assert not any(km.is_user_modified for km in bpy.context.window_manager.keyconfigs.user.keymaps)


def test_commands_need_the_maya_keys_and_unrun_commands_stay_greyed():
    _setup()
    he = _he()
    ctx = bpy.context
    no = next(r for r in he.rows() if r.get("path") and not r["editable"])
    assert he.assign(ctx, no, {"type": "F6"}) == (False, [])
    assert bpy.ops.allset.hotkey_assign(row=no["index"], key="F6") == {'CANCELLED'}
    keymap = m("keymap")
    keymap.deactivate()
    try:
        assert he.assign(ctx, _cmd("MergeToCenter"), {"type": "F6"}) == (False, [])
        assert not _window_items()
    finally:
        keymap.activate()


def test_import_and_settings_round_trip():
    """A Maya hotkey set (.mhk) binding a menu command gives it the key; the kit's settings export carries it."""
    _setup()
    he = _he()
    ctx = bpy.context
    text = ('nameCommand -annotation "Merge to Center" -sourceType "mel" -command ("MergeToCenter") '
            'MergeToCenterNameCommand;\n'
            'hotkey -keyShortcut "m" -ctl -alt -name ("MergeToCenterNameCommand");\n')
    done, skipped = he.import_hotkeys(ctx, text)
    assert done == 1 and not skipped, (done, skipped)
    row = _cmd("MergeToCenter")
    assert he.kit_text(ctx, row) == "Ctrl+Alt+M *"
    sio = m("settings_io")
    items = sio.export_hotkeys(ctx)
    assert any(i["command"] == "MergeToCenter" and i["key"]["type"] == "M" for i in items), items
    he.restore_all(ctx)
    assert he.kit_text(ctx, row) == "—"
    done, skipped = sio.import_hotkeys(ctx, items)
    assert done == 1, (done, skipped)
    assert he.kit_text(ctx, row) == "Ctrl+Alt+M *"
    he.restore_all(ctx)
