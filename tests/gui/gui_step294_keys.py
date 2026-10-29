"""#215 #212 in a real UI: Move tool, Ctrl held before the press on the Z arrow = Z only with grid snapping, Ctrl
first on the XY plane handle = moves in XY with snapping (no box select), Ctrl+click on the centre keeps the
selection; Shift+W / E / R key Translate / Rotate / Scale over the Outliner, Time Slider, Channel Box dock, Graph
Editor (graph and channel list) and Dope Sheet, never in edit mode; the Attribute Editor shows keyed channels in
the key colour."""

import os
import sys
from importlib import import_module

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_location_3d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import (MODULE, check, dock_area, ev, run, step, setup, screenshot, view3d, win, scale,  # noqa: E402
                 load_maya_layout)

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
STEPS = 8


def mod(name):
    return import_module(f"{MODULE}.{name}")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def ob1():
    return bpy.data.objects["pCube1"]


def screen(world):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, world)
    return Vector((region.x + p.x, region.y + p.y))


def px_world(at):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, at)
    w = region_2d_to_location_3d(region, region.data, p + Vector((1, 0)), at)
    return (w - at).length


def handle_point(axis, frac):
    c = ob1().matrix_world.translation
    n = mod("ui.manipulator").ARROW_PX * bpy.context.preferences.view.gizmo_size / 75.0 * scale()
    return screen(c + Vector(axis) * n * frac * px_world(c))


def hover(p):
    ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))
    ev('MOUSEMOVE', 'NOTHING', x=int(p.x) + 1, y=int(p.y))


def ctrl_drag(start, end):
    """Steps: hover; real Ctrl key, then the press; moves (own steps); release, Ctrl up; one more tick."""
    def s1():
        hover(start())

    def s2():
        ev('LEFT_CTRL', 'PRESS', ctrl=True)
        C["a"], C["b"] = start(), end()
        ev('LEFTMOUSE', 'PRESS', x=int(C["a"].x), y=int(C["a"].y), ctrl=True)

    def s3():
        a, b = C["a"], C["b"]
        q = a + (b - a) * (2 / STEPS)
        ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), ctrl=True)

    def s3b():
        a, b = C["a"], C["b"]
        for i in range(3, STEPS + 1):
            q = a + (b - a) * (i / STEPS)
            ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), ctrl=True)

    def s4():
        ev('LEFTMOUSE', 'RELEASE', x=int(C["b"].x), y=int(C["b"].y), ctrl=True)
        ev('LEFT_CTRL', 'RELEASE')

    def s5():
        print("STEP294 last ops", [op.bl_idname for op in bpy.context.window_manager.operators][-3:])
    for s in (s1, s2, s3, s3b, s4, s5):
        step(s)


def whole_cm(v):
    k = mod("operators.units").maya_unit()
    return abs(v / k - round(v / k)) < 1e-3


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_cube():
    bpy.ops.allset.keymap_activate()
    view3d()[1].data.view_distance *= 2.0
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
    ob1().location = (0.0313, 0.0271, 0.0)      # off the grid: a snapped move lands on whole cm
    C["start"] = ob1().location.copy()
    redraw()


ctrl_drag(lambda: handle_point((0, 0, 1), 0.6), lambda: handle_point((0, 0, 1), 0.6) + Vector((4, 90)))


@step
def s_z_check():
    d = ob1().location - C["start"]
    k = mod("operators.units").maya_unit()
    check(f"#215 Ctrl first + Z arrow: Z only ({d.x / k:.3f}, {d.y / k:.3f}, {d.z / k:.3f} cm)",
          abs(d.x) < 1e-7 and abs(d.y) < 1e-7 and abs(d.z) > 0.5 * k)
    check(f"#215 ... with grid snapping (Z moved {d.z / k:.4f} cm)", whole_cm(d.z))
    h = mod("operators.manip").HANDLES.get('TRANSLATE')
    check(f"#215 Z is the active handle ({h})", h is not None and tuple(h["constraint_axis"]) == (False, False, True))
    ob1().location = C["start"]
    C["sel"] = [o.name for o in bpy.context.selected_objects]
    redraw()


ctrl_drag(lambda: handle_point((1, 1, 0), 0.6), lambda: handle_point((1, 1, 0), 0.6) + Vector((-70, -40)))


@step
def s_plane_check():
    d = ob1().location - C["start"]
    k = mod("operators.units").maya_unit()
    last = [op.bl_idname for op in bpy.context.window_manager.operators][-1:]
    check(f"#215 Ctrl first + XY plane handle moves in XY ({d.x / k:.3f}, {d.y / k:.3f}, {d.z / k:.3f} cm, {last})",
          abs(d.z) < 1e-7 and (abs(d.x) > 0.5 * k or abs(d.y) > 0.5 * k))
    check(f"#215 ... with grid snapping (moved {d.x / k:.4f}, {d.y / k:.4f} cm)", whole_cm(d.x) and whole_cm(d.y))
    check("#215 ... no box select (selection kept)", [o.name for o in bpy.context.selected_objects] == C["sel"])
    C["l2"] = ob1().location.copy()
    hover(screen(ob1().matrix_world.translation))


@step
def s_center_ctrl():
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    p = screen(ob1().matrix_world.translation)
    ev('LEFTMOUSE', 'PRESS', x=int(p.x), y=int(p.y), ctrl=True)


@step
def s_center_ctrl_up():
    p = screen(ob1().matrix_world.translation)
    ev('LEFTMOUSE', 'RELEASE', x=int(p.x), y=int(p.y), ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


@step
def s_center_check():
    h = mod("operators.manip").HANDLES.get('TRANSLATE')
    check(f"Ctrl+click on the centre frees the active handle ({h})", h is None)
    check("... doesn't move the cube", (ob1().location - C["l2"]).length < 1e-7)
    check(f"... keeps the selection ({[o.name for o in bpy.context.selected_objects]})",
          [o.name for o in bpy.context.selected_objects] == C["sel"])


ctrl_drag(lambda: screen(ob1().matrix_world.translation),
          lambda: screen(ob1().matrix_world.translation) + Vector((50, 30)))


@step
def s_center_drag_check():
    d = ob1().location - C["l2"]
    k = mod("operators.units").maya_unit()
    check(f"#215 Ctrl first + centre drag moves ({d.x / k:.3f}, {d.y / k:.3f}, {d.z / k:.3f} cm)", d.length > 0.5 * k)
    check(f"#215 ... with grid snapping (moved {d.x / k:.4f}, {d.y / k:.4f}, {d.z / k:.4f} cm)",
          all(whole_cm(v) for v in d))


# --- #212 Shift+W / E / R in every editor -----------------------------------------------------------------------

def area_of(pred):
    return next((a for a in win().screen.areas if pred(a)), None)


def region_centre(area, rtype='WINDOW'):
    r = next(r for r in area.regions if r.type == rtype)
    return Vector((r.x + r.width // 2, r.y + r.height // 2))


EXPECT = {"W": "location", "E": "rotation_euler", "R": "scale"}


def shift_key(name, where, key):
    def s1():
        if ob1().animation_data:
            ob1().animation_data_clear()
        p = where()
        C["where_" + name] = p
        if p is None:
            return
        hover(p)

    def s2():
        if C["where_" + name] is None:
            return
        ev('LEFT_SHIFT', 'PRESS', shift=True)
        ev(key, 'PRESS', shift=True)
        ev(key, 'RELEASE', shift=True)
        ev('LEFT_SHIFT', 'RELEASE')

    def s3():
        if C["where_" + name] is None:
            check(f"#212 {name}: area found", False)
            return
        paths = sorted({fc.data_path for fc in _fcurves(ob1())})
        check(f"#212 Shift+{key} over {name} keys {EXPECT[key]} only ({paths})", paths == [EXPECT[key]])
    for s in (s1, s2, s3):
        step(s)


def _fcurves(ob):
    return list(mod("compat").id_fcurves(ob))


@step
def s_keys_setup():
    ob1().location = (0.0, 0.0, 0.0)
    for o in bpy.context.scene.objects:
        o.select_set(o == ob1())
    bpy.context.view_layer.objects.active = ob1()
    dock_area('CHANNEL_BOX')
    redraw()


shift_key("the Outliner", lambda: (lambda a: region_centre(a) if a else None)(area_of(lambda a: a.type == 'OUTLINER')),
          "W")
shift_key("the Time Slider", lambda: (lambda a: region_centre(a) if a else None)(
    area_of(lambda a: a.type == 'DOPESHEET_EDITOR' and a.ui_type == 'TIMELINE')), "E")
shift_key("the Channel Box dock", lambda: region_centre(dock_area()), "R")


@step
def s_to_graph():
    a = area_of(lambda a: a.type == 'OUTLINER')
    C["outliner"] = a.as_pointer() if a else None
    if a is not None:
        a.ui_type = 'FCURVES'
    redraw()


def _converted():
    return area_of(lambda a: a.as_pointer() == C.get("outliner"))


shift_key("the Graph Editor", lambda: region_centre(_converted()) if _converted() else None, "W")
shift_key("the Graph Editor channel list", lambda: region_centre(_converted(), 'CHANNELS') if _converted() else None,
          "W")


@step
def s_to_dope():
    a = _converted()
    if a is not None:
        a.ui_type = 'DOPESHEET'
    redraw()


shift_key("the Dope Sheet", lambda: region_centre(_converted()) if _converted() else None, "R")


@step
def s_back_outliner():
    a = _converted()
    if a is not None:
        a.ui_type = 'OUTLINER'
    if ob1().animation_data:
        ob1().animation_data_clear()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='EDIT')
    hover(region_centre(area))


@step
def s_edit_key():
    ev('LEFT_SHIFT', 'PRESS', shift=True)
    ev('W', 'PRESS', shift=True)
    ev('W', 'RELEASE', shift=True)
    ev('LEFT_SHIFT', 'RELEASE')


@step
def s_edit_check():
    check(f"#212 Shift+W in edit mode keys nothing ({[fc.data_path for fc in _fcurves(ob1())]})",
          not _fcurves(ob1()))
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='OBJECT')


# --- #212 AE key colour -----------------------------------------------------------------------------------------

@step
def s_ae():
    ob = ob1()
    ob.location = (0.0, 0.0, 0.25)
    ob.keyframe_insert("location", index=2, frame=bpy.context.scene.frame_current)
    ob.keyframe_insert("rotation_euler", index=1, frame=bpy.context.scene.frame_current + 10)   # animated, no key here
    bpy.context.window_manager.allset_dock = 'ATTRIBUTE_EDITOR'
    bpy.context.window_manager.allset_ae_tab = "T"
    redraw()


for _i in range(4):
    step(redraw)


@step
def s_ae_shot():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_step294_ae_keyed.png"))
    cbm = mod("ui.channel_box")
    check("#212 AE state: tz keyed, ry animated, tx plain",
          cbm.channel_state(ob1(), "tz") == 'KEYED' and cbm.channel_state(ob1(), "ry") == 'ANIMATED'
          and cbm.channel_state(ob1(), "tx") is None)
    bpy.context.window_manager.allset_dock = 'CHANNEL_BOX'
    redraw()


for _i in range(3):
    step(redraw)


@step
def s_cb_shot():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_step294_cb_keyed.png"))


run()
