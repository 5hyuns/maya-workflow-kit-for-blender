"""Generate src/allset/ui/menu_icon_data.py: Maya menu item -> the kit drawing of the same command (step 131 lane
MENU, issue #23; docs/steps/step_131_menu.md).

    python tools/gen_menu_icons.py [--report]

Maya 2022 shows an icon on 1772 main-menu entries (look-only capture ``menu_icons.json``: menu path -> icon file;
read from ``research/maya/menu_icons131.json``, else ``tmp/maya_icons131/menu_icons.json``). The kit has its own
drawing for every factory shelf button (``ui/shelf_icons.py``), so a menu item gets an icon when it is the same
command as a shelf button:

1. same picture: the menu item's Maya icon is the shelf button's Maya icon (``research/maya/shelves.json`` image1);
2. same command: the menu item's runTimeCommand (``research/maya/menus.json`` "command") is the button's command,
   or ``ui/shelf_map.MENU`` names the item as the button's menu item;
3. ``GLYPHS`` below: items whose Maya icon is the picture of a Status Line button or a Tool Box tool the kit has
   drawn (``ui/status_icons.py``, ``ui/kit_icons.py``; docs/steps/step_131_status.md, step_131_toolbox.md);
4. menu-only drawings (step 142, #54): the ``@icon(path, ...)`` decorators of ``ui/menu_drawings*.py`` (read with
   ast) draw items that are on no shelf; an item whose Maya icon file is a drawn item's gets that drawing too.

All four only for items Maya shows with an icon. Only Maya icon file names are compared; none is written to the
output (decision 6). Items whose picture the kit has not drawn stay without an icon.
"""

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT.parent.parent.parent if ROOT.parent.name == "worktrees" else ROOT   # a worktree reads the main repo
UI = ROOT / "src" / "allset" / "ui"
OUT = UI / "menu_icon_data.py"

# Maya menu item -> (module, glyph) for pictures the kit drew outside the shelf: the Maya icon of each item is the one
# of that Status Line button / Tool Box tool (research/maya/re/icons131.md "Status Line", "Tool Box").
GLYPHS = {
    "Windows/General Editors/Attribute Editor": ("status", "ed_ATTRIBUTE"),
    "Windows/General Editors/Channel Box / Layer Editor": ("status", "ed_CHANNEL_BOX"),
    "Windows/General Editors/Tool Settings": ("status", "ed_TOOL_SETTINGS"),
    "Windows/Modeling Editors/Modeling Toolkit": ("status", "ed_MODELING_TOOLKIT"),
    "Windows/Rendering Editors/Hypershade": ("status", "hypershade"),
    "Windows/Rendering Editors/Render View": ("status", "render_view"),
    "Windows/Rendering Editors/Light Editor": ("status", "light_editor"),
    "Select/Components/Vertex": ("status", "vertex"),
    "Select/Components/Edge": ("status", "edge"),
    "Select/Components/Face": ("status", "face"),
    "Modify/Transformation Tools/Move Tool": ("kit", "tool:builtin.move"),
    "Modify/Transformation Tools/Rotate Tool": ("kit", "tool:builtin.rotate"),
    "Modify/Transformation Tools/Scale Tool": ("kit", "tool:builtin.scale"),
}


def _first(*paths):
    for p in paths:
        if p.exists():
            return p
    raise SystemExit("gen_menu_icons: missing " + " / ".join(str(p) for p in paths))


def _research(*rel):
    return _first(*(base / "research" / "maya" / Path(*rel) for base in (ROOT, MAIN)))


def _load_module(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _literal(path, name):
    """A module-level literal dict of a kit source file (read with ast: the module needs bpy)."""
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == name:
            out = {}
            for k, v in zip(node.value.keys, node.value.values):
                try:
                    out[ast.literal_eval(k)] = ast.literal_eval(v)
                except ValueError:      # entries built by helper calls: not needed here
                    pass
            return out
    return {}


def _walk(items, prefix, children):
    """(path, item) like ``ui/menu_sets.iter_items``: a label repeated among siblings gets "#2", "#3"; Maya's run-time
    submenus come from ``menu_map.CHILDREN``."""
    seen = {}
    for it in items:
        if it[0] == "-":
            continue
        n = seen[it[0]] = seen.get(it[0], 0) + 1
        path = f"{prefix}/{it[0]}" + (f"#{n}" if n > 1 else "")
        yield path, it
        kids = children.get(path) or (it[1] if len(it) > 1 else None)
        if kids:
            yield from _walk(kids, path, children)


def _drawn():
    """{Maya menu path: drawing name} from the ``@icon(...)`` decorators of ``ui/menu_drawings*.py`` (the name is
    the decorator's first path, like ``menu_drawings.icon``)."""
    out = {}
    for path in sorted(UI.glob("menu_drawings*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.FunctionDef):
                continue
            for deco in node.decorator_list:
                if isinstance(deco, ast.Call) and getattr(deco.func, "id", "") == "icon":
                    paths = [ast.literal_eval(a) for a in deco.args]
                    for p in paths:
                        if p in out:
                            raise SystemExit(f"gen_menu_icons: {p} drawn twice ({path.name})")
                        out[p] = paths[0]
    return out


def _menu_commands():
    """{kit-style path: runTimeCommand} from research/maya/menus.json (labels that are MEL expressions skipped)."""
    data = json.loads(_research("menus.json").read_text(encoding="utf-8"))["menus"]
    out = {}

    def walk(items, prefix):
        seen = {}
        for it in items:
            label = it.get("label")
            if it.get("divider") or not label or label.startswith("<"):
                continue
            n = seen[label] = seen.get(label, 0) + 1
            path = f"{prefix}/{label}" + (f"#{n}" if n > 1 else "")
            cmd = (it.get("command") or it.get("rtc") or "").strip()
            if re.match(r"^[A-Za-z_]\w*$", cmd):
                out.setdefault(path, cmd)
            if it.get("children"):
                walk(it["children"], path)

    for menu in data:
        walk(menu.get("items", []), menu.get("label", ""))
    return out


def build():
    menu_data = _load_module("menu_data", UI / "menu_data.py")
    shelf_data = _load_module("shelf_data", UI / "shelf_data.py")
    ref = _first(MAIN / "research" / "maya" / "menu_icons131.json", MAIN / "tmp" / "maya_icons131" / "menu_icons.json")
    shelves = json.loads(_research("shelves.json").read_text(encoding="utf-8"))["factory"]

    children = _literal(UI / "menu_map.py", "CHILDREN")
    kit_paths = set()
    for label, _set, _src, items in menu_data.MENUS.values():
        kit_paths.update(p for p, _it in _walk(items, label, children))

    by_image, by_command, by_label = {}, {}, {}
    for shelf, _tab, buttons in shelf_data.SHELVES:
        raw = shelves[shelf]
        for i, (label, command) in enumerate(buttons):
            button = ("shelf", shelf, label, i)
            by_label.setdefault(f"{shelf}/{label}", button)
            image = raw[i].get("image1") if i < len(raw) else None
            if image:
                by_image.setdefault(image, button)       # first shelf (Maya tab order) wins
            if command:
                by_command.setdefault(command, button)
    shelf_menu = {}
    for key, path in _literal(UI / "shelf_map.py", "MENU").items():
        if key in by_label:
            shelf_menu.setdefault(path, by_label[key])

    images = {}
    for e in json.loads(ref.read_text(encoding="utf-8")):
        images.setdefault(e["path"], e["image"])
    commands = _menu_commands()

    icons, how = {}, {}
    maya_kit = sorted(p for p in images if p in kit_paths)
    for path in maya_kit:
        button = by_image.get(images[path])
        if button is not None:
            icons[path], how[path] = button, "image"
            continue
        button = by_command.get(commands.get(path, "")) or shelf_menu.get(path)
        if button is not None:
            icons[path], how[path] = button, "command"
            continue
        if path in GLYPHS:
            icons[path], how[path] = GLYPHS[path], "glyph"
    stray = sorted(set(GLYPHS) - set(maya_kit))
    if stray:
        raise SystemExit(f"gen_menu_icons: GLYPHS paths that are no Maya icon item of the kit menus: {stray}")

    drawn = _drawn()
    stray = sorted(set(drawn) - set(maya_kit))
    if stray:
        raise SystemExit(f"gen_menu_icons: drawn paths that are no Maya icon item of the kit menus: {stray}")
    twice = sorted(p for p in drawn if p in icons)
    if twice:
        raise SystemExit(f"gen_menu_icons: drawn paths that already have a shelf / glyph picture: {twice}")
    by_image = {}
    for path, name in sorted(drawn.items()):
        icons[path], how[path] = ("menu", name), "drawn"
        by_image.setdefault(images[path], ("menu", name))
    for path in maya_kit:          # Maya shows the same picture: the same drawing
        if path not in icons and images[path] in by_image:
            icons[path], how[path] = by_image[images[path]], "drawn image"
    return icons, how, images, maya_kit


def write(icons):
    lines = ['# SPDX-License-Identifier: GPL-3.0-or-later',
             '"""Maya menu item -> kit drawing of the same command (generated by tools/gen_menu_icons.py — do not edit;',
             'step 131 lane MENU, issue #23).',
             '',
             'ICONS = {Maya menu path: picture}; picture = ("shelf", shelf file, button label, button index) = that',
             "button's kit drawing (``shelf_icons.draw``), like Maya shows the shelf picture of the same command in its",
             'menus; ("status", glyph) = a ``status_icons`` glyph, ("kit", glyph) = a ``kit_icons`` glyph (the same',
             'Maya picture on the Status Line / Tool Box); ("menu", name) = a ``menu_drawings`` drawing (step 142,',
             '#54: items on no shelf). Only items Maya 2022 draws with an icon are listed.',
             '"""',
             '',
             'ICONS = {']
    for path, pic in sorted(icons.items()):
        lines.append(f'    {path!r}: {pic!r},')
    lines.append('}')
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    icons, how, images, maya_kit = build()
    write(icons)
    n = {k: sum(1 for v in how.values() if v == k) for k in ("image", "command", "glyph", "drawn", "drawn image")}
    print(f"gen_menu_icons: wrote {OUT.relative_to(ROOT)}: {len(icons)} items with an icon "
          f"({n['image']} same shelf picture, {n['command']} same shelf command, {n['glyph']} Status Line / Tool Box "
          f"glyph, {n['drawn']} + {n['drawn image']} menu drawings) of {len(maya_kit)} Maya icon items in the kit "
          f"menus ({len(images)} Maya menu entries with an icon)")
    if "--report" in sys.argv:
        for path in maya_kit:
            print(("  + " if path in icons else "  - ") + path, how.get(path, ""), icons.get(path, ""))


if __name__ == "__main__":
    main()
