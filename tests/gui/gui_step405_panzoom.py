"""2D Pan/Zoom in a real UI (Maya Workflow Kit layout): the \\ key and View > Camera Tools > 2D Pan/Zoom Tool.

Persp view (Blender's own view): a \\ tap turns 2D Pan/Zoom on (nothing moves), a second tap turns it off; \\ held +
middle drag right 80 px moves the picture 80 px with the mouse and 2D Pan/Zoom stays on after the key is let go; \\
held + right drag right 80 px zooms in (lens / exp(-80 / view width)) without opening the marking menu; \\ held + left
drag does nothing (view and selection kept); a quick \\ press + middle drag + release is a tap: off again, and the view
is exactly the one before every 2D move. Top view (orthographic): \\ + middle drag up 80 px moves the picture up 80 px,
a tap puts the view back. Camera view: \\ + middle drag right / up 80 px moves the picture 80 px right / up (the
camera stays), \\ + right drag zooms by the same rule, tap off = the whole frame, tap on = the 2D pan / zoom back.
2D Pan/Zoom Tool (picked from the panel's View > Camera Tools row): picking it keeps 2D Pan/Zoom off; LMB drag right /
MMB drag up pan 80 px; Ctrl+LMB box zooms into the box (its centre comes to the middle); Mode 2D Zoom: LMB drag zooms,
Zoom scale 2 doubles the rate; RMB opens the marking menu, not a pan; Esc keeps the tool, Q leaves it, Y comes back; a
\\ tap still toggles. Shots with ``--shots``."""

import json
import math
import os
import sys
from importlib import import_module

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
TOOL = "allset.pan_zoom_tool"


def mod(name):
    return import_module(f"{MODULE}.{name}")


def pz():
    return mod("operators.pan_zoom")


def space():
    return view3d()[0].spaces.active


def rv():
    return view3d()[1].data


def is_on():
    return pz().is_on(rv())


def mid():
    _a, r = view3d()
    return r.x + r.width // 2, r.y + r.height // 2


def at(p):
    """Region position of world point ``p`` in the main view."""
    _a, r = view3d()
    return view3d_utils.location_3d_to_region_2d(r, r.data, Vector(p))


def fac():
    return mod("operators.camera_overscan").zoom_to_fac(rv().view_camera_zoom)


def view_now():
    r = rv()
    return (tuple(r.view_location), tuple(r.view_rotation), r.view_distance, space().lens, r.view_perspective,
            tuple(r.view_camera_offset), r.view_camera_zoom)


def same(a, b, eps=1e-4):
    def flat(v):
        out = []
        for x in v:
            if isinstance(x, (tuple, list)):
                out += list(x)
            elif isinstance(x, str):
                out.append(x)
            else:
                out.append(x)
        return out
    fa, fb = flat(a), flat(b)
    return len(fa) == len(fb) and all((x == y) if isinstance(x, str) else abs(x - y) < eps for x, y in zip(fa, fb))


def moved(key, want, eps=1.5):
    """The picture point recorded under ``key`` moved by ``want`` px on screen."""
    p = at(C[key + "_p"])
    if p is None:
        return False, None
    d = (p.x - C[key + "_px"].x, p.y - C[key + "_px"].y)
    return abs(d[0] - want[0]) < eps and abs(d[1] - want[1]) < eps, (round(d[0], 2), round(d[1], 2))


def mark(key, p):
    C[key + "_p"] = Vector(p)
    C[key + "_px"] = at(p).copy()


def tool_id():
    t = win().workspace.tools.from_space_view3d_mode('OBJECT', create=False)
    return t.idname if t else ""


def tool_props():
    return win().workspace.tools.from_space_view3d_mode('OBJECT', create=False).operator_properties(
        "allset.pan_zoom_drag")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def modal_ids():
    return [op.bl_idname for op in win().modal_operators]


def held_drag(button, dx, dy, key=True, mods=None):
    """Steps: [\\ press +] button press at the middle, 4 moves, button release [+ \\ release] (0.8 s: a hold)."""
    mods = mods or {}

    def a():
        x, y = mid()
        if mods.get("ctrl"):
            ev('LEFT_CTRL', 'PRESS', ctrl=True)
        if mods.get("shift"):
            ev('LEFT_SHIFT', 'PRESS', shift=True)
        if key:
            ev('BACK_SLASH', 'PRESS')
        ev(button, 'PRESS', x=x, y=y, **mods)

    def b():
        x, y = mid()
        for i in range(1, 5):
            ev('MOUSEMOVE', 'NOTHING', x=x + dx * i // 4, y=y + dy * i // 4, **mods)

    def c():
        x, y = mid()
        ev(button, 'RELEASE', x=x + dx, y=y + dy, **mods)
        if key:
            ev('BACK_SLASH', 'RELEASE')
        if mods.get("shift"):
            ev('LEFT_SHIFT', 'RELEASE')
        if mods.get("ctrl"):
            ev('LEFT_CTRL', 'RELEASE')
        x, y = mid()
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    for f in (a, b, c):
        step(f)


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 0.0))
    r = rv()
    r.view_perspective = 'PERSP'
    r.view_location = (0.0, 0.0, 0.0)
    r.view_distance = 30.0
    pz().clear()
    x, y = mid()
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    redraw()


@step
def s_persp():
    C["view0"] = view_now()
    C["sel0"] = [o.name for o in bpy.context.scene.objects if o.select_get()]
    check(f"the main view is Blender's persp view ({rv().view_perspective}), 2D Pan/Zoom off",
          rv().view_perspective == 'PERSP' and not is_on() and C["sel0"])
    tap('BACK_SLASH')


@step
def s_tap_on():
    check("persp: a \\ tap turns 2D Pan/Zoom on", is_on())
    check("... and nothing moves", same(view_now(), C["view0"]))
    tap('BACK_SLASH')


@step
def s_tap_off():
    check("persp: a second \\ tap turns it off", not is_on() and same(view_now(), C["view0"]))
    mark("pan", (0.0, 0.0, 0.0))
    C["eye0"] = rv().view_location + rv().view_rotation @ Vector((0.0, 0.0, rv().view_distance))


held_drag('MIDDLEMOUSE', 80, 0)


@step
def s_mmb_check():
    ok, d = moved("pan", (80, 0))
    eye = rv().view_location + rv().view_rotation @ Vector((0.0, 0.0, rv().view_distance))
    check(f"persp: \\ held + middle drag right 80 px moves the picture with the mouse ({d})", ok)
    check("... the eye stays and the lens stays", (eye - C["eye0"]).length < 1e-3
          and abs(space().lens - C["view0"][3]) < 1e-6)
    check("... and 2D Pan/Zoom stays on after the key is let go", is_on())
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_step405_persp_pan.png"))
    C["lens1"] = space().lens


held_drag('RIGHTMOUSE', 80, 0)


@step
def s_rmb_check():
    want = C["lens1"] / pz().zoom_factor(80, 0, view3d()[1].width)
    check(f"persp: \\ held + right drag right 80 px zooms in ({C['lens1']:.3f} -> {space().lens:.3f}, want "
          f"{want:.3f})", abs(space().lens - want) < 1e-3)
    check(f"... without a marking menu ({modal_ids()})", "ALLSET_OT_mm_engine" not in modal_ids())
    C["view1"] = view_now()


held_drag('LEFTMOUSE', 120, -60)


@step
def s_lmb_check():
    sel = [o.name for o in bpy.context.scene.objects if o.select_get()]
    check("persp: \\ held + left drag does nothing (view and selection kept)",
          same(view_now(), C["view1"]) and sel == C["sel0"] and is_on())


@step
def s_quick():
    x, y = mid()
    ev('BACK_SLASH', 'PRESS')
    ev('MIDDLEMOUSE', 'PRESS', x=x, y=y)
    for i in range(1, 5):
        ev('MOUSEMOVE', 'NOTHING', x=x + 10 * i, y=y)
    ev('MIDDLEMOUSE', 'RELEASE', x=x + 40, y=y)
    ev('BACK_SLASH', 'RELEASE')
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_quick_check():
    check("persp: a quick \\ press + middle drag + release is a tap: 2D Pan/Zoom off", not is_on())
    check("... and the view is exactly the one before every 2D move", same(view_now(), C["view0"]))
    r = rv()
    r.view_perspective = 'ORTHO'
    r.view_rotation = (1.0, 0.0, 0.0, 0.0)          # looking down -Z: the top view
    r.view_location = (0.0, 0.0, 0.0)
    r.view_distance = 20.0
    redraw()


@step
def s_top():
    C["top0"] = view_now()
    check("top view: 2D Pan/Zoom off", rv().view_perspective == 'ORTHO' and not is_on())
    mark("top", (0.0, 0.0, 0.0))


held_drag('MIDDLEMOUSE', 0, 80)


@step
def s_top_check():
    ok, d = moved("top", (0, 80))
    check(f"top: \\ held + middle drag up 80 px moves the picture up 80 px ({d})", ok and is_on())
    tap('BACK_SLASH')


@step
def s_top_off():
    check("top: a tap turns it off and puts the view back", not is_on() and same(view_now(), C["top0"]))
    cam = bpy.data.objects.new("camera405", bpy.data.cameras.new("camera405"))
    bpy.context.scene.collection.objects.link(cam)
    cam.location, cam.rotation_euler = (0.0, -10.0, 0.0), (math.radians(90.0), 0.0, 0.0)
    rv().view_perspective = 'PERSP'
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.panel_look_through(camera=cam.name)
    redraw()


@step
def s_cam():
    redraw()


@step
def s_cam_ready():
    C["cam_loc"] = tuple(bpy.data.objects["camera405"].location)
    C["cam0"] = view_now()
    check(f"camera view, 2D Pan/Zoom off ({rv().view_perspective})", rv().view_perspective == 'CAMERA' and not is_on())
    mark("cam", (0.0, 0.0, 0.0))


held_drag('MIDDLEMOUSE', 80, 0)


@step
def s_cam_right():
    ok, d = moved("cam", (80, 0))
    check(f"camera: \\ held + middle drag right 80 px moves the picture 80 px ({d})", ok and is_on())
    check("... the camera stays", tuple(bpy.data.objects["camera405"].location) == C["cam_loc"])
    mark("cam", (0.0, 0.0, 0.0))


held_drag('MIDDLEMOUSE', 0, 80)


@step
def s_cam_up():
    ok, d = moved("cam", (0, 80))
    check(f"camera: \\ held + middle drag up 80 px moves the picture up 80 px ({d})", ok)
    C["fac1"] = fac()


held_drag('RIGHTMOUSE', 80, 0)


@step
def s_cam_zoom():
    want = 1.0 / pz().zoom_factor(80, 0, view3d()[1].width)
    got = fac() / C["fac1"]
    check(f"camera: \\ held + right drag right 80 px zooms in ({got:.4f}, want {want:.4f})", abs(got - want) < 1e-3)
    C["cam1"] = view_now()
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_step405_camera_pan_zoom.png"))
    tap('BACK_SLASH')


@step
def s_cam_off():
    off = tuple(rv().view_camera_offset)
    check(f"camera: a tap turns it off: the whole frame ({off})", not is_on() and abs(off[0]) < 1e-6
          and abs(off[1]) < 1e-6)
    tap('BACK_SLASH')


@step
def s_cam_on():
    check("camera: a tap turns it on: the 2D pan / zoom comes back", is_on() and same(view_now(), C["cam1"]))
    tap('BACK_SLASH')        # off before the tool


@step
def s_pick_tool():
    check("camera: off again", not is_on())
    pz().forget(rv())           # the tool checks start from no kept 2D pan / zoom (a drag would bring it back first)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.panel_run(op="wm.tool_set_by_id", props=json.dumps({"name": TOOL}))
    redraw()


@step
def s_tool_on():
    check(f"View > Camera Tools > 2D Pan/Zoom Tool picks the tool ({tool_id()})", tool_id() == TOOL)
    check("... picking it leaves 2D Pan/Zoom off", not is_on())
    mark("tool", (0.0, 0.0, 0.0))


held_drag('LEFTMOUSE', 80, 0, key=False)


@step
def s_tool_lmb():
    ok, d = moved("tool", (80, 0))
    check(f"tool: LMB drag right 80 px pans 80 px ({d}) and turns 2D Pan/Zoom on", ok and is_on())
    mark("tool", (0.0, 0.0, 0.0))


held_drag('MIDDLEMOUSE', 0, 80, key=False)


@step
def s_tool_mmb():
    ok, d = moved("tool", (0, 80))
    check(f"tool: MMB drag up 80 px pans 80 px ({d})", ok)
    _a, r = view3d()
    cx, cy = r.width // 2, r.height // 2          # the box: from the middle (whole px) 80 px right and down
    C["box_p"] = view3d_utils.region_2d_to_location_3d(r, r.data, (cx + 40, cy - 40), Vector((0.0, 0.0, 0.0)))
    C["fac2"] = fac()


held_drag('LEFTMOUSE', 80, -80, key=False, mods={"ctrl": True})


@step
def s_tool_box():
    _a, r = view3d()
    p = at(C["box_p"])
    k = max(80 / r.width, 80 / r.height)
    got = fac() / C["fac2"]
    check(f"tool: Ctrl+LMB box zooms into the box ({got:.3f}, want {1 / k:.3f})", abs(got - 1 / k) / (1 / k) < 0.02)
    check(f"... and its centre comes to the middle ({p}, middle {r.width / 2}, {r.height / 2})",
          p is not None and abs(p.x - r.width / 2) < 3 and abs(p.y - r.height / 2) < 3)
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_step405_tool_box.png"))
    tool_props().mode = 'ZOOM'
    C["fac3"] = fac()


held_drag('LEFTMOUSE', 80, 0, key=False)


@step
def s_tool_zoom():
    want = 1.0 / pz().zoom_factor(80, 0, view3d()[1].width)
    got = fac() / C["fac3"]
    check(f"tool: Mode 2D Zoom, LMB drag right 80 px zooms in ({got:.4f}, want {want:.4f})", abs(got - want) < 1e-3)
    tool_props().zoom_scale = 2.0
    C["fac4"] = fac()


held_drag('LEFTMOUSE', 80, 0, key=False)


@step
def s_tool_scale():
    want = 1.0 / pz().zoom_factor(80, 0, view3d()[1].width) ** 2
    got = fac() / C["fac4"]
    check(f"tool: Zoom scale 2 doubles the rate ({got:.4f}, want {want:.4f})", abs(got - want) < 2e-3)
    p = tool_props()
    p.mode, p.zoom_scale = 'PAN', 1.0
    C["view_rmb"] = view_now()
    x, y = mid()
    ev('RIGHTMOUSE', 'PRESS', x=x, y=y)


@step
def s_tool_rmb():
    ids = modal_ids()
    check(f"tool: RMB opens the marking menu ({ids})", "ALLSET_OT_mm_engine" in ids)
    x, y = mid()
    ev('RIGHTMOUSE', 'RELEASE', x=x, y=y)
    tap('ESC')


@step
def s_tool_esc():
    check("... and doesn't pan / zoom", same(view_now(), C["view_rmb"]))
    tap('ESC')


@step
def s_tool_kept():
    check(f"tool: Esc keeps the tool ({tool_id()})", tool_id() == TOOL)
    tap('Q')


@step
def s_tool_q():
    check(f"tool: Q leaves it ({tool_id()})", tool_id() != TOOL)


@step
def s_wait():
    tap('Y')


@step
def s_tool_y():
    check(f"tool: Y comes back to it ({tool_id()})", tool_id() == TOOL)
    C["on_before"] = is_on()
    tap('BACK_SLASH')


@step
def s_tool_tap():
    check("tool: a \\ tap still toggles 2D Pan/Zoom", is_on() != C["on_before"])
    tap('Q')


run()
