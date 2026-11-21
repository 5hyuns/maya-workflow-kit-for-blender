"""#226 in a real UI: "Keep Blender Keys" off = Tab over the viewport doesn't change the mode (Maya mode as before);
on = Tab toggles Object / Edit Mode in the 3D View (also from Edit Mode back), Alt+E toggles Local View; the Quad Draw
tool keeps its own Tab; Tab over the UV Editor, the Graph Editor and the Outliner changes no mode; off again = Tab
does nothing to the mode."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

GUI_TIMEOUT = 200
C = {}


def prefs():
    return bpy.context.preferences.addons[MODULE].preferences


def v3d_override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def to_viewport():
    _area, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


def mode():
    return bpy.context.object.mode if bpy.context.object else None


def local_view():
    area, _r = view3d()
    return area.spaces.active.local_view is not None


def tab():
    ev('TAB', 'PRESS')
    ev('TAB', 'RELEASE')


def other_area():
    """An area other than the 3D View and the dock, turned into the other editors and back: the largest one (the
    Maya layout shows no Outliner until it is asked for)."""
    if "other" not in C:
        areas = [a for a in win().screen.areas if a.type not in {'VIEW_3D', 'PROPERTIES'}]
        area = max(areas, key=lambda a: a.width * a.height)
        C["other"], C["other_type"] = area.as_pointer(), area.ui_type
    return next(a for a in win().screen.areas if a.as_pointer() == C["other"])


def over(area):
    r = next(r for r in area.regions if r.type == 'WINDOW')
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
    check(f"the preference is off by default ({prefs().keep_blender_keys})", not prefs().keep_blender_keys)
    to_viewport()
    tab()


@step
def s_off_tab():
    check(f"off: Tab over the viewport keeps Object Mode ({mode()})", mode() == 'OBJECT')
    ev('ESC', 'PRESS')          # the operator search Tab opens
    ev('ESC', 'RELEASE')


@step
def s_on():
    bpy.data.objects[C["cube"]].rotation_euler.z = 0.5
    prefs().keep_blender_keys = True
    to_viewport()
    tab()


@step
def s_on_tab_edit():
    check(f"on: Tab over the viewport goes to Edit Mode ({mode()})", mode() == 'EDIT')
    tab()


@step
def s_on_tab_object():
    check(f"on: Tab again goes back to Object Mode ({mode()})", mode() == 'OBJECT')
    ev('E', 'PRESS', alt=True)
    ev('E', 'RELEASE', alt=True)


@step
def s_local_view_on():
    check(f"on: Alt+E turns Local View on ({local_view()})", local_view())
    ev('E', 'PRESS', alt=True)
    ev('E', 'RELEASE', alt=True)


@step
def s_local_view_off():
    check(f"on: Alt+E again turns it off ({local_view()})", not local_view())
    ob = bpy.data.objects[C["cube"]]
    check(f"on: Alt+E leaves the rotation alone ({ob.rotation_euler.z})", abs(ob.rotation_euler.z - 0.5) < 1e-6)
    tab()                       # to Edit Mode for the Quad Draw and UV Editor checks


@step
def s_quad_draw():
    check(f"in Edit Mode again ({mode()})", mode() == 'EDIT')
    with v3d_override():
        bpy.ops.allset.quad_draw_start()
    ev('TAB', 'PRESS')


@step
def s_quad_draw_held():
    check(f"Quad Draw: Tab is Quad Draw's Tab, the mode stays ({mode()})", mode() == 'EDIT')
    ev('TAB', 'RELEASE')


@step
def s_quad_draw_released():
    check(f"Quad Draw: still Edit Mode after Tab ({mode()})", mode() == 'EDIT')
    with v3d_override():
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    area = other_area()
    area.ui_type = 'UV'


@step
def s_uv():
    over(other_area())
    tab()


@step
def s_uv_done():
    check(f"UV Editor: Tab changes no mode ({mode()}, {other_area().ui_type})", mode() == 'EDIT')
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')
    other_area().ui_type = 'FCURVES'


@step
def s_graph():
    over(other_area())
    tab()


@step
def s_graph_done():
    check(f"Graph Editor: Tab changes no mode ({mode()}, {other_area().ui_type})", mode() == 'EDIT')
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')
    other_area().ui_type = 'OUTLINER'


@step
def s_outliner():
    over(other_area())
    tab()


@step
def s_outliner_done():
    check(f"Outliner: Tab changes no mode ({mode()})", mode() == 'EDIT')
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')
    other_area().ui_type = C["other_type"]
    to_viewport()
    tab()


@step
def s_back_to_object():
    check(f"on: Tab over the viewport leaves Edit Mode ({mode()})", mode() == 'OBJECT')
    prefs().keep_blender_keys = False
    to_viewport()
    tab()


@step
def s_off_again():
    check(f"off again: Tab keeps Object Mode ({mode()})", mode() == 'OBJECT')
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')
    ev('E', 'PRESS', alt=True)
    ev('E', 'RELEASE', alt=True)


@step
def s_off_alt_e():
    ob = bpy.data.objects[C["cube"]]
    check(f"off again: Alt+E is no Local View ({local_view()})", not local_view())
    check(f"off again: Alt+E clears the rotation as before ({ob.rotation_euler.z})", abs(ob.rotation_euler.z) < 1e-6)


run()
