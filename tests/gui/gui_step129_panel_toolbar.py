"""Step 129 (#10): every button of the Maya panel toolbar clicked twice with simulated mouse clicks in the Maya
Workflow Kit layout — state before -> click -> after -> click -> after.

The viewport looks through a camera (so the camera buttons are enabled) and a cube is selected (Isolate Select).
Toggles must change on the first click and come back on the second (Maya iconTextCheckBox); commands act; greyed
buttons change nothing. Value fields (exposure / gamma / view transform) are not clicked."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, button_under_mouse, check, ev, run, screenshot, setup, step, view3d, win, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 420
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {"buttons": {}, "rows": []}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def header():
    area, _r = view3d()
    return area, next(r for r in area.regions if r.type == 'TOOL_HEADER')


def snapshot():
    area, _r = view3d()
    sp = area.spaces.active
    sh, ov = sp.shading, sp.overlay
    scene = bpy.context.scene
    cam = bpy.data.objects.get(C.get("cam", ""))
    vs = scene.view_settings
    tool = bpy.context.workspace.tools.from_space_view3d_mode('OBJECT', create=False)
    return {
        "shading": sh.type, "light": sh.light, "color": sh.color_type, "shadows": sh.show_shadows,
        "cavity": sh.show_cavity, "xray": sh.show_xray, "dof": sh.use_dof, "wire_on_shaded": ov.show_wireframes,
        "xray_bone": ov.show_xray_bone, "grid": mod("ui.maya_grid").visible(sp),
        "cam_locked": bool(cam and all(cam.lock_location) and all(cam.lock_rotation)),
        "film_gate": bool(cam and cam.data.show_sensor), "gate_mask": bool(cam and cam.data.show_passepartout),
        "safe": bool(cam and cam.data.show_safe_areas), "isolate": sp.local_view is not None,
        "exposure": round(vs.exposure, 3), "gamma": round(vs.gamma, 3), "cm": vs.view_transform,
        "selected": tuple(sorted(o.name for o in scene.objects if o.select_get())),
        "objects": len(scene.objects), "tool": tool.idname if tool else "",
        "camera_view": sp.region_3d.view_perspective,
    }


def diff(a, b):
    return {k: (a[k], b[k]) for k in a if a[k] != b[k]}


@step
def s_setup():
    setup()
    # Maya density (effective UI scale 1.0) so the whole toolbar fits the header: since step 130 the kit no longer
    # sets Blender's UI scale, and at 1.25 the toolbar is cut off (#52). Sandbox preferences only.
    bpy.context.preferences.view.ui_scale = round(1.0 / max(bpy.context.preferences.system.ui_scale, 0.1), 3)
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CAMERA')
        C["cam"] = bpy.context.view_layer.objects.active.name
        bpy.ops.allset.panel_look_through(camera=C["cam"])
        bpy.ops.allset.create(kind='CUBE')
    C["cube"] = bpy.context.view_layer.objects.active.name
    vs = bpy.context.scene.view_settings
    vs.exposure, vs.gamma = 1.0, 1.4      # non-default, so the exposure / gamma icons have a value to switch
    for a in win().screen.areas:
        a.tag_redraw()


def sweep():
    """One probe per tick along the tool header's middle row, 4 px apart: every button's command and x range."""
    state = {}

    def look():
        area, region = header()
        if not state:
            state["x"] = region.x + 2
            state["y"] = region.y + region.height // 2
        else:
            path, cmd = button_under_mouse(area, region)
            key = cmd or path
            if key:
                lo, hi = C["buttons"].get(key, (state["x"], state["x"]))
                C["buttons"][key] = (min(lo, state["x"]), max(hi, state["x"]))
            state["x"] += 4
            if state["x"] >= region.x + region.width - 2:
                return
        ev('MOUSEMOVE', 'NOTHING', x=state["x"], y=state["y"])
        import sim
        sim._steps.insert(0, look)
    return look


step(sweep())


@step
def s_found():
    _a, region = header()
    names = list(C["buttons"])
    print("PT buttons", len(names))
    for k, v in C["buttons"].items():
        print("PT", v, k)
    pt = mod("ui.panel_toolbar")
    expected = sum(len(g) for g in pt.TOOLBAR)
    clickable = [k for k in names if "view_settings." not in k]
    check(f"panel toolbar: every icon found under the mouse ({len(clickable)} buttons, {expected} icons + 3 colour "
          "management icons)", len(clickable) >= expected + 3)
    C["queue"] = clickable
    C["y"] = region.y + region.height // 2
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_step129_toolbar_camera_view.png"))


def label_of(cmd):
    pt = mod("ui.panel_toolbar")
    for group in pt.TOOLBAR:
        for _g, kind, data, label in group:
            if kind == "set" and f"key='{data}'" in cmd:
                return label
            if kind == "prop" and cmd.endswith(f"{data[0] if data[0] != 'space' else ''}.{data[1]}".lstrip(".")):
                return label
            if kind == "run" and f'"{data[0]}"' in cmd:
                return label
            if kind == "grey" and f"Panel toolbar/{label}" in cmd:
                return label
    for key, label in (("EXPOSURE", "Exposure icon"), ("GAMMA", "Gamma icon"), ("CM_ENABLE", "Colour management")):
        if f"key='{key}'" in cmd:
            return label
    return cmd


def kind_of(cmd):
    if "menu_unavailable" in cmd:
        return "grey"
    if "SELECT_CAMERA" in cmd or "panel_run" in cmd:
        return "command"
    return "toggle"


def click_steps():
    def hover():
        if not C["queue"]:
            return
        cmd = C["queue"][0]
        lo, hi = C["buttons"][cmd]
        C["xy"] = ((lo + hi) // 2, C["y"])
        C["s0"] = snapshot()
        ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0], y=C["xy"][1])

    def click():
        if C["queue"]:
            ev('LEFTMOUSE', 'PRESS', x=C["xy"][0], y=C["xy"][1])
            ev('LEFTMOUSE', 'RELEASE', x=C["xy"][0], y=C["xy"][1])

    def mid():
        if C["queue"]:
            C["s1"] = snapshot()
            ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0] + 1, y=C["xy"][1])

    def end():
        if not C["queue"]:
            return
        cmd = C["queue"].pop(0)
        s0, s1, s2 = C["s0"], C["s1"], snapshot()
        C["rows"].append((label_of(cmd), kind_of(cmd), cmd, diff(s0, s1), diff(s1, s2), diff(s0, s2)))
        if "SELECT_CAMERA" in cmd or "wm.tool_set_by_id" in cmd:   # put the cube selection / Move tool back
            scene = bpy.context.scene
            for ob in scene.objects:
                ob.select_set(ob.name == C["cube"])
            bpy.context.view_layer.objects.active = scene.objects[C["cube"]]
            area, region = view3d()
            with bpy.context.temp_override(window=win(), area=area, region=region):
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        import sim
        if C["queue"]:
            for f in reversed(seq):
                sim._steps.insert(0, f)
    seq = (hover, click, mid, click, end)
    return seq


for _f in click_steps():
    step(_f)


@step
def s_table():
    print("TABLE | Button | kind | 1st click | 2nd click | net |")
    for label, kind, cmd, d1, d2, d0 in C["rows"]:
        print(f"TABLE | {label} | {kind} | {d1} | {d2} | {d0} |")
        if kind == "toggle":
            check(f"toolbar {label}: click turns it on, click again gives the start back ({d1} / {d0})",
                  d1 and not d0)
        elif kind == "grey":
            check(f"toolbar {label}: greyed button changes nothing ({d1})", not d1 and not d0)
        else:
            check(f"toolbar {label}: command acts ({d1} {d2})", d1 or d2)


run(interval=0.12)
