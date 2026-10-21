"""Step 115: no surprises — enabling changes nothing until the user opts in, no automatic preference saves, a code-free
layout template that leaves with a user disable, kit draws that keep other add-ons' UI (docs/steps/step_115.md)."""

import os
import re
import shutil
from importlib import import_module

import addon_utils
import bpy

import kit

AUTO_ENABLE = False
SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep + os.path.join("src", "allset")


def _mod(name):
    return import_module(f"{kit.MODULE}.{name}")


# Snapshot parts that must not change by enabling alone (the user's settings and Blender's behaviour).
UNCHANGED = ("active_keyconfig", "keyconfigs", "handlers", "prefs_inputs", "prefs_view", "prefs_edit",
             "prefs_system_wire", "theme", "ui_styles", "panel_polls", "render_panel_polls", "props", "sys_modules")


def test_enable_alone_changes_nothing():
    before = kit.snapshot()
    kit.enable(maya=False)
    try:
        during = kit.snapshot()
        changed = [k for k in UNCHANGED if before[k] != during[k]]
        assert not changed, "enabling alone changed: " + ", ".join(changed) + "\n" + "\n".join(
            d for d in kit.diff(before, during) if d.split(":")[0].split(".")[0] in changed)
        sw = _mod("switch")
        assert not sw.is_on() and not sw.has_snapshot()
        assert not hasattr(bpy.types.Scene, "allset_cb"), "Maya mode modules registered without opting in"
        assert bpy.context.window_manager.keyconfigs.active.name == "Blender"
        assert not _mod("app_template").is_installed()
        # what enabling alone does add: the opt-in and the switch
        for op in ("welcome", "switch_mode", "restore_blender"):
            assert getattr(bpy.ops.allset, op).get_rna_type() is not None, op
        funcs = [getattr(f, "__name__", "") for f in bpy.types.TOPBAR_HT_upper_bar.draw._draw_funcs]
        assert "draw_topbar_switch" in funcs, funcs
    finally:
        kit.disable()
    d = kit.diff(before, kit.snapshot())
    assert not d, "state leaked after disable:\n" + "\n".join(d)


def test_opt_in_turns_maya_on_and_disable_restores():
    before = kit.snapshot()
    kit.enable(maya=False)
    _mod("welcome").opt_in(open_layout=False)      # what the dialog's confirm / the preferences button run
    prefs = _mod("preferences").get()
    assert _mod("switch").is_on() and hasattr(bpy.types.Scene, "allset_cb")
    assert bpy.context.window_manager.keyconfigs.active.name == "Blender", "step 130: the active keyconfig stays"
    assert _mod("keymap").is_applied()
    assert bpy.context.preferences.themes[0].name == "Studio Grey (Maya-inspired)"
    assert prefs.maya_theme and prefs.start_in_maya_layout and prefs.layout_installed
    assert _mod("app_template").is_installed()
    assert bpy.context.preferences.is_dirty, "the choice is marked for Blender's own preference save"
    tpl = _mod("app_template").installed_dir()
    kit.disable()
    assert not os.path.isdir(tpl), "a user disable takes the layout template with it"
    d = kit.diff(before, kit.snapshot())
    assert not d, "state leaked after disable:\n" + "\n".join(d)


def test_quit_and_update_keep_the_template():
    kit.enable()
    app_template = _mod("app_template")
    app_template.install()
    tpl = app_template.installed_dir()
    assert not _mod("switch").user_disabling(), "not inside addon_utils.disable"
    # Quitting / reloading scripts / updating the extension unregister with default_set=False
    addon_utils.disable(kit.MODULE, default_set=False)
    assert os.path.isfile(os.path.join(tpl, app_template.MARKER)), "quit removed the template"
    kit.enable()
    app_template = _mod("app_template")
    assert _mod("preferences").get().layout_installed
    # gone while the preferences still want it (e.g. an older build's disable): register puts it back
    shutil.rmtree(tpl)
    assert app_template.reinstall_if_wanted() and app_template.is_installed()
    kit.disable()
    assert not os.path.isdir(tpl)


def test_template_has_no_code():
    app_template = _mod("app_template")
    files = os.listdir(app_template.SOURCE_DIR)
    assert not [f for f in files if f.endswith((".py", ".pyc")) or f == "__pycache__"], files
    kit.enable()
    try:
        dst = app_template.install()
        assert not [f for f in os.listdir(dst) if f.endswith(".py")], os.listdir(dst)
    finally:
        kit.disable()


def test_no_automatic_preference_save():
    hits = []
    for root, _dirs, files in os.walk(SRC):
        for name in files:
            if name.endswith(".py"):
                path = os.path.join(root, name)
                with open(path, encoding="utf-8") as fh:
                    for line in fh:
                        if "save_userpref" in line and not line.lstrip().startswith("#"):
                            hits.append((os.path.relpath(path, SRC).replace(os.sep, "/"), line.strip()))
    # Maya's File > Save Preferences menu item is the user's own action
    assert hits == [("ui/menu_map.py", '"File/Save Preferences": "wm.save_userpref",')], hits


def test_keymap_never_changes_the_active_keyconfig():
    """Step 130 replaced the template-switch re-activation (``wants_maya`` / ``_keep_keyconfig``): the Maya keys are
    add-on items, so nothing has to be put back after a template switch and no load_post handler is left."""
    kit.enable()
    try:
        keymap = _mod("keymap")
        assert not hasattr(keymap, "wants_maya") and not hasattr(keymap, "_keep_keyconfig")
        assert bpy.context.window_manager.keyconfigs.active.name == "Blender"
        assert not [f for f in bpy.app.handlers.load_post if "keymap" in getattr(f, "__module__", "")]
    finally:
        kit.disable()

def _other_addon(self, context):
    pass


def _other_addon_later(self, context):
    pass


CLASSES = ("STATUSBAR_HT_header", "OUTLINER_HT_header", "IMAGE_HT_header", "IMAGE_HT_tool_header",
           "TOPBAR_HT_upper_bar")


def _names(cls):
    return [getattr(f, "__qualname__", "") for f in cls.draw._draw_funcs]


def test_kit_draws_keep_other_addons_ui():
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active
    classes = [getattr(bpy.types, c) for c in CLASSES] + [VIEW3D_PT_tools_active]
    for cls in classes:
        cls.append(_other_addon)
    try:
        own = {cls: cls.draw._draw_funcs[0] for cls in classes}
        kit.enable()
        for cls in classes:
            names = _names(cls)
            assert "_other_addon" in names, (cls.__name__, names)
            cls.append(_other_addon_later)
        for c in CLASSES:   # only Blender's own draw is swapped, in place
            assert getattr(bpy.types, c).draw._draw_funcs[0] is not own[getattr(bpy.types, c)], c
        assert "_draw_begin" in _names(VIEW3D_PT_tools_active) and "_draw_end" in _names(VIEW3D_PT_tools_active)
        kit.disable()
        for cls in classes:
            funcs = cls.draw._draw_funcs
            assert funcs[0] is own[cls], (cls.__name__, _names(cls))
            assert _names(cls)[1:] == ["_other_addon", "_other_addon_later"], (cls.__name__, _names(cls))
    finally:
        for cls in classes:
            for fn in (_other_addon, _other_addon_later):
                cls.remove(fn)
        if kit.is_enabled():
            kit.disable()


def test_keystate_unknown_off_windows_or_on_failure():
    kit.enable()
    try:
        keystate = _mod("operators.keystate")
        saved = keystate._user32

        class Broken:
            def GetAsyncKeyState(self, vk):
                raise OSError("no user32")
        try:
            keystate._user32 = None                 # another OS
            assert keystate.is_down('A') is None
            keystate._user32 = Broken()
            assert keystate.is_down('A') is None
        finally:
            keystate._user32 = saved
        # callers act only on an explicit False (None = unknown: Blender's RELEASE event decides)
        bad = []
        for root, _dirs, files in os.walk(SRC):
            for name in files:
                if name.endswith(".py") and name != "keystate.py":
                    with open(os.path.join(root, name), encoding="utf-8") as fh:
                        for n, line in enumerate(fh, 1):
                            if re.search(r"not\s+keystate\.is_down|keystate\.is_down\([^)]*\)\s*(==|is)\s*None", line):
                                bad.append(f"{name}:{n}")
        assert not bad, bad
    finally:
        kit.disable()


def test_stale_snapshot_is_dropped_not_applied():
    """A snapshot left by an earlier install must not overwrite the user's current values on a fresh enable."""
    view = bpy.context.preferences.view
    kit.enable(maya=False)
    sw = _mod("switch")
    view.ui_scale = 1.3
    sw.take_snapshot()                              # "the user's values" of some earlier time
    view.ui_scale = 1.0
    addon_utils.disable(kit.MODULE, default_set=False)   # like a quit: the file stays
    assert os.path.isfile(sw.snapshot_path())
    kit.enable(maya=False)
    try:
        sw = _mod("switch")
        assert not sw.has_snapshot() and view.ui_scale == 1.0, (sw.has_snapshot(), view.ui_scale)
    finally:
        kit.disable()


def test_user_disable_drops_the_snapshot():
    kit.enable()
    sw = _mod("switch")
    assert sw.has_snapshot()
    path = sw.snapshot_path()
    kit.disable()
    assert not os.path.isfile(path), "a user disable leaves nothing for a next start"
