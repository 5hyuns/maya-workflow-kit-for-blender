# SPDX-License-Identifier: GPL-3.0-or-later
""" notices: the near substitute + one line, for Maya menu items ( 「Maya 워크플로우
계획」 W3,  「계획」 (b)).

One table for every place a Maya item has no Blender equivalent, or a different one: the item's tooltip
(greyed items: ``maya_kit.menu_unavailable``; items with a substitute: ``maya_kit.menu_item``) and the Help
Line, which shows the notice while the tooltip is up — Maya's Help Line shows a menu item's annotation the same
way (). Keys are Maya menu label paths (``ui/menu_sets.iter_items``).
"""

import time

import bpy

# path: (substitute in Blender, one line). Paths with an action in menu_map.MAP run that substitute.
NOTICES = {
    # Pivot / snapping (step 59, )
    "Modify/Make Live": (
        "Face snapping", "Blender snaps onto every surface, not only the live one: Make Live turns face "
        "snapping on and names the surface in the Status Line."),
    "Modify/Bake Pivot": (
        "Pivot orientation", "Blender has one pivot (the origin), so only the pivot orientation is baked into "
        "Rotate; the position already is the object's pivot."),
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
    # Rendering (W3: Light Editor -> kit light list, step 67)
    "Windows/Rendering Editors/Light Editor": (
        "kit Light Editor", "Blender has no Light Editor: Maya Kit lists the scene lights in a 3D View sidebar tab "
        "(Exposure is part of Power)."),
    "Windows/Rendering Editors/Hypershade": (
        "Shader Editor + kit list", "Blender has no Hypershade: the Shader Editor is the graph, its Hypershade sidebar "
        "tab the browser (add nodes with Shift+A)."),
    **{f"Render/{item}": (
        "Command line", "Blender has no batch render queue: render frames with blender -b file.blend -a "
        "(or Render Sequence here).") for item in ("Batch Render", "Cancel Batch Render", "Show Batch Render")},
    "Render/IPR Render Current Frame": (
        "Viewport Rendered", "Blender's IPR is the viewport in Rendered shading (Render Region: Ctrl+B)."),
    # FX (step 68, , )
    **{path: ("one-point mesh emitter", "Blender particles come from a mesh: Maya Kit makes a one-point mesh emitter1 "
              "with the particles, sized in Maya units.")
       for path in ("nParticles/Create Emitter", "nParticles/Create Emitter#2")},
    "nCloth/Create nCloth": (
        "Cloth modifier", "Blender cloth simulates real sizes: Maya Kit scales collision distances, stiffness and gravity "
        "so one unit moves like Maya's (nucleus Space Scale in the Attribute Editor)."),
    **{f"nCache/{item}": (
        "Baked caches", "Blender always plays a baked cache: Delete Cache to simulate again.")
       for item in ("Enable All Caches on Selected", "Disable All Caches on Selected")},
    # Lights (PLAN W5, )
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
    # UV (step 66): Blender cuts / sews UVs in the UV Editor only
    "UV/3D Cut and Sew UV Tool": (
        "Cut / Sew", "Blender has no 3D cut-and-sew tool (not in Maya Kit yet): select edges in the 3D View, then Cut (Shift+X) / "
        "Sew (Shift+S) in the UV Editor."),
    "UV/Auto Seams": (
        "Smart UV Project", "Blender has no automatic seams: UV > Automatic (Smart UV Project) cuts by angle."),
    # Modeling (step 64): the Crease Tool works, with Blender's 0-1 crease underneath
    "Mesh Tools/Crease Tool": (
        "Edge crease", "Blender stores creases as 0-1 (1 = fully sharp). The kit shows Maya's value (sharp for that "
        "many smooth levels) and stores sqrt(value / 10); see it with 3 (smooth mesh preview)."),
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


# Notices of kit panel rows that are not Maya menu items (e.g. Modeling Toolkit options, step 63),
# filled by the panels' register(); same (substitute, line) form.
PANEL_NOTICES = {}


def tooltip(path, mapped):
    """Tooltip text for a Maya menu item with a notice (also shows it in the Help Line)."""
    n = NOTICES.get(path) or PANEL_NOTICES.get(path)
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
