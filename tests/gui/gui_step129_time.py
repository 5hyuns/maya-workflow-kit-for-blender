"""Step 129 (issues #37, #38) in the Maya Workflow Kit layout: S over the viewport keys the cube and the Time
Slider shows a red tick at that frame even while it is the current frame (Blender's playhead box drew over it);
the Auto Key button is Maya's key button and keys a changed, already keyed channel on another frame."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, find_button, run, screenshot, setup, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def shot(name):
    path = os.path.join(SHOTS or os.path.join(os.environ.get("TEMP", "."), "gui129"), name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    screenshot(path)
    return path


def timeline():
    for area in win().screen.areas:
        if area.type == 'DOPESHEET_EDITOR' and area.spaces.active.mode == 'TIMELINE':
            return (area, next(r for r in area.regions if r.type == 'WINDOW'),
                    next(r for r in area.regions if r.type == 'HEADER'))
    raise LookupError("no timeline")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def red_in(path, x0, x1, y0, y1):
    """Count of key-red pixels in the window rect [x0, x1) x [y0, y1) (y from the bottom) of a screenshot."""
    im = bpy.data.images.load(path, check_existing=False)
    w, _h = im.size
    px = im.pixels[:]
    bpy.data.images.remove(im)
    n = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            i = (y * w + x) * 4
            r, g, b = px[i], px[i + 1], px[i + 2]
            if r > 0.75 and g < 0.25 and b < 0.25:
                n += 1
    return n


def frame_x(f):
    _a, r, _h = timeline()
    return r.x + int(r.view2d.view_to_region(f, 0, clip=False)[0])


@step
def s_setup():
    setup()
    bpy.ops.allset.layout_install()
    bpy.ops.wm.read_homefile(app_template="Maya_Workflow_Kit")


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    sc = bpy.context.scene
    sc.frame_set(10)
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 3)


@step
def s_key():
    tap('S')        # Maya Set Key over the viewport


@step
def s_wait():
    redraw()


@step
def s_tick_shot():
    ob = bpy.data.objects["pCube1"]
    check("S keyed the cube at frame 10", ob.animation_data is not None and ob.animation_data.action is not None)
    path = shot("gui_step129_key_current.png")
    _a, r, _h = timeline()
    x = frame_x(10)
    n = red_in(path, x - 6, x + 7, r.y, r.y + r.height)
    check(f"#38: the key at the current frame shows red around the playhead on the Time Slider ({n} red px)",
          n >= 15)
    bpy.context.scene.frame_set(20)
    redraw()


@step
def s_other_frame_shot():
    path = shot("gui_step129_key_other.png")
    _a, r, _h = timeline()
    x = frame_x(10)
    n = red_in(path, x - 3, x + 4, r.y, r.y + r.height)
    check(f"#38: the key at frame 10 shows a red tick while the time is 20 ({n} red px)", n >= 15)


step(find_button(lambda: timeline()[0::2], lambda path, cmd: "use_keyframe_insert_auto" in path, C, "auto",
                     step_px=6))


@step
def s_click_auto():
    pos = C.get("auto")
    check(f"#37: the Auto Key button is in the Time Slider strip ({pos})", pos is not None)
    if pos:
        ev('MOUSEMOVE', 'NOTHING', x=pos[0], y=pos[1])


@step
def s_press_auto():
    if C.get("auto"):
        ev('LEFTMOUSE', 'PRESS')
        ev('LEFTMOUSE', 'RELEASE')


@step
def s_auto_on():
    ts = bpy.context.scene.tool_settings
    check("#37: clicking it turns Auto Key on", ts.use_keyframe_insert_auto)
    redraw()


@step
def s_auto_shot():
    shot("gui_step129_auto_key_on.png")
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.transform.translate(value=(2.0, 0.0, 0.0))
    ob = bpy.data.objects["pCube1"]
    fc = ob.animation_data.action.fcurves.find("location", index=0)
    frames = sorted(round(k.co.x) for k in fc.keyframe_points) if fc else []
    check(f"#37: moving the keyed cube at frame 20 with Auto Key on keys it there ({frames})", 20 in frames)
    sx = ob.animation_data.action.fcurves.find("scale", index=0)
    check("#37: the moved channels are keyed, scale keeps its one key",
          sx is not None and len(sx.keyframe_points) == 1)


run()
