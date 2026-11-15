# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya's interface look while Maya mode is on, and the user's own theme back the moment it is off.

Maya mode on puts Maya's interface greys into the Blender theme (``LOOK``): #444444 panels, menu bars and headers,
#373737 separators, tab rows and Outliner, #2b2b2b fields, #5d5d5d buttons and frame headers, #525252 menus,
#5285a6 selection, light text, square scroll bars and Maya's pale yellow tooltips. Only theme values change; every
other Blender preference stays the user's.

The user's values are kept in the extension's user folder (``maya_look.json``) and put back:

- Maya mode off, the add-on disabled or removed: every value that still holds the Maya value gets the user's value
  back. A value the user changed while Maya mode was on stays as the user set it, and a theme the user picked from
  the theme menu in the meantime (its file path changes) stays as picked.
- Quitting Blender: back before Blender's Auto-Save Preferences writes the preferences (``exit_pre`` runs first), so
  the saved file holds the user's theme. Blender also unregisters add-ons on quit, after that.
- Save Preferences while Maya mode is on: the kit notices the newer userpref.blend (``check_saved``, once a second)
  and saves it again with the user's theme values, then puts the Maya values back on screen. A start without the
  kit reads the user's theme.
- Load Factory Settings: Blender's factory theme is the new one, nothing is put back (the add-on is no longer in
  the preferences' add-on list when Blender unregisters it).
- A backup left by a crash is applied once at the next start (values still holding the Maya value) and dropped.

Changing the theme marks nothing: the preferences' unsaved state stays as it was.
"""

import json
import os

import bpy
from bpy.app.handlers import persistent

# (struct below the theme, {property: value}); colours as #rrggbb / #rrggbbaa
_BUTTON = {"outline": "#626262ff", "inner": "#5d5d5dff", "inner_sel": "#5285a6ff", "text": "#eeeeee",
           "text_sel": "#ffffff", "roundness": 0.1}
_FIELD = {"outline": "#2b2b2bff", "inner": "#2b2b2bff", "text": "#c8c8c8", "roundness": 0.1}
_HEADER = {"header": "#444444b3", "header_text": "#c8c8c8"}
LOOK = (
    ("user_interface", {"editor_border": "#373737", "editor_outline": "#44444400", "panel_roundness": 0.1,
                        "panel_header": "#5d5d5dff", "panel_back": "#444444ff", "panel_title": "#bbbbbb",
                        "panel_text": "#bbbbbb"}),
    ("user_interface.wcol_regular", dict(_BUTTON, show_shaded=False)),
    ("user_interface.wcol_tool", dict(_BUTTON, show_shaded=False)),
    ("user_interface.wcol_toolbar_item", {"inner": "#444444ff", "inner_sel": "#5285a6ff", "roundness": 0.1}),
    ("user_interface.wcol_radio", dict(_BUTTON, show_shaded=False)),
    ("user_interface.wcol_toggle", _BUTTON),
    ("user_interface.wcol_menu", _BUTTON),
    ("user_interface.wcol_text", _FIELD),
    ("user_interface.wcol_num", _FIELD),
    ("user_interface.wcol_numslider", _FIELD),
    ("user_interface.wcol_option", {"outline": "#2b2b2bff", "inner": "#2b2b2bff", "inner_sel": "#5285a6ff",
                                    "item": "#eeeeeeff", "text": "#bbbbbb", "roundness": 0.1}),
    ("user_interface.wcol_box", {"roundness": 0.1}),
    ("user_interface.wcol_pulldown", {"inner_sel": "#5285a6ff", "text": "#c8c8c8", "text_sel": "#ffffff",
                                      "roundness": 0.0}),
    ("user_interface.wcol_menu_back", {"outline": "#333333ff", "inner": "#525252ff", "text": "#eeeeee",
                                       "roundness": 0.0}),
    ("user_interface.wcol_menu_item", {"inner_sel": "#5285a6ff", "text": "#eeeeee", "text_sel": "#ffffff",
                                       "roundness": 0.0}),
    ("user_interface.wcol_tooltip", {"outline": "#000000ff", "inner": "#ffffdcff", "text": "#000000",
                                     "roundness": 0.0}),
    ("user_interface.wcol_list_item", {"inner_sel": "#5285a6ff", "text": "#bbbbbb", "text_sel": "#ffffff",
                                       "roundness": 0.0}),
    ("user_interface.wcol_scroll", {"outline": "#373737ff", "inner": "#373737ff", "item": "#5d5d5dff",
                                    "show_shaded": False, "roundness": 0.0}),
    ("user_interface.wcol_tab", {"outline": "#2b2b2bff", "inner": "#373737ff", "inner_sel": "#444444ff",
                                 "text": "#bbbbbb", "text_sel": "#eeeeee", "roundness": 0.1}),
    ("view_3d.space", _HEADER),
    ("graph_editor.space", _HEADER),
    ("dopesheet_editor.space", _HEADER),
    ("nla_editor.space", _HEADER),
    ("image_editor.space", _HEADER),
    ("sequence_editor.space", _HEADER),
    ("clip_editor.space", _HEADER),
    ("node_editor.space", _HEADER),
    ("file_browser.space", _HEADER),
    ("spreadsheet.space", _HEADER),
    ("properties.space", dict(_HEADER, back="#444444")),
    ("preferences.space", dict(_HEADER, back="#444444")),
    ("outliner", {"selected_highlight": "#5285a6", "active": "#5285a6", "selected_object": "#ffffff",
                  "active_object": "#ffffff"}),
    ("outliner.space", dict(_HEADER, back="#373737")),
    ("text_editor.space", dict(_HEADER, back="#2b2b2b")),
    ("console.space", dict(_HEADER, back="#2b2b2b")),
    ("info.space", dict(_HEADER, back="#2b2b2b")),
    ("topbar.space", dict(_HEADER, back="#444444")),
    ("statusbar.space", {"header": "#444444b3", "back": "#444444"}),
)

STATE_FILE = "maya_look.json"
CHECK_EVERY = 1.0           # s between looks at userpref.blend
# Headless Blender (-b) shows no interface: the look is put in place there only when asked (tests)
IN_BACKGROUND = os.environ.get("ALLSET_MAYA_LOOK_BACKGROUND") == "1"

_quitting = [False]


def _colour(text):
    return tuple(int(text[i:i + 2], 16) / 255 for i in range(1, len(text), 2))


def values():
    """{path below the theme ("user_interface.wcol_regular.inner"): Maya value}."""
    out = {}
    for struct, props in LOOK:
        for prop, v in props.items():
            out[f"{struct}.{prop}"] = _colour(v) if isinstance(v, str) else v
    return out


def _theme():
    return bpy.context.preferences.themes[0]


def _owner(path):
    struct, _, prop = path.rpartition(".")
    try:
        owner = _theme().path_resolve(struct)
    except ValueError:
        return None, prop
    return (owner, prop) if hasattr(owner, prop) else (None, prop)


def _get(path):
    owner, prop = _owner(path)
    if owner is None:
        return None
    v = getattr(owner, prop)
    return tuple(v) if hasattr(v, "__len__") and not isinstance(v, str) else v


def _set(path, value):
    owner, prop = _owner(path)
    if owner is None or value is None:
        return
    try:
        setattr(owner, prop, tuple(value) if isinstance(value, list) else value)
    except (TypeError, ValueError):
        cur = getattr(owner, prop)
        if hasattr(cur, "__len__"):         # a colour with or without alpha in this Blender
            n = len(cur)
            setattr(owner, prop, (tuple(value) + tuple(cur)[len(value):])[:n])


def _same(a, b):
    if a is None or b is None:
        return a is b
    if isinstance(a, (tuple, list)):
        return len(a) == len(b) and all(abs(x - y) < 0.6 / 255 for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        return abs(float(a) - float(b)) < 1e-4
    return a == b


def _quietly(fn):
    prefs = bpy.context.preferences
    dirty = prefs.is_dirty
    try:
        return fn()
    finally:
        prefs.is_dirty = dirty
        _redraw()


def _redraw():
    wm = bpy.context.window_manager
    for window in getattr(wm, "windows", ()):
        for area in window.screen.areas:
            area.tag_redraw()


# --- state ---------------------------------------------------------------------------------------------------------

def _state_path():
    return os.path.join(bpy.utils.extension_path_user(__package__, create=True), STATE_FILE)


def read_state():
    try:
        with open(_state_path(), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _write_state(state):
    with open(_state_path(), "w", encoding="utf-8") as fh:
        json.dump(state, fh)


def _drop_state():
    try:
        os.remove(_state_path())
    except OSError:
        pass


def _userpref_mtime():
    path = os.path.join(bpy.utils.user_resource('CONFIG'), "userpref.blend")
    try:
        return os.stat(path).st_mtime_ns
    except OSError:
        return 0


def is_applied():
    return read_state() is not None


def _still_applied(state):
    """Paths whose value is still the Maya value the kit put there."""
    return [p for p, v in state["applied"].items() if _same(_get(p), v)]


def _put_back(state, paths):
    for p in paths:
        _set(p, state["backup"][p])


# --- on / off ------------------------------------------------------------------------------------------------------

def wanted():
    return not bpy.app.background or IN_BACKGROUND


def apply():
    """Maya's look in place, the user's values kept (nothing when it is already in place)."""
    state = read_state()
    if state is not None:
        # left by a crash or a kill: the user's values first, then a fresh start
        _quietly(lambda: _put_back(state, _still_applied(state)))
        _drop_state()
    look = values()
    backup = {p: _get(p) for p in look}
    look = {p: v for p, v in look.items() if backup[p] is not None}      # what this Blender has
    _quietly(lambda: [_set(p, v) for p, v in look.items()])
    _write_state({"backup": {p: backup[p] for p in look}, "applied": {p: _get(p) for p in look},
                  "filepath": _theme().filepath, "saved": _userpref_mtime()})
    _watch(True)


def restore():
    """The user's values back. Returns the paths kept as they are now (changed by the user while on)."""
    state = read_state()
    _watch(False)
    if state is None:
        return []
    if _theme().filepath != state["filepath"]:
        kept = list(state["applied"])        # the user picked a theme from the theme menu: it stays
    else:
        back = _still_applied(state)
        _quietly(lambda: _put_back(state, back))
        kept = [p for p in state["applied"] if p not in back]
    _drop_state()
    return kept


def forget():
    """The kept values dropped without putting them back (Load Factory Settings replaced the theme)."""
    _watch(False)
    _drop_state()


def check_saved():
    """userpref.blend written while Maya's look is on screen: write it again with the user's theme values, then
    put the Maya values back on screen. Returns True when it saved."""
    state = read_state()
    if state is None or _userpref_mtime() == state["saved"]:
        return False
    if _theme().filepath != state["filepath"]:
        forget()
        return False
    on = _still_applied(state)
    prefs = bpy.context.preferences

    def resave():
        _put_back(state, on)
        try:
            bpy.ops.wm.save_userpref()
        finally:
            for p in on:
                _set(p, state["applied"][p])
    _quietly(resave)
    prefs.is_dirty = False
    state["saved"] = _userpref_mtime()
    _write_state(state)
    return True


def _tick():
    try:
        check_saved()
    except Exception as ex:        # noqa: BLE001  never stop the session over this
        print("Maya Workflow Kit: Maya look save check:", ex)
    return CHECK_EVERY if is_applied() else None


def _watch(on):
    if bpy.app.background:
        return
    registered = bpy.app.timers.is_registered(_tick)
    if on and not registered:
        bpy.app.timers.register(_tick, first_interval=CHECK_EVERY, persistent=True)
    elif not on and registered:
        bpy.app.timers.unregister(_tick)


@persistent
def _exit_pre(*_args):
    # before Blender's Auto-Save Preferences on quit
    _quitting[0] = True
    restore()


def register():
    _quitting[0] = False
    if _exit_pre not in bpy.app.handlers.exit_pre:
        bpy.app.handlers.exit_pre.append(_exit_pre)
    if wanted():
        apply()


def unregister():
    if _exit_pre in bpy.app.handlers.exit_pre:
        bpy.app.handlers.exit_pre.remove(_exit_pre)
    if _quitting[0]:
        _watch(False)
        return
    if __package__ not in bpy.context.preferences.addons:
        forget()                     # Load Factory Settings: Blender's factory theme is the user's choice now
    else:
        restore()
