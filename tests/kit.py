"""Helpers shared by tests (runs inside Blender)."""

import os
import sys

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
                "SpaceView3D", "ToolSettings", "Preferences", "Bone", "PoseBone")


def _timeline_classes():
    from bl_ui import space_time
    if hasattr(space_time, "TIME_HT_editor_buttons"):
        return space_time.TIME_HT_editor_buttons, space_time.TIME_MT_editor_menus
    from bl_ui import space_dopesheet   # Blender 5.x: the Timeline is a Dope Sheet mode
    return space_dopesheet.DOPESHEET_HT_editor_buttons, space_dopesheet.DOPESHEET_MT_editor_menus


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
    # The class's own draw stays as the first entry after append()+remove(); like
    # bpy_types._GenericUI.is_extended, a list holding only that is not an extension.
    snap["ui_extensions"] = {}
    for name in dir(bpy.types):
        draw = getattr(getattr(bpy.types, name), "draw", None)
        funcs = getattr(draw, "_draw_funcs", None)
        if funcs and len(funcs) > 1:
            snap["ui_extensions"][name] = [getattr(f, "__qualname__", repr(f)) for f in funcs]
    # Methods the add-on swaps on Blender UI classes (step 7: Maya top bar).
    topbar = bpy.types.TOPBAR_HT_upper_bar
    # step 20: Time / Range Slider in the Timeline header (Blender 5.x: the Dope Sheet's, step 53)
    time_buttons, time_menus = _timeline_classes()
    snap["ui_methods"] = [f"{f.__module__}.{f.__qualname__}" for f in
                          (topbar.draw_left, topbar.draw_right,
                           bpy.types.IMAGE_HT_header.draw, bpy.types.IMAGE_HT_tool_header.draw,
                           time_buttons.draw_header)]
    # step 37: Maya panel menus replace the 3D View header menus (a class attribute while enabled).
    snap["ui_methods"].append("VIEW3D_MT_editor_menus.draw_collapsible overridden: "
                              f"{'draw_collapsible' in bpy.types.VIEW3D_MT_editor_menus.__dict__}")
    # step 49: Tool Box (toolbar draw filter), status bar row, dock-only sidebar polls.
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active
    snap["ui_methods"] += [f"VIEW3D_PT_tools_active.{n} own: {VIEW3D_PT_tools_active.__dict__.get(n)!r}"
                           for n in ("draw", "tools_from_context")]
    # step 59: Move/Rotate/Scale ToolDefs carry the Maya manipulator's gizmo group while enabled.
    from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
    for mode in ("OBJECT", "EDIT_MESH"):
        snap["ui_methods"] += sorted(
            f"tool {mode} {it.idname}: {it.widget}"
            for it, _i in ToolSelectPanelHelper._tools_flatten_with_tool_index(VIEW3D_PT_tools_active._tools[mode])
            if it is not None and not callable(it) and it.idname in ("builtin.move", "builtin.rotate", "builtin.scale"))
    snap["ui_methods"].append(f"STATUSBAR_HT_header.draw: {bpy.types.STATUSBAR_HT_header.draw!r}")
    # step 50: Maya Outliner header, timeline menus moved into the Range Slider's preferences menu
    snap["ui_methods"].append(f"OUTLINER_HT_header.draw: {bpy.types.OUTLINER_HT_header.draw!r}")
    snap["ui_methods"].append("TIME_MT_editor_menus.draw_collapsible overridden: "
                              f"{'draw_collapsible' in time_menus.__dict__}")
    snap["panel_polls"] = sorted(
        f"{c.__name__}: {c.__dict__.get('poll')!r} registered={c.is_registered}"
        for c in _all_panels() if getattr(c, "bl_space_type", None) == 'VIEW_3D'
        and not c.__name__.startswith("MAYAKIT_"))
    snap["sys_modules"] = sorted(m for m in sys.modules if m == "maya" or m.startswith("maya."))

    snap["addons"] = sorted(bpy.context.preferences.addons.keys())
    # Blender preferences the add-on may change (navigation preset, step 4).
    prefs = bpy.context.preferences
    snap["prefs_inputs"] = _rna_values(prefs.inputs)
    snap["prefs_view"] = _rna_values(prefs.view)
    snap["prefs_edit"] = _rna_values(prefs.edit)   # step 30: undo steps
    # step 44: aliased wires (use_overlay_smooth_wire / use_edit_mode_smooth_wire)
    snap["prefs_system_wire"] = [prefs.system.use_overlay_smooth_wire, prefs.system.use_edit_mode_smooth_wire]
    # step 42: the Maya theme is restored on disable; fonts/styles must not leak either.
    snap["theme"] = [_struct_hash(prefs.themes[0])]
    snap["ui_styles"] = {k: [v] for k, v in _walk(prefs.ui_styles[0]).items()}
    return snap


def _all_panels(cls=None):
    for sub in (cls or bpy.types.Panel).__subclasses__():
        yield sub
        yield from _all_panels(sub)


def _walk(struct, prefix="", out=None, depth=0):
    """All non-pointer RNA values under ``struct`` (nested pointers/collections followed)."""
    out = {} if out is None else out
    for prop in struct.bl_rna.properties:
        ident = prop.identifier
        if ident == "rna_type" or depth > 6:
            continue
        value = getattr(struct, ident)
        key = f"{prefix}{ident}"
        if prop.type == 'POINTER':
            if value is not None:
                _walk(value, key + ".", out, depth + 1)
        elif prop.type == 'COLLECTION':
            for i, item in enumerate(value):
                _walk(item, f"{key}[{i}].", out, depth + 1)
        else:
            if not isinstance(value, (str, int, float, bool)):
                value = tuple(round(v, 5) if isinstance(v, float) else v for v in value)
            elif isinstance(value, float):
                value = round(value, 5)
            out[key] = repr(value)
    return out


def _struct_hash(struct):
    import hashlib
    items = sorted(_walk(struct).items())
    return hashlib.sha1(repr(items).encode()).hexdigest()


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
