"""Step 2: the generated "Maya" keyconfig (docs/steps/step_2.md)."""

import json
import sys
from pathlib import Path

import bpy

import kit

ROOT = Path(__file__).resolve().parent.parent
# Pure-data helpers from the installed extension (imported, not re-registered).
from importlib import import_module  # noqa: E402
ic_data = import_module(kit.MODULE + ".keymap.ic_data")
maya_patches = import_module(kit.MODULE + ".keymap.maya_patches")
mapping = import_module(kit.MODULE + ".keymap.mapping")
patch = import_module(kit.MODULE + ".keymap.patch")

KC_NAME = "Maya"


def _kc():
    return bpy.context.window_manager.keyconfigs[KC_NAME]


def _kmis(km_name, idname, type, value="PRESS", shift=False, ctrl=False, alt=False):
    km = _kc().keymaps[km_name]
    return [k for k in km.keymap_items
            if k.idname == idname and k.type == type and k.value == value
            and k.shift == shift and k.ctrl == ctrl and k.alt == alt and not k.oskey]


def _one(km_name, idname, type, value="PRESS", **mods):
    found = _kmis(km_name, idname, type, value, **mods)
    assert len(found) == 1, f"{km_name}: {idname} {type} {value} {mods} -> {len(found)} items"
    return found[0]


def _any_event(km_name, type, value="PRESS", shift=False, ctrl=False, alt=False):
    km = _kc().keymaps[km_name]
    return [k.idname for k in km.keymap_items if k.active and k.type == type and k.value == value
            and k.shift == shift and k.ctrl == ctrl and k.alt == alt and not k.oskey]


def test_maya_keyconfig_is_active_and_full():
    kcs = bpy.context.window_manager.keyconfigs
    assert kcs.active.name == KC_NAME, kcs.active.name
    n = sum(len(km.keymap_items) for km in _kc().keymaps)
    assert len(_kc().keymaps) >= 240 and n > 2000, (len(_kc().keymaps), n)


# --- selection rules: Shift=toggle, Ctrl=deselect, Ctrl+Shift=add ----------

def test_viewport_click_select():
    for km, value in (("3D View", "CLICK"), ("3D View Tool: Tweak", "PRESS")):
        p = _one(km, "view3d.select", "LEFTMOUSE", value).properties
        assert p.deselect_all and not p.toggle and not p.deselect and not p.extend, km
        assert _one(km, "view3d.select", "LEFTMOUSE", value, shift=True).properties.toggle, km
        assert _one(km, "view3d.select", "LEFTMOUSE", value, ctrl=True).properties.deselect, km
        p = _one(km, "view3d.select", "LEFTMOUSE", value, shift=True, ctrl=True).properties
        assert p.extend and not p.toggle and not p.deselect, km


def test_uv_click_select():
    km = "UV Editor"
    assert _one(km, "uv.select", "LEFTMOUSE", "CLICK", shift=True).properties.toggle
    assert _one(km, "uv.select", "LEFTMOUSE", "CLICK", ctrl=True).properties.deselect
    p = _one(km, "uv.select", "LEFTMOUSE", "CLICK", shift=True, ctrl=True).properties
    assert p.extend and not p.toggle


def test_box_select_modes():
    exact = {(False, False): "SET", (True, False): "XOR", (False, True): "SUB", (True, True): "ADD"}
    # uv/outliner/graph select_box have no XOR mode: Shift adds (workaround).
    no_xor = {**exact, (True, False): "ADD"}
    cases = (("3D View Tool: Select Box", "view3d.select_box", exact),
             ("3D View Tool: Select Box (fallback)", "view3d.select_box", exact),
             ("Image Editor Tool: Uv, Select Box", "uv.select_box", no_xor),
             ("Image Editor Tool: Uv, Select Box (fallback)", "uv.select_box", no_xor),
             ("Outliner", "outliner.select_box", no_xor),
             ("Graph Editor", "graph.select_box", no_xor))
    for km, idname, want in cases:
        for (shift, ctrl), mode in want.items():
            kmi = _one(km, idname, "LEFTMOUSE", "CLICK_DRAG", shift=shift, ctrl=ctrl)
            assert kmi.properties.mode == mode, (km, shift, ctrl, kmi.properties.mode)


def test_outliner_and_graph_click_select():
    # No 'deselect' option on these operators: Ctrl / Ctrl+Shift approximate with toggle.
    for shift, ctrl in ((True, False), (False, True), (True, True)):
        assert _one("Outliner", "outliner.item_activate", "LEFTMOUSE", "CLICK",
                    shift=shift, ctrl=ctrl).properties.extend
        assert _one("Graph Editor", "graph.clickselect", "LEFTMOUSE", "PRESS",
                    shift=shift, ctrl=ctrl).properties.extend
    assert not _one("Outliner", "outliner.item_activate", "LEFTMOUSE", "CLICK").properties.extend
    assert not _one("Graph Editor", "graph.clickselect", "LEFTMOUSE", "PRESS").properties.extend


# --- 4/5/6/7, F8 ------------------------------------------------------------

def test_display_keys():
    for key, mode in maya_patches.DISPLAY_KEYS:
        assert _one("3D View", "maya_kit.display_mode", key).properties.mode == mode
        assert _any_event("Object Non-modal", key) == [], key
    assert _one("Object Non-modal", "object.editmode_toggle", "F8")


# --- Ctrl+G -----------------------------------------------------------------

def test_group_keys():
    for km in ("Object Mode", "Outliner"):
        assert _any_event(km, "G", ctrl=True) == ["maya_kit.group"], km


# --- Space free, playback on Alt+V ------------------------------------------

def test_space_is_free_for_hotbox():
    for km in ("Window", "Screen", "Frames", "3D View", "3D View Generic", "Object Mode",
               "Object Non-modal", "Mesh", "Graph Editor", "Dopesheet", "Outliner"):
        assert _any_event(km, "SPACE") == [], (km, _any_event(km, "SPACE"))
    assert _one("Frames", "screen.animation_play", "V", alt=True)
    assert not _one("Frames", "screen.frame_jump", "V", alt=True, shift=True).properties.end


# --- conflicts ---------------------------------------------------------------

def _conflicts(data):
    out = set()
    for km_name, _args, content in data:
        for pair in patch.conflicts(content["items"]):
            out.add(patch.conflict_signature(km_name, pair))
    return out


def test_no_new_conflicts_within_keymaps():
    base = _conflicts(ic_data.generate())
    maya = _conflicts(maya_patches.apply(ic_data.generate()))
    new = sorted(maya - base, key=str)
    assert not new, "new conflicts:\n" + "\n".join(map(str, new))


# Keymaps that can handle an event in the same place as the patched keymap.
_VIEW3D_STACK = ("Window", "Screen", "Frames", "3D View", "3D View Generic", "Object Mode",
                 "Object Non-modal", "Mesh", "Curve", "Curves", "Armature", "Pose", "Metaball",
                 "Lattice", "Particle", "Font", "Sculpt", "Weight Paint", "Vertex Paint",
                 "Image Paint", "Grease Pencil")
# Object Mode items only run in object mode, where other mode keymaps are inactive.
_OBJECT_MODE_STACK = ("Window", "Screen", "Frames", "3D View", "3D View Generic",
                      "Object Mode", "Object Non-modal")
_STACKS = {"3D View": _VIEW3D_STACK, "Object Mode": _OBJECT_MODE_STACK,
           "Object Non-modal": _VIEW3D_STACK,
           "Outliner": ("Window", "Screen", "Outliner", "View2D", "View2D Buttons List"),
           "Frames": None}  # None = every non-modal keymap (Frames is in most editors)


def test_added_bindings_not_shadowed():
    data = maya_patches.apply(ic_data.generate())
    assert maya_patches.ADDED, "no added bindings recorded"
    problems = []
    for km, idname, ev, _props, shadows in maya_patches.ADDED:
        stack = _STACKS[km]
        k = patch.event_key(ev)
        for km_name, args, content in data:
            if args.get("modal") or (stack is not None and km_name not in stack):
                continue
            if km_name in shadows:  # declared intentional (maya_patches._add)
                continue
            for it in content["items"]:
                if patch.event_key(it[1]) == k and not (km_name == km and it[0] == idname):
                    problems.append(f"{km} {idname} {ev} <-> {km_name} {it[0]}")
    assert not problems, "\n".join(problems)


# --- mapping table ------------------------------------------------------------

def test_mapping_rows_are_bound():
    hk_path = ROOT / "research" / "maya" / "hotkeys_default.json"
    hotkeys = json.loads(hk_path.read_text(encoding="utf-8"))["hotkeys"]
    assert len(hotkeys) == 468, len(hotkeys)
    kd = patch.KeyconfigData(maya_patches.apply(ic_data.generate()))
    checked, bad = 0, []
    for hk in hotkeys:
        mapping.maya_event(hk)  # every Maya key converts
        entry = mapping.entry_for(hk)
        if hk["platform"] != "mac-only" and entry and entry["check"]:
            checked += 1
            if not mapping.check_entry(kd, hk, entry):
                bad.append(hk["display"])
    assert checked >= 20 and not bad, (checked, bad)


def test_disable_restores_previous_keyconfig():
    kcs = bpy.context.window_manager.keyconfigs
    kit.disable()
    try:
        assert KC_NAME not in kcs, [k.name for k in kcs]
        assert kcs.active is not None and kcs.active.name != KC_NAME
    finally:
        kit.enable()
    assert kcs.active.name == KC_NAME
