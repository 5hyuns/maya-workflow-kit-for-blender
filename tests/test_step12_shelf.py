"""Maya shelf (factory shelves as Blender buttons, user Python shelves, strip area).

"""

import json
import os
import types
from importlib import import_module

import bpy

import kit

shelf = import_module(kit.MODULE + ".ui.shelf")
shelf_data = import_module(kit.MODULE + ".ui.shelf_data")
shelf_map = import_module(kit.MODULE + ".ui.shelf_map")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
runner = import_module(kit.MODULE + ".command_line.runner")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANDBOX = os.path.join(ROOT, "tmp")


class FakeLayout:
    def __init__(self, log=None):
        self.log = [] if log is None else log

    def _sub(self, *_a, **_k):
        return FakeLayout(self.log)

    row = column = box = _sub

    def operator(self, idname, text=None, icon='NONE', **kw):
        props = types.SimpleNamespace()
        self.log.append(("op", idname, text, icon, props))
        return props

    def menu(self, idname, text=None, **kw):
        self.log.append(("menu", idname, text))

    def separator(self, *a, **kw):
        pass

    def label(self, *a, **kw):
        pass

    def prop(self, *a, **kw):
        pass


def _fresh():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def _icons():
    return set(bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items.keys())


def _tool_ids():
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as T
    ids = set()

    def walk(items):
        for it in items:
            if isinstance(getattr(it, "idname", None), str):
                ids.add(it.idname)
            elif isinstance(it, (tuple, list)):
                walk(it)
    for _mode, items in T.tools_all():
        walk(items)
    return ids


# --- data -------------------------------------------------------------------------------------


def test_mapping_targets_and_icons_exist():
    icons, tools, bad = _icons(), _tool_ids(), []
    entries = list(shelf_map.BY_COMMAND.items()) + list(shelf_map.BY_LABEL.items())
    for key, (action, icon) in entries:
        if icon not in icons:
            bad.append((key, "icon", icon))
        kind, target, props = menu_map.normalize(action)
        if kind in ("op", "v3d"):
            mod, name = target.split(".")
            try:
                rna = getattr(getattr(bpy.ops, mod), name).get_rna_type()
            except (AttributeError, KeyError):
                bad.append((key, "no operator", target))
                continue
            bad.extend((key, target, p) for p in props if p not in rna.properties)
        elif kind == "tool" and target not in tools:
            bad.append((key, "tool", target))
    assert not bad, bad
    # Every mapped key names a real button.
    commands = {c for _n, _l, bs in shelf_data.SHELVES for _lab, c in bs if c}
    labels = {f"{n}/{lab}" for n, _l, bs in shelf_data.SHELVES for lab, _c in bs}
    assert not set(shelf_map.BY_COMMAND) - commands, set(shelf_map.BY_COMMAND) - commands
    assert not set(shelf_map.BY_LABEL) - labels, set(shelf_map.BY_LABEL) - labels


def test_mapped_buttons_per_shelf():
    counts = {name: len(shelf.factory_buttons(name)) for name, _l, _b in shelf_data.SHELVES}
    print("mapped shelf buttons:", counts)
    assert counts["Polygons"] >= 30, counts      # 37 in the factory shelf; no Sweep, SVG, ...
    assert counts["UVEditing"] >= 10, counts     # 12 in the factory shelf
    assert counts["Rigging"] >= 13 and counts["Animation"] >= 13 and counts["Rendering"] >= 13, counts
    assert all(v >= 1 for v in counts.values()), counts


# --- running ---------------------------------------------------------------------------------------

def _index(shelf_name, label):
    return next(i for i, lab, _a, _ic in shelf.factory_buttons(shelf_name) if lab == label)


def test_poly_cube_button_creates_maya_cube():
    _fresh()
    res = bpy.ops.allset.shelf_button(shelf="Polygons", index=_index("Polygons", "Polygon Cube"))
    assert res == {'FINISHED'}
    ob = bpy.context.view_layer.objects.active
    assert ob.name == "pCube1" and tuple(ob.dimensions) == (1.0, 1.0, 1.0)
    bpy.ops.allset.shelf_button(shelf="Polygons", index=_index("Polygons", "Freeze Transformations"))
    bpy.ops.allset.shelf_button(shelf="Rendering", index=_index("Rendering", "Lambert Material"))
    assert ob.active_material.name == "lambert2"   # lambert1 = the default material
    node = next(n for n in ob.active_material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    assert node.inputs["Roughness"].default_value == 1.0


# --- user shelves ------------------------------------------------------------------------------------

def test_store_path_in_sandbox():
    path = os.path.normcase(os.path.abspath(shelf.store_path()))
    assert path.startswith(os.path.normcase(os.path.abspath(SANDBOX))), path
    assert path.endswith("shelves.json")


def test_user_shelf_lifecycle():
    path = shelf.store_path()
    if os.path.exists(path):
        os.remove(path)
    shelf.reload_user()
    assert [s[1] for s in shelf.shelves()][-1] == "Custom"           # Maya's empty Custom tab
    assert bpy.ops.allset.shelf_new(name="Mine") == {'FINISHED'}
    assert shelf.current() == "USER:Mine"
    bpy.ops.allset.shelf_add_button(label="Hello", icon="NOT_AN_ICON",
                                      script="bpy.context.scene['shelf_ran'] = 42")
    bpy.ops.allset.shelf_add_button(label="Broken", icon="ERROR", script="1/0")
    s = shelf.user_shelf("Mine")
    assert [b["label"] for b in s["buttons"]] == ["Hello", "Broken"]
    assert s["buttons"][0]["icon"] == 'SCRIPT'                           # invalid icon replaced
    assert bpy.ops.allset.shelf_button(shelf="USER:Mine", index=0) == {'FINISHED'}
    assert bpy.context.scene["shelf_ran"] == 42
    try:
        res = bpy.ops.allset.shelf_button(shelf="USER:Mine", index=1)
    except RuntimeError:
        res = {'CANCELLED'}                                              # reported as an error
    assert res == {'CANCELLED'}
    on_disk = json.load(open(path, encoding="utf-8"))
    assert [x["name"] for x in on_disk["shelves"]] == ["Custom", "Mine"]
    shelf.reload_user()
    assert len(shelf.user_shelf("Mine")["buttons"]) == 2
    bpy.ops.allset.shelf_edit_button(index=0, label="Hi", icon="MESH_CUBE", script="x = 1")
    assert shelf.user_shelf("Mine")["buttons"][0] == {"label": "Hi", "icon": "MESH_CUBE", "script": "x = 1"}
    bpy.ops.allset.shelf_remove_button(index=1)
    assert len(shelf.user_shelf("Mine")["buttons"]) == 1
    runner.run("bpy.context.scene['from_cmd'] = 7")
    bpy.ops.allset.shelf_add_last_command()
    assert shelf.user_shelf("Mine")["buttons"][-1]["script"] == "bpy.context.scene['from_cmd'] = 7"
    bpy.ops.allset.shelf_delete()
    assert shelf.user_shelf("Mine") is None and shelf.current() == "Polygons"
    assert not bpy.ops.allset.shelf_delete.poll()                      # factory shelf: nothing to delete


def test_tab_step_and_select():
    shelf.reload_user()
    bpy.ops.allset.shelf_select(shelf="Polygons")
    bpy.ops.allset.shelf_step(forward=True)
    assert shelf.current() == "Sculpting"
    bpy.ops.allset.shelf_step(forward=False)
    bpy.ops.allset.shelf_step(forward=False)
    assert shelf.current() == "Surfaces"
    bpy.ops.allset.shelf_step(forward=False)
    assert shelf.current() == "Curves"                                 # the first tab
    bpy.ops.allset.shelf_step(forward=False)                           # wraps to the last tab
    assert shelf.current() == shelf.shelves()[-1][0]
    bpy.ops.allset.shelf_select(shelf="Polygons")


def test_draw_shelf():
    shelf.reload_user()
    bpy.ops.allset.shelf_select(shelf="Polygons")
    lay = FakeLayout()
    shelf.draw_shelf(lay, bpy.context)
    buttons = [e for e in lay.log if e[0] == "op" and e[1] == "allset.shelf_button"]
    assert len(buttons) == len(shelf.factory_buttons("Polygons"))
    assert buttons[1][3] == 'MESH_CUBE' and buttons[1][2] == ""          # icon only, like Maya
    assert ("menu", "ALLSET_MT_shelf_tabs", "Poly Modeling") in lay.log
    bpy.ops.allset.shelf_select(shelf="USER:Custom")
    lay = FakeLayout()
    shelf.draw_shelf(lay, bpy.context)
    assert any(e[0] == "op" and e[1] == "allset.shelf_add_button" for e in lay.log)  # empty: add
    bpy.ops.allset.shelf_select(shelf="Polygons")


# --- strip ---------------------------------------------------------------------------------------------

def test_image_headers_patched():
    # only Blender's own draw in the class's draw list is swapped (ui/own_draw.py)
    assert shelf._draw_image_header in bpy.types.IMAGE_HT_header.draw._draw_funcs
    assert shelf._draw_image_tool_header in bpy.types.IMAGE_HT_tool_header.draw._draw_funcs


def test_template_has_marked_strip():
    path = os.path.join(os.path.dirname(import_module(kit.MODULE).__file__),
                        "app_template", "Maya_Workflow_Kit", "startup.blend")
    bpy.ops.wm.open_mainfile(filepath=path, load_ui=True)
    scr = bpy.context.window_manager.windows[0].screen
    strip = shelf.strip_area(scr)
    assert strip is not None, [a.type for a in scr.areas]
    sp = strip.spaces.active
    assert not sp.show_region_ui and sp.mask.name == shelf.MARKER
    # Status Line and Shelf are two header-only rows (they follow the UI scale)
    row = shelf.shelf_row_area(scr)
    assert row is not None and row.y < strip.y and not sp.show_region_tool_header
    assert row.spaces.active.mask.name == shelf.SHELF_MARKER
    assert sum(1 for a in scr.areas if a.type == 'IMAGE_EDITOR') == 2


def test_icon_registry_recognizes_builtin_png_and_maya_icons():
    icons = shelf.shelf_icons
    builtin = next(iter(icons._builtin_icon_names()))
    assert icons.is_icon_name(builtin)
    procedural_key = next(iter(icons.ICONS))
    assert icons.is_icon_name("MWK:" + procedural_key)
    assert "MWK:" + procedural_key in icons.icon_names("MWK")
    paths = icons._png_icon_paths()
    if paths:
        filename = next(iter(paths.values())).rsplit(os.sep, 1)[-1].rsplit(".", 1)[0]
        assert icons.is_icon_name("PNG:" + filename)



def test_icon_caches_stay_in_the_kit_user_folder():
    """Icons taken out of the packed archive and icon previews are written next to shelves.json (the extension's
    user folder), never to Blender's config folder; PNG icons are looked up only in the kit's own folders."""
    icons = shelf.shelf_icons
    norm = lambda p: os.path.normcase(os.path.abspath(p))
    user = norm(os.path.dirname(shelf.store_path()))
    package = norm(os.path.dirname(os.path.dirname(icons.__file__)))
    packed = icons._packed_blender_icon_path("CUBE")
    assert packed and os.path.isfile(packed) and norm(packed).startswith(user), packed
    assert norm(icons._preview_cache_path("test")).startswith(user)
    config = bpy.utils.user_resource('CONFIG')
    assert not os.path.exists(os.path.join(config, "allset_shelf_icon_previews"))
    for path in icons._png_icon_paths(refresh=True).values():
        assert norm(path).startswith(package) or norm(path).startswith(user), path

def test_shelf_editor_three_way_merge_preserves_concurrent_edits():
    editor = import_module(kit.MODULE + ".ui.shelf_editor")
    base = {
        "shelves": [{"name": "Custom", "buttons": [
            {"label": "Old", "icon": "SCRIPT", "script": "pass"},
        ]}],
        "extra": {"Polygons": [{"label": "Menu A", "menu": "Create/Polygon Primitives/Cube"}]},
    }
    draft = json.loads(json.dumps(base))
    draft["shelves"][0]["buttons"][0]["label"] = "Renamed in Editor"
    latest = json.loads(json.dumps(base))
    latest["shelves"][0]["buttons"].append(
        {"label": "Added from Shelf", "icon": "PNG:tool", "script": "pass"})
    latest["shelves"].append({"name": "New from Gear", "buttons": []})
    latest["extra"]["Polygons"].append(
        {"label": "Menu B", "menu": "Create/Polygon Primitives/Sphere"})
    merged = editor._merge_documents(base, draft, latest)
    custom = next(item for item in merged["shelves"] if item["name"] == "Custom")
    assert custom["buttons"][0]["label"] == "Renamed in Editor"
    assert custom["buttons"][1]["label"] == "Added from Shelf"
    assert any(item["name"] == "New from Gear" for item in merged["shelves"])
    assert len(merged["extra"]["Polygons"]) == 2

    # A live gear-menu deletion of a button / Shelf must not be resurrected.
    base_removed = {
        "shelves": [{"name": "Custom", "buttons": [
            {"label": "Keep", "icon": "SCRIPT", "script": "pass"},
            {"label": "Remove Me", "icon": "SCRIPT", "script": "pass"},
        ]}],
        "extra": {},
    }
    latest_removed = json.loads(json.dumps(base_removed))
    latest_removed["shelves"][0]["buttons"].pop(1)
    merged_removed = editor._merge_documents(base_removed, base_removed, latest_removed)
    assert [b["label"] for b in merged_removed["shelves"][0]["buttons"]] == ["Keep"]
    removed = editor._merge_documents(base, draft, {"shelves": [], "extra": {}})
    assert removed["shelves"] == []
