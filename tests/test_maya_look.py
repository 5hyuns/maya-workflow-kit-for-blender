"""Maya's interface look while Maya mode is on (maya_look.py), and the user's own theme back afterwards.

In this process (the look is put in place in headless Blender too, ``maya_look.IN_BACKGROUND``): nothing changes
without Maya mode; Maya mode on sets every listed value; off puts every value back, again and again; a theme edit
made while on stays; a theme picked from the theme menu while on stays; disabling restores; quitting restores
before Blender saves. Across sessions in a sandbox of its own: Save Preferences while on (the saved file holds the
user's theme: restart with the kit, and without it after a command line remove), Remove while on, Load Factory
Preferences while on, and a crash while on.
"""

import json
import os
import shutil
import subprocess
from importlib import import_module

import bpy

import kit

AUTO_ENABLE = False
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MENU = "USERPREF_MT_interface_theme_presets"
SKIP = ("filepath", "name")
OWN = {"user_interface.wcol_regular.inner": (0.5, 0.2, 0.2, 1.0), "properties.space.back": (0.15, 0.25, 0.15),
       "outliner.space.back": (0.25, 0.15, 0.25), "user_interface.panel_roundness": 0.8}


def _look():
    return import_module(kit.MODULE + ".maya_look")


def _switch():
    return import_module(kit.MODULE + ".switch")


def _values():
    return {k: v for k, v in kit._walk(bpy.context.preferences.themes[0]).items() if k not in SKIP}


def _diff(a, b):
    return [k for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


def _set(path, value):
    struct, _, prop = path.rpartition(".")
    setattr(bpy.context.preferences.themes[0].path_resolve(struct), prop, value)


def _get(path):
    struct, _, prop = path.rpartition(".")
    v = getattr(bpy.context.preferences.themes[0].path_resolve(struct), prop)
    return tuple(v) if hasattr(v, "__len__") else v


def _close(a, b):
    if isinstance(b, tuple):
        return len(a) == len(b) and all(abs(x - y) < 0.6 / 255 for x, y in zip(a, b))
    return abs(float(a) - float(b)) < 1e-4 if isinstance(b, float) else a == b


def _own_theme():
    bpy.ops.preferences.reset_default_theme()
    for p, v in OWN.items():
        _set(p, v)
    return _values()


def _on():
    _switch().set_mode(True, layout=False)


def _off():
    _switch().set_mode(False, layout=False)


def _start():
    kit.enable(maya=False)
    _look().IN_BACKGROUND = True
    return _own_theme()


def test_no_maya_mode_changes_nothing():
    own = _start()
    dirty = bpy.context.preferences.is_dirty
    assert not _diff(own, _values()), "enabling the add-on changed the theme"
    assert not _look().is_applied()
    kit.disable()
    assert not _diff(own, _values())
    assert bpy.context.preferences.is_dirty == dirty


def test_on_sets_every_value_and_off_puts_every_value_back():
    own = _start()
    look = _look().values()
    for round_ in range(3):
        _on()
        wrong = [p for p, v in look.items() if not _close(_get(p), v)]
        assert not wrong, f"round {round_}: not Maya's: {wrong[:10]}"
        assert _look().is_applied()
        _off()
        d = _diff(own, _values())
        assert not d, f"round {round_}: not the user's theme after Maya mode off: {d[:10]}"
        assert not _look().is_applied(), "the kept values are dropped"
    kit.disable()


def test_only_theme_values_change():
    _start()
    prefs = bpy.context.preferences
    before = {s: kit._struct_hash(getattr(prefs, s)) for s in ("view", "system", "inputs", "edit", "apps")}
    _on()
    after = {s: kit._struct_hash(getattr(prefs, s)) for s in before}
    _off()
    kit.disable()
    assert before == after, [s for s in before if before[s] != after[s]]


def test_theme_edit_while_on_stays():
    own = _start()
    _on()
    _set("graph_editor.space.header", (0.6, 0.1, 0.6, 1.0))           # a value Maya mode set
    _set("view_3d.vertex", (0.9, 0.9, 0.1))                          # one it doesn't touch
    _off()
    assert _close(_get("graph_editor.space.header"), (0.6, 0.1, 0.6, 1.0)), "the user's edit stays"
    assert _close(_get("view_3d.vertex"), (0.9, 0.9, 0.1))
    d = [k for k in _diff(own, _values()) if not k.startswith(("graph_editor.space.header", "view_3d.vertex"))]
    assert not d, f"everything else is the user's again: {d[:10]}"
    kit.disable()


def test_theme_picked_while_on_stays():
    _start()
    _on()
    light = next(os.path.join(d, f) for d in bpy.utils.preset_paths("interface_theme") for f in os.listdir(d)
                 if "light" in f.lower() and f.endswith(".xml"))
    bpy.ops.script.execute_preset(filepath=light, menu_idname=MENU)
    picked = _values()
    _off()
    assert not _diff(picked, _values()), "the theme picked from the menu stays"
    assert not _look().is_applied()
    kit.disable()
    bpy.ops.preferences.reset_default_theme()


def test_disable_while_on_restores():
    own = _start()
    _on()
    kit.disable()
    assert not _diff(own, _values())


def test_quit_restores_before_blender_saves():
    """Blender runs exit_pre first on quit, then Auto-Save Preferences, then unregisters the add-ons."""
    own = _start()
    _on()
    for fn in list(bpy.app.handlers.exit_pre):
        if getattr(fn, "__module__", "").startswith(kit.MODULE):
            fn()
    assert not _diff(own, _values()), "the user's theme is in place for the save on quit"
    assert not _look().is_applied()
    _look()._quitting[0] = False
    kit.disable()


class _Rec:
    """A stand-in layout that records the operators a draw function asks for."""

    def __init__(self, ops):
        object.__setattr__(self, "ops", ops)

    def operator(self, idname, **_kw):
        self.ops.append(idname)

    def __getattr__(self, name):
        if name in ("row", "column", "split", "box", "column_flow", "grid_flow"):
            return lambda *a, **k: self
        return lambda *a, **k: None

    def __setattr__(self, name, value):
        pass


def _save_entries():
    from types import SimpleNamespace
    prefs = bpy.context.preferences
    ops, auto = [], prefs.use_preferences_save
    try:
        prefs.use_preferences_save = True                  # the Save & Load menu item shows
        bpy.types.USERPREF_MT_save_load.draw(SimpleNamespace(layout=_Rec(ops)), bpy.context)
        prefs.use_preferences_save = False                 # the save button shows
        bpy.types.USERPREF_HT_header.draw_buttons(_Rec(ops), bpy.context)
    finally:
        prefs.use_preferences_save = auto
    return [o for o in ops if "save_userpref" in o]


def test_blender_save_entries_run_the_kits_save_in_maya_mode():
    _start()
    assert _save_entries() == ["wm.save_userpref"] * 2, "Blender's own save without Maya mode"
    _on()
    assert _save_entries() == ["allset.save_userpref"] * 2, _save_entries()
    _off()
    assert _save_entries() == ["wm.save_userpref"] * 2, "Blender's own save again after Maya mode"
    kit.disable()


# --- across sessions, in a sandbox of its own ------------------------------------------------------------------

def _sandbox(name):
    root = os.path.abspath(os.path.join(bpy.utils.user_resource('CONFIG'), "..", name))
    assert "tmp" in root.replace("\\", "/").split("/"), root
    if os.path.isdir(root):
        shutil.rmtree(root)
    env = dict(os.environ)
    for var, sub in (("BLENDER_USER_CONFIG", "config"), ("BLENDER_USER_SCRIPTS", "scripts"),
                     ("BLENDER_USER_EXTENSIONS", "extensions")):
        os.makedirs(os.path.join(root, sub))     # Blender ignores a BLENDER_USER_* folder that doesn't exist
        env[var] = os.path.join(root, sub)
    env.update(ALLSET_NO_WELCOME="1", ALLSET_PROJECTS_DIR=os.path.join(root, "projects"),
               PYTHONDONTWRITEBYTECODE="1", ALLSET_MAYA_LOOK_BACKGROUND="1")
    rc, log = _run([bpy.app.binary_path, "--command", "extension", "install-file", "-r", "user_default",
                    _kit_zip()], env)
    assert rc == 0, log[-3000:]
    return root, env


def _kit_zip():
    import tomllib
    with open(os.path.join(ROOT, "src", "allset", "blender_manifest.toml"), "rb") as fh:
        ver = tomllib.load(fh)["version"]
    return os.path.join(ROOT, "dist", f"maya-workflow-kit-{ver}.zip")


def _run(cmd, env):
    p = subprocess.run(cmd, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=240)
    return p.returncode, p.stdout + p.stderr


def _session(root, env, name, *actions):
    out = os.path.join(root, f"{name}.json")
    rc, log = _run([bpy.app.binary_path, "-b", "--python", os.path.join(HERE, "ml_session.py"), "--", out,
                    *actions], env)
    assert os.path.isfile(out), f"session {name} wrote nothing (exit {rc}):\n{log[-3000:]}"
    assert "Traceback" not in log, f"session {name}:\n{log[-3000:]}"
    with open(out, encoding="utf-8") as fh:
        return json.load(fh)


def _maya(values):
    """Every value Maya mode sets holds Maya's value in what a session wrote."""
    return all(k in values and _close(eval(values[k], {}), v) for k, v in _look().values().items())   # noqa: S307


def test_save_while_on_keeps_the_users_theme_in_the_file():
    root, env = _sandbox("maya_look_save")
    own = _session(root, env, "own", "own_theme", "save")
    on = _session(root, env, "on", "enable", "maya_on", "save_ui")           # Save Preferences while on
    assert on["kit"] and on["state"] and _maya(on["values"]), "Maya's look on screen"
    again = _session(root, env, "restart")                                   # the kit starts in Maya mode
    assert again["kit"] and _maya(again["values"]), "Maya's look again after a restart in Maya mode"
    off = _session(root, env, "off", "maya_off", "save")
    assert not _diff(own["values"], off["values"]), _diff(own["values"], off["values"])[:10]
    _session(root, env, "on2", "maya_on", "save_ui")
    rc, log = _run([bpy.app.binary_path, "--command", "extension", "remove", "user_default.allset"], env)
    assert rc == 0, log[-3000:]
    gone = _session(root, env, "without_kit")                                # the kit never ran this time
    assert not gone["kit"] and not _diff(own["values"], gone["values"]), _diff(own["values"], gone["values"])[:10]
    shutil.rmtree(root)


def test_save_while_on_without_the_check_would_keep_mayas_theme():
    """Why the check exists: the file Save Preferences wrote holds Maya's look until the kit saves it again."""
    root, env = _sandbox("maya_look_nocheck")
    _session(root, env, "own", "own_theme", "save")
    _session(root, env, "on", "enable", "maya_on", "save", "crash")         # no tick: ended at once
    plain = dict(env)
    plain.pop("ALLSET_MAYA_LOOK_BACKGROUND")                                 # read the file, change nothing
    held = _session(root, plain, "held")
    assert _maya(held["values"]), "the file held Maya's look"
    shutil.rmtree(root)


def _previous_file(root, env, name):
    """What userpref.blend1 (a previous file, when this Blender keeps one) holds, read in a copy of the config;
    None when there is none (Blender 5.2 / 5.3 keep no previous preferences file)."""
    src = os.path.join(root, "config", "userpref.blend1")
    if not os.path.isfile(src):
        return None
    copy = os.path.join(root, name)
    os.makedirs(os.path.join(copy, "config"), exist_ok=True)
    shutil.copyfile(src, os.path.join(copy, "config", "userpref.blend"))
    env2 = dict(env, BLENDER_USER_CONFIG=os.path.join(copy, "config"))
    env2.pop("ALLSET_MAYA_LOOK_BACKGROUND")
    return _session(root, env2, name)


def test_ui_save_while_on_writes_the_users_theme_to_both_files():
    root, env = _sandbox("maya_look_ui_save")
    own = _session(root, env, "own", "own_theme", "save")
    _session(root, env, "on", "enable", "maya_on", "save_ui", "crash")       # killed right after saving
    plain = dict(env)
    plain.pop("ALLSET_MAYA_LOOK_BACKGROUND")
    held = _session(root, plain, "held")
    assert not _diff(own["values"], held["values"]), _diff(own["values"], held["values"])[:10]
    prev = _previous_file(root, env, "blend1")
    assert prev is None or not _diff(own["values"], prev["values"]), _diff(own["values"], prev["values"])[:10]
    shutil.rmtree(root)


def test_script_save_while_on_is_saved_again_into_both_files():
    root, env = _sandbox("maya_look_script_save")
    own = _session(root, env, "own", "own_theme", "save")
    _session(root, env, "on", "enable", "maya_on", "save", "tick", "crash")   # wm.save_userpref, then the check
    plain = dict(env)
    plain.pop("ALLSET_MAYA_LOOK_BACKGROUND")
    held = _session(root, plain, "held")
    assert not _diff(own["values"], held["values"]), _diff(own["values"], held["values"])[:10]
    prev = _previous_file(root, env, "blend1")
    assert prev is None or not _diff(own["values"], prev["values"]), _diff(own["values"], prev["values"])[:10]
    shutil.rmtree(root)


def test_crash_while_on_is_mended_at_the_next_start():
    root, env = _sandbox("maya_look_crash")
    own = _session(root, env, "own", "own_theme", "save")
    crashed = _session(root, env, "on", "enable", "maya_on", "save", "crash")
    assert crashed["state_file"], "the kept values are on disk"
    nxt = _session(root, env, "next", "maya_off", "save")                    # next start (Maya mode), then off
    assert not _diff(own["values"], nxt["values"]), _diff(own["values"], nxt["values"])[:10]
    assert not nxt["state_file"]
    shutil.rmtree(root)


def test_edit_while_on_survives_save_and_off():
    root, env = _sandbox("maya_look_edit")
    own = _session(root, env, "own", "own_theme", "save")
    _session(root, env, "on", "enable", "maya_on", "edit", "save", "tick")
    off = _session(root, env, "off", "maya_off", "save")
    d = _diff(own["values"], off["values"])
    assert d and all(k.startswith("graph_editor.space.header") for k in d), d[:10]
    shutil.rmtree(root)


def test_remove_while_on_restores():
    root, env = _sandbox("maya_look_remove")
    own = _session(root, env, "own", "own_theme", "save")
    removed = _session(root, env, "remove", "enable", "maya_on", "uninstall", "save")
    assert not removed["kit"] and not removed["state_file"]
    assert not _diff(own["values"], removed["values"]), _diff(own["values"], removed["values"])[:10]
    after = _session(root, env, "after")
    assert not _diff(own["values"], after["values"])
    shutil.rmtree(root)


def test_load_factory_while_on_gives_the_factory_theme():
    root, env = _sandbox("maya_look_factory")
    factory = _session(root, env, "factory_start")
    _session(root, env, "own", "own_theme", "save")
    reset = _session(root, env, "reset", "enable", "maya_on", "factory", "save")
    assert not reset["kit"], "Load Factory Preferences turns the add-on off"
    assert not reset["state_file"], "the kept values are dropped"
    assert not _diff(factory["values"], reset["values"]), _diff(factory["values"], reset["values"])[:10]
    after = _session(root, env, "after")
    assert not _diff(factory["values"], after["values"])
    shutil.rmtree(root)
