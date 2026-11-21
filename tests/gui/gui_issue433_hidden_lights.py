"""#433: a panel's Show > None then Show > Polygons hides the light shapes in that view and the lights still light the
shaded view, like Maya (Show > Lights only hides the light icons). Blender draws light, camera and locator shapes
together (overlay Extras), so with cameras shown the lights are hidden by type and stop lighting the view."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
TMP = os.environ.get("ALLSET_GUI_TMP", "") or bpy.app.tempdir
C = {}
WAIT = 12            # timer ticks for the material preview to settle after a change


def _wait():
    for _ in range(WAIT):
        step(lambda: None)


def _mean(path, area):
    """Mean brightness of the 3D View area in a window screenshot (0..1)."""
    import numpy as np
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    px = px.reshape(h, w, 4)[area.y + 20:area.y + area.height - 40, area.x + 20:area.x + area.width - 20, :3]
    return float(px.mean())


def _shot(name):
    path = os.path.join(TMP, f"gui_issue433_{name}.png")
    screenshot(path)
    C[name] = _mean(path, C["area"])
    if SHOTS:
        screenshot(os.path.join(SHOTS, f"gui_issue433_{name}.png"))


@step
def s_setup():
    setup()
    scene = bpy.context.scene
    for ob in list(scene.objects):
        if ob.type != 'LIGHT':
            bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("pPlane1")
    me.from_pydata([(-20, -20, 0), (20, -20, 0), (20, 20, 0), (-20, 20, 0)], [], [(0, 1, 2, 3)])
    scene.collection.objects.link(bpy.data.objects.new("pPlane1", me))
    lamp = next(ob for ob in scene.objects if ob.type == 'LIGHT')
    lamp.location = (0.0, 0.0, 3.0)
    lamp.data.energy = 3000.0
    C["lamp"] = lamp
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)
    if world.node_tree and "Background" in world.node_tree.nodes:
        world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    area, _r = view3d()
    C["area"] = area
    sp = area.spaces.active
    sp.shading.type = 'MATERIAL'
    sp.shading.use_scene_lights = True
    sp.shading.use_scene_world = True
    sp.overlay.show_overlays = False
    sp.region_3d.view_perspective = 'ORTHO'
    sp.region_3d.view_rotation = (1.0, 0.0, 0.0, 0.0)      # top view
    sp.region_3d.view_location = (0.0, 0.0, 0.0)
    sp.region_3d.view_distance = 12.0


_wait()


def _panel_set(key):
    area = C["area"]
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.panel_set(key=key)


@step
def s_shown():
    _shot("shown")
    _panel_set("SHOW_NONE")                         # Show > None, then Show > Polygons
    C["area"].spaces.active.show_object_viewport_mesh = True
    C["area"].tag_redraw()


_wait()


@step
def s_hidden():
    _shot("hidden")
    sp = C["area"].spaces.active
    from importlib import import_module
    from sim import MODULE
    ps = import_module(MODULE + ".ui.panel_state")
    with bpy.context.temp_override(window=win(), area=C["area"]):
        C["lights_row"] = ps.state(bpy.context, "SHOW_LIGHTS")
    C["extras"] = sp.overlay.show_extras
    _panel_set("SHOW_CAMERAS")                      # a camera shown again: Blender can't keep only the lights' light
    C["mixed"] = (sp.show_object_viewport_light, sp.overlay.show_extras)
    _panel_set("SHOW_CAMERAS")
    C["back"] = (sp.show_object_viewport_light, sp.overlay.show_extras)
    _panel_set("SHOW_ALL")
    C["all"] = (sp.show_object_viewport_light, sp.overlay.show_extras)
    C["lamp"].data.energy = 0.0
    C["area"].tag_redraw()


_wait()


@step
def s_dark():
    _shot("dark")
    C["lamp"].data.energy = 3000.0


@step
def s_check():
    shown, hidden, dark = C["shown"], C["hidden"], C["dark"]
    print(f"GUI INFO brightness shown {shown:.4f} hidden {hidden:.4f} no light {dark:.4f}", flush=True)
    check(f"the light lights the view ({shown:.3f} > {dark:.3f})", shown > dark + 0.02)
    check(f"Show > None + Polygons: the hidden light still lights the view ({hidden:.3f} ~ {shown:.3f})",
          abs(hidden - shown) < 0.25 * (shown - dark))
    check(f"... the Show > Lights row is off ({C['lights_row']}) and the light shapes are hidden (Extras "
          f"{C['extras']})", C["lights_row"] is False and C["extras"] is False)
    check(f"... Cameras on: lights hidden by type, camera shapes drawn {C['mixed']}", C["mixed"] == (False, True))
    check(f"... Cameras off again: the lights light the view again {C['back']}", C["back"] == (True, False))
    check(f"... Show > All: lights and their shapes shown {C['all']}", C["all"] == (True, True))


run()
