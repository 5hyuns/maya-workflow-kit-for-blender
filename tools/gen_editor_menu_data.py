"""Generate src/allset/ui/editor_menu_data.py from the Maya editor captures (docs/steps/step_104.md).

    python tools/gen_editor_menu_data.py

Source: research/maya/screens/editors104/_editors104.json, a Maya 2026 GUI capture (factory prefs, step 269; it was
a Maya 2022 capture before): every menu of the Graph Editor, Dope Sheet, UV Editor and UV Toolkit menu bars, popped
up so Maya filled it. Only labels, structure, option boxes and check / radio items are kept (no commands, no Maya
resources).

The other editors (Hypershade / Render Settings / Script Editor, Reference Editor, Component / Shape / Connection
Editor) come from Maya 2022 captures that are no longer on disk (step 269): while a capture file is missing, its
editors are read back unchanged from the current editor_menu_data.py.
"""

import ast
import json
import pprint
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "research" / "maya" / "screens" / "editors104" / "_editors104.json"
# step 105: Hypershade, Render Settings, Script Editor (research/scripts/maya_editors105/)
SRC_105 = ROOT / "research" / "maya" / "screens" / "editors105" / "_editors105.json"
# step 209: Reference Editor (research/scripts/maya_refs209/)
SRC_209 = ROOT / "research" / "maya" / "screens" / "refs209" / "_refs209.json"
# step 213: Component / Shape / Connection Editor (research/scripts/maya_editors212/)
SRC_213 = ROOT / "research" / "maya" / "screens" / "editors212" / "_editors212.json"
OUT = ROOT / "src" / "allset" / "ui" / "editor_menu_data.py"

# capture key -> kit editor name; the UV Editor window holds two menu bars (UV Editor, then the UV Toolkit's)
EDITORS = (("graph_editor", "Graph Editor"), ("dope_sheet", "Dope Sheet"), ("uv_editor", "UV Editor"))
# the window's first menu bar only (the Hypershade's panels have their own icon rows, no menus)
EDITORS_105 = (("hypershade", "Hypershade"), ("render_settings", "Render Settings"), ("script_editor", "Script Editor"))
EDITORS_209 = (("reference_editor", "Reference Editor"),)
EDITORS_213 = (("component_editor", "Component Editor"), ("shape_editor", "Shape Editor"),
               ("connection_editor", "Connection Editor"))
UV_TOOLKIT_MENUS = ("Options", "Help")
# The UV Editor's Textures menu lists the textures of the captured scene (control "...Texture<n>"): the 2026 capture's
# scene had one ("openPBR_shader1"), the 2022 capture's none. Scene content is not menu structure: the entry is kept
# as Maya's empty-scene row (the 2022 capture's label), which the kit draws greyed.
SCENE_TEXTURE = re.compile(r"Texture\d+$")
NO_TEXTURE = "No texture found"


def convert(items, prefix, boxes, checks):
    """(label,) | (label, [children]) | ("-", section label), like menu_data; option boxes / checks by path."""
    out, seen, last = [], {}, None
    # Maya answers radioButton only for the checked item of a radio collection: the checkable items between two
    # dividers form one collection, radio if one of them answered.
    group, radio_groups = 0, set()
    for e in items:
        if e["sep"] or e.get("divider"):
            group += 1
        elif e.get("radioButton"):
            radio_groups.add(group)
    group = 0
    for e in items:
        if e["sep"] or e.get("divider"):
            group += 1
        if e.get("optionBox"):
            if last is not None:
                boxes.add(last)
            continue
        if not e.get("visible", True):
            continue
        if e["sep"] or e.get("divider"):
            label = e.get("dividerLabel") or ""
            if out and out[-1][0] == "-" and not label:
                continue
            out.append(("-", label))
            continue
        label = e["text"].strip()
        if SCENE_TEXTURE.search(e.get("maya") or "") and "TexturesMenu" in e.get("props", {}).get("originalName", ""):
            if any(x[0] == NO_TEXTURE for x in out):
                continue
            label, e = NO_TEXTURE, {**e, "checkable": False}
        n = seen[label] = seen.get(label, 0) + 1
        path = f"{prefix}/{label}" + (f"#{n}" if n > 1 else "")
        last = path
        if e["checkable"] and group in radio_groups:
            checks[path] = "radio"
        elif e["checkable"]:
            checks[path] = "check"
        kids = e.get("items")
        if kids:
            out.append((label, convert(kids, path, boxes, checks)))
        else:
            out.append((label,))
    while out and out[-1][0] == "-" and not out[-1][1]:
        out.pop()
    return out


def kept(names):
    """Editors whose capture is missing: (editors, option boxes, checks) read back from the current module."""
    if not OUT.exists():
        raise SystemExit(f"{OUT.relative_to(ROOT)} missing: the editors {names} have no capture to rebuild them from")
    values = {}
    for node in ast.parse(OUT.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            values[node.targets[0].id] = node.value
    editors = ast.literal_eval(values["EDITORS"])
    boxes = ast.literal_eval(values["OPTION_BOXES"].args[0])
    checks = ast.literal_eval(values["CHECKS"])
    mine = lambda path: path.split("/", 1)[0] in names
    return ({n: editors[n] for n in names}, {p for p in boxes if mine(p)},
            {p: v for p, v in checks.items() if mine(p)})


def build(data, data_105=None, data_209=None, data_213=None):
    editors, boxes, checks = {}, set(), {}
    for key, name in EDITORS:
        window = data[key][0]
        menus = [m for bar in window["bars"] for m in bar["menus"]]
        if key == "uv_editor":
            # the toolkit bar comes after the editor's (its own Help)
            split = len(menus) - len(UV_TOOLKIT_MENUS)
            groups = (("UV Editor", menus[:split]), ("UV Toolkit", menus[split:]))
        else:
            groups = ((name, menus),)
        for ed, ms in groups:
            editors[ed] = [(m["title"], convert(m["items"], f"{ed}/{m['title']}", boxes, checks)) for m in ms]
    for key, name in EDITORS_105 if data_105 else ():
        bars = sorted(data_105[key][0]["bars"], key=lambda b: b["y"])
        editors[name] = [(m["title"], convert(m["items"], f"{name}/{m['title']}", boxes, checks))
                         for m in bars[0]["menus"]]
    for key, name in EDITORS_209 if data_209 else ():
        bars = sorted(data_209[key][0]["bars"], key=lambda b: b["y"])
        editors[name] = [(m["title"], convert(m["items"], f"{name}/{m['title']}", boxes, checks))
                         for m in bars[0]["menus"]]
    for key, name in EDITORS_213 if data_213 else ():
        bars = sorted(data_213[key][0]["bars"], key=lambda b: b["y"])
        editors[name] = [(m["title"], convert(m["items"], f"{name}/{m['title']}", boxes, checks))
                         for m in bars[0]["menus"]]
    return editors, boxes, checks


def _read(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def main():
    later = ((SRC_105, EDITORS_105), (SRC_209, EDITORS_209), (SRC_213, EDITORS_213))
    old = {}
    for src, eds in later:
        if not src.exists():
            names = tuple(name for _k, name in eds)
            print(f"{src.relative_to(ROOT)} missing: {', '.join(names)} kept from {OUT.relative_to(ROOT)}")
            old[src] = kept(names)
    editors, boxes, checks = build(*[_read(p) for p in (SRC, SRC_105, SRC_209, SRC_213)])
    for src, _eds in later:
        if src in old:
            e, b, c = old[src]
            editors.update(e)
            boxes |= b
            checks.update(c)
    text = ['# SPDX-License-Identifier: GPL-3.0-or-later',
            '"""Maya editor menu bars: Graph Editor, Dope Sheet, UV Editor, UV Toolkit, Hypershade, Render Settings,',
            'Script Editor, Reference Editor, Component / Shape / Connection Editor (generated by',
            'tools/gen_editor_menu_data.py — do not edit).',
            '',
            'Source: research/maya/screens/editors104/_editors104.json + editors105/_editors105.json + refs209/_refs209.json',
            '+ editors212/_editors212.json (Graph Editor / Dope Sheet / UV Editor / UV Toolkit captured in a Maya 2026 GUI,',
            'step 269; the other editors in a Maya 2022 GUI, docs/steps/step_104.md, step_105.md, step_209.md, step_213.md;',
            'labels and structure only).',
            'EDITORS[editor] = [(menu title, items)]; item = (label,) | (label, [children]) |',
            '("-", section label). Paths are "<editor>/<menu>/<label>" (a repeated label gets "#2").',
            '"""',
            '',
            f'EDITORS = {pprint.pformat(editors, width=118, sort_dicts=False)}',
            '',
            f'OPTION_BOXES = frozenset({pprint.pformat(sorted(boxes), width=118)})',
            '',
            f'CHECKS = {pprint.pformat(dict(sorted(checks.items())), width=118)}',
            '']
    OUT.write_text("\n".join(text), encoding="utf-8")
    n = sum(1 for _ in _leaves(editors))
    print(f"editor_menu_data: {len(editors)} editors, {sum(len(v) for v in editors.values())} menus, {n} leaves, "
          f"{len(boxes)} option boxes, {len(checks)} check items -> {OUT.relative_to(ROOT)}")


def _leaves(editors):
    def walk(items):
        for it in items:
            if it[0] == "-":
                continue
            if len(it) > 1:
                yield from walk(it[1])
            else:
                yield it
    for menus in editors.values():
        for _title, items in menus:
            yield from walk(items)


if __name__ == "__main__":
    main()
