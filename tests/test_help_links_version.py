"""Help links (main menu Help, editor Help menus, marking menus, shelf, repeat, option boxes, Layer Editor,
Outliner, Maya Preferences) open the Blender manual / API / release notes of the running Blender: 5.3's on
Blender 5.3, 5.2's on 5.2 (and on other versions). The kit's tables name the main target's pages (5.2); the version
is set when a link runs or is drawn (``compat.docs_url``). No browser opens here: the link operator call is caught."""

import os
import re
from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "allset")
TARGET = "5.2"
LINK = re.compile(r"(?:docs\.blender\.org/(?:manual/[a-z_A-Z]+|api)|developer\.blender\.org/docs/release_notes)/"
                  r"(\d+\.\d+)/")
RUNNING = tuple(bpy.app.version[:2])
WANT = "%d.%d" % RUNNING if RUNNING in ((5, 2), (5, 3)) else TARGET

compat = import_module(kit.MODULE + ".compat")
modal = import_module(kit.MODULE + ".marking.modal")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
repeat_maya = import_module(kit.MODULE + ".operators.repeat_maya")
HELP_ITEMS = ("Help/Quick Tour", "Help/Scripting Reference/Python Command Reference",
              "Help/Services and Support/Release Notes Updates", "Graph Editor/Help/Help on Graph Editor")


def test_every_versioned_blender_link_is_the_main_target():
    found, wrong = 0, []
    for root, _dirs, files in os.walk(SRC):
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as fh:
                for n, line in enumerate(fh, 1):
                    for version in LINK.findall(line):
                        found += 1
                        if version != TARGET:
                            wrong.append(f"{os.path.relpath(path, SRC)}:{n} {version}")
    assert found >= 5, found
    assert not wrong, wrong


def test_docs_url_is_the_running_blenders():
    assert compat.DOCS_VERSION == WANT, (compat.DOCS_VERSION, WANT)
    for base in ("https://docs.blender.org/manual/en/5.2/editors/outliner/index.html",
                 "https://docs.blender.org/api/5.2/bpy.types.html",
                 "https://developer.blender.org/docs/release_notes/5.2/"):
        got = compat.docs_url(base)
        assert got == base.replace("/5.2/", f"/{WANT}/"), got
    other = "https://github.com/5hyuns/maya-workflow-kit-for-blender/releases/5.2/"
    assert compat.docs_url(other) == other


class _Caught:
    """Stands in for ``modal._call`` (the operator call of a menu action): records the link, opens nothing."""

    def __init__(self):
        self.urls = []

    def __call__(self, op, option, props):
        self.urls.append(props.get("url"))
        return {'FINISHED'}


def _catching(run):
    caught, old = _Caught(), modal._call
    modal._call = caught
    try:
        run()
    finally:
        modal._call = old
    return caught.urls


def test_menu_items_open_the_running_blenders_pages():
    for path in HELP_ITEMS:
        urls = _catching(lambda: bpy.ops.allset.menu_item(item=path))
        assert len(urls) == 1 and f"/{WANT}/" in urls[0], (path, urls)


def test_marking_shelf_and_repeat_runs_open_the_running_blenders_pages():
    path = "Help/Quick Tour"
    for run in (lambda: modal.run_action(bpy.context, menu_map.MAP[path], path=path),       # menu / marking menu
                lambda: modal.run_action(bpy.context, ("item", path)),                     # shelf / marking "item"
                lambda: repeat_maya.run_entry(bpy.context, {"action": menu_map.MAP[path], "path": path})):  # G
        urls = _catching(run)
        assert len(urls) == 1 and f"/{WANT}/" in urls[0], urls


class _Layout:
    """Records the operator buttons a draw function makes."""

    def __init__(self):
        self.ops = []

    def operator(self, idname, **_kw):
        props = SimpleNamespace(idname=idname)
        self.ops.append(props)
        return props


def _drawn_urls(draw):
    layout = _Layout()
    draw(layout)
    return [p.url for p in layout.ops if p.idname == "wm.url_open"]


def test_drawn_help_buttons_name_the_running_blenders_pages():
    item_draw = import_module(kit.MODULE + ".ui.menu_item_draw")
    layer_editor = import_module(kit.MODULE + ".ui.layer_editor")
    maya_outliner = import_module(kit.MODULE + ".ui.maya_outliner")
    maya_prefs = import_module(kit.MODULE + ".ui.maya_prefs")
    draws = {
        "marking menu item": lambda lay: item_draw.draw_spec(lay, "Quick Tour", menu_map.spec("Help/Quick Tour"),
                                                             "Help/Quick Tour"),
        "Layer Editor": lambda lay: layer_editor.ALLSET_MT_le_help.draw(SimpleNamespace(layout=lay), bpy.context),
        "Outliner": lambda lay: maya_outliner.ALLSET_MT_outliner_help.draw(SimpleNamespace(layout=lay), bpy.context),
        "Preferences": lambda lay: maya_prefs.ALLSET_MT_prefs_help.draw(SimpleNamespace(layout=lay), bpy.context),
    }
    for name, draw in draws.items():
        urls = _drawn_urls(draw)
        assert len(urls) == 1 and f"/{WANT}/" in urls[0], (name, urls)


def test_every_drawn_link_button_goes_through_docs_url():
    """A help button drawn with ``wm.url_open`` sets its url through ``compat.docs_url`` (that line or the next)."""
    bad = []
    for root, _dirs, files in os.walk(SRC):
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            for n, line in enumerate(lines):
                if 'operator("wm.url_open"' in line and "docs_url(" not in line + "".join(lines[n + 1:n + 2]):
                    bad.append(f"{os.path.relpath(path, SRC)}:{n + 1}")
    assert not bad, bad
