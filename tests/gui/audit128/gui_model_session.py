"""Audit 128 dogfood session (modeling lane): Maya Workflow Kit layout, pCube1, keys as a Maya user types them.
Each check states the Maya behaviour (PASS = Maya-like). Prints AUDIT lines with observed values."""

import os
import sys
from importlib import import_module

import bpy
import bmesh

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win  # noqa: E402

GUI_TIMEOUT = 240
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def ts():
    return bpy.context.scene.tool_settings


def in_v3d(fn, *a, **kw):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return fn(*a, **kw)


def centre():
    _a, r = view3d()
    return r.x + r.width // 2, r.y + r.height // 2


def hover():
    x, y = centre()
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


def ob():
    return bpy.context.active_object


def faces():
    o = bpy.data.objects[C["ob"]]
    if o.mode == 'EDIT':
        return len(bmesh.from_edit_mesh(o.data).faces)
    return len(o.data.polygons)


def modals():
    return [op.bl_idname for op in win().modal_operators]


def shot(name):
    if SHOTS:
        with bpy.context.temp_override(window=win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    bpy.ops.allset.layout_install()
    bpy.ops.wm.read_homefile(app_template="Maya_Workflow_Kit")


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    in_v3d(bpy.ops.allset.create, kind='CUBE')
    C["ob"] = ob().name
    print("AUDIT created", C["ob"], "soft obj/edit", ts().use_proportional_edit_objects, ts().use_proportional_edit)
    check("startup: soft select off (objects and components)",
          not ts().use_proportional_edit_objects and not ts().use_proportional_edit)
    hover()


@step
def s_b_object():
    tap('B')        # soft select on, in object mode


@step
def s_f11():
    C["soft_obj"] = ts().use_proportional_edit_objects
    hover()
    tap('F11')      # face mode


@step
def s_after_f11():
    print("AUDIT after B (object) + F11:", bpy.context.mode, "objects", ts().use_proportional_edit_objects,
          "edit", ts().use_proportional_edit)
    check("B in object mode turned soft select on", C["soft_obj"])
    check("Soft select is one Maya setting: still on after F11 (component mode)", ts().use_proportional_edit)
    ts().use_proportional_edit = False
    ts().use_proportional_edit_objects = False
    o = bpy.data.objects[C["ob"]]
    bm = bmesh.from_edit_mesh(o.data)
    for f in bm.faces:
        f.select_set(False)
    for f in bm.faces:   # deselect first: a later face's select_set(False) would drop shared verts
        if f.normal.z > 0.9:
            f.select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(o.data)
    C["f0"] = faces()
    hover()
    ev('E', 'PRESS', ctrl=True)
    ev('E', 'RELEASE', ctrl=True)


@step
def s_extruded():
    C["f1"] = faces()
    print("AUDIT Ctrl+E faces", C["f0"], "->", C["f1"], "modals", modals())
    check(f"Ctrl+E extrudes the face ({C['f0']} -> {C['f1']})", C["f1"] == C["f0"] + 4)
    hover()
    tap('G')         # Maya: G = repeat last command (polyExtrudeFacet again)


@step
def s_repeat():
    C["f2"] = faces()
    print("AUDIT G after Ctrl+E faces", C["f1"], "->", C["f2"], "modals", modals())
    check(f"G repeats the extrude ({C['f1']} -> {C['f2']})", C["f2"] == C["f1"] + 4)
    if modals():
        tap('ESC')
    C["f3"] = faces()
    hover()
    ev('B', 'PRESS', ctrl=True)
    ev('B', 'RELEASE', ctrl=True)


@step
def s_bevel():
    C["bevel_modal"] = [m for m in modals() if "BEVEL" in m.upper()]
    print("AUDIT Ctrl+B faces", C["f3"], "->", faces(), "modals", modals())
    shot("model_bevel.png")
    check(f"Ctrl+B bevels at once, no modal left waiting for a click (modals={modals()})", not C["bevel_modal"])
    if C["bevel_modal"]:
        x, y = centre()
        ev('MOUSEMOVE', 'NOTHING', x=x + 40, y=y)


@step
def s_bevel_end():
    if C["bevel_modal"]:
        tap('ESC')     # what a Maya user does when the "bevel follows the mouse"


@step
def s_bevel_after():
    C["f4"] = faces()
    print("AUDIT after Ctrl+B (+ESC if modal) faces", C["f3"], "->", C["f4"])
    check(f"Ctrl+B leaves a bevel ({C['f3']} -> {C['f4']})", C["f4"] > C["f3"])
    # Ctrl+D with a face selected: Maya duplicates the whole object (pCube2), the mesh keeps its faces, no move
    o = bpy.data.objects[C["ob"]]
    bm = bmesh.from_edit_mesh(o.data)
    for f in bm.faces:
        f.select_set(False)
    bm.faces.ensure_lookup_table()
    bm.faces[0].select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(o.data)
    C["n_obj"] = len(bpy.context.scene.objects)
    C["f5"] = faces()
    hover()
    ev('D', 'PRESS', ctrl=True)
    ev('D', 'RELEASE', ctrl=True)


@step
def s_dup_edit():
    C["dup_modals"] = modals()
    print("AUDIT Ctrl+D in face mode: objects", C["n_obj"], "->", len(bpy.context.scene.objects), "faces", C["f5"],
          "->", faces(), "modals", C["dup_modals"])
    if C["dup_modals"]:
        tap('ESC')


@step
def s_dup_edit_check():
    check(f"Ctrl+D (face mode) = new object pCube2, pCube1 faces unchanged (objects {len(bpy.context.scene.objects)}, "
          f"faces {C['f5']} -> {faces()}, modal {C['dup_modals']})",
          len(bpy.context.scene.objects) == C["n_obj"] + 1 and faces() == C["f5"])
    hover()
    tap('THREE')


@step
def s_smooth3():
    o = bpy.data.objects[C["ob"]]
    C["mods3"] = [m.type for m in o.modifiers]
    print("AUDIT 3 in edit mode modifiers", C["mods3"])
    check("3 = smooth preview in component mode too", 'SUBSURF' in C["mods3"])
    hover()
    tap('ONE')


@step
def s_smooth1():
    o = bpy.data.objects[C["ob"]]
    vis = [m.type for m in o.modifiers if m.show_viewport]
    print("AUDIT 1 visible modifiers", vis)
    check("1 hides the smooth preview", 'SUBSURF' not in vis)
    hover()
    tap('F8')


@step
def s_obj():
    print("AUDIT F8 mode", bpy.context.mode)
    check("F8 -> object mode", bpy.context.mode == 'OBJECT')


run()
