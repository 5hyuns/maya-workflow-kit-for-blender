# SPDX-License-Identifier: GPL-3.0-or-later
"""「Not in Blender」 notices: the near substitute + one line, for Maya menu items (docs/PLAN.md 「Maya 워크플로우
계획」 W3, docs/steps/step_54.md 「계획」 (b)).

One table for every place a Maya item has no Blender equivalent, or a different one: the item's tooltip
(greyed items: ``maya_kit.menu_unavailable``; items with a substitute: ``maya_kit.menu_item``) and the Help
Line, which shows the notice while the tooltip is up — Maya's Help Line shows a menu item's annotation the same
way (research/maya/ui_layout.md:295-298). Keys are Maya menu label paths (``ui/menu_sets.iter_items``).
"""

import time

import bpy

# path: (substitute in Blender, one line). Paths with an action in menu_map.MAP run that substitute.
NOTICES = {
    # Animation (W3: Animation Layers -> NLA, Character Sets -> Keying Sets, Time Editor / Trax -> NLA)
    "Windows/Relationship Editors/Animation Layers": (
        "NLA Editor", "Blender has no animation layers: stack actions as NLA tracks (blend mode per strip)."),
    "Windows/Animation Editors/Trax Editor": (
        "NLA Editor", "Blender has no Trax: clips are actions laid out as NLA strips."),
    "Windows/Animation Editors/Time Editor": (
        "NLA Editor", "Blender has no Time Editor: clips are actions laid out as NLA strips."),
    "Windows/Relationship Editors/Character Sets": (
        "Keying Sets", "Blender has no character sets: a Keying Set (Scene properties) keys a chosen set of channels."),
    "Control/Create Character Set": (
        "Keying Set", "Blender has no character sets: a Keying Set (Scene properties) keys a chosen set of channels."),
    "Key/Create Character Set": (
        "Keying Set", "Blender has no character sets: a Keying Set (Scene properties) keys a chosen set of channels."),
    # Playback (step 56): Blender playback always loops
    **{f"Playback/Playback Looping/{kind}": (
        "Continuous", "Blender playback always loops (no Once / Oscillate).") for kind in ("Once", "Oscillate")},
    # Selection sets (W3: Quick Select Sets -> collections)
    "Create/Sets/Quick Select Set...": (
        "Collection", "Blender has no quick select sets: put the objects in a collection and select it in the Outliner."),
    "Select/Quick Select Sets": (
        "Collection", "Blender has no quick select sets: select a collection's objects from the Outliner."),
    # Dependency graph editors (W3: Node Editor -> none, Hypergraph -> Outliner)
    "Windows/Node Editor": (
        "Shader Editor", "Blender has no node graph of attribute connections: attribute links are drivers "
        "(Expression Editor), material nodes are in the Shader Editor (Hypershade)."),
    "Windows/General Editors/Hypergraph: Hierarchy": (
        "Outliner", "Blender has no Hypergraph: the Outliner shows the hierarchy."),
    "Windows/General Editors/Hypergraph: Connections": (
        "Drivers", "Blender has no connection graph: attribute links are drivers (Expression Editor)."),
    "Windows/General Editors/Namespace Editor": (
        "ns: name prefix", "Blender has no namespaces: Maya Kit keeps them as a \"ns:\" prefix in names."),
    # Rendering (W3: Light Editor -> kit light list, step 64)
    "Windows/Rendering Editors/Light Editor": (
        "Outliner + Properties", "Blender has no Light Editor yet in Maya Kit: select lights in the Outliner, "
        "Power and Color are in the Attribute Editor."),
    # Lights (PLAN W5, research/maya/workflows/render.md:185-187)
    **{f"Create/Lights/{kind} Light": (
        f"{kind} light", "Blender lights always get darker with the square of the distance (no No Decay); "
        "Maya Kit scales the power to the Maya unit.") for kind in ("Point", "Spot", "Area")},
    # Rigging (W3: HumanIK / Quick Rig -> Rigify)
    **{path: ("Rigify", "Blender has no HumanIK / Quick Rig: the bundled Rigify add-on builds a rig from a "
                        "meta-rig fitted to the mesh (Generate Rig).")
       for path in ("Skeleton/HumanIK", "Skeleton/Quick Rig", "Windows/Animation Editors/HumanIK",
                    "Windows/Animation Editors/Quick Rig")},
    # Scene / files (W3: Reference -> link + library override, Set Project -> relative paths)
    "File/Create Reference...": (
        "Link", "Blender references are linked data: Link the file's collection, then Library Override to pose it."),
    "File/Reference Editor": (
        "Outliner: Blender File", "Linked files are listed in the Outliner's Blender File view (relocate / reload there)."),
    "File/Set Project...": (
        "Relative paths", "Blender has no projects: save the file, then textures and caches use paths relative to it (//)."),
    "File/Project Window": (
        "Relative paths", "Blender has no projects: save the file, then textures and caches use paths relative to it (//)."),
    # FX (W3: nucleus -> scene gravity + per-object settings; Gravity field)
    "Modify/Evaluate Nodes/nucleuses": (
        "Scene gravity", "Blender has no nucleus node: gravity is in Scene properties, solver settings are per object."),
    "Fields/Solvers/Gravity": (
        "Wind field", "Blender has no gravity field: a wind field blowing down; the scene's gravity is global "
        "(Scene properties)."),
}

SHOW_SECONDS = 5.0
_current = {"text": "", "until": 0.0}
_status_area = []   # the status bar area, seen while drawing it (global areas aren't in screen.areas)


def notice(path):
    """(substitute, line) for a Maya menu path, or None."""
    return NOTICES.get(path)


def tooltip(path, mapped):
    """Tooltip text for a Maya menu item with a notice (also shows it in the Help Line)."""
    n = NOTICES.get(path)
    if n is None:
        return None
    substitute, line = n
    head = f"Maya: {path}  →  Blender: {substitute}" if mapped else f"Maya: {path} (greyed)  →  {substitute}"
    show(f"{path.rsplit('/', 1)[-1]}: {line}")
    return f"{head}\n{line}"


def show(text):
    """Put ``text`` in the Help Line for a few seconds."""
    _current["text"] = text
    _current["until"] = time.monotonic() + SHOW_SECONDS
    _redraw_status_later()
    if not bpy.app.timers.is_registered(_expire):
        bpy.app.timers.register(_expire, first_interval=SHOW_SECONDS + 0.1)


def current():
    return _current["text"] if time.monotonic() < _current["until"] else ""


def remember_status_area(area):
    if area is not None and (not _status_area or _status_area[0] != area):
        _status_area[:] = [area]


def _redraw_status():
    for area in _status_area:
        try:
            area.tag_redraw()
        except ReferenceError:
            _status_area.clear()
    return None


def _redraw_status_later():
    # Not from inside a tooltip / draw callback: one tick later.
    if not bpy.app.timers.is_registered(_redraw_status):
        bpy.app.timers.register(_redraw_status, first_interval=0.0)


def _expire():
    if not current():
        _current["text"] = ""
        _redraw_status()
        return None
    return 0.5


def register():
    pass


def unregister():
    for fn in (_expire, _redraw_status):
        if bpy.app.timers.is_registered(fn):
            bpy.app.timers.unregister(fn)
    _current.update(text="", until=0.0)
    _status_area.clear()
