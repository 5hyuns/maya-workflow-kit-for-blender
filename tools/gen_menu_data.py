"""Generate src/maya_kit/ui/menu_data.py from research/maya/menus.json.

    python tools/gen_menu_data.py

Keeps only the menu structure (menu sets, menu labels, item labels, dividers,
submenus, which items have an option box) — no MEL command strings (docs/user_decisions.md #6). Cleans the
heuristic static parse (docs/steps/step_7.md 「계획」 2): unknown
``<dynamic:...>`` labels and parse leftovers are dropped, repeated labels in a
row collapse to one.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "research" / "maya" / "menus.json"
OUT = ROOT / "src" / "maya_kit" / "ui" / "menu_data.py"

DYNAMIC = {"$QuitLabel": "Exit", "$kIncrementAndSaveLabel": "Increment and Save"}
# Placeholder items the static parse made parents of their following siblings: their label, and
# the swallowed siblings come back after them (the only one in menus.json: Render > Render Using,
# research/maya/menus.md:1686-1704; docs/steps/step_67.md 「계획」 3).
PLACEHOLDERS = {'("renMenuRenderUsingItemMenuItem")': "Render Using"}
_CLEAN = re.compile(r"^[A-Za-z0-9][\w ./&+()'\-]*$")

# Run-time items the static parse can't see (docs/steps/step_101.md 「계획」 1; labels and order from a live
# Maya 2022, research/maya/re/menu_honesty.md §1).
# Top-level ``<dynamic:...>`` labels, filled in order (the rest are dropped as before).
RUNTIME_LABELS = {
    "mainModifyMenu": ["Center Pivot", "Bake Pivot", "Prefix Hierarchy Names...", "Search and Replace Names...",
                       "Add Attribute...", "Edit Attribute...", "Delete Attribute..."],
    "MainHelpMenu": ["Maya Help", "YouTube Learning Channel", "About Maya"],
}
# Menus built entirely by Python at run time (empty in menus.json): maya/ge/soundMenu.py:197-231,
# maya/app/stereo/stereoCameraSettings.py:113-135 + stereoCameraMenus.py:197-223.
RUNTIME_MENUS = {
    "mainAudioMenu": [("Import Audio...",), ("Import Audio Clip to Time Editor...",), ("-", "Sounds"),
                      ("No sounds available",), ("-", ""), ("Mute",), ("Adjust Volume",), ("Delete Sounds",),
                      ("Waveform Display", [("Top",), ("Bottom",), ("Centered",)])],
    "mainStereoMenu": [("-", "Stereo Cameras"),
                       ("Editors", [("Custom Stereo Rig...",), ("Custom Multi Rig...",)]),
                       ("Create", [("Stereo Camera",), ("Multi Stereo Rig",)]),
                       ("-", "Stereo Links"), ("Make Links",), ("Break Links",)],
}
# Maya 2022's Cache menu = three plug-in submenus; the static parse saw only AniGeoCacheMenu.mel (Geometry
# Cache). Alembic: $M/scripts/others/AlembicCreateUI.mel:158-198, GPU: gpuCacheCreateUI.mel:812-841.
CACHE_MENU = "mainPipelineCacheMenu"
ALEMBIC = [("Open Alembic...",), ("Reference Alembic...",), ("Import Alembic...",), ("Replace Alembic...",),
           ("Export All to Alembic...",), ("Export Selection to Alembic...",), ("About Alembic...",)]
GPU_CACHE = [("Import...",), ("Export All...",), ("Export Selection...",), ("Refresh All...",)]
CACHE_BOXES = {"Cache/Alembic Cache/Import Alembic...", "Cache/Alembic Cache/Export All to Alembic...",
               "Cache/Alembic Cache/Export Selection to Alembic...", "Cache/GPU Cache/Import...",
               "Cache/GPU Cache/Export All...", "Cache/GPU Cache/Export Selection..."}
_XGEN = [("XGen Editor",), ("XGen Library",), ("-", ""), ("Create Description...",),
         ("Import Collections or Descriptions...",), ("Export Collections or Descriptions...",),
         ("Export Selection as Archive(s)...",), ("Batch Convert Scenes to Archives...",),
         ("Convert XGen Primitives to Polygons...",), ("Convert to Interactive Groom...",), ("Import Preset...",),
         ("Export as Preset...",), ("-", ""), ("Create Interactive Groom Splines",), ("Interactive Groom Editor",),
         ("Interactive Grooming Tools",), ("Cache",), ("Convert Interactive Groom to Polygons...",),
         ("Display HUD",), ("-", "")]
# Top-level items a live Maya 2022 shows that menus.json lacks (plug-in menus, step_98.md #13):
# menu: [(where, anchor label, items)], where = "before" / "after" the first top-level anchor, or "end".
INSERTS = {
    "mainFileMenu": [("after", "Export Selection...", [("-", ""), ("Game Exporter",), ("-", ""),
                                                        ("Send To Unity",), ("Send To Unreal",)])],
    "mainCreateMenu": [("before", "Type", [("Sweep Mesh",)]),
                       ("before", "Scene Assembly", [("Universal Scene Description (USD)",)])],
    "mainSelectMenu": [("end", None, [("-", ""), ("USD Selection Mode",)])],
    "mainPlaybackMenu": [("after", "Playblast", [("Cached Playback",)])],
    "mainVisualizeMenu": [("after", "Create Turntable...", [("-", ""), ("Open Ghosting Editor",), ("Ghost Selected",),
                                                            ("Unghost Selected",), ("Unghost All",)]),
                          ("end", None, [("-", ""), ("Time Slider Bookmarks",)])],
    **{name: [("after", "Pose Space Deformation", [("-", ""), ("Muscle",)])]
       for name in ("mainDeformMenu", "mainRigDeformationsMenu", "mainDeformationMenu")},
    "mainGenerateMenu": [("before", "Character Generator", _XGEN)],
}


def insert_items(items, inserts):
    """Apply INSERTS to a converted top-level list (no two dividers in a row)."""
    out = list(items)
    for where, anchor, new in inserts:
        if where == "end":
            at = len(out)
        else:
            at = next(i for i, it in enumerate(out) if it[0] == anchor) + (where == "after")
        out[at:at] = new
    cleaned = []
    for it in out:
        if it[0] == "-" and cleaned and cleaned[-1][0] == "-":
            cleaned[-1] = it if it[1] else cleaned[-1]
            continue
        cleaned.append(it)
    return cleaned


def label_of(item, runtime=None):
    label = (item.get("label") or "").strip()
    m = re.match(r"<dynamic:\(?(\$\w+)\)?>", label)
    if m:
        if m.group(1) not in DYNAMIC and runtime:
            return runtime.pop(0)
        return DYNAMIC.get(m.group(1))
    if not _CLEAN.match(label) or '"' in label:
        return None
    return label


_OPTION = {}   # id(converted entry) -> the Maya item has an option box (menus.json "optionBox")


def convert(items, runtime=None):
    """``runtime``: labels for this level's unknown ``<dynamic:...>`` items, used up in order."""
    out = []
    for it in items:
        if it.get("divider"):
            text = label_of(it) if it.get("label") else ""
            entry = ("-", text or "")
            if out and out[-1][0] == "-":  # empty section: keep only the later divider
                out[-1] = entry
            elif out:
                out.append(entry)
            continue
        raw = (it.get("label") or "").strip()
        if raw in PLACEHOLDERS:
            entry = (PLACEHOLDERS[raw],)
            _OPTION[id(entry)] = False
            out.append(entry)
            out.extend(convert(it.get("children") or []))
            continue
        label = label_of(it, runtime)
        if not label:
            continue
        children = convert(it.get("children") or [])
        if out and out[-1][0] == label and not children:
            continue
        if children and children[0][0] == label and len(children[0]) > 1:
            # Parse leftover (Edit > Delete by Type): the submenu swallowed its
            # own siblings; the real submenu is the first child, the rest follow it.
            out.extend(children)
            continue
        entry = (label, children) if children else (label,)
        _OPTION[id(entry)] = bool(it.get("optionBox"))
        out.append(entry)
    while out and out[-1][0] == "-":
        out.pop()
    return out


def option_paths(items, prefix):
    """Label paths (ui/menu_sets.children rules: a label repeated among siblings gets "#2", ...)
    of the entries whose Maya item has an option box."""
    seen = {}
    for it in items:
        if it[0] == "-":
            continue
        n = seen[it[0]] = seen.get(it[0], 0) + 1
        path = f"{prefix}/{it[0]}" + (f"#{n}" if n > 1 else "")
        if _OPTION.get(id(it)):
            yield path
        if len(it) > 1:
            yield from option_paths(it[1], path)


def build(data):
    """{menu name: (label, menu set, builder, items)} from menus.json data (with the run-time fixes)."""
    menus = {}
    for m in data["menus"]:
        src = m["builders"][0]["file"] if m.get("builders") else m.get("mappingSource", "")
        items = convert(m["items"], list(RUNTIME_LABELS.get(m["name"], ())))
        items = RUNTIME_MENUS.get(m["name"], items)
        if m["name"] == CACHE_MENU:
            items = [("Alembic Cache", ALEMBIC), ("Geometry Cache", items), ("GPU Cache", GPU_CACHE)]
        items = insert_items(items, INSERTS.get(m["name"], ()))
        menus[m["name"]] = (m["label"].strip(), m["menuSet"], src, items)
    return menus


def option_boxes(menus):
    """Label paths with a Maya option box (call right after ``build``: it reads the items' ids)."""
    return {p for m in menus.values() for p in option_paths(m[3], m[0])} | CACHE_BOXES


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    sets = [(s["id"], s["label"], s["menus"]) for s in data["menuSetsFromUserPrefs"]]
    menus = build(data)
    lines = [
        '# SPDX-License-Identifier: GPL-3.0-or-later',
        '"""Maya 2022 main menu structure (generated by tools/gen_menu_data.py — do not edit).',
        '',
        'Source: research/maya/menus.json (static parse of Maya\'s shipped menu builders;',
        'structure and labels only). MENUS[name] = (label, menu set, Maya builder file:line,',
        'items); item = (label,) | (label, [children]) | ("-", section label).',
        '"""',
        '',
        f'MENU_SETS = {sets!r}',
        '',
        'MENUS = {',
    ]
    for name, value in menus.items():
        lines.append(f'    {name!r}: {value!r},')
    lines.append('}')
    boxes = sorted(option_boxes(menus))
    lines += ['', '# Label paths of the items with a Maya option box (menus.json "optionBox", step 51).',
              'OPTION_BOXES = frozenset({']
    lines += [f'    {p!r},' for p in boxes]
    lines.append('})')
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    total = sum(1 for _ in _walk(m[3] for m in menus.values()))
    print(f"wrote {OUT.relative_to(ROOT)}: {len(menus)} menus, {total} items, {len(boxes)} option boxes")


def _walk(lists):
    for items in lists:
        for it in items:
            if it[0] != "-":
                yield it
                if len(it) > 1:
                    yield from _walk([it[1]])


if __name__ == "__main__":
    main()
