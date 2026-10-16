"""Helpers shared by tests (runs inside Blender)."""

import os

import addon_utils
import bpy

MODULE = os.environ.get("MAYA_KIT_MODULE", "bl_ext.user_default.maya_kit")


def _raise(ex):
    raise ex


def enable():
    mod = addon_utils.enable(MODULE, default_set=True, handle_error=_raise)
    assert mod is not None, f"addon_utils.enable({MODULE!r}) returned None"
    assert MODULE in bpy.context.preferences.addons, f"{MODULE} not in preferences.addons"
    return mod


def disable():
    addon_utils.disable(MODULE, default_set=True, handle_error=_raise)
    assert MODULE not in bpy.context.preferences.addons, f"{MODULE} still in preferences.addons"


def is_enabled():
    return MODULE in bpy.context.preferences.addons


# RNA types an add-on typically extends with properties.
_PROP_OWNERS = ("Scene", "Object", "WindowManager", "ViewLayer", "Mesh", "Collection",
                "SpaceView3D", "ToolSettings", "Preferences")


def snapshot():
    """Global state an add-on can leak after unregister."""
    snap = {}
    snap["types"] = sorted(dir(bpy.types))
    snap["props"] = {t: sorted(getattr(bpy.types, t).bl_rna.properties.keys())
                     for t in _PROP_OWNERS}
    # Python-level attributes too: bpy.props assigned to a type show up here.
    snap["type_attrs"] = {t: sorted(dir(getattr(bpy.types, t))) for t in _PROP_OWNERS}
    snap["ops"] = sorted(dir(bpy.ops))

    kcs = bpy.context.window_manager.keyconfigs
    snap["keyconfigs"] = sorted(k.name for k in kcs)
    snap["active_keyconfig"] = [kcs.active.name if kcs.active else None]
    kc = kcs.addon
    snap["addon_keymaps"] = sorted(
        (km.name, kmi.idname, kmi.type, kmi.value, kmi.shift, kmi.ctrl, kmi.alt)
        for km in (kc.keymaps if kc else ()) for kmi in km.keymap_items)

    snap["handlers"] = {
        name: [getattr(f, "__qualname__", repr(f)) for f in getattr(bpy.app.handlers, name)]
        for name in dir(bpy.app.handlers)
        if isinstance(getattr(bpy.app.handlers, name), list)}

    # UI classes extended with .append()/.prepend() keep their callbacks in draw._draw_funcs.
    snap["ui_extensions"] = {}
    for name in dir(bpy.types):
        draw = getattr(getattr(bpy.types, name), "draw", None)
        funcs = getattr(draw, "_draw_funcs", None)
        if funcs:
            snap["ui_extensions"][name] = [getattr(f, "__qualname__", repr(f)) for f in funcs]

    snap["addons"] = sorted(bpy.context.preferences.addons.keys())
    # Blender preferences the add-on may change (navigation preset, step 4).
    prefs = bpy.context.preferences
    snap["prefs_inputs"] = _rna_values(prefs.inputs)
    snap["prefs_view"] = _rna_values(prefs.view)
    return snap


def _rna_values(struct):
    out = {}
    for prop in struct.bl_rna.properties:
        if prop.identifier == "rna_type" or prop.type in {'POINTER', 'COLLECTION'}:
            continue
        value = getattr(struct, prop.identifier)
        if not isinstance(value, (str, int, float, bool)):
            value = tuple(value) if hasattr(value, "__iter__") else value
        out[prop.identifier] = [repr(value)]
    return out


def diff(a, b):
    """Human-readable list of differences between two snapshots."""
    out = []
    for key in sorted(set(a) | set(b)):
        va, vb = a.get(key), b.get(key)
        if va == vb:
            continue
        if isinstance(va, dict) and isinstance(vb, dict):
            for sub in sorted(set(va) | set(vb)):
                if va.get(sub) != vb.get(sub):
                    out.append(_list_diff(f"{key}.{sub}", va.get(sub) or [], vb.get(sub) or []))
        else:
            out.append(_list_diff(key, va or [], vb or []))
    return out


def _list_diff(label, a, b):
    sa, sb = set(map(repr, a)), set(map(repr, b))
    added, removed = sorted(sb - sa), sorted(sa - sb)
    if not added and not removed:
        return f"{label}: order/duplicates changed"
    return f"{label}: +{added} -{removed}"
