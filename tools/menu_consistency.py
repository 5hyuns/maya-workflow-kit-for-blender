"""Find Maya menu items that are greyed in one menu while the same Maya command works in another (step 166).

    python tools/menu_consistency.py          # list the pairs (exit 1 when there is one)

A leaf's identity = its label (without the "#n" of repeated labels) + the Maya command it runs:
- main menus: the runTimeCommand / command of research/maya/menus.json (tools/gen_menu_data.command_paths);
- editor menu bars: the item's annotation in the Maya GUI capture (research/maya/screens/editors104 / 105) — Maya's
  menu items show their runTimeCommand's annotation, so equal annotations mean the same command;
- marking menus: the command of the item with that label in research/maya/marking_menus.json (the proc's items).
A main-menu command is turned into its annotation through research/maya/runtime_commands.json, so a main item and
an editor item compare on the same text. Leaves without a known command are skipped (no claim).

``pairs(leaves)`` is pure: tests/test_step166_menu_consistency.py feeds it the live kit (``working`` from
menu_map.MAP / the marking engine's rules); ``main()`` builds the leaves without Blender (tools/menu_count._load).
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "research" / "maya"


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def base_label(path):
    return re.sub(r"#\d+$", "", path.rsplit("/", 1)[-1])


def _norm(text):
    return re.sub(r"\s+", " ", text or "").strip().lower()


def annotations():
    """{runTimeCommand name: annotation} (research/maya/runtime_commands.json)."""
    data = _json(RESEARCH / "runtime_commands.json")["runtime_commands"]
    return {r["name"]: r.get("annotation") or "" for r in data}


def by_category():
    """{(menu path, label): runTimeCommand name} from the runtime commands' menu categories ("Menu items.Common.Select.
    Convert Selection" = the item under Select > Convert Selection): main items the static parse saw no command for
    ($cmd, run-time built) still name their command there."""
    out = {}
    for r in _json(RESEARCH / "runtime_commands.json")["runtime_commands"]:
        for cat in (r.get("category") or "").split(";"):
            parts = cat.split(".")
            if len(parts) > 2 and parts[0] == "Menu items" and r.get("label"):
                out.setdefault(("/".join(parts[2:]), r["label"]), r["name"])
    return out


def main_commands():
    """{main menu path: Maya command} (menus.json, same paths as ui/menu_sets)."""
    sys.path.insert(0, str(ROOT / "tools"))
    import gen_menu_data as g
    menus = g.build(_json(g.SRC))
    out = {}
    for m in menus.values():
        out.update(dict(g.command_paths(m[3], m[0])))
    return out


def editor_annotations():
    """{editor menu path: annotation} from the Maya GUI captures (gen_editor_menu_data path rules)."""
    sys.path.insert(0, str(ROOT / "tools"))
    import gen_editor_menu_data as g
    out = {}

    def walk(items, prefix):
        seen = {}
        for e in items:
            if e["sep"] or e.get("divider") or e.get("optionBox") or not e.get("visible", True):
                continue
            label = e["text"].strip()
            n = seen[label] = seen.get(label, 0) + 1
            path = f"{prefix}/{label}" + (f"#{n}" if n > 1 else "")
            if e.get("items"):
                walk(e["items"], path)
            elif e.get("annotation"):
                out[path] = e["annotation"]

    data = _json(g.SRC)
    for key, name in g.EDITORS:
        menus = [m for bar in data[key][0]["bars"] for m in bar["menus"]]
        if key == "uv_editor":
            split = len(menus) - len(g.UV_TOOLKIT_MENUS)
            groups = (("UV Editor", menus[:split]), ("UV Toolkit", menus[split:]))
        else:
            groups = ((name, menus),)
        for ed, ms in groups:
            for m in ms:
                walk(m["items"], f"{ed}/{m['title']}")
    if g.SRC_105.exists():
        data = _json(g.SRC_105)
        for key, name in g.EDITORS_105:
            bars = sorted(data[key][0]["bars"], key=lambda b: b["y"])
            for m in bars[0]["menus"]:
                walk(m["items"], f"{name}/{m['title']}")
    return out


def marking_commands():
    """{(proc, label): command} of the Maya marking menu items (first item with that label per proc)."""
    out = {}
    for proc, m in _json(RESEARCH / "marking_menus.json")["menus"].items():
        for it in m.get("items", ()):
            label, cmd = it.get("label"), it.get("command")
            if label and cmd and (proc, label) not in out:
                out[(proc, label)] = cmd
    return out


def signature(command, notes):
    """Comparable text of a Maya command: its runTimeCommand's annotation when it is one, else the command."""
    if not command or "$" in command or "<" in command:
        return None                     # built at run time ($cmd): nothing to compare
    word = command.split()[0].rstrip(";")
    if word in notes and notes[word]:
        return _norm(notes[word])
    return _norm(command)


def pairs(leaves):
    """``leaves`` = [(path, signature, working)]; [(greyed path, working path)] for every greyed leaf whose
    label + signature equals a working leaf's."""
    working = {}
    for path, sig, ok in leaves:
        if sig and ok:
            working.setdefault((base_label(path), sig), path)
    return sorted({(path, working[(base_label(path), sig)]) for path, sig, ok in leaves
                   if sig and not ok and (base_label(path), sig) in working})


def menu_leaves(paths_working):
    """[(path, signature, working)] for main / editor menu leaves; ``paths_working`` = [(path, working)]."""
    notes = annotations()
    main = main_commands()
    eds = editor_annotations()
    cats = by_category()
    out = []
    for path, ok in paths_working:
        if path in eds:
            sig = _norm(eds[path])
        else:
            sig = signature(main.get(path), notes)
            if sig is None:
                rtc = cats.get((path.rsplit("/", 1)[0], base_label(path)))
                sig = _norm(notes.get(rtc)) if rtc else None
        out.append((path, sig, ok))
    return out


def marking_leaves(entries):
    """``entries`` = [(proc, label path, working)] -> [(proc/label path, signature, working)]."""
    notes = annotations()
    cmds = marking_commands()
    out = []
    for proc, label_path, ok in entries:
        label = label_path.rsplit("/", 1)[-1]
        out.append((f"{proc}/{label_path}", signature(cmds.get((proc, label)), notes), ok))
    return out


def panel_leaves(pmd):
    """[(path, signature, working)] of the viewport panel menus / panel toolbar / greyed Status Line widgets
    (ui/panel_menu_data, step 177): a row with a Maya runTimeCommand compares on its annotation, the others on their
    label within the panel family ("panel:<label>", e.g. a toolbar button and the menu row of the same name)."""
    notes = annotations()
    out = []
    for _family, path, ok in pmd.leaves():
        label = base_label(path)
        rtc = pmd.COMMANDS.get(label)
        sig = _norm(notes.get(rtc)) if rtc and notes.get(rtc) else "panel:" + _norm(label)
        out.append((path, sig, ok))
    return out


RESEARCH_PROC = {"buildObjectMenuItemsNow_pivot": "buildObjectMenuItemsNow", "dagMenuProc_curve": "dagMenuProc"}


def marking_entries(mk, menu_map_keys):
    """[(Maya proc, label path, working)] of every marking menu leaf (``mk`` = marking/menus; working = drawn
    enabled: an action, and a main-menu ``("item", path)`` only when that path is mapped)."""
    out = []
    for name, menu in mk.MENUS.items():
        for path, _label, action in mk.label_walk(menu, ""):
            if isinstance(action, mk.Sub) and not mk.is_greyed(action):
                continue                                    # a submenu, not a leaf
            ok = not mk.is_greyed(action)
            if ok and isinstance(action, tuple) and len(action) == 2 and action[0] == "item":
                ok = action[1] in menu_map_keys
            out.append((RESEARCH_PROC.get(name, name), path.lstrip("/"), ok))
    return out


def _marking():
    """marking/menus.py on its own (bpy-free; its package __init__ imports bpy)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("allset_marking_menus", ROOT / "src" / "allset" / "marking" / "menus.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    import menu_count
    md, mm, nt = menu_count._load()
    paths = []
    for name, (label, _set, _src, items) in md.MENUS.items():
        paths += [(p, p in mm.MAP) for p, _it in menu_count.leaves(md, mm, items, label)]
    for editor, menus in md.EDITORS.items():
        for title, items in menus:
            paths += [(p, p in mm.MAP) for p, _it in menu_count.leaves(md, mm, items, f"{editor}/{title}")]
    mk = _marking()
    found = pairs(menu_leaves(sorted(set(paths))) + marking_leaves(marking_entries(mk, mm.MAP)) + panel_leaves(md.PANEL))
    for greyed, ok in found:
        print(f"{greyed}  (works as {ok})")
    print(f"menu_consistency: {len(found)} greyed item(s) with a working twin (main / editor / marking / panel menus)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools"))
    sys.exit(main())
