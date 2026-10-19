# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya ⇄ Blender switch and the complete revert.

The extension stays enabled; "Maya mode" is the set of sub-packages ``__init__.MODE``
(keymap, UI, operators, theme, ...). Switching off unregisters them, which already puts
back everything they changed (``tests/test_enable_disable.py`` enforces it), switching on
registers them again. Only this module and the preferences stay registered in Blender
mode, so the switch is always there: a small toggle at the right of the top bar, the
add-on preferences, Edit (Blender) / Windows > Settings/Preferences (Maya) menu items that
the menu search finds, and Ctrl+Alt+Shift+M (free in Blender, Industry Compatible and
Maya's factory hotkeys, *.json, ).

Complete revert: before the first switch on, a snapshot of everything the kit may change in
the preferences (``FOOTPRINT``, the theme and UI styles as XML, the active keyconfig) is
written to the extension's user folder. Switching off compares and puts back those values,
then deletes the snapshot; values outside the footprint (other add-ons, the user's own
keymap edits, settings changed while in Maya mode) are left alone. A snapshot found at start
while Maya mode is off means a switch was interrupted: it is restored then.

Layout: switching on in a file that has no Maya layout appends the template's layout
workspace (named "Maya-style") and activates it; switching off goes back to the previous
workspace and deletes the appended one. Scenes and objects are never touched.
"""

import json
import os

import bpy

_ADDON = __package__
SNAPSHOT = "switch_snapshot.json"
WORKSPACE = "Maya-style"


def keymap_name():
    from .keymap import KEYCONFIG_NAME
    return KEYCONFIG_NAME


TEMPLATE_WORKSPACE = "General"
PREV_KEY = "allset_switch_prev"
SHORTCUT = ('M', {"ctrl": True, "alt": True, "shift": True})

# Every preference the kit writes (prefs_preset.GROUPS, set_runtime callers, panel menus).
FOOTPRINT = (
    "inputs.view_rotate_method", "inputs.use_rotate_around_active", "inputs.use_mouse_depth_navigate",
    "inputs.use_zoom_to_mouse", "inputs.use_auto_perspective", "inputs.view_zoom_method",
    "inputs.view_zoom_axis", "inputs.invert_mouse_zoom", "inputs.invert_zoom_wheel",
    "edit.undo_steps", "edit.use_keyframe_insert_available", "view.show_splash", "view.ui_scale", "view.font_path_ui", "view.gizmo_size",
    "system.use_overlay_smooth_wire", "system.use_edit_mode_smooth_wire", "system.use_region_overlap",
)
_THEME_MAP = (("themes[0]", "Theme"), ("ui_styles[0]", "ThemeStyle"))


# --- snapshot -----------------------------------------------------------------------------------

def user_folder(create=False):
    try:
        return bpy.utils.extension_path_user(_ADDON, create=create)
    except ValueError:   # legacy add-on build
        return bpy.utils.user_resource('CONFIG', path="allset", create=create)


def snapshot_path(create=False):
    return os.path.join(user_folder(create=create), SNAPSHOT)


def has_snapshot():
    return os.path.isfile(snapshot_path())


def _resolve(prefs, path):
    owner, attr = path.split(".")
    return getattr(prefs, owner), attr


def _rna_xml():
    try:
        import rna_xml
    except ImportError:   # Blender 5.x (step 53)
        import _rna_xml as rna_xml
    return rna_xml


def _theme_xml(prefs):
    """Theme + UI styles as XML text (the same dump the theme module backs up)."""
    import tempfile
    rna_xml = _rna_xml()
    fd, path = tempfile.mkstemp(suffix=".xml")
    os.close(fd)
    try:
        rna_xml.xml_file_write(prefs, path, _THEME_MAP)
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    finally:
        os.remove(path)


def take_snapshot(prefs=None):
    """The user's values before Maya mode (kept until the switch back off has restored them)."""
    prefs = prefs or bpy.context.preferences
    kcs = bpy.context.window_manager.keyconfigs
    data = {
        "version": 1,
        "blender": bpy.app.version_string,
        "keyconfig": prefs.keymap.active_keyconfig or (kcs.active.name if kcs.active else ""),
        "values": {},
        "theme_xml": _theme_xml(prefs),
        "theme_filepath": prefs.themes[0].filepath,
        "theme_name": prefs.themes[0].name,
        "addons": sorted(a.module for a in prefs.addons),
    }
    for path in FOOTPRINT:
        owner, attr = _resolve(prefs, path)
        value = getattr(owner, attr)
        data["values"][path] = value if isinstance(value, (str, int, float, bool)) else list(value)
    with open(snapshot_path(create=True), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    return data


def forget_snapshot():
    try:
        os.remove(snapshot_path())
    except OSError:
        pass


def maya_state_saved(prefs=None):
    """The preferences Blender started with are in their Maya state (it quit in Maya mode): the
    stored keyconfig name is "Maya". After a disable the user's keyconfig name is stored again."""
    prefs = prefs or bpy.context.preferences
    return prefs.keymap.active_keyconfig == keymap_name()


def maya_state_left(prefs=None):
    """The preferences still show Maya mode (stored keyconfig "Maya-style" or the Maya theme) although Maya mode is
    off: a switch to Blender was interrupted. Otherwise a snapshot found at start is stale (step 115)."""
    prefs = prefs or bpy.context.preferences
    from .theme import THEME_NAME
    return maya_state_saved(prefs) or prefs.themes[0].name == THEME_NAME


def read_snapshot():
    try:
        with open(snapshot_path(), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def kit_values(prefs=None):
    """The values Maya mode writes (prefs_preset groups, density, font): a footprint value that
    still equals one of these was not put back by its module (a crash, a lost backup)."""
    out = {}
    try:
        from . import prefs_preset
    except ImportError:
        return out
    for group in prefs_preset.GROUPS:
        try:
            preset = prefs_preset.preset_of(group)
        except Exception:
            continue
        for path, value in preset:
            out[path] = value
    return out


def restore_snapshot(prefs=None, delete=True):
    """Fallback after the Maya mode modules have restored their own backups: footprint values,
    theme and keyconfig still in their Maya state go back to the snapshot. Values the user set
    (differing from the Maya value) are left alone, so a newer choice is never overwritten.
    Returns the paths put back."""
    prefs = prefs or bpy.context.preferences
    data = read_snapshot()
    if data is None:
        return None
    maya = kit_values(prefs)
    changed = []
    for path, value in data.get("values", {}).items():
        try:
            owner, attr = _resolve(prefs, path)
            cur = getattr(owner, attr)
            cur = cur if isinstance(cur, (str, int, float, bool)) else list(cur)
            kit = maya.get(path, cur)        # paths without a fixed Maya value (gizmo size): restore
            kit = kit if isinstance(kit, (str, int, float, bool)) else list(kit)
            if cur != value and cur == kit:
                setattr(owner, attr, value)
                changed.append(path)
        except (AttributeError, TypeError, ValueError):
            pass
    xml = data.get("theme_xml")
    from .theme import THEME_NAME
    if xml and prefs.themes[0].name == THEME_NAME:
        import tempfile
        from bl_ui.space_userpref import USERPREF_MT_interface_theme_presets as presets
        fd, path = tempfile.mkstemp(suffix=".xml")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(xml)
            _rna_xml().xml_file_run(prefs, path, _THEME_MAP, secure_types=presets.preset_xml_secure_types)
        finally:
            os.remove(path)
        prefs.themes[0].filepath = data.get("theme_filepath", "")
        name = data.get("theme_name") or "Default"
        prefs.themes[0].name = "Default" if name == THEME_NAME else name
        changed.append("theme")
    kcs = bpy.context.window_manager.keyconfigs
    name = data.get("keyconfig") or ""
    maya_kc = keymap_name()
    if name and name != maya_kc:
        if kcs.get(name) is not None and (kcs.active is None or kcs.active.name == maya_kc):
            kcs.active = kcs.get(name)
            changed.append("keyconfig")
        if prefs.keymap.active_keyconfig == maya_kc:
            # the stored name still says "Maya" while Blender fell back to its keyconfig by itself
            # (Maya mode ended without a switch): the next start would look for "Maya" again
            try:
                prefs.keymap.active_keyconfig = name
                changed.append("keymap.active_keyconfig")
            except (AttributeError, TypeError):
                pass
    if changed:
        prefs.is_dirty = True
    if delete:
        try:
            os.remove(snapshot_path())
        except OSError:
            pass
    return changed


def user_disabling():
    """True while the user disables or removes the extension (Preferences checkbox, Extensions Remove): the
    ``addon_utils.disable`` call that unregisters us has ``default_set=True``. Quitting (``bpy.utils._on_exit`` →
    ``disable_all``), script reloads and extension updates disable with ``default_set=False`` (Blender 4.5,
    $S/modules/addon_utils.py:538, $S/addons_core/bl_pkg/bl_extension_ops.py:681; )."""
    import sys
    frame = sys._getframe(1)
    while frame is not None:
        code = frame.f_code
        if code.co_name == "disable" and code.co_filename.replace("\\", "/").endswith("/addon_utils.py"):
            return frame.f_locals.get("module_name") == _ADDON and frame.f_locals.get("default_set") is True
        frame = frame.f_back
    return False


# --- mode on / off ------------------------------------------------------------------------------

def _prefs_addon():
    from . import preferences
    return preferences.get()


def is_on():
    try:
        return bool(_prefs_addon().maya_mode)
    except KeyError:
        return False


def _template_blend():
    from .app_template import SOURCE_DIR
    return os.path.join(SOURCE_DIR, "startup.blend")


def _window_override(window):
    return {"window": window, "screen": window.screen}


def is_maya_workspace(ws):
    """A workspace that already is the Maya layout (appended by the switch or a Allset file)."""
    if ws is None:
        return False
    if PREV_KEY in ws:
        return True
    for screen in ws.screens:
        for area in screen.areas:
            space = area.spaces.active
            if area.type == 'IMAGE_EDITOR' and getattr(space, "mask", None) is not None \
                    and space.mask.name.startswith(".Allset"):
                return True
    return False


def _fit_views(ws, scene):
    """The template views are in cm (Maya unit 0.01 BU): keep them on the same Maya-unit scene."""
    from .operators import units
    ratio = units.maya_unit(scene) / 0.01
    for screen in ws.screens:
        for area in screen.areas:
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                # The tool header is Maya's panel toolbar in views with a header (step 113); the Tool Box column has
                # neither. Set it explicitly: an appended screen came back with it shown (checked, step 60).
                space.show_region_tool_header = space.show_region_header
                for key, value in units.clip(scene).items():
                    setattr(space, key, value)
                space.overlay.grid_scale = units.grid_scale(scene)
                if abs(ratio - 1.0) > 1e-9:
                    for rv3d in (space.region_3d, *space.region_quadviews):
                        rv3d.view_location = rv3d.view_location * ratio
                        rv3d.view_distance *= ratio


def enter_layout(window):
    """Append and activate the Maya layout workspace in ``window`` (unless it already is one)."""
    if window is None or is_maya_workspace(window.workspace):
        return None
    prev = window.workspace.name
    before = set(bpy.data.workspaces)
    with bpy.context.temp_override(**_window_override(window)):
        bpy.ops.workspace.append_activate(idname=TEMPLATE_WORKSPACE, filepath=_template_blend())
    new = [ws for ws in bpy.data.workspaces if ws not in before]
    ws = new[0] if new else window.workspace
    ws[PREV_KEY] = prev
    ws.name = WORKSPACE
    window.workspace = ws
    _mark_strips(ws)
    _fit_views(ws, window.scene)
    return ws


STRIP_MASKS = (".AllsetStrip", ".AllsetShelf")   # ui/shelf.MARKER, SHELF_MARKER (top to bottom)
MASK_KEY = "allset_switch_masks"


def _mark_strips(ws):
    """Appending a workspace doesn't bring the Masks its Image Editors point to, and those mark the
    Status Line row and the Shelf row (ui/shelf.is_strip, checked): load them and point the two
    top Image Editors (Status Line above the Shelf) at them again."""
    missing = [m for m in STRIP_MASKS if m not in bpy.data.masks]
    if missing:
        with bpy.data.libraries.load(_template_blend(), link=False) as (src, dst):
            dst.masks = [m for m in missing if m in src.masks]
        ws[MASK_KEY] = missing
    for screen in ws.screens:
        rows = sorted((a for a in screen.areas if a.type == 'IMAGE_EDITOR'), key=lambda a: -a.y)
        for area, name in zip(rows, STRIP_MASKS):
            mask = bpy.data.masks.get(name)
            if mask is not None:
                area.spaces.active.mask = mask


def leave_layout(window):
    """Back to the workspace from before ``enter_layout``; the appended one is deleted."""
    if window is None:
        return False
    ws = window.workspace
    if ws is None or PREV_KEY not in ws:
        return False
    prev = bpy.data.workspaces.get(ws[PREV_KEY]) or next(
        (w for w in bpy.data.workspaces if w != ws and not is_maya_workspace(w)), None)
    if prev is None:
        return False
    window.workspace = prev
    added = list(ws.get(MASK_KEY, ()))
    with bpy.context.temp_override(**_window_override(window), workspace=ws):
        try:
            bpy.ops.workspace.delete()
        except RuntimeError:
            pass
    for name in added:                       # masks the switch loaded go too: the file is as before
        mask = bpy.data.masks.get(name)
        if mask is not None:
            bpy.data.masks.remove(mask)
    return True


def _windows():
    wm = bpy.context.window_manager
    return list(wm.windows) if wm is not None else []


def _mode_modules():
    from . import MODE
    return MODE


def register_mode():
    for mod in _mode_modules():
        mod.register()


def unregister_mode():
    for mod in reversed(_mode_modules()):
        mod.unregister()


def set_mode(on, layout=True, theme=True):
    """Switch Maya mode on / off now (no restart). The open file's scenes are not touched. ``theme=False`` leaves
    the theme option as it is (tests: Maya mode as a plain enable gave it before step 115)."""
    prefs = _prefs_addon()
    if on == bool(prefs.maya_mode) and (on == _registered[0]):
        return False
    if on:
        if not has_snapshot():
            take_snapshot()
        prefs.maya_mode = True
        if not _registered[0]:
            register_mode()
            _registered[0] = True
        from . import keymap
        keymap.activate()
        # Maya mode = Maya keymap, layout, menus *and* look (the switch's own description): the Maya theme comes on
        # with it (the user's theme is in the snapshot and comes back on the switch to Blender; step 113 — Blender's
        # theme made the Maya top area read as Blender, user report 2026-10-19).
        if theme and not prefs.maya_theme:
            prefs.maya_theme = True
        if layout and not bpy.app.background:
            for window in _windows()[:1]:
                enter_layout(window)
    else:
        if layout:
            for window in _windows():
                leave_layout(window)
        prefs.maya_mode = False
        if _registered[0]:
            unregister_mode()
            _registered[0] = False
        restore_snapshot()
        prefs["maya_theme"] = False   # theme restored above; no update callback (the theme module is unregistered)
        from .theme import forget_backup
        forget_backup()        # the theme module keeps it across quits; a switch to Blender is final
    bpy.context.preferences.is_dirty = True
    _redraw()
    return True


_registered = [False]


def _redraw():
    for window in _windows():
        for area in window.screen.areas:
            area.tag_redraw()


def finish_interrupted():
    """Maya mode is off but its snapshot is still there: Blender stopped during a switch to Blender (or quit
    without saving the preferences after it). Put the user's values back; nothing is saved (step 115: the kit never
    saves the preferences by itself) — Blender's Auto-Save Preferences or the user does. The restore only touches
    values still in their Maya state, so it is repeated at each start until it finds nothing left to restore, and
    only then is the snapshot dropped."""
    changed = restore_snapshot(delete=False)
    if changed is not None and not changed:
        forget_snapshot()


def restore_blender(context=None):
    """Everything back as before Allset ("Restore Blender Settings"): Maya mode off, the
    Make Blender Maya options off, the layout template removed, the snapshot applied."""
    prefs = _prefs_addon()
    if prefs.maya_mode:
        set_mode(False)
    for name in ("maya_theme", "maya_hide_splash", "maya_density", "maya_font", "maya_wire",
                 "start_in_maya_layout"):
        # option off without its update callbacks running against unregistered modules
        prefs[name] = False
    from . import app_template
    try:
        if app_template.is_installed():
            app_template.remove()
    except (OSError, RuntimeError):
        pass
    restore_snapshot()
    from .theme import forget_backup
    forget_backup()
    bpy.context.preferences.is_dirty = True


# --- UI -----------------------------------------------------------------------------------------

_pending = []


def _apply_pending():
    while _pending:
        on, layout = _pending.pop(0)
        try:
            set_mode(on, layout=layout)
        except Exception as ex:   # never leave a timer raising forever
            print("Allset: switch failed:", ex)
            import traceback
            traceback.print_exc()
    return None


def request(on, layout=True):
    """Switch from a timer, after the calling operator / draw has finished."""
    _pending.append((on, layout))
    if not bpy.app.timers.is_registered(_apply_pending):
        bpy.app.timers.register(_apply_pending, first_interval=0.0)


class ALLSET_OT_switch_mode(bpy.types.Operator):
    """Switch between Maya mode (Maya keymap, layout, menus and theme) and plain Blender.
    Nothing in the open file's scenes changes; switching back to Blender restores your settings"""
    bl_idname = "allset.switch_mode"
    bl_label = "Switch Maya / Blender"
    bl_options = {'REGISTER'}

    mode: bpy.props.EnumProperty(
        name="Mode", items=(('TOGGLE', "Toggle", ""), ('MAYA', "Maya", ""), ('BLENDER', "Blender", "")),
        default='TOGGLE', options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, props):
        if props.mode == 'MAYA':
            return "Switch to Maya mode: Maya keymap, layout, menus and theme (Ctrl+Alt+Shift+M)"
        if props.mode == 'BLENDER':
            return "Switch back to plain Blender: your keymap, theme and preferences come back (Ctrl+Alt+Shift+M)"
        return "Switch between Maya mode and plain Blender (Ctrl+Alt+Shift+M)"

    def execute(self, context):
        on = (not is_on()) if self.mode == 'TOGGLE' else self.mode == 'MAYA'
        request(on)
        self.report({'INFO'}, "Maya mode" if on else "Blender mode")
        return {'FINISHED'}


class ALLSET_OT_restore_blender(bpy.types.Operator):
    """Turn Maya mode off and put every preference Allset changed back as it was before
    (keymap, theme, navigation, splash, UI scale), remove the Maya layout template"""
    bl_idname = "allset.restore_blender"
    bl_label = "Restore Blender Settings"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(
            self, event, title="Restore Blender Settings",
            message="Maya mode off, Maya options off, Maya layout template removed")

    def execute(self, context):
        if is_on():
            # unregistering the mode from inside an operator is fine here: this class stays
            request(False)
        bpy.app.timers.register(lambda: (restore_blender(), None)[1], first_interval=0.05)
        self.report({'INFO'}, "Blender settings restored")
        return {'FINISHED'}


def draw_topbar_switch(self, context):
    """Top bar, right: [Maya | Blender] (both modes)."""
    region = context.region
    if region is None or region.alignment != 'RIGHT':
        return
    on = is_on()
    # Maya's menu bar has nothing here: flat text, the current mode bright and the other dim (step 113)
    row = self.layout.row(align=True)
    row.scale_x = 0.85
    sub = row.row(align=True)
    sub.active = on
    sub.operator(ALLSET_OT_switch_mode.bl_idname, text="Maya", emboss=False).mode = 'MAYA'
    row.label(text="|")
    sub = row.row(align=True)
    sub.active = not on
    sub.operator(ALLSET_OT_switch_mode.bl_idname, text="Blender", emboss=False).mode = 'BLENDER'


def draw_edit_menu(self, context):
    """Blender's Edit menu: found by the menu search (F3) in Blender mode."""
    if is_on():
        return
    self.layout.separator()
    self.layout.operator(ALLSET_OT_switch_mode.bl_idname, text="Switch to Maya Mode",
                         icon='EVENT_M').mode = 'MAYA'


classes = (ALLSET_OT_switch_mode, ALLSET_OT_restore_blender)
_keymaps = []


def _add_shortcut():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc is None:
        return
    km = kc.keymaps.new(name="Window", space_type='EMPTY', region_type='WINDOW')
    key, mods = SHORTCUT
    kmi = km.keymap_items.new(ALLSET_OT_switch_mode.bl_idname, key, 'PRESS', **mods)
    kmi.properties.mode = 'TOGGLE'
    _keymaps.append((km, kmi))


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_HT_upper_bar.append(draw_topbar_switch)
    bpy.types.TOPBAR_MT_edit.append(draw_edit_menu)
    _add_shortcut()


def unregister():
    for km, kmi in _keymaps:
        try:
            km.keymap_items.remove(kmi)
        except (ReferenceError, RuntimeError):
            pass
    _keymaps.clear()
    bpy.types.TOPBAR_MT_edit.remove(draw_edit_menu)
    bpy.types.TOPBAR_HT_upper_bar.remove(draw_topbar_switch)
    if bpy.app.timers.is_registered(_apply_pending):
        bpy.app.timers.unregister(_apply_pending)
    _pending.clear()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
