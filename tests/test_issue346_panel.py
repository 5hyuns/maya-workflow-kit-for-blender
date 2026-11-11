"""#346: the viewport panel's Bookmarks and 2D Pan/Zoom buttons work like Maya's, and a panel torn off the Maya
Workflow Kit layout keeps the panel menu bar and toolbar.

- A window of one area showing a Maya workspace (Panels > Tear Off / Tear Off Copy) is a Maya layout view: its header
  draws the panel menu bar, its tool header the panel toolbar and no Status Line. GUI side:
  tests/gui/gui_issue346_tear_off.py.
- Bookmarks: the toolbar button adds a camera bookmark (cameraView1, cameraView2 ..., gaps not filled) on the view's
  camera (the camera's place and lens) or, in Blender's persp / top / front / side view, on that startup camera (the
  view itself); View > Bookmarks and the button's right-click menu list them, picking one puts the view back (with
  undo for a camera), a locked camera stays. A 2D bookmark keeps the camera view's 2D pan / zoom.
- 2D Pan/Zoom: per view; off shows the whole camera frame and remembers the 2D pan / zoom, on brings it back; the \\
  key (2D pan / zoom) turns it on. Blender's own views have it too (tests/test_step405_panzoom.py); 2D bookmarks
  need a camera view.
"""

import math
import sys
import types
from importlib import import_module

import bpy
from mathutils import Matrix

import kit

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from test_step106_tool_settings_ae import Recorder  # noqa: E402
from test_step37_panel_menus import Ctx, _space  # noqa: E402

pm = import_module(kit.MODULE + ".ui.panel_menus")
pmd = import_module(kit.MODULE + ".ui.panel_menu_data")
pt = import_module(kit.MODULE + ".ui.panel_toolbar")
sl = import_module(kit.MODULE + ".ui.status_line")
cb = import_module(kit.MODULE + ".ui.camera_bookmarks")
switch = import_module(kit.MODULE + ".switch")
notices = import_module(kit.MODULE + ".ui.notices")
startup_cameras = import_module(kit.MODULE + ".operators.startup_cameras")
toolbar_fit = import_module(kit.MODULE + ".ui.toolbar_fit")


# --- torn-off panels -------------------------------------------------------------------------------------------------

def _maya_workspace():
    ws = bpy.data.workspaces[0]
    ws[switch.TEMPLATE_KEY] = "Maya Classic"
    return ws


def _plain_workspace():
    ws = bpy.data.workspaces[0]
    ws.pop(switch.TEMPLATE_KEY, None)
    assert not switch.is_maya_workspace(ws)
    return ws


class _TornCtx(Ctx):
    """A context of a 3D View alone in a window of its own (Panels > Tear Off) with a real 3D View space."""

    def __init__(self, ws, n_areas=1, region='TOOL_HEADER'):
        super().__init__(_space())
        self.area = types.SimpleNamespace(type='VIEW_3D', width=900, height=600, show_menus=True,
                                          spaces=types.SimpleNamespace(active=self.space_data), tag_redraw=lambda: None,
                                          as_pointer=lambda: 346, regions=[])
        others = [types.SimpleNamespace(type='OUTLINER', width=10, height=10) for _ in range(n_areas - 1)]
        self.screen = types.SimpleNamespace(areas=[self.area] + others)
        self.window = types.SimpleNamespace(screen=self.screen, workspace=ws)
        self.region = types.SimpleNamespace(type=region, width=2400)


def test_torn_off_window_is_a_maya_layout_view():
    try:
        ctx = _TornCtx(_maya_workspace())
        assert pt.torn_off(ctx) and pt.maya_screen(ctx) and pt.maya_layout(ctx)
        # the strip is in the main window only: the torn-off screen has none
        assert import_module(kit.MODULE + ".ui.shelf").strip_area(ctx.screen) is None
        # a window with several areas is not a torn-off panel
        assert not pt.torn_off(_TornCtx(_maya_workspace(), n_areas=2))
        # the IPR window (a render picture) keeps its header
        ipr = import_module(kit.MODULE + ".ui.ipr_window")
        saved = ipr.window
        ipr.window = lambda: ctx.window
        try:
            assert not pt.torn_off(ctx)
        finally:
            ipr.window = saved
        # no window (headless / a draw without one)
        ctx.window = None
        assert not pt.torn_off(ctx) and not pt.maya_layout(ctx)
        # a window of another workspace (Blender's) keeps Blender's header
        assert not pt.torn_off(_TornCtx(_plain_workspace()))
        assert not pt.maya_layout(_TornCtx(_plain_workspace()))
    finally:
        _plain_workspace()


def test_torn_off_view_draws_the_panel_bar_and_toolbar_not_the_status_line():
    try:
        ctx = _TornCtx(_maya_workspace(), region='HEADER')
        rec = Recorder()
        pt._header(types.SimpleNamespace(layout=rec), ctx)
        assert rec.texts("menu") == [label for label, _i in pm.BAR], rec.log
        ctx = _TornCtx(_maya_workspace())
        rec = Recorder()
        pt._tool_header(types.SimpleNamespace(layout=rec), ctx)
        keys = [getattr(p, "key", None) for p in rec.ops(pm.ALLSET_OT_panel_set.bl_idname)]
        assert "SELECT_CAMERA" in keys and "BOOKMARK" in keys and "PAN_ZOOM" in keys, keys
        # the kit's Status Line stays in the main window
        drawn = []
        saved = sl.draw_status_line
        sl.draw_status_line = lambda *a, **k: drawn.append(a)
        try:
            sl.draw_tool_header(types.SimpleNamespace(layout=Recorder()), ctx)
            assert not drawn
            sl.draw_tool_header(types.SimpleNamespace(layout=Recorder()), _TornCtx(_plain_workspace()))
            assert drawn, "a floating view of another workspace keeps its Status Line"
        finally:
            sl.draw_status_line = saved
    finally:
        _plain_workspace()


# --- bookmarks -------------------------------------------------------------------------------------------------------

def _clear():
    for ob in bpy.data.objects:
        getattr(ob, cb.PROP).clear()


def _camera_view(space, name="camera346"):
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(ob)
    ob.lock_location = ob.lock_rotation = (False,) * 3
    ob.location, ob.rotation_euler = (1.0, -8.0, 2.0), (math.radians(80.0), 0.0, 0.2)
    ob.data.lens = 35.0
    space.camera = ob
    space.use_local_camera = True
    space.region_3d.view_perspective = 'CAMERA'
    bpy.context.view_layer.update()
    return ob


def _close(a, b, eps=1e-5):
    return all(abs(x - y) < eps for x, y in zip(a, b))


def _flat(m):
    return [v for row in m for v in row]


def test_toolbar_rows_work():
    group = {g: (kind, data) for g, kind, data, _label in pmd.TOOLBAR[0]}
    assert group["bookmark"] == ("set", "BOOKMARK") and group["pan_zoom"] == ("set", "PAN_ZOOM")
    working = {p for _f, p, ok in pmd.leaves() if ok}
    assert pmd.toolbar_path("Bookmarks") in working and pmd.toolbar_path("2D Pan/Zoom") in working
    assert pmd.toolbar_path("2D Pan/Zoom") not in notices.PANEL_MENU
    # View > Bookmarks, after View Along Axis like Maya
    labels = [r[1] for r in pmd.VIEW if r[0] == "menu"]
    assert labels.index("Bookmarks") == labels.index("View Along Axis") + 1, labels
    assert ("menu", "Bookmarks", "ALLSET_MT_panel_bookmarks") in pmd.VIEW
    assert hasattr(bpy.types, "ALLSET_MT_panel_bookmarks")
    # the button tooltips say what they do
    assert "bookmark" in pm.TIPS["BOOKMARK"].lower() and "2D" in pm.TIPS["PAN_ZOOM"]


def test_bookmark_button_bookmarks_the_camera_and_puts_it_back():
    _clear()
    space = _space()
    cam = _camera_view(space)
    ctx = Ctx(space)
    assert pm.apply(ctx, "BOOKMARK")
    marks = cb.bookmarks(cam)
    assert [b.name for b in marks] == ["cameraView1"], [b.name for b in marks]
    bm = marks[0]
    assert not bm.view and not bm.pan_zoom and _close(bm.matrix, _flat(cam.matrix_world)) and bm.lens == 35.0
    start = Matrix(cam.matrix_world)
    cam.location = (5.0, 5.0, 5.0)
    cam.data.lens = 85.0
    bpy.context.view_layer.update()
    assert cb.apply(ctx, *cb.find(ctx, "cameraView1")) is None
    bpy.context.view_layer.update()
    assert _close(_flat(cam.matrix_world), _flat(start)) and cam.data.lens == 35.0
    # Maya names: one past the highest, a deleted one's number not used again
    assert cb.add(ctx) == "cameraView2"
    assert cb.remove(cam, "cameraView1")
    assert cb.add(ctx) == "cameraView3"
    assert [b.name for b in cb.bookmarks(cam)] == ["cameraView2", "cameraView3"]
    # a locked camera (Lock Camera) stays where it is
    cam.lock_location = cam.lock_rotation = (True,) * 3
    cam.location = (9.0, 9.0, 9.0)
    bpy.context.view_layer.update()
    assert cb.apply(ctx, *cb.find(ctx, "cameraView2")) is not None
    assert tuple(cam.location) == (9.0, 9.0, 9.0)
    cam.lock_location = cam.lock_rotation = (False,) * 3


def test_bookmark_operators_run_with_undo():
    _clear()
    area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    space = area.spaces.active
    cam = _camera_view(space, "camera346b")
    name = cam.name
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.ed.undo_push(message="before")
        assert bpy.ops.allset.camera_bookmark_add('EXEC_DEFAULT', True) == {'FINISHED'}
    cam = bpy.data.objects[name]
    assert [b.name for b in cb.bookmarks(cam)] == ["cameraView1"]
    cam.location = (3.0, 3.0, 3.0)
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.ed.undo_push(message="moved")
        assert bpy.ops.allset.camera_bookmark_apply('EXEC_DEFAULT', True, name="cameraView1") == {'FINISHED'}
    cam = bpy.data.objects[name]
    assert _close(cam.location, (1.0, -8.0, 2.0)), tuple(cam.location)
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.ed.undo()
    cam = bpy.data.objects[name]
    assert _close(cam.location, (3.0, 3.0, 3.0)), tuple(cam.location)       # undo: the move to the bookmark
    with bpy.context.temp_override(area=area, region=region):
        assert bpy.ops.allset.camera_bookmark_delete('EXEC_DEFAULT', True, name="cameraView1") == {'FINISHED'}
    assert not cb.bookmarks(bpy.data.objects[name])
    space = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D').spaces.active
    space.region_3d.view_perspective = 'PERSP'


def test_persp_view_bookmark_keeps_the_view_on_the_startup_camera():
    _clear()
    space = _space()
    rv3d = space.region_3d
    rv3d.view_perspective = 'PERSP'
    rv3d.view_location, rv3d.view_distance = (1.0, 2.0, 3.0), 12.0
    rv3d.view_rotation = (0.9, 0.3, 0.2, 0.1)
    space.lens = 50.0
    ctx = Ctx(space)
    name = cb.add(ctx)
    persp = next(o for o in bpy.context.scene.objects if o.get(startup_cameras.MARK) == "persp")
    bm = cb.bookmarks(persp)[-1]
    assert bm.name == name and bm.view and not bm.ortho
    want = (tuple(rv3d.view_location), tuple(rv3d.view_rotation), rv3d.view_distance)
    rv3d.view_location, rv3d.view_distance, space.lens = (0.0, 0.0, 0.0), 40.0, 35.0
    rv3d.view_rotation = (1.0, 0.0, 0.0, 0.0)
    assert cb.apply(ctx, *cb.find(ctx, name)) is None
    assert _close(rv3d.view_location, want[0]) and _close(rv3d.view_rotation, want[1])
    assert abs(rv3d.view_distance - want[2]) < 1e-5 and abs(space.lens - 50.0) < 1e-5
    # no 2D bookmark without a camera view; the 2D Pan/Zoom button works in every view (like Maya)
    assert cb.add(ctx, pan_zoom=True) is None
    assert cb.toggle_pan_zoom(ctx) and pm.state(ctx, "PAN_ZOOM") is True
    assert pm.apply(ctx, "PAN_ZOOM") and pm.state(ctx, "PAN_ZOOM") is False


def test_menus_list_the_bookmarks_like_maya():
    _clear()
    space = _space()
    cam = _camera_view(space)
    ctx = Ctx(space)
    a = cb.add(ctx)
    b = cb.add(ctx, pan_zoom=True)
    c = cb.add(ctx)
    menu = type("Menu", (), {})
    rec = Recorder()
    menu.layout = rec
    cb.ALLSET_MT_panel_bookmarks.draw(menu, ctx)
    # View > Bookmarks: the bookmarks, then the 2D ones, then Edit Bookmarks...
    assert rec.texts("operator") == [a, c, f"{b} (2D Pan/Zoom)", "Edit Bookmarks..."], rec.texts("operator")
    assert [p.name for p in rec.ops(cb.ALLSET_OT_camera_bookmark_apply.bl_idname)] == [a, c, b]
    rec = Recorder()
    menu.layout = rec
    cb.ALLSET_MT_pt_bookmarks.draw(menu, ctx)
    assert rec.texts("operator") == [a, c, "Create 2D Bookmark", "Edit 2D Bookmarks..."], rec.texts("operator")
    rec = Recorder()
    menu.layout = rec
    cb.ALLSET_MT_pt_pan_zoom.draw(menu, ctx)
    assert rec.texts("operator") == [f"{b} (2D Pan/Zoom)", "Create 2D Bookmark", "Edit 2D Bookmarks..."]
    assert [p.pan_zoom for p in rec.ops(cb.ALLSET_OT_camera_bookmark_add.bl_idname)] == [True]
    # the editor lists them with name / description, New Bookmark / New 2D Bookmark / Apply / Delete
    rec = Recorder()
    cb.ALLSET_PT_camera_bookmarks.draw(types.SimpleNamespace(layout=rec), ctx)
    assert rec.texts("operator") == ["New Bookmark", "New 2D Bookmark", "Apply", "Delete"], rec.texts("operator")
    assert rec.texts("prop") == ["Name", "Description"], rec.texts("prop")
    assert cam.name in rec.texts("label")[0]
    space.region_3d.view_perspective = 'PERSP'


def test_right_click_menus_by_button():
    """The right-click menu of the toolbar's first group by the button under the mouse."""
    system = bpy.context.preferences.system
    x0 = toolbar_fit.starts(pt.fit_groups(), system.ui_scale, system.pixel_size)[0]
    u = toolbar_fit.unit(system.ui_scale, system.pixel_size)
    ctx = types.SimpleNamespace(region=types.SimpleNamespace(type='TOOL_HEADER', width=2400),
                                preferences=bpy.context.preferences)
    got = {}
    for i, item in enumerate(pmd.TOOLBAR[0]):
        got[item[0]] = pt._rmb_menu(ctx, types.SimpleNamespace(mouse_region_x=x0 + i * u + u // 2))
    assert got["cam_select"] == "ALLSET_MT_panel_cameras"
    assert got["bookmark"] == "ALLSET_MT_pt_bookmarks" and got["pan_zoom"] == "ALLSET_MT_pt_pan_zoom"
    assert not got["cam_lock"] and not got["image_plane"], got
    assert pt._rmb_menu(ctx, types.SimpleNamespace(mouse_region_x=x0 - 3)) == ""
    for idname in pt.RMB_MENUS.values():
        assert hasattr(bpy.types, idname), idname


# --- 2D Pan/Zoom ---------------------------------------------------------------------------------------------------

def test_pan_zoom_off_shows_the_frame_and_on_brings_it_back():
    _clear()
    space = _space()
    _camera_view(space)
    rv3d = space.region_3d
    ctx = Ctx(space)
    cb.pan_zoom_forget(rv3d)
    rv3d.view_camera_zoom, rv3d.view_camera_offset = 0.0, (0.0, 0.0)
    assert pm.state(ctx, "PAN_ZOOM") is False
    # the \ key moved the camera view: the button lights up
    rv3d.view_camera_zoom, rv3d.view_camera_offset = 25.0, (0.12, -0.04)
    cb.pan_zoom_moved(rv3d)
    assert pm.state(ctx, "PAN_ZOOM") is True
    # off: the whole frame (no pan); the camera stays
    cam = space.camera
    where = tuple(cam.location)
    assert pm.apply(ctx, "PAN_ZOOM")
    assert pm.state(ctx, "PAN_ZOOM") is False and _close(rv3d.view_camera_offset, (0.0, 0.0))
    assert tuple(cam.location) == where
    # on: the same 2D pan / zoom again
    assert pm.apply(ctx, "PAN_ZOOM")
    assert pm.state(ctx, "PAN_ZOOM") is True
    assert abs(rv3d.view_camera_zoom - 25.0) < 1e-4 and _close(rv3d.view_camera_offset, (0.12, -0.04))
    # a 2D bookmark keeps it; applying one turns the button on
    name = cb.add(ctx, pan_zoom=True)
    rv3d.view_camera_zoom, rv3d.view_camera_offset = 0.0, (0.0, 0.0)
    cb.pan_zoom_forget(rv3d)
    assert cb.apply(ctx, *cb.find(ctx, name)) is None
    assert abs(rv3d.view_camera_zoom - 25.0) < 1e-4 and _close(rv3d.view_camera_offset, (0.12, -0.04))
    assert pm.state(ctx, "PAN_ZOOM") is True
    # the camera frame fitted again (another camera, Overscan): nothing to bring back
    cb.pan_zoom_forget(rv3d)
    assert pm.state(ctx, "PAN_ZOOM") is False
    space.region_3d.view_perspective = 'PERSP'


def test_pan_zoom_hold_turns_the_button_on():
    import inspect
    pz = import_module(kit.MODULE + ".operators.pan_zoom")
    space = _space()
    _camera_view(space)
    rv3d = space.region_3d
    cb.pan_zoom_forget(rv3d)
    assert not cb.pan_zoom_on(rv3d)
    assert pz.pan(space, rv3d, 10, 0, (800, 600)) and cb.pan_zoom_on(rv3d)       # a \\ drag lights the button
    space.region_3d.view_perspective = 'PERSP'
    pz.clear()
    co = import_module(kit.MODULE + ".operators.camera_overscan")
    assert "pan_zoom_forget(rv3d)" in inspect.getsource(co.apply_view)
