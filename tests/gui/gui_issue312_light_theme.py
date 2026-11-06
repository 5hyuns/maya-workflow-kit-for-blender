"""Issue #312 in a real UI: with Blender's Light theme the kit-drawn Graph Editor list, Time Slider and Range Slider
turn light too (screenshots); the factory theme comes back at the end."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, screenshot, setup, step, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def light_preset():
    for d in bpy.utils.preset_paths("interface_theme"):
        for f in os.listdir(d):
            if "light" in f.lower() and f.endswith(".xml"):
                return os.path.join(d, f)
    return None


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_light():
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    for f, v in ((1, 0.0), (24, 5.0)):
        ob.location.x = v
        ob.keyframe_insert("location", index=0, frame=f)
    sc.frame_set(12)
    path = light_preset()
    check(f"Blender ships a light theme preset ({path})", path is not None)
    bpy.ops.script.execute_preset(filepath=path, menu_idname="USERPREF_MT_interface_theme_presets")
    th = bpy.context.preferences.themes[0]
    C["back"] = tuple(th.dopesheet_editor.space.back)
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    area.ui_type = 'FCURVES'
    C["area"] = area


@step
def s_wait():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_check():
    tf = import_module(MODULE + ".ui.theme_follow")
    ec = import_module(MODULE + ".ui.editor_chrome")
    ts = import_module(MODULE + ".ui.time_slider")
    back = tf.follow(ec.BACK, "graph_editor", "back")
    ruler = ts._themed(ts.RULER_BG, "back")
    d = C["back"][0] - tf.FACTORY["back"][0]
    check(f"light theme (background {C['back'][0]:.2f}, +{d:.2f}): list {back[0]:.2f}, ruler {ruler[0]:.2f} move with it",
          d > 0.1 and abs(back[0] - (ec.BACK[0] + d)) < 1e-3 and abs(ruler[0] - (ts.RULER_BG[0] + d)) < 1e-3)
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue312_light.png"))


@step
def s_back():
    bpy.ops.preferences.reset_default_theme()
    tf = import_module(MODULE + ".ui.theme_follow")
    check("factory theme again", abs(tf.theme_color("graph_editor", "back")[0] - tf.FACTORY["back"][0]) < 1e-3)


run()
