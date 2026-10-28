"""Audit 128 (UI lane): items of a torn-off Maya menu (Maya: a torn-off menu window runs its items exactly like the
menu) must run from the floating window. The torn window is a Properties editor,
so every "op"-kind menu item is polled there and in the main viewport (object mode with pCube1 selected, then edit
mode with all faces selected); items that poll in the viewport but not in the torn window are listed. Then runs
Mesh > Smooth from a torn Mesh menu window (the operator a user clicks) and checks it worked.
PASSES when no item is lost in the torn window."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import MODULE, check, run, setup, step, win, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 240
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def v3d():
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def floating():
    md = mod(".ui.maya_dock")
    return [w for w in bpy.context.window_manager.windows if md.is_floating(w)]


def polls_in(window, area, region, paths):
    ms = mod(".ui.menu_sets")
    mm = mod(".ui.menu_map")
    out = set()
    with bpy.context.temp_override(window=window, screen=window.screen, area=area, region=region):
        for p in paths:
            s = mm.spec(p)
            if s and s[0] == "op" and ms.op_polls(s[1]):
                out.add(p)
    return out


def op_paths():
    mm = mod(".ui.menu_map")
    return [p for p in mm.MAP if (mm.spec(p) or ("",))[0] == "op"]


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    a, r = v3d()
    with bpy.context.temp_override(window=win(), area=a, region=r):
        bpy.ops.allset.create(kind='CUBE')
    with bpy.context.temp_override(window=win()):
        mod(".ui.maya_dock").tear_menu(bpy.context, "ALLSET_MT_mainMeshMenu", "Mesh")


@step
def s_wait():
    pass


@step
def s_compare_object():
    fl = floating()
    check("the Mesh menu tore off into a floating window", bool(fl))
    if not fl:
        return
    C["fw"] = fl[-1]
    fa = fl[-1].screen.areas[0]
    fr = next(r for r in fa.regions if r.type == 'WINDOW')
    a, r = v3d()
    paths = op_paths()
    in_view = polls_in(win(), a, r, paths)
    in_torn = polls_in(fl[-1], fa, fr, paths)
    lost = sorted(in_view - in_torn)
    C["lost_obj"] = lost
    print("AUDIT128 object-mode lost in torn window", len(lost), lost)
    with bpy.context.temp_override(window=win(), area=a, region=r):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')


@step
def s_compare_edit():
    fw = C.get("fw")
    if not fw:
        return
    fa = fw.screen.areas[0]
    fr = next(r for r in fa.regions if r.type == 'WINDOW')
    a, r = v3d()
    paths = op_paths()
    lost = sorted(polls_in(win(), a, r, paths) - polls_in(fw, fa, fr, paths))
    C["lost_edit"] = lost
    print("AUDIT128 edit-mode lost in torn window", len(lost), lost)
    with bpy.context.temp_override(window=win(), area=a, region=r):
        bpy.ops.object.mode_set(mode='OBJECT')
    ob = bpy.context.active_object
    C["mods_before"] = len(ob.modifiers)
    C["polys_before"] = len(ob.data.polygons)
    with bpy.context.temp_override(window=fw, screen=fw.screen, area=fa, region=fr):
        try:
            C["smooth"] = bpy.ops.allset.menu_item(item="Mesh/Smooth")
        except RuntimeError as ex:
            C["smooth"] = repr(ex)


@step
def s_check():
    ob = bpy.context.active_object
    print("AUDIT128 smooth from torn window", C.get("smooth"), len(ob.data.polygons), C.get("polys_before"))
    check(f"Mesh > Smooth runs from the torn-off Mesh menu ({C.get('smooth')}, modifiers {C.get('mods_before')} -> "
          f"{len(ob.modifiers)})", len(ob.modifiers) > C.get("mods_before", 1e9))
    lost = sorted(set(C.get("lost_obj", [])) | set(C.get("lost_edit", [])))
    check(f"every menu item that works in the viewport also works in a torn-off menu window ({len(lost)} lost: "
          f"{lost[:25]})", not lost)


run()
