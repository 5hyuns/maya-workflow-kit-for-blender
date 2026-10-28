"""Generate src/allset/ui/menu_data.py from the Maya 2026 GUI menu dump.

    python tools/gen_menu_data.py

Step 219 (Issue #130): the source is research/maya/re/maya2026_menus_dump.json — every main menu as a running Maya
2026 builds it (postMenuCommand run, plug-in and run-time items included). The menu sets (which menu belongs to which
set) still come from research/maya/menus.json. Keeps only the menu structure (menu labels, item labels, dividers,
submenus, which items have an option box) — no MEL command strings in the output (docs/user_decisions.md #6).
The Maya 2022 static-parse fixes (RUNTIME_LABELS, INSERTS, ...) below are kept for the record but no longer applied:
the live dump has those items in Maya 2026's own places.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "research" / "maya" / "menus.json"          # menu sets (and the Maya 2022 static parse)
DUMP = ROOT / "research" / "maya" / "re" / "maya2026_menus_dump.json"   # step 219: the menu structure
OUT = ROOT / "src" / "allset" / "ui" / "menu_data.py"

DYNAMIC = {"$QuitLabel": "Exit", "$kIncrementAndSaveLabel": "Increment and Save"}
# Placeholder items the static parse made parents of their following siblings: their label, and
# the swallowed siblings come back after them (the only one in menus.json: Render > Render Using,
# research/maya/menus.md:1686-1704; docs/steps/step_67.md 「계획」 3).
PLACEHOLDERS = {'("renMenuRenderUsingItemMenuItem")': "Render Using"}
# Step 111 (decision 12, docs/distribution/extensions_audit.md): Maya menu labels that read as an Autodesk storefront
# are drawn under a neutral name for the item's Blender counterpart.
LABEL_RENAMES = {"Autodesk App Store": "Blender Extensions"}
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
# Maya 2022's Cache menu = three plug-in submenus; the static parse saw only the Geometry
# Cache one. Alembic and GPU Cache items: Maya 2022 Cache menu labels.
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
_COMMAND = {}  # id(converted entry) -> the Maya runTimeCommand it runs (menus.json "command" / "rtc"; step 108)


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
        label = LABEL_RENAMES.get(label, label)
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
        if it.get("command") or it.get("rtc"):
            _COMMAND[id(entry)] = it.get("command") or it.get("rtc")
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


def command_paths(items, prefix):
    """(label path, Maya runTimeCommand) of the entries whose Maya item names one (same path rules as
    ``option_paths``)."""
    seen = {}
    for it in items:
        if it[0] == "-":
            continue
        n = seen[it[0]] = seen.get(it[0], 0) + 1
        path = f"{prefix}/{it[0]}" + (f"#{n}" if n > 1 else "")
        if _COMMAND.get(id(it)):
            yield path, _COMMAND[id(it)]
        if len(it) > 1:
            yield from command_paths(it[1], path)


# Labels Maya 2026 builds with the live state in them (Edit > Undo "<last command>").
_LIVE_LABELS = (re.compile(r'^(Undo|Redo) ".*"$'),)


def _live_label(label):
    for rx in _LIVE_LABELS:
        m = rx.match(label)
        if m:
            return m.group(1)
    return label


def kit_filled():
    """Label paths whose children the kit builds at run time (``menu_map.CHILDREN``, or a ``("menu", ...)`` action
    that opens a kit menu listing the scene's sets / bookmarks / workspaces ...): the dump's children there are the
    dumping scene's state, not menu structure, so the entry stays a leaf (step 219)."""
    sys.path.insert(0, str(ROOT / "tools"))
    import menu_count
    _data, menu_map, _notices = menu_count._load()
    out = set(menu_map.CHILDREN)            # (only Windows > Settings/Preferences since step 219)
    for path, action in menu_map.MAP.items():
        if isinstance(action, tuple) and action and action[0] == "menu":
            out.add(path)
    return out


_RTC = {}    # runTimeCommand name -> its recorded command (from menus.json; hotkeys match on it, step 108)


def convert_live(items, prefix="", filled=frozenset()):
    """Dump items -> menu_data items (labels as Maya 2026 draws them). ``prefix`` = the label path of ``items``'
    parent (menu_sets.children rules), ``filled`` = paths left childless (``kit_filled``)."""
    out = []
    seen = {}
    for it in items:
        if "divider" in it:
            entry = ("-", (it.get("divider") or "").strip())
            if out and out[-1][0] == "-":
                out[-1] = entry if entry[1] or not out[-1][1] else out[-1]
            elif out:
                out.append(entry)
            continue
        label = (it.get("label") or "").strip()
        if not label:
            continue
        label = LABEL_RENAMES.get(_live_label(label), _live_label(label))
        n = seen[label] = seen.get(label, 0) + 1
        path = f"{prefix}/{label}" + (f"#{n}" if n > 1 else "")
        rel = path.split("/", 1)[1] if "/" in path else path       # CHILDREN keys have no top menu label
        kids = [] if (path in filled or rel in filled) else (it.get("items") or [])
        children = convert_live(kids, path, filled)
        entry = (label, children) if children else (label,)
        _OPTION[id(entry)] = bool(it.get("optionBox"))
        if it.get("command"):
            _COMMAND[id(entry)] = _RTC.get(it["command"], it["command"])
        out.append(entry)
    while out and out[-1][0] == "-":
        out.pop()
    return out


def build(data=None):
    """{menu name: (label, menu set, source, items)}: the Maya 2026 live dump for every menu the kit draws (the menu
    list and menu sets from menus.json ``data``; read from disk when not given)."""
    data = data if data and "menus" in data else json.loads(SRC.read_text(encoding="utf-8"))
    dump = json.loads(DUMP.read_text(encoding="utf-8"))
    _RTC.clear()
    _RTC.update(dump.get("runTimeCommands") or {})
    live = {m["name"]: m for v in dump.values() if isinstance(v, list) for m in v if isinstance(m, dict)}
    filled = kit_filled()
    menus = {}
    for m in data["menus"]:
        src = live.get(m["name"])
        if src is None:
            continue
        label = src["menu"].strip()
        menus[m["name"]] = (label, m["menuSet"], "maya2026_menus_dump.json",
                            convert_live(src["items"], label, filled))
    return menus


def build_2022(data):
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
    return {p for m in menus.values() for p in option_paths(m[3], m[0])}


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    sets = [(s["id"], s["label"], s["menus"]) for s in data["menuSetsFromUserPrefs"]]
    menus = build(data)
    lines = [
        '# SPDX-License-Identifier: GPL-3.0-or-later',
        '"""Maya 2026 main menu structure (generated by tools/gen_menu_data.py — do not edit).',
        '',
        'Source: research/maya/re/maya2026_menus_dump.json (menus as a running Maya 2026 builds them; structure',
        'and labels only), menu sets from research/maya/menus.json. MENUS[name] = (label, menu set, source,',
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
