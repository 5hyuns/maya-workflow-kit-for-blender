"""The panel toolbar camera icon's right-click list is Maya's (issue #325): every camera of the scene once, in
name order (perspective and orthographic together, hidden ones too, the startup persp / top / front / side among
them), then New Perspective, a New Orthographic submenu (Front / Side / Top) and a greyed Stereo Cameras row; New
Orthographic makes front1 / side1 / top1 with the startup camera's settings and looks through it."""

import sys
from importlib import import_module

import bpy

import kit

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from test_step106_tool_settings_ae import Recorder  # noqa: E402

panel_toolbar = import_module(kit.MODULE + ".ui.panel_toolbar")
panel_menus = import_module(kit.MODULE + ".ui.panel_menus")
panel_menu_data = import_module(kit.MODULE + ".ui.panel_menu_data")
notices = import_module(kit.MODULE + ".ui.notices")
startup_cameras = import_module(kit.MODULE + ".operators.startup_cameras")


def _scene():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    startup_cameras.ensure(bpy.context.scene)


def _camera(name, ortho=False, hide=False):
    data = bpy.data.cameras.new(name + "Shape")
    if ortho:
        data.type = 'ORTHO'
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    if hide:
        ob.hide_set(True)
    return ob


def _draw():
    rec = Recorder()
    panel_toolbar.ALLSET_MT_panel_cameras.draw(type("Menu", (), {"layout": rec})(), bpy.context)
    return rec


def test_one_list_in_name_order_then_new_and_stereo():
    _scene()
    _camera("zebra_persp")
    _camera("alpha_ortho", ortho=True)
    _camera("mid_persp", hide=True)
    _camera("omega_ortho", ortho=True)
    rec = _draw()
    ops = rec.texts("operator")
    assert ops[:8] == ["alpha_ortho", "front", "mid_persp", "omega_ortho", "persp", "side", "top", "zebra_persp"], ops
    assert ops[8:] == ["New Perspective", "Stereo Cameras"], ops
    assert rec.texts("menu") == ["New Orthographic"]
    # the startup rows are the kit's view switches, the others look through the camera object
    runs = rec.ops(panel_menus.ALLSET_OT_panel_run.bl_idname)
    assert [p.op for p in runs] == ["allset.hb_view"] * 4
    looks = rec.ops(panel_menus.ALLSET_OT_panel_look_through.bl_idname)
    assert [p.camera for p in looks] == ["alpha_ortho", "mid_persp", "omega_ortho", "zebra_persp"]
    grey = rec.ops(panel_menus.GREY_OP)
    assert len(grey) == 1 and grey[0].item == panel_menu_data.item_path("ALLSET_MT_panel_panels", "Stereo")
    assert notices.greyed_notice(grey[0].item), grey[0].item          # the row carries the stereo notice


def test_no_mark_and_no_duplicate_for_the_current_camera():
    _scene()
    cam = _camera("camera1")
    bpy.context.scene.camera = cam
    rec = _draw()
    ops = rec.texts("operator")
    assert ops.count("camera1") == 1 and ops[:5] == ["camera1", "front", "persp", "side", "top"], ops
    for _k, _t, kw in rec.log:
        assert kw.get("icon", 'NONE') in ('NONE', 'OUTLINER_OB_CAMERA'), kw.get("icon")


def test_new_orthographic_submenu_rows():
    rec = Recorder()
    panel_menus.ALLSET_MT_panel_new_ortho.draw(type("Menu", (), {"layout": rec})(), bpy.context)
    assert rec.texts("operator") == ["Front", "Side", "Top"]
    kinds = [p.kind for p in rec.ops(panel_menus.ALLSET_OT_panel_new_ortho.bl_idname)]
    assert kinds == ['front', 'side', 'top']


def test_new_orthographic_makes_a_startup_like_camera():
    _scene()
    area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(area=area, region=region):
        assert bpy.ops.allset.panel_new_ortho(kind='side') == {'FINISHED'}
    ob = bpy.context.active_object
    assert ob is not None and ob.type == 'CAMERA' and ob.name == "side1", ob and ob.name
    assert ob.data.type == 'ORTHO'
    startup = next(o for o in bpy.context.scene.objects if o.get(startup_cameras.MARK) == "side")
    assert abs(ob.data.ortho_scale - startup.data.ortho_scale) < 1e-6
    assert max(abs(a - b) for ra, rb in zip(ob.matrix_world, startup.matrix_world) for a, b in zip(ra, rb)) < 1e-4
    assert area.spaces.active.camera == ob and area.spaces.active.region_3d.view_perspective == 'CAMERA'
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.allset.panel_new_ortho(kind='side')
    assert bpy.context.active_object.name == "side2"
