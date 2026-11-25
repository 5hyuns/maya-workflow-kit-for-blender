"""#559: a key changed in the kit's Hotkey Editor stays through every later restart, not only the first one.

Maya mode, Hotkey Editor (pick the row, Assign New Hotkey, press the key): Smooth Mesh Preview 3 (key 3) -> Alt+F5,
and Merge to Center (a menu item without a Maya hotkey) -> Ctrl+Alt+Shift+F6; then the Hotkey Editor's Save and
Close (like Maya's) saves the preferences. Three more GUI Blenders start one after the other from the test's own
config folder without --factory-startup (this file again, with a phase argument). Each one checks the keys and
quits the normal way (File > Quit: Blender's own auto-save of the preferences runs); none of them saves by hand,
the second one also opens and closes the Hotkey Editor. Last, the add-on goes off and on again the way Blender's
extension install / upgrade does it, and one more Blender starts. Shot of the editor: ALLSET_GUI_SHOTS."""

import json
import os
import subprocess
import sys
import time
from importlib import import_module
from pathlib import Path

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, run, tap, view3d, win  # noqa: E402

GUI_TIMEOUT = 900
_ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PHASE = _ARGS[1] if len(_ARGS) > 1 else "first"
C = {}
# (row command, its Maya key ("" = none), search text, the name the list shows, new key, modifiers, key text)
KEYS = (("HighQualityDisplay", "3", "HighQualityDisplay", "HighQualityDisplay", 'F5', {"alt": True}, "Alt+F5"),
        ("MergeToCenter", "", "merge to center", "Merge to Center", 'F6', {"ctrl": True, "alt": True, "shift": True},
         "Ctrl+Alt+Shift+F6"))


def step(fn):
    def traced():
        print("STEP", PHASE, fn.__name__, flush=True)
        return fn()
    traced.__name__ = fn.__name__
    return sim.step(traced)


def mod(name):
    return import_module(MODULE + name)


def he():
    return mod(".ui.hotkey_editor")


def row(command, maya_key):
    return next(r for r in he().rows() if r["command"] == command and (not maya_key or r["maya_key"] == maya_key))


def to_viewport():
    area, region = view3d()
    sim.ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 2)


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def hk():
    mw = mod(".ui.marked_window")
    w = mw.find_window(bpy.context, "HOTKEY_EDITOR")
    if w is None:
        return None, None, None
    area = next(a for a in w.screen.areas if mw.kind_of(a) == "HOTKEY_EDITOR")
    return w, area, next(r for r in area.regions if r.type == 'WINDOW')


def to_window(w, region, type, value, **kw):
    kw.setdefault("x", region.x + region.width // 2)
    kw.setdefault("y", region.y + region.height // 2)
    w.event_simulate(type=type, value=value, **kw)


def open_he():
    @step
    def open_editor():
        if hk()[0] is None:
            to_viewport()
            area, region = view3d()
            with bpy.context.temp_override(window=win(), area=area, region=region):
                bpy.ops.allset.menu_item(item="Windows/Settings/Preferences/Hotkey Editor")
        redraw()


def close_he():
    @step
    def close():
        w = hk()[0]
        if w is not None:
            with bpy.context.temp_override(window=w):
                bpy.ops.wm.window_close()


def assign(command, maya_key, search, shown, key, mods, text):
    open_he()

    @step
    def pick():
        wm = bpy.context.window_manager
        C["row"] = -1
        if hk()[0] is None:
            return
        wm.allset_hk_search = search
        C["row"] = next((i for i, r in enumerate(wm.allset_hk_rows)
                         if r.command == shown and (not maya_key or r.maya_key == maya_key)), -1)
        wm.allset_hk_active = C["row"]
        redraw()

    @step
    def capture():
        w, area, region = hk()
        if w is None or C["row"] < 0:
            return
        to_window(w, region, 'MOUSEMOVE', 'NOTHING')
        with bpy.context.temp_override(window=w, area=area, region=region):
            bpy.ops.allset.hotkey_assign('INVOKE_DEFAULT')
        redraw()

    @step
    def key_press():
        w, _area, region = hk()
        if w is not None:
            to_window(w, region, key, 'PRESS', **mods)
            to_window(w, region, key, 'RELEASE', **mods)
        redraw()

    @step
    def pending():
        w, _area, region = hk()
        wm = bpy.context.window_manager
        if w is not None and wm.allset_hk_capture and wm.allset_hk_pending:     # a used key: Enter takes it
            to_window(w, region, 'RET', 'PRESS')
            to_window(w, region, 'RET', 'RELEASE')

    @step
    def assigned():
        got = he().kit_text(bpy.context, row(command, maya_key))
        check(f"Hotkey Editor: {command} ({maya_key or 'no Maya key'}) > Assign New Hotkey > {text} shows {got!r}",
              got == text + " *")

    close_he()


def key_checks(tag):
    @step
    def keys():
        for command, maya_key, _search, _shown, _key, _mods, text in KEYS:
            got = he().kit_text(bpy.context, row(command, maya_key))
            check(f"{tag}: the Hotkey Editor row {command} shows {text} ({got!r})", got == text + " *")


def restart(phase, label):
    """Start this file again as a new GUI Blender on the same config folder and wait until it has quit."""
    run_ = {}

    @step
    def again():
        root = Path(bpy.utils.user_resource('CONFIG')).parent
        run_["out"] = out = root / "results" / f"gui_issue559_hotkey_restarts_{phase}.json"
        log = root / "logs" / f"gui_issue559_hotkey_restarts_{phase}.log"
        out.unlink(missing_ok=True)
        env = dict(os.environ, ALLSET_NO_SLOTS="1")
        cmd = [bpy.app.binary_path, "--enable-event-simulate", "--window-geometry", "0", "0", "1600", "900",
               "--python", os.path.abspath(__file__), "--", str(out), phase]
        log.parent.mkdir(parents=True, exist_ok=True)
        run_["log"] = open(log, "w", encoding="utf-8", errors="replace")
        run_["proc"] = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=run_["log"],
                                        stderr=subprocess.STDOUT)
        run_["until"] = time.monotonic() + 300

    def wait():
        proc = run_["proc"]
        if proc.poll() is None and time.monotonic() < run_["until"]:
            sim._steps.insert(0, wait)
            return
        code = proc.poll()
        if code is None:
            proc.kill()
            proc.wait()
            code = "timeout"
        run_["log"].close()
        out = run_["out"]
        got = json.loads(out.read_text(encoding="utf-8")) if out.exists() else []
        check(f"{label}: Blender starts again from the saved preferences (exit {code}, {len(got)} checks)", bool(got))
        for r in got:
            check(f"{label}: {r['name']}", r["ok"])
    sim.step(wait)


def start_again():
    @step
    def start():
        tap('ESC')
        to_viewport()

    @step
    def started():
        check("starts in Maya mode, as saved", mod(".switch").is_on())
        print("GUI INFO prefs dirty after start", bpy.context.preferences.is_dirty, flush=True)


if PHASE == "first":
    @step
    def s_setup():
        sim.setup()
        sim.load_maya_layout()

    @step
    def s_keys():
        bpy.ops.allset.keymap_activate()
        to_viewport()

    for k in KEYS:
        assign(*k)
    key_checks("just changed")

    open_he()

    @step
    def shot():
        w = hk()[0]
        if os.environ.get("ALLSET_GUI_SHOTS") and w is not None:
            with bpy.context.temp_override(window=w):
                bpy.ops.screen.screenshot(filepath=os.path.join(os.environ["ALLSET_GUI_SHOTS"],
                                                                "gui_issue559_hotkey_editor.png"))

    @step
    def save():
        config = Path(bpy.utils.user_resource('CONFIG'))
        assert "/tmp/" in config.as_posix(), config
        saved = config / "userpref.blend"
        C["mtime"] = saved.stat().st_mtime if saved.exists() else 0.0
        w, area, region = hk()
        C["save"] = None
        if w is not None:
            with bpy.context.temp_override(window=w, area=area, region=region):
                C["save"] = bpy.ops.allset.hotkey_save(close=True)

    step(lambda: None)
    step(lambda: None)

    @step
    def saved():
        saved = Path(bpy.utils.user_resource('CONFIG')) / "userpref.blend"
        check(f"Hotkey Editor > Save and Close saves the preferences and closes the window ({C['save']}, "
              f"window {hk()[0] is not None})",
              C["save"] == {'FINISHED'} and saved.exists() and saved.stat().st_mtime > C["mtime"] and hk()[0] is None)

    restart("r1", "1st restart")
    restart("r2", "2nd restart")
    restart("r3", "3rd restart")

    # an extension update: the add-on goes off and on again in this session, then Blender quits and starts again
    @step
    def update():
        import addon_utils
        # as Blender's extension install / upgrade does: off and on again, the add-on's preferences kept
        addon_utils.disable(MODULE, default_set=False, refresh_handled=True)
        for key in [k for k in sys.modules if k == MODULE or k.startswith(MODULE + ".")]:
            sys.modules.pop(key, None)
        C["off"] = "off"
        C["on"] = addon_utils.enable(MODULE, default_set=False, refresh_handled=True) is not None

    for _ in range(8):
        step(lambda: None)

    @step
    def updated():
        print("GUI INFO addon off / on", C["off"], C["on"], "prefs dirty", bpy.context.preferences.is_dirty,
              "maya", mod(".switch").is_on(), "keys", mod(".keymap").is_applied(), flush=True)

    key_checks("after the add-on went off and on (an update)")
    restart("r4", "restart after an update")
else:
    start_again()
    key_checks(f"after a restart ({PHASE})")
    if PHASE == "r2":
        open_he()
        close_he()
        key_checks(f"after a restart ({PHASE}), Hotkey Editor opened and closed")

run(interval=0.25, first=2.0 if PHASE == "first" else 4.0)
