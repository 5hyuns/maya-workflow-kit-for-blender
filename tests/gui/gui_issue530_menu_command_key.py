"""#530 / #531 in a real UI.

#530: the kit Hotkey Editor finds "Merge to Center" (a menu item without a Maya hotkey); Assign New Hotkey takes a
pressed key, and that key over the viewport merges the selected vertices at their centre, like the menu item.
#531: Mesh Display > Apply Color shows the colour at once: the Solid viewport switches to the colour attribute, as
Maya turns the mesh's Display Colors on."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

GUI_TIMEOUT = 150
C = {}
KEY = dict(type='F5', ctrl=True, alt=True, shift=True)


def mod(name):
    return import_module(MODULE + name)


def hk():
    """(window, area, WINDOW region) of the Hotkey Editor, else (None, None, None)."""
    mw = mod(".ui.marked_window")
    w = mw.find_window(bpy.context, "HOTKEY_EDITOR")
    if w is None:
        return None, None, None
    area = next(a for a in w.screen.areas if mw.kind_of(a) == "HOTKEY_EDITOR")
    return w, area, next(r for r in area.regions if r.type == 'WINDOW')


def ev2(type, value, **kw):
    """An event into the Hotkey Editor window (sim.ev always goes to the main window)."""
    w, _a, region = hk()
    kw.setdefault("x", region.x + region.width // 2)
    kw.setdefault("y", region.y + region.height // 2)
    w.event_simulate(type=type, value=value, **kw)


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def merge_row():
    return next(r for r in mod(".ui.hotkey_editor").rows() if r["command"] == "MergeToCenter")


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_open():
    bpy.ops.allset.keymap_activate()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["open"] = bpy.ops.allset.menu_item(item="Windows/Settings/Preferences/Hotkey Editor")


@step
def s_opened():
    redraw()


@step
def s_search():
    w, _area, _region = hk()
    check(f"the Hotkey Editor is open ({C['open']})", w is not None)
    wm = bpy.context.window_manager
    wm.allset_hk_search = "merge to center"
    shown = [r.command for r in wm.allset_hk_rows]
    check(f"searching 'merge to center' finds the menu item ({shown})", "Merge to Center" in shown)
    wm.allset_hk_active = shown.index("Merge to Center") if "Merge to Center" in shown else 0
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
def s_press():
    wm = bpy.context.window_manager
    check(f"Assign New Hotkey waits for a key ({C.get('capture')}, capturing={wm.allset_hk_capture})",
          wm.allset_hk_capture)
    if hk()[0] is not None:
        ev2(value='PRESS', **KEY)
        ev2(value='RELEASE', **KEY)


@step
def s_pending():
    wm = bpy.context.window_manager
    if wm.allset_hk_capture and wm.allset_hk_pending and hk()[0] is not None:     # a used key: Enter takes it
        ev2('RET', 'PRESS')
        ev2('RET', 'RELEASE')


@step
def s_assigned():
    he = mod(".ui.hotkey_editor")
    wm = bpy.context.window_manager
    text = he.kit_text(bpy.context, merge_row())
    check(f"the pressed key is Merge to Center's ({text!r}, capturing={wm.allset_hk_capture})",
          text == "Ctrl+Alt+Shift+F5 *" and not wm.allset_hk_capture)
    if wm.allset_hk_capture:
        ev2('ESC', 'PRESS')
        ev2('ESC', 'RELEASE')
    w = hk()[0]
    if w is not None:
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


@step
def s_mesh():
    ctx = bpy.context
    me = bpy.data.meshes.new("i530")
    bm = bmesh.new()
    for co in ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 2.0, 0.0)):
        bm.verts.new(co)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("i530", me)
    ctx.scene.collection.objects.link(ob)
    for o in ctx.view_layer.objects:
        o.select_set(False)
    ctx.view_layer.objects.active = ob
    ob.select_set(True)
    area, region = view3d()
    with ctx.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me)
    for v in bm.verts:
        v.select_set(v.index in (0, 1))
    bm.select_flush_mode()
    bmesh.update_edit_mesh(me)
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 2)


@step
def s_key():
    area, region = view3d()
    ev(value='PRESS', x=region.x + region.width // 2, y=region.y + region.height // 2, **KEY)
    ev(value='RELEASE', x=region.x + region.width // 2, y=region.y + region.height // 2, **KEY)


@step
def s_merged():
    ob = bpy.data.objects["i530"]
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='OBJECT')
    xs = sorted(round(v.co.x, 3) for v in ob.data.vertices)
    check(f"the key over the viewport merges the two vertices at their centre ({xs})",
          len(ob.data.vertices) == 2 and 1.0 in xs)
    he = mod(".ui.hotkey_editor")
    he.restore(bpy.context, merge_row())
    check("Restore takes the key away again", he.kit_text(bpy.context, merge_row()) == "—")


@step
def s_apply_color():
    """#531: Apply Color on a cube in the Solid viewport."""
    area, region = view3d()
    space = area.spaces.active
    space.shading.type = 'SOLID'
    space.shading.color_type = 'MATERIAL'
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
        C["apply"] = bpy.ops.allset.menu_item(item="Mesh Display/Apply Color")


@step
def s_colors_shown():
    area, _region = view3d()
    ob = bpy.context.active_object
    attr = ob.data.color_attributes.active_color if ob is not None and ob.type == 'MESH' else None
    shading = area.spaces.active.shading
    check(f"Apply Color writes the colour set ({C.get('apply')}, {attr.name if attr else None})", attr is not None)
    check(f"the Solid viewport shows the colours at once (color type {shading.color_type})",
          shading.color_type == 'VERTEX')


run()
