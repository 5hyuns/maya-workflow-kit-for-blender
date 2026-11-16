"""#381 in a real UI: in the Hotkey Editor, the second Undo row (Maya's Ctrl+Z) is told apart from the first (z);
Assign New Hotkey + Y warns that Y is used (NonSacredTool = Last Tool in Object Mode and in Mesh) and Return gives Y to
Undo; the Last Tool keys lose it, so Y over the viewport undoes, in object mode and in mesh edit mode, and the other
Undo row keeps z. Restore All Maya Hotkeys gives every key back."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

GUI_TIMEOUT = 200
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def shot(name):
    w = hk()[0]
    if SHOTS and w is not None:
        with bpy.context.temp_override(window=w):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def mod(name):
    return import_module(MODULE + name)


def he():
    return mod(".ui.hotkey_editor")


def hk():
    """(window, area, WINDOW region) of the Hotkey Editor, else (None, None, None)."""
    mw = mod(".ui.marked_window")
    w = mw.find_window(bpy.context, "HOTKEY_EDITOR")
    if w is None:
        return None, None, None
    area = next(a for a in w.screen.areas if mw.kind_of(a) == "HOTKEY_EDITOR")
    return w, area, next(r for r in area.regions if r.type == 'WINDOW')


def ev2(type, value, **kw):
    """An event into the Hotkey Editor window, mid-region (sim.ev always goes to the main window)."""
    w, _a, r = hk()
    kw.setdefault("x", r.x + r.width // 2)
    kw.setdefault("y", r.y + r.height // 2)
    w.event_simulate(type=type, value=value, **kw)


def row(command, maya_key):
    return next(r for r in he().rows() if r["command"] == command and r["maya_key"] == maya_key)


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def v3d_override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def to_viewport():
    _area, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    with v3d_override():
        bpy.ops.allset.create(kind='CUBE')
    C["cube"] = bpy.context.active_object.name
    to_viewport()
    with v3d_override():
        C["open"] = bpy.ops.allset.menu_item(item="Windows/Settings/Preferences/Hotkey Editor")


@step
def s_opened():
    redraw()


@step
def s_search():
    w, _a, _r = hk()
    check(f"the Hotkey Editor opens ({C['open']})", w is not None)
    if w is None:
        return
    wm = bpy.context.window_manager
    wm.allset_hk_search = "undo"
    shown = [(r.command, r.maya_key) for r in wm.allset_hk_rows]
    check(f"the two Undo rows are told apart ({shown})",
          ("Undo", "Z") in shown and ("Undo (2nd hotkey)", "Ctrl+Z") in shown)
    i = next((i for i, r in enumerate(wm.allset_hk_rows) if r.maya_key == "Ctrl+Z" and r.command.startswith("Undo")),
             -1)
    wm.allset_hk_active = i
    redraw()


@step
def s_capture():
    w, area, region = hk()
    if w is None:
        return
    ev2('MOUSEMOVE', 'NOTHING')
    with bpy.context.temp_override(window=w, area=area, region=region):
        C["capture"] = bpy.ops.allset.hotkey_assign('INVOKE_DEFAULT')
    redraw()


@step
def s_press_y():
    wm = bpy.context.window_manager
    check(f"Assign New Hotkey waits for a key ({C.get('capture')}, capturing={wm.allset_hk_capture})",
          wm.allset_hk_capture)
    if hk()[0] is not None:
        ev2('Y', 'PRESS')
        ev2('Y', 'RELEASE')
    redraw()


@step
def s_warned():
    wm = bpy.context.window_manager
    pending = getattr(wm, "allset_hk_pending", "")
    check(f"Y warns that it is used by NonSacredTool in Object Mode and Mesh ({pending!r})",
          wm.allset_hk_capture and "NonSacredTool (Object Mode, Mesh)" in pending)
    shot("gui_issue381_warning.png")


@step
def s_confirm():
    if hk()[0] is not None:
        ev2('RET', 'PRESS')
        ev2('RET', 'RELEASE')
    redraw()


@step
def s_assigned():
    wm = bpy.context.window_manager
    ctx = bpy.context
    undo2, undo1, nst = row("Undo", "Ctrl+Z"), row("Undo", "Z"), row("NonSacredTool", "Y")
    texts = (he().kit_text(ctx, undo2), he().kit_text(ctx, undo1), he().kit_text(ctx, nst))
    check(f"Return gives Y to the second Undo row, the first keeps z, NonSacredTool lost Y ({texts}, "
          f"capturing={wm.allset_hk_capture})", texts == ("Y *", "Z", "— *") and not wm.allset_hk_capture)
    shot("gui_issue381_assigned.png")
    to_viewport()
    obj = bpy.data.objects[C["cube"]]
    C["x0"] = obj.location.x
    obj.location.x += 2.0
    with v3d_override():
        bpy.ops.ed.undo_push(message="Move")


@step
def s_y_object():
    ev('Y', 'PRESS')
    ev('Y', 'RELEASE')


@step
def s_y_object_done():
    obj = bpy.data.objects[C["cube"]]
    check(f"Y over the viewport undoes in object mode (x {C['x0']} -> {obj.location.x})",
          abs(obj.location.x - C["x0"]) < 1e-4)
    with v3d_override():
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set('EXEC_DEFAULT', True, mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        C["z0"] = max(v.co.z for v in bmesh.from_edit_mesh(obj.data).verts)
        bpy.ops.transform.translate('EXEC_DEFAULT', True, value=(0.0, 0.0, 1.0))
    C["z1"] = max(v.co.z for v in bmesh.from_edit_mesh(obj.data).verts)
    to_viewport()


@step
def s_y_mesh():
    ev('Y', 'PRESS')
    ev('Y', 'RELEASE')


@step
def s_y_mesh_done():
    obj = bpy.data.objects[C["cube"]]
    z = max(v.co.z for v in bmesh.from_edit_mesh(obj.data).verts) if obj.mode == 'EDIT' else None
    check(f"Y over the viewport undoes in mesh edit mode (z {C['z0']} -> {C['z1']} -> {z}, {obj.mode})",
          obj.mode == 'EDIT' and z is not None and abs(z - C["z0"]) < 1e-4 and abs(C["z1"] - C["z0"]) > 0.5)
    if obj.mode != 'OBJECT':
        with v3d_override():
            bpy.ops.object.mode_set(mode='OBJECT')
    C["restore"] = bpy.ops.allset.hotkey_restore(all=True)


@step
def s_restored():
    ctx = bpy.context
    texts = (he().kit_text(ctx, row("Undo", "Ctrl+Z")), he().kit_text(ctx, row("NonSacredTool", "Y")))
    check(f"Restore All Maya Hotkeys gives Ctrl+Z and Y back ({C['restore']}, {texts})", texts == ("Ctrl+Z", "Y"))
    check("no user-modified keymap left",
          not any(km.is_user_modified for km in bpy.context.window_manager.keyconfigs.user.keymaps))
    w = hk()[0]
    if w is not None:
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


run()
