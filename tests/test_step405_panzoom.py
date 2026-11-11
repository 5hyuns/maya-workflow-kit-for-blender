"""2D Pan/Zoom like Maya: the \\ key and View > Camera Tools > 2D Pan/Zoom Tool.

- \\ tapped (pressed and let go within 0.25 s) turns the view's 2D Pan/Zoom on / off, whatever happened in between; a
  longer hold never toggles. \\ held + middle drag = 2D pan (the picture follows the mouse), \\ held + right drag = 2D
  zoom (right / down = in, left / up = out, a diagonal cancels, multiplicative: zoom x exp(-d / view width)), \\ held
  + left drag does nothing. A drag turns 2D Pan/Zoom on and it stays on.
- Every view: a camera view pans / zooms Blender's camera view (offset / zoom: the camera and the render stay),
  Blender's orthographic views move the view in its plane / change its size, the perspective view turns about the
  eye / changes its lens. Off shows the view without its 2D pan / zoom (exactly the view before), on brings it back.
- 2D Pan/Zoom Tool: a tool; LMB / MMB drag pans (Mode 2D Pan) or zooms (Mode 2D Zoom, Zoom scale multiplies the
  rate), Ctrl+LMB box zooms into the box; entering it changes nothing. Its panel menu row is no longer greyed.
GUI side: tests/gui/gui_step405_panzoom.py.
"""

import math
import sys
from importlib import import_module

import bpy
from mathutils import Euler, Vector

import kit

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from test_step37_panel_menus import Ctx, _space  # noqa: E402

pz = import_module(kit.MODULE + ".operators.pan_zoom")
pm = import_module(kit.MODULE + ".ui.panel_menus")
pmd = import_module(kit.MODULE + ".ui.panel_menu_data")
notices = import_module(kit.MODULE + ".ui.notices")
camera_tools = import_module(kit.MODULE + ".ui.camera_tools")
overscan = import_module(kit.MODULE + ".operators.camera_overscan")

SIZE = (875, 698)          # a view region (px)


def _close(a, b, eps=1e-5):
    return all(abs(x - y) < eps for x, y in zip(a, b))


def _view(space):
    rv3d = space.region_3d
    return (tuple(rv3d.view_location), tuple(rv3d.view_rotation), rv3d.view_distance, space.lens)


def _same_view(a, b, eps=1e-5):
    return _close(a[0], b[0], eps) and _close(a[1], b[1], eps) and abs(a[2] - b[2]) < eps and abs(a[3] - b[3]) < eps


def _eye(rv3d):
    return rv3d.view_location + rv3d.view_rotation @ Vector((0.0, 0.0, rv3d.view_distance))


def _user_view(space, ortho=False):
    pz.clear()
    rv3d = space.region_3d
    rv3d.view_perspective = 'ORTHO' if ortho else 'PERSP'
    rv3d.view_location = (1.0, 2.0, 3.0)
    rv3d.view_rotation = (Euler((0.0, 0.0, 0.0)) if ortho else Euler((1.1, 0.0, 0.7))).to_quaternion()
    rv3d.view_distance = 20.0
    space.lens = 50.0
    return rv3d


def _camera_view(space, name="camera405p"):
    pz.clear()
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(ob)
    ob.location, ob.rotation_euler = (0.0, -10.0, 0.0), (math.radians(90.0), 0.0, 0.0)
    space.camera = ob
    space.use_local_camera = True
    rv3d = space.region_3d
    rv3d.view_perspective = 'CAMERA'
    rv3d.view_camera_zoom, rv3d.view_camera_offset = 0.0, (0.0, 0.0)
    return rv3d


# --- the rules ---------------------------------------------------------------------------------------------------

def test_tap_is_a_short_press():
    assert pz.TAP_SECONDS == 0.25
    assert pz.is_tap(0.0) and pz.is_tap(0.1) and pz.is_tap(0.25)
    assert not pz.is_tap(0.3) and not pz.is_tap(0.6) and not pz.is_tap(1.2)


def test_zoom_rule_matches_maya():
    w = 875
    assert abs(pz.zoom_factor(80, 0, w) - 0.91263) < 1e-5              # right = in
    assert abs(pz.zoom_factor(0, -80, w) - 0.91263) < 1e-5             # down = in (dy is up-positive)
    assert abs(pz.zoom_factor(-80, 0, w) - 1.09574) < 1e-5             # left = out
    assert abs(pz.zoom_factor(0, 80, w) - 1.09574) < 1e-5              # up = out
    assert abs(pz.zoom_factor(80, 80, w) - 1.0) < 1e-12                # right + up cancel
    assert abs(pz.zoom_factor(160, 0, w) - 0.83289) < 1e-5             # multiplicative
    assert abs(pz.zoom_factor(80, 0, w, scale=2.0) - 0.83289) < 1e-5   # Zoom scale multiplies the rate


def test_key_hold_buttons():
    """\\ held: MMB = pan, RMB = zoom, LMB = nothing (used up); Alt+MMB / Alt+RMB stay the camera's 3D moves."""
    assert pz.key_button('MIDDLEMOUSE') == 'PAN' and pz.key_button('RIGHTMOUSE') == 'ZOOM'
    assert pz.key_button('LEFTMOUSE') == 'NOTHING'
    assert pz.key_button('MIDDLEMOUSE', alt=True) is None and pz.key_button('RIGHTMOUSE', alt=True) is None
    assert pz.key_button('A') is None


# --- camera view ---------------------------------------------------------------------------------------------------

def test_camera_view_pan_follows_the_mouse():
    fac = overscan.zoom_to_fac(0.0)
    x, y = pz.camera_pan((0.0, 0.0), 0.0, 80, 0, *SIZE)
    assert abs(x + 80 / (2 * fac * SIZE[0])) < 1e-9 and y == 0.0
    x2, y2 = pz.camera_pan((0.0, 0.0), 0.0, 0, 80, *SIZE)      # vertical: by the view's height
    assert x2 == 0.0 and abs(y2 + 80 / (2 * fac * SIZE[1])) < 1e-9
    near = pz.camera_pan((0.0, 0.0), 100.0, 80, 0, *SIZE)       # zoomed in: a smaller step, still 1:1 on screen
    assert abs(near[0]) < abs(x) and abs(near[0] + 80 / (2 * overscan.zoom_to_fac(100.0) * SIZE[0])) < 1e-9
    assert pz.camera_pan((0.1, -0.2), 0.0, 0, 0, *SIZE) == (0.1, -0.2)


def test_camera_view_zoom_keeps_the_centre():
    z = pz.camera_zoom(0.0, 0.91263)
    assert abs(overscan.zoom_to_fac(z) / overscan.zoom_to_fac(0.0) - 1 / 0.91263) < 1e-6
    assert pz.camera_zoom(0.0, 1e-6) == overscan.ZOOM_MAX and pz.camera_zoom(0.0, 1e6) == overscan.ZOOM_MIN


def test_camera_view_drags_box_and_toggle():
    space = _space()
    rv3d = _camera_view(space)
    assert pz.kind(rv3d) == 'CAMERA' and not pz.is_on(rv3d)
    fac = overscan.zoom_to_fac(0.0)
    assert pz.pan(space, rv3d, 80, 0, SIZE)
    assert pz.is_on(rv3d) and _close(rv3d.view_camera_offset, (-80 / (2 * fac * SIZE[0]), 0.0))
    assert pz.zoom(space, rv3d, pz.zoom_factor(80, 0, SIZE[0]), SIZE)
    assert abs(overscan.zoom_to_fac(rv3d.view_camera_zoom) / fac - 1 / 0.91263) < 1e-4
    shown = (rv3d.view_camera_zoom, tuple(rv3d.view_camera_offset))
    # off: the whole frame (no window here: no pan); on: the 2D pan / zoom again; the camera never moves
    where = tuple(space.camera.matrix_world.translation)
    assert pz.toggle(space, rv3d) and not pz.is_on(rv3d) and _close(rv3d.view_camera_offset, (0.0, 0.0))
    assert pz.toggle(space, rv3d) and pz.is_on(rv3d)
    assert abs(rv3d.view_camera_zoom - shown[0]) < 1e-4 and _close(rv3d.view_camera_offset, shown[1])
    assert tuple(space.camera.matrix_world.translation) == where
    # Ctrl+LMB box (80 x 80 right-down of the middle): the box centre comes to the middle, the box fills the view
    rv3d.view_camera_zoom, rv3d.view_camera_offset = 0.0, (0.0, 0.0)
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    assert pz.box(space, rv3d, (cx, cy - 80, cx + 80, cy), SIZE)
    k = max(80 / SIZE[0], 80 / SIZE[1])
    assert abs(overscan.zoom_to_fac(rv3d.view_camera_zoom) / fac - 1 / k) < 1e-3
    assert _close(rv3d.view_camera_offset, (40 / (2 * fac * SIZE[0]), -40 / (2 * fac * SIZE[1])))
    space.region_3d.view_perspective = 'PERSP'


# --- Blender's own views ------------------------------------------------------------------------------------------

def test_persp_view_pan_turns_about_the_eye_and_off_puts_the_view_back():
    space = _space()
    rv3d = _user_view(space)
    view0, eye0 = _view(space), _eye(rv3d)
    rot0 = rv3d.view_rotation.copy()
    assert pz.kind(rv3d) == 'PERSP' and not pz.is_on(rv3d)
    assert pz.pan(space, rv3d, 80, 0, SIZE)
    assert pz.is_on(rv3d)
    f_px = space.lens * max(SIZE) / pz.VIEW_SENSOR
    fwd0, fwd = rot0 @ Vector((0, 0, -1)), rv3d.view_rotation @ Vector((0, 0, -1))
    right0, up0 = rot0 @ Vector((1, 0, 0)), rot0 @ Vector((0, 1, 0))
    # the eye stays; the view turned left (the picture followed the mouse to the right) by atan(80 / focal px)
    assert (_eye(rv3d) - eye0).length < 1e-4
    assert abs(fwd0.angle(fwd) - math.atan(80 / f_px)) < 1e-5
    assert (fwd - fwd0).dot(right0) < 0 and abs((fwd - fwd0).dot(up0)) < 1e-6
    assert abs(rv3d.view_distance - 20.0) < 1e-9 and abs(space.lens - 50.0) < 1e-9
    shown = _view(space)
    # a drag up tilts it down (the picture follows the mouse up), a drag down back
    assert pz.pan(space, rv3d, 0, 80, SIZE)
    assert (rv3d.view_rotation @ Vector((0, 0, -1)) - fwd).dot(up0) < 0
    assert pz.pan(space, rv3d, 0, -80, SIZE)
    assert _same_view(_view(space), shown, 1e-4)
    # off: exactly the view before; on: the 2D pan again
    assert pz.toggle(space, rv3d) and not pz.is_on(rv3d)
    assert _same_view(_view(space), view0)
    assert pz.toggle(space, rv3d) and pz.is_on(rv3d)
    assert _same_view(_view(space), shown, 1e-4)
    pz.clear()


def test_persp_view_zoom_is_the_lens():
    space = _space()
    rv3d = _user_view(space)
    view0 = _view(space)
    assert pz.zoom(space, rv3d, 0.91263, SIZE)
    assert abs(space.lens - 50.0 / 0.91263) < 1e-4 and pz.is_on(rv3d)
    # Blender's view lens ends at 250 mm: deeper zooms stop there, and off still gives the view back
    assert pz.zoom(space, rv3d, 0.01, SIZE)
    assert abs(space.lens - pz.LENS_MAX) < 1e-6
    assert pz.toggle(space, rv3d) and _same_view(_view(space), view0)
    # a box zoom turns to the box centre and narrows the lens by the box
    pz.clear()
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    fwd0 = rv3d.view_rotation @ Vector((0, 0, -1))
    assert pz.box(space, rv3d, (cx - 100, cy - 50, cx + 100, cy + 50), SIZE)
    assert abs(space.lens - 50.0 / max(200 / SIZE[0], 100 / SIZE[1])) < 1e-4
    assert (rv3d.view_rotation @ Vector((0, 0, -1)) - fwd0).length < 1e-6      # centred box: no turn
    pz.clear()


def test_ortho_view_pan_and_zoom_move_the_view_in_its_plane():
    space = _space()
    rv3d = _user_view(space, ortho=True)
    view0 = _view(space)
    assert pz.kind(rv3d) == 'ORTHO'
    wpp = rv3d.view_distance * pz.VIEW_SENSOR / (space.lens * max(SIZE))       # world units per pixel
    assert pz.pan(space, rv3d, 80, 0, SIZE)
    right = rv3d.view_rotation @ Vector((1, 0, 0))
    assert _close(rv3d.view_location, Vector(view0[0]) - right * 80 * wpp)
    assert abs(rv3d.view_distance - 20.0) < 1e-9 and tuple(rv3d.view_rotation) == view0[1]
    assert pz.zoom(space, rv3d, 0.5, SIZE)
    assert abs(rv3d.view_distance - 10.0) < 1e-9
    # after the zoom a pan of 80 px moves half as far (the picture still follows the mouse 1:1)
    loc = rv3d.view_location.copy()
    assert pz.pan(space, rv3d, 0, 80, SIZE)
    up = rv3d.view_rotation @ Vector((0, 1, 0))
    assert _close(rv3d.view_location, loc - up * 80 * wpp * 0.5)
    shown = _view(space)
    assert pz.toggle(space, rv3d) and _same_view(_view(space), view0)
    assert pz.toggle(space, rv3d) and _same_view(_view(space), shown)
    pz.clear()


def test_camera_moves_while_on_keep_the_2d_pan_zoom():
    """Maya: tracking / dollying the camera while 2D Pan/Zoom is on leaves the 2D values; off then shows the moved
    camera without them."""
    space = _space()
    rv3d = _user_view(space, ortho=True)
    view0 = _view(space)
    assert pz.pan(space, rv3d, 80, 0, SIZE) and pz.zoom(space, rv3d, 0.5, SIZE)
    rv3d.view_location = rv3d.view_location + Vector((0.0, 3.0, 0.0))        # a track by the user
    assert pz.toggle(space, rv3d) and not pz.is_on(rv3d)
    assert _close(rv3d.view_location, Vector(view0[0]) + Vector((0.0, 3.0, 0.0)), 1e-4)
    assert abs(rv3d.view_distance - 20.0) < 1e-6
    space2 = _space()
    rv3d2 = _user_view(space2)
    view0 = _view(space2)
    assert pz.pan(space2, rv3d2, 0, 60, SIZE) and pz.zoom(space2, rv3d2, 0.8, SIZE)
    rv3d2.view_distance = 35.0                                                # a dolly by the user
    assert pz.toggle(space2, rv3d2)
    assert abs(space2.lens - 50.0) < 1e-4 and abs(rv3d2.view_distance - 35.0) < 1e-6
    assert _close(rv3d2.view_rotation, view0[1], 1e-5)                      # the 2D turn is gone
    pz.clear()


def test_a_drag_while_off_brings_the_kept_values_back():
    """Maya keeps the 2D pan / zoom while it is off; a drag turns it on with them."""
    space = _space()
    rv3d = _user_view(space, ortho=True)
    assert pz.zoom(space, rv3d, 0.5, SIZE) and abs(rv3d.view_distance - 10.0) < 1e-9
    assert pz.toggle(space, rv3d) and abs(rv3d.view_distance - 20.0) < 1e-9 and not pz.is_on(rv3d)
    assert pz.pan(space, rv3d, 0, 0, SIZE)
    assert pz.is_on(rv3d) and abs(rv3d.view_distance - 10.0) < 1e-9
    pz.clear()


def test_views_keep_their_own_2d_state():
    """Per view and per kind: a perspective view's 2D state is not an orthographic or camera view's."""
    space = _space()
    rv3d = _user_view(space)
    assert pz.pan(space, rv3d, 40, 0, SIZE) and pz.is_on(rv3d)
    rv3d.view_perspective = 'ORTHO'
    assert not pz.is_on(rv3d)
    rv3d.view_perspective = 'PERSP'
    assert pz.is_on(rv3d)
    pz.forget(rv3d)                              # the camera frame fitted again: only the camera view forgets
    assert pz.is_on(rv3d)
    pz.clear()
    assert not pz.is_on(rv3d)


def test_toolbar_button_works_in_every_view():
    space = _space()
    _user_view(space)
    ctx = Ctx(space)
    assert pm.state(ctx, "PAN_ZOOM") is False
    assert pm.apply(ctx, "PAN_ZOOM") and pm.state(ctx, "PAN_ZOOM") is True
    assert pm.apply(ctx, "PAN_ZOOM") and pm.state(ctx, "PAN_ZOOM") is False
    pz.clear()


# --- the tool ------------------------------------------------------------------------------------------------------

def test_pan_zoom_tool():
    assert camera_tools.PAN_ZOOM_TOOL == "allset.pan_zoom_tool"
    tools = camera_tools.PAN_ZOOM_TOOLS
    assert {t.bl_context_mode for t in tools} == {'OBJECT', 'EDIT_MESH'}
    for t in tools:
        assert t.bl_idname == camera_tools.PAN_ZOOM_TOOL and t.bl_label == "2D Pan/Zoom Tool"
        assert t.bl_cursor == 'SCROLL_XY'                        # Maya's four-way arrow
        keys = {(k[1]["type"], bool(k[1].get("ctrl")), bool(k[1].get("shift"))): k[0] for k in t.bl_keymap}
        assert keys == {('LEFTMOUSE', False, False): "allset.pan_zoom_drag",
                        ('LEFTMOUSE', False, True): "allset.pan_zoom_drag",
                        ('MIDDLEMOUSE', False, False): "allset.pan_zoom_drag",
                        ('LEFTMOUSE', True, False): "allset.pan_zoom_box"}, keys
        assert not any(k[1]["type"] == 'RIGHTMOUSE' for k in t.bl_keymap)     # RMB keeps the marking menu
    # Maya's tool settings: Zoom scale 1, Mode 2D Pan / 2D Zoom
    props = bpy.ops.allset.pan_zoom_drag.get_rna_type().properties
    assert props["zoom_scale"].default == 1.0
    assert props["mode"].default == 'PAN' and [i.identifier for i in props["mode"].enum_items] == ['PAN', 'ZOOM']
    assert [i.name for i in props["mode"].enum_items] == ["2D Pan", "2D Zoom"]
    assert hasattr(bpy.types, "ALLSET_OT_pan_zoom_box")
    registered = bpy.types.VIEW3D_PT_tools_active._tools
    for mode in ('OBJECT', 'EDIT_MESH'):
        ids = set()
        for t in registered[mode]:
            for x in ((t,) if hasattr(t, "idname") else t if isinstance(t, tuple) else ()):
                ids.add(getattr(x, "idname", None))
        assert camera_tools.PAN_ZOOM_TOOL in ids, mode


def test_panel_menu_row_picks_the_tool():
    row = next(r for r in pmd.CAMERA_TOOLS if r[1] == "2D Pan/Zoom Tool")
    assert row[0] == "run" and row[2] == "wm.tool_set_by_id" and row[3] == {"name": camera_tools.PAN_ZOOM_TOOL}
    path = pmd.item_path("ALLSET_MT_panel_camera_tools", "2D Pan/Zoom Tool")
    assert path not in notices.PANEL_MENU
    working = {p for _f, p, ok in pmd.leaves() if ok}
    assert path in working


def test_keymap_item():
    kc = kit.maya_kc()
    items = [k for k in kc.keymaps["3D View"].keymap_items if k.active and k.type == 'BACK_SLASH'
             and not (k.shift or k.ctrl or k.alt)]
    assert [k.idname for k in items] == ["allset.pan_zoom_hold"] and items[0].value == 'PRESS'
