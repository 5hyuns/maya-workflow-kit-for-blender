"""Audit 128 (menu sweep): run every mapped Maya menu item of the modeling / rigging / animation menus the way a
click does (marking.modal.run_action, INVOKE), in object mode (pCube1 + pSphere1 selected) and in component mode
(pCube1, all faces). A Python traceback from an item is a bug; other errors (Maya-style warnings, poll failures)
are listed for reading. Modals / popups left open are cancelled with ESC before the next item.
Output: AUDIT lines + tmp file ALLSET_SWEEP_OUT (TSV). PASSes when no item raises a Python traceback."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import MODULE, check, run, setup, step, tap, view3d, win, ev, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 1500
OUT = os.environ.get("ALLSET_SWEEP_OUT", "")
TOPS = ("Edit", "Modify", "Display", "Select", "Create", "Mesh", "Edit Mesh", "Mesh Tools", "Mesh Display",
        "Deform", "Skeleton", "Skin", "Constrain", "Key", "Control", "Curves", "Surfaces", "UV")
SKIP_WORDS = ("Open", "Save", "Import", "Export", "Reference", "Project", "Preferences", "Exit", "Editor",
              "Window", "Hypershade", "Render", "Playblast", "Script", "Outliner", "Graph", "Tool Settings",
              "Hotkey", "Shelf", "Help", "Plug-in", "Recent", "Archive", "Optimize Scene", "Send to",
              "Bake Simulation", "Create Turntable", "Search", "Find", "Visor", "Content Browser")
C = {"res": [], "i": 0}


def ov(fn, *a, **kw):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return fn(*a, **kw)


def items():
    ms = import_module(MODULE + ".ui.menu_sets")
    mm = import_module(MODULE + ".ui.menu_map")
    seen = set()
    out = []
    for path, _it in ms.iter_items():
        top = path.split("/")[0]
        if top not in TOPS or path in seen or any(w in path for w in SKIP_WORDS):
            continue
        seen.add(path)
        s = mm.spec(path)
        if s is None or s[0] in ("menu", "pie"):
            continue
        if s[1] == "allset.open_editor":      # issue #36: closing these windows within 2 s crashes Blender
            continue
        out.append(path)
    return out


def reset(edit):
    if bpy.context.mode != 'OBJECT':
        try:
            ov(bpy.ops.object.mode_set, mode='OBJECT')
        except Exception:
            pass
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    ov(bpy.ops.allset.create, kind='SPHERE')
    ov(bpy.ops.allset.create, kind='CUBE')
    cube = bpy.context.active_object
    for ob in bpy.context.scene.objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = cube
    if edit:
        for ob in bpy.context.scene.objects:
            ob.select_set(ob == cube)
        ov(bpy.ops.object.mode_set, mode='EDIT')
        ov(bpy.ops.mesh.select_mode, type='FACE')
        ov(bpy.ops.mesh.select_all, action='SELECT')


SEP, NL = chr(9), chr(10)


def clean(text):
    return text.replace(SEP, " ").replace(NL, " ")


def _log(r):
    if OUT:
        with open(OUT, "a", encoding="utf-8") as fh:
            fh.write(SEP.join([r[0], "edit" if r[1] else "object", r[2], clean(r[3])]) + NL)


def close_extra_windows():
    main = win()
    for w in list(bpy.context.window_manager.windows):
        if w != main:
            try:
                with bpy.context.temp_override(window=w):
                    bpy.ops.wm.window_close()
            except Exception:
                pass


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_list():
    bpy.ops.allset.keymap_activate()
    C["items"] = [(p, False) for p in items()] + [(p, True) for p in items()
                                                    if p.split("/")[0] in ("Edit Mesh", "Mesh", "Mesh Tools", "Select",
                                                                           "Edit", "Modify", "UV", "Deform")]
    print("AUDIT sweep items", len(C["items"]))
    for _ in range(len(C["items"])):
        step(s_run)
        step(s_clean)
    step(s_report)


def s_run():
    path, edit = C["items"][C["i"]]
    C["i"] += 1
    print("AUDIT item", C["i"], path, "edit" if edit else "object", flush=True)
    C["cur"] = (path, edit)
    try:
        reset(edit)
    except Exception as ex:
        C["res"].append((path, edit, "reset", repr(ex)))
        return
    modal = import_module(MODULE + ".marking.modal")
    mm = import_module(MODULE + ".ui.menu_map")
    area, region = view3d()
    try:
        with bpy.context.temp_override(window=win(), area=area, region=region):
            res = modal.run_action(bpy.context, mm.MAP[path], path=path)
        C["res"].append((path, edit, "ok", str(res)))
        _log(C["res"][-1])
    except Exception as ex:
        text = str(ex)
        kind = "TRACEBACK" if ("Traceback" in text or not isinstance(ex, RuntimeError)) else "error"
        last = " / ".join(l.strip() for l in text.strip().splitlines()[-3:])
        C["res"].append((path, edit, kind, f"{type(ex).__name__}: {last}"))
        _log(C["res"][-1])
        if kind == "TRACEBACK":
            print("AUDIT TRACEBACK", path, "edit" if edit else "object", last)


def s_clean():
    if win().modal_operators:
        x, y = view3d()[1].x + 300, view3d()[1].y + 300
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        tap('ESC')
        tap('ESC')
    close_extra_windows()


def s_report():
    tb = [r for r in C["res"] if r[2] == "TRACEBACK"]
    err = [r for r in C["res"] if r[2] == "error"]
    print("AUDIT sweep done", len(C["res"]), "tracebacks", len(tb), "errors", len(err))
    if OUT:
        with open(OUT, "w", encoding="utf-8") as fh:
            for r in C["res"]:
                fh.write("\t".join([r[0], "edit" if r[1] else "object", r[2], r[3].replace("\t", " ")]) + "\n")
    check(f"no menu item raises a Python traceback ({len(tb)}: {[r[0] for r in tb][:12]})", not tb)


run(interval=0.12)
