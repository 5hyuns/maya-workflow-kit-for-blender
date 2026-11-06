"""#321: Lighting/Shading > Light Linking Editor and Windows > Relationship Editors > Light Linking open a window that
shows the light's links: a Properties window on the Object tab with only the Light Linking / Shadow Linking panels
(Blender's property search opens them), in EEVEE and in Cycles. With a mesh active and a light selected the window
is pinned to the light; with the light active it follows the active object."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import check, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
CASES = [("BLENDER_EEVEE", "Lighting/Shading/Light Linking Editor/Light-Centric", "cube"),
         ("CYCLES", "Windows/Relationship Editors/Light Linking/Object-Centric", "cube"),
         ("CYCLES", "Lighting/Shading/Light Linking Editor", "light"),
         ("BLENDER_EEVEE", "Windows/Relationship Editors/Light Linking/Light-Centric", "light")]


def override():
    a, region = view3d()
    return bpy.context.temp_override(window=win(), screen=win().screen, area=a, region=region)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    with override():
        bpy.ops.allset.create(kind='CUBE')
        C["cube"] = bpy.context.view_layer.objects.active.name
        bpy.ops.allset.create(kind='POINT_LIGHT')
        C["light"] = bpy.context.view_layer.objects.active.name


def case(i):
    engine, path, active = CASES[i]

    def s_open():
        scene = bpy.context.scene
        scene.render.engine = engine
        for ob in scene.objects:
            ob.select_set(ob.name in (C["cube"], C["light"]))
        bpy.context.view_layer.objects.active = bpy.data.objects[C[active]]
        C["n"] = len(bpy.context.window_manager.windows)
        C["tries"] = 0
        with override():
            C["res"] = bpy.ops.allset.menu_item(item=path)

    def s_check():
        wins = bpy.context.window_manager.windows
        w = wins[-1] if len(wins) > C["n"] else None
        a = w.screen.areas[0] if w else None
        sp = a.spaces.active if a is not None and a.type == 'PROPERTIES' else None
        ctx = sp.context if sp is not None else None
        C["tries"] += 1
        if ctx != 'OBJECT' and C["tries"] < 15:          # the tab is set from a timer once the window has drawn
            sim._steps.insert(0, s_check)
            return
        pinned = sp.pin_id.name if sp is not None and sp.use_pin_id and sp.pin_id else None
        want = C["light"] if active == "cube" else None
        check(f"{engine} {path} ({C['res']}), {active} active: a Properties window on the Object tab "
              f"({ctx}), search {sp.search_filter if sp else None!r}, pinned to {pinned}",
              ctx == 'OBJECT' and sp.search_filter == "Light Linking" and pinned == want)
        if SHOTS and w is not None:
            with bpy.context.temp_override(window=w):
                bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, f"gui_issue321_light_linking_{i}.png"))

    step(s_open)
    step(s_check)


for _i in range(len(CASES)):
    case(_i)


@step
def s_follow():
    """The unpinned window (light active) shows whatever is active next, like Blender's Properties."""
    w = bpy.context.window_manager.windows[-1]
    sp = w.screen.areas[0].spaces.active
    check("with the light active the window isn't pinned", not sp.use_pin_id)


run()
