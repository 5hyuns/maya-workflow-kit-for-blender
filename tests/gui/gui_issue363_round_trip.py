"""#363 the way the report describes it, in a real UI: the user's own key changes stay through Maya -> Blender ->
Maya, through a restart of Blender in Maya mode and in Blender mode, and through a settings export / import.

The changes are made the way a user makes them:
- Maya mode, the kit's Hotkey Editor (pick the row, Assign New Hotkey, press the key): Smooth Mesh Preview 3 (key 3)
  -> Alt+F5, Undo (key z) -> Alt+F6;
- Maya mode, Edit > Preferences > Keymap (search, click the kit item's key, press the new key): Smooth Mesh Preview 1
  (key 1, Object Mode) -> Alt+F7;
- Blender mode, Edit > Preferences > Keymap: Blender's Hide Objects (h, Object Mode) -> Alt+F8.
Maya / Blender is switched with Ctrl+Alt+Shift+M over the viewport. Every check presses the new key over the viewport
(the command runs) and the old key (it no longer does). The preferences are saved into the test's own config folder
and two more GUI Blenders start from it without --factory-startup (this file again, with a phase argument): one
saved in Maya mode, one saved in Blender mode; the last one also exports the settings, restores every Maya hotkey and
imports the file."""

import json
import os
import re
import subprocess
import sys
import time
from importlib import import_module
from pathlib import Path

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, ev, run, tap, view3d, win  # noqa: E402

GUI_TIMEOUT = 900
_ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PHASE = _ARGS[1] if len(_ARGS) > 1 else "first"     # first = the runner's session; maya / blender = restarts
C = {}

ALT = {"alt": True}
NEW = {"high": ('F5', ALT), "undo": ('F6', ALT), "low": ('F7', ALT), "hide": ('F8', ALT)}
TEXT = {name: "Alt+" + key for name, (key, _m) in NEW.items()}
ROWS = {"high": ("HighQualityDisplay", "3"), "undo": ("Undo", "Z"), "low": ("LowQualityDisplay", "1")}
OLD = {"high": "3", "undo": "Z", "low": "1"}


def step(fn):
    """sim.step, printing each step's name (the restarted Blenders' logs show where they are)."""
    def traced():
        print("STEP", PHASE, fn.__name__, flush=True)
        return fn()
    traced.__name__ = fn.__name__
    return sim.step(traced)


def mod(name):
    return import_module(MODULE + name)


def maya_on():
    return mod(".switch").is_on()


def he():
    return mod(".ui.hotkey_editor")


def row(name):
    command, maya_key = ROWS[name]
    return next(r for r in he().rows() if r["command"] == command and r["maya_key"] == maya_key)


def kcs():
    return bpy.context.window_manager.keyconfigs


def v3d_override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def to_viewport():
    _area, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


def press(key, **mods):
    ev(key, 'PRESS', **mods)
    ev(key, 'RELEASE', **mods)


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def cube():
    return bpy.data.objects.get(C.get("cube", ""))


def select_only(ob):
    for o in bpy.context.view_layer.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob


def make_cube():
    with v3d_override():
        bpy.ops.mesh.primitive_cube_add()
    C["cube"] = bpy.context.view_layer.objects.active.name


def level():
    """Smooth Mesh Preview level of the cube as Maya shows it: 1 off, 2 cage + smooth, 3 smooth."""
    ob = cube()
    m = ob.modifiers.get(mod(".operators.display").PREVIEW_MOD_NAME)
    if m is None or not m.show_viewport:
        return 1
    return 2 if ob.show_wire else 3


def used(key, mods):
    """Active items of the user keyconfig on this key (any keymap)."""
    out = []
    for km in kcs().user.keymaps:
        for k in km.keymap_items:
            if k.active and k.type == key and (k.any or all(bool(getattr(k, m)) == bool(mods.get(m))
                                                            for m in ("ctrl", "alt", "shift", "oskey"))):
                out.append(f"{km.name}: {k.idname}")
    return out


def hide_item():
    """The user keyconfig's Object Mode Hide Objects item (h in Blender)."""
    km = kcs().user.keymaps.get("Object Mode")
    return next((k for k in km.keymap_items if k.idname == "object.hide_view_set"
                 and not k.properties.unselected), None) if km is not None else None


def is_hide_h(k):
    return k.idname == "object.hide_view_set" and k.type == 'H' and not (k.ctrl or k.alt or k.shift) \
        and not k.properties.unselected


def is_smooth_1(k):
    return k.idname == "allset.smooth_preview" and k.type == 'ONE' and not (k.ctrl or k.alt or k.shift) \
        and k.properties.level == 1


# --- Maya / Blender switch -----------------------------------------------------------------------------------------

def switch(to_maya, tag):
    @step
    def press_switch():
        to_viewport()
        key, mods = mod(".switch").SHORTCUT
        press(key, **mods)

    @step
    def wait():
        pass

    @step
    def switched():
        to_viewport()
        check(f"{tag}: Ctrl+Alt+Shift+M over the viewport switches to {'Maya' if to_maya else 'Blender'} mode",
              maya_on() == to_maya)


# --- the kit's Hotkey Editor ---------------------------------------------------------------------------------------

def hk():
    """(window, area, WINDOW region) of the Hotkey Editor, else (None, None, None)."""
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


def he_assign(name):
    command, maya_key = ROWS[name]
    key, mods = NEW[name]

    @step
    def open_editor():
        if hk()[0] is None:
            to_viewport()
            with v3d_override():
                bpy.ops.allset.menu_item(item="Windows/Settings/Preferences/Hotkey Editor")
        redraw()

    @step
    def pick():
        w = hk()[0]
        wm = bpy.context.window_manager
        C["he_row"] = -1
        if w is None:
            return
        wm.allset_hk_search = command
        C["he_row"] = next((i for i, r in enumerate(wm.allset_hk_rows)
                            if r.command == command and r.maya_key == maya_key), -1)
        wm.allset_hk_active = C["he_row"]
        redraw()

    @step
    def capture():
        w, area, region = hk()
        if w is None or C["he_row"] < 0:
            return
        to_window(w, region, 'MOUSEMOVE', 'NOTHING')
        with bpy.context.temp_override(window=w, area=area, region=region):
            bpy.ops.allset.hotkey_assign('INVOKE_DEFAULT')
        redraw()

    @step
    def key_press():
        w, _area, region = hk()
        C["capturing"] = bpy.context.window_manager.allset_hk_capture
        if w is not None:
            to_window(w, region, key, 'PRESS', **mods)
            to_window(w, region, key, 'RELEASE', **mods)
        redraw()

    @step
    def assigned():
        wm = bpy.context.window_manager
        text = he().kit_text(bpy.context, row(name))
        check(f"Maya mode, Hotkey Editor: {command} (Maya {maya_key}) > Assign New Hotkey > {TEXT[name]}: the list "
              f"shows {text!r} (window {hk()[0] is not None}, row {C['he_row']}, waited for a key {C['capturing']}, "
              f"warning {wm.allset_hk_pending!r})",
              C["capturing"] and not wm.allset_hk_capture and text == TEXT[name] + " *")


def close_he():
    @step
    def close():
        w = hk()[0]
        if w is not None:
            with bpy.context.temp_override(window=w):
                bpy.ops.wm.window_close()


# --- Blender's Preferences > Keymap --------------------------------------------------------------------------------

def prefs_win():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type == 'PREFERENCES':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


ITEM_OP = re.compile(r"preferences\.keyitem_(?:remove|restore)\(item_id=(\d+)\)")


def op_under(w, area, region):
    """The Python command of the operator button under the mouse in the Preferences window ("" when none)."""
    wm = bpy.context.window_manager
    wm.clipboard = ""
    try:
        with bpy.context.temp_override(window=w, area=area, region=region):      # (a temporary screen)
            bpy.ops.ui.copy_python_command_button()
    except RuntimeError:
        pass
    return wm.clipboard


def shown(search):
    """[(keymap name, item)] in the order Preferences > Keymap lists them for a name search."""
    out = []
    for km in kcs().user.keymaps:
        for k in km.active().keymap_items:
            if search in k.idname.lower() or search in k.name.lower():
                out.append((km.name, k))
    return out


def scan(search, km_name, match, found):
    """A step that finds the key button of the item ``match`` accepts in ``km_name``, as listed by the name search:
    the mouse goes down columns near the window's right edge (one probe per tick) counting the items' Remove /
    Restore buttons (their command names the item) to that item's row; its key button is the next button left of
    them. ``found["pos"]`` = a point inside it, or None."""
    st = {}

    def look():
        w, area, region = prefs_win()
        if w is None:
            found["pos"] = None
            return
        unit = round(20 * sim.scale())
        if not st:
            items = shown(search)
            n = next((i for i, (name, k) in enumerate(items) if name == km_name and match(k)), None)
            found.update(pos=None, row=n, rows=len(items), id=items[n][1].id if n is not None else None)
            if n is None:
                return
            st.update(cols=[1.6, 2.4, 1.0, 3.2], step=max(4, unit // 3), count=0, cur=None, ids=[])
            st["x"], st["y"] = region.x + region.width - round(unit * st["cols"][0]), region.y + region.height - 4
        else:
            m = ITEM_OP.search(op_under(w, area, region))
            hit = m.group(1) if m else None
            if hit != st["cur"]:
                if st["cur"] is not None and st["count"] == found["row"] + 1:     # past the item's row
                    found["pos"] = (st["x"] - 3 * unit, (st["first"] + st["last"]) // 2)
                    found["ids"] = st["ids"]
                    return
                if hit is not None:
                    st["count"] += 1
                    st["ids"].append(int(hit))
                    st["first"] = st["y"]
                st["cur"] = hit
            if hit is not None:
                st["last"] = st["y"]
            st["y"] -= st["step"]
            if st["y"] < region.y + 2:
                found["ids"] = st["ids"]
                st["cols"].pop(0)
                if not st["cols"]:
                    return
                st.update(count=0, cur=None, ids=[])
                st["x"], st["y"] = region.x + region.width - round(unit * st["cols"][0]), region.y + region.height - 4
        w.event_simulate(type='MOUSEMOVE', value='NOTHING', x=st["x"], y=st["y"])
        sim._steps.insert(0, look)
    return look


def prefs_edit(tag, search, km_name, match, name, label):
    key, mods = NEW[name]
    found = {}

    @step
    def open_prefs():
        to_viewport()
        with v3d_override():
            bpy.ops.screen.userpref_show('INVOKE_DEFAULT', section='KEYMAP')

    @step
    def type_search():
        w, area, _region = prefs_win()
        if w is None:
            return
        space = area.spaces.active
        space.filter_type = 'NAME'
        space.filter_text = search
        area.tag_redraw()

    @step
    def drawn():
        pass

    step(scan(search, km_name, match, found))

    @step
    def hover():
        w = prefs_win()[0]
        if w is None or found.get("pos") is None:
            return
        x, y = found["pos"]
        w.event_simulate(type='MOUSEMOVE', value='NOTHING', x=x, y=y)

    @step
    def click():
        w, area, region = prefs_win()
        if w is None or found.get("pos") is None:
            return
        found["over"] = op_under(w, area, region)        # the key button is no operator button
        x, y = found["pos"]
        w.event_simulate(type='LEFTMOUSE', value='PRESS', x=x, y=y)
        w.event_simulate(type='LEFTMOUSE', value='RELEASE', x=x, y=y)

    @step
    def key_press():
        w = prefs_win()[0]
        if w is None or found.get("pos") is None:
            return
        x, y = found["pos"]
        w.event_simulate(type=key, value='PRESS', x=x, y=y, **mods)
        w.event_simulate(type=key, value='RELEASE', x=x, y=y, **mods)

    @step
    def close():
        w = prefs_win()[0]
        check(f"{tag}, Edit > Preferences > Keymap: search {search!r}, click the key of {label}, press {TEXT[name]} "
              f"(window {w is not None}, item {found.get('row')} of {found.get('rows')} id {found.get('id')}, rows' "
              f"ids {found.get('ids')}, key button at {found.get('pos')}, operator there {found.get('over')!r})",
              w is not None and found.get("pos") is not None and not found.get("over")
              and found["ids"][-1] == found.get("id"))
        if w is not None:
            with bpy.context.temp_override(window=w):
                bpy.ops.wm.window_close()


# --- the checks ----------------------------------------------------------------------------------------------------

def maya_checks(tag):
    @step
    def m1():
        to_viewport()
        ob = cube()
        ob.hide_set(False)
        select_only(ob)
        C["texts"] = {n: he().kit_text(bpy.context, row(n)) for n in ROWS}
        items = he().row_items(bpy.context, row("low"))
        C["prefs_low"] = [(km.name, k.type, bool(k.alt), k.is_user_modified) for km, k in items]
        mod(".operators.display").set_smooth_preview(ob, 1)
        press('THREE')

    @step
    def m2():
        C["after_3"] = level()
        press(*NEW["high"][:1], **NEW["high"][1])

    @step
    def m3():
        C["after_high"] = level()
        press('ONE')

    @step
    def m4():
        C["after_1"] = level()
        press(*NEW["low"][:1], **NEW["low"][1])

    @step
    def m5():
        after_low = level()
        want = {n: TEXT[n] + " *" for n in ROWS}
        check(f"{tag}: the Hotkey Editor shows the changed keys ({C['texts']})", C["texts"] == want)
        check(f"{tag}: Preferences > Keymap shows Smooth Mesh Preview 1 on Alt+F7 in Object Mode ({C['prefs_low']})",
              bool(C["prefs_low"]) and C["prefs_low"][0] == ("Object Mode", 'F7', True, True))
        check(f"{tag}: 3 over the viewport no longer runs Smooth Mesh Preview 3 (level {C['after_3']}), Alt+F5 does "
              f"(level {C['after_high']})", C["after_3"] == 1 and C["after_high"] == 3)
        check(f"{tag}: 1 no longer runs Smooth Mesh Preview 1 (level {C['after_1']}), Alt+F7 does (level {after_low})",
              C["after_1"] == 3 and after_low == 1)
        ob = cube()
        C["x0"] = ob.location.x
        ob.location.x += 2.0
        with v3d_override():
            bpy.ops.ed.undo_push(message="Move")
        C["on_z"] = used('Z', {})
        press('Z')

    @step
    def m6():
        C["after_z"] = cube().location.x
        press(*NEW["undo"][:1], **NEW["undo"][1])

    @step
    def m7():
        x = cube().location.x
        check(f"{tag}: z no longer undoes (x {C['x0']:.3f} + 2 -> {C['after_z']:.3f}; on z: {C['on_z']}), Alt+F6 "
              f"does (-> {x:.3f})", abs(C["after_z"] - C["x0"] - 2.0) < 1e-4 and abs(x - C["x0"]) < 1e-4)


def blender_checks(tag):
    @step
    def b1():
        to_viewport()
        ob = cube()
        ob.hide_set(False)
        select_only(ob)
        k = hide_item()
        C["hide_key"] = (k.type, bool(k.alt), k.is_user_modified) if k is not None else None
        press(*NEW["hide"][:1], **NEW["hide"][1])

    @step
    def b2():
        ob = cube()
        C["hidden_new"] = ob.hide_get()
        ob.hide_set(False)
        select_only(ob)
        press('H')

    @step
    def b3():
        ob = cube()
        hidden_old = ob.hide_get()
        ob.hide_set(False)
        select_only(ob)
        check(f"{tag}: Preferences > Keymap shows Hide Objects on Alt+F8 ({C['hide_key']}); Alt+F8 over the viewport "
              f"hides the cube ({C['hidden_new']}), h no longer does ({hidden_old})",
              C["hide_key"] == ('F8', True, True) and C["hidden_new"] and not hidden_old)


def free_keys(tag, names):
    @step
    def free():
        taken = {TEXT[n]: used(*NEW[n]) for n in names}
        check(f"{tag}: the new keys are free before the test ({taken})", not any(taken.values()))


# --- restarts ------------------------------------------------------------------------------------------------------

def save_prefs(tag):
    @step
    def save():
        config = Path(bpy.utils.user_resource('CONFIG'))
        assert "/tmp/" in config.as_posix(), config
        check(f"{tag}: Save Preferences ({bpy.ops.wm.save_userpref()})", (config / "userpref.blend").exists())


def restart(phase, label):
    """Start this file again as a new GUI Blender on the same config folder; this Blender's event loop keeps running
    (one probe per tick) until that one has quit, then its checks are this file's checks."""
    run_ = {}

    @step
    def again():
        root = Path(bpy.utils.user_resource('CONFIG')).parent
        run_["out"] = out = root / "results" / f"gui_issue363_round_trip_{phase}.json"
        log = root / "logs" / f"gui_issue363_round_trip_{phase}.log"
        out.unlink(missing_ok=True)
        env = dict(os.environ, ALLSET_NO_SLOTS="1")     # started from a slotted Blender that waits for it
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
            proc.kill()                 # only the Blender started here
            proc.wait()
            code = "timeout"
        run_["log"].close()
        out = run_["out"]
        got = json.loads(out.read_text(encoding="utf-8")) if out.exists() else []
        check(f"{label}: Blender starts again from the saved preferences (exit {code}, {len(got)} checks)", bool(got))
        for r in got:
            check(f"{label}: {r['name']}", r["ok"])
    sim.step(wait)


def start_again(maya):
    @step
    def start():
        tap('ESC')
        try:
            mod(".operators.keystate").is_down = lambda t: t in sim._down
        except ImportError:
            pass
        to_viewport()

    @step
    def started():
        check(f"starts in {'Maya' if maya else 'Blender'} mode, as saved", maya_on() == maya)
        make_cube()
        to_viewport()


# --- E: settings export / import -----------------------------------------------------------------------------------

def export_import():
    parts = {"preferences": False, "shelves": False, "marking_menus": False}

    @step
    def export():
        path = Path(bpy.utils.user_resource('CONFIG')).parent / "issue363_settings.json"
        path.unlink(missing_ok=True)
        C["settings"] = str(path)
        C["export"] = bpy.ops.allset.settings_export(filepath=str(path), **parts)
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        got = sorted((h.get("command"), h.get("maya_key"), h.get("key", {}).get("type"), h.get("key", {}).get("alt"))
                     for h in data.get("hotkeys", []))
        want = sorted((ROWS[n][0], ROWS[n][1], NEW[n][0], True) for n in ROWS)
        check(f"Export Settings... writes the changed kit hotkeys ({C['export']}, {got})", got == want)
        C["restore"] = bpy.ops.allset.hotkey_restore(all=True)

    @step
    def restored():
        texts = {n: he().kit_text(bpy.context, row(n)) for n in ROWS}
        check(f"Hotkey Editor > Restore All Maya Hotkeys gives 3 / z / 1 back ({C['restore']}, {texts})",
              texts == OLD)
        C["import"] = bpy.ops.allset.settings_import(filepath=C["settings"], **parts)

    @step
    def imported():
        texts = {n: he().kit_text(bpy.context, row(n)) for n in ROWS}
        check(f"Import Settings... gives the changed keys back ({C['import']}, {texts})",
              texts == {n: TEXT[n] + " *" for n in ROWS})


# --- the sessions --------------------------------------------------------------------------------------------------

if PHASE == "first":
    @step
    def s_setup():
        sim.setup()
        sim.load_maya_layout()

    @step
    def s_scene():
        bpy.ops.allset.keymap_activate()
        make_cube()

    free_keys("Maya mode", NEW)
    # D: a Blender key changed in Blender mode
    switch(False, "Blender mode")
    free_keys("Blender mode", ("hide",))
    prefs_edit("Blender mode", "hide_view_set", "Object Mode", is_hide_h, "hide", "Hide Objects (h, Object Mode)")
    blender_checks("Blender mode, just changed")
    # A and B: Maya keys changed in Maya mode, in the Hotkey Editor and in Preferences > Keymap
    switch(True, "Maya mode")
    he_assign("high")
    he_assign("undo")
    close_he()
    prefs_edit("Maya mode", "smooth_preview", "Object Mode", is_smooth_1, "low", "Smooth Mesh Preview 1 (1, Object Mode)")
    maya_checks("Maya mode, just changed")
    switch(False, "Maya -> Blender")
    blender_checks("Blender mode after the Maya key changes")
    switch(True, "Maya -> Blender -> Maya")
    maya_checks("Maya -> Blender -> Maya")
    # C: restarts
    save_prefs("Maya mode")
    restart("maya", "restart (saved in Maya mode)")
    restart("blender", "restart (saved in Blender mode)")
elif PHASE == "maya":
    start_again(True)
    maya_checks("after a restart in Maya mode")
    switch(False, "Blender mode after the restart")
    blender_checks("Blender mode after the restart")
    save_prefs("Blender mode")
elif PHASE == "blender":
    start_again(False)
    blender_checks("after a restart in Blender mode")
    switch(True, "Maya mode after the restart")
    maya_checks("Maya mode after a restart in Blender mode")
    # E: settings export / import
    export_import()
    maya_checks("after Restore All + Import Settings")

run(interval=0.25, first=2.0 if PHASE == "first" else 4.0)
