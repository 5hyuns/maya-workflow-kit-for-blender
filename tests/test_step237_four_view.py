"""Issue #148: Maya Four View = four real 3D View panels, each with its own shading / Show settings / camera.

Blender's Quad View is one area cut by a cross (one header, one shading for all four). The kit now splits
the 3D View area in four (ui/four_view.py). Background mode never gives a just-split area a size (0 x 0, so
it can't be split again) and hangs in screen.area_close: making / leaving the four view is checked in
tests/gui/gui_step237_four_view.py; here the parts that don't need a window: panel settings, roles, the record.
"""

import json
from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

four_view = import_module(kit.MODULE + ".ui.four_view")
view = import_module(kit.MODULE + ".operators.view")


def check(ok, msg):
    if not ok:
        raise AssertionError(msg)


def _window():
    return bpy.context.window_manager.windows[0]


def _two():
    """Two real 3D View areas (one split works in background) -> (a, b) spaces."""
    win = _window()
    panes = four_view.panes(win.screen)
    if len(panes) < 2:
        new = four_view._split(bpy.context, win, panes[0], 'HORIZONTAL', four_view.SPLITS[0])
        check(new is not None, "one split")
        panes = four_view.panes(win.screen)
    return panes[0].spaces.active, panes[1].spaces.active


def test_two_panels_keep_their_own_shading_and_show_settings():
    a, b = _two()
    a.shading.type, b.shading.type = 'WIREFRAME', 'MATERIAL'
    a.overlay.show_floor, b.overlay.show_floor = False, True
    a.show_object_viewport_mesh = False
    check((a.shading.type, b.shading.type) == ('WIREFRAME', 'MATERIAL'), "shading per panel")
    check(b.overlay.show_floor and b.show_object_viewport_mesh, "overlays / shown types per panel")


def test_settings_travel_by_role():
    a, b = _two()
    four_view.default(a, "top", bpy.context.scene)
    a.shading.type = 'WIREFRAME'
    a.shading.show_xray = True
    four_view.default(b, "persp", bpy.context.scene)
    b.shading.type = 'SOLID'
    data = four_view.capture(a)
    json.dumps(data)                              # the record is plain JSON (saved on the Screen)
    keep = four_view.capture(b)
    four_view.apply(b, data)
    check(b.shading.type == 'WIREFRAME' and b.shading.show_xray, "shading copied")
    check(view.ortho_key(b.region_3d) == "TOP", f"camera copied {view.ortho_key(b.region_3d)}")
    four_view.apply(b, keep)
    check(b.shading.type == 'SOLID' and b.region_3d.view_perspective == 'PERSP', "back to its own")


def test_maya_cameras_per_role():
    a, _b = _two()
    want = {"top": "TOP", "front": "FRONT", "side": "SIDE-"}
    for role, key in want.items():
        four_view.default(a, role, bpy.context.scene)
        got = view.ortho_key(a.region_3d)
        check(got is not None and got.startswith(key.rstrip("-")), f"{role}: {got}")
        check(abs(a.region_3d.view_distance - view.maya_ortho_distance(a)) < 1e-6, "Maya width 30")
        check(a.region_3d.is_orthographic_side_view, "named ortho view")
    four_view.default(a, "persp", bpy.context.scene)
    check(a.region_3d.view_perspective == 'PERSP', "persp")


def _camera(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(ob)
    return ob


def _looks_through(space):
    if space.region_3d.view_perspective != 'CAMERA':
        return None
    ob = space.camera if space.use_local_camera else bpy.context.scene.camera
    return ob.name if ob is not None else None


def test_a_camera_panel_keeps_its_camera():
    """#362: a panel that looks through a camera gets it back (its own camera, zoom and offset), like a Maya panel."""
    a, b = _two()
    scene = bpy.context.scene
    scene.camera = _camera("cam_scene")
    four_view.default(a, "persp", scene)
    four_view.default(b, "top", scene)
    a.use_local_camera = True
    a.camera = _camera("cam_own")
    a.lock_camera = True
    a.region_3d.view_perspective = 'CAMERA'
    a.region_3d.view_camera_zoom = 9.0
    a.region_3d.view_camera_offset = (0.1, -0.05)
    data = four_view.capture(a)
    json.dumps(data)
    four_view.apply(b, data, scene)
    check(_looks_through(b) == "cam_own" and b.use_local_camera and b.lock_camera, f"own camera {_looks_through(b)}")
    check(scene.camera.name == "cam_scene", "the scene camera stays")
    check(abs(b.region_3d.view_camera_zoom - 9.0) < 1e-4, f"zoom {b.region_3d.view_camera_zoom}")
    check(abs(b.region_3d.view_camera_offset[0] - 0.1) < 1e-4 and abs(b.region_3d.view_camera_offset[1] + 0.05) < 1e-4,
          f"offset {tuple(b.region_3d.view_camera_offset)}")
    # the scene's camera (View > Cameras > Active Camera)
    four_view.default(a, "persp", scene)
    a.region_3d.view_perspective = 'CAMERA'
    four_view.default(b, "top", scene)
    four_view.apply(b, four_view.capture(a), scene)
    check(_looks_through(b) == "cam_scene" and not b.use_local_camera, f"scene camera {_looks_through(b)}")
    # a camera that is gone: the perspective view
    a.use_local_camera = True
    a.camera = _camera("cam_gone")
    a.region_3d.view_perspective = 'CAMERA'
    data = four_view.capture(a)
    bpy.data.objects.remove(bpy.data.objects["cam_gone"])
    four_view.default(b, "top", scene)
    four_view.apply(b, data, scene)
    check(b.region_3d.view_perspective == 'PERSP', f"gone camera -> {b.region_3d.view_perspective}")


def test_a_new_panel_has_no_camera_of_its_own():
    """A panel split off a view that looks through a camera starts with the scene camera (Blender copies the view)."""
    a, _b = _two()
    a.use_local_camera = True
    a.camera = _camera("cam_own")
    a.lock_camera = True
    four_view.default(a, "front", bpy.context.scene)
    check(not a.use_local_camera and not a.lock_camera, "local camera / camera lock off")


def test_roles_by_place():
    def area(x, y):
        return SimpleNamespace(x=x, y=y, width=100, height=80)
    tl, tr, bl, br = area(0, 80), area(100, 80), area(0, 0), area(100, 0)
    got = four_view.roles(None, [br, tl, bl, tr])
    check(got == {"top": tl, "persp": tr, "front": bl, "side": br}, got)
    check(four_view.roles(None, [tl, tr, bl]) == {}, "three panels are no four view")


def test_record_on_the_screen_and_background_refusal():
    win = _window()
    screen = win.screen
    n = len(screen.areas)
    check(four_view.enter(bpy.context, four_view.panes(screen)[0], win) == {}, "background: no four view")
    check(len(screen.areas) == n and not four_view.is_four(screen), "nothing split")
    four_view._save_state(screen, {"on": False, "single": "side"})
    check(four_view.state(screen)["single"] == "side", "state")
    check(four_view.collapse_all(bpy.context) == 0, "nothing to collapse")
    for a in four_view.panes(screen):
        check(not a.spaces.active.region_quadviews, "Blender Quad View is not used")
