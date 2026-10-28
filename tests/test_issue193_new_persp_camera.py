"""#193: Panels > Perspective > New makes a perspective camera and looks through it in that view.

Maya 2026 behaviour (measured in the GUI): New makes ``persp1`` (then ``persp2``) with the camera settings of a new
scene's persp (35 mm, translate 28 21 28, aimed at the origin), selects it, looks through it in the panel, lists it
under Panels > Perspective (above New), and one undo removes it again."""

from importlib import import_module

import bpy
from mathutils import Vector

import kit

panel_menus = import_module(kit.MODULE + ".ui.panel_menus")
units = import_module(kit.MODULE + ".operators.units")
startup_cameras = import_module(kit.MODULE + ".operators.startup_cameras")


def _view3d():
    win = bpy.context.window_manager.windows[0]
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return win, area, region


def _new():
    win, area, region = _view3d()
    with bpy.context.temp_override(window=win, area=area, region=region):
        return bpy.ops.allset.panel_new_persp('EXEC_DEFAULT', True)     # True: an undo step like a menu click


def _clean():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    startup_cameras.ensure(bpy.context.scene, bpy.context.view_layer)
    bpy.ops.ed.undo_push(message="start")


def test_new_makes_persp1_and_looks_through_it():
    _clean()
    assert _new() == {'FINISHED'}
    ob = bpy.data.objects.get("persp1")
    assert ob is not None and ob.type == 'CAMERA' and ob.data.type == 'PERSP', [o.name for o in bpy.data.objects]
    assert ob.data.name == "perspShape1"
    assert abs(ob.data.lens - 35.0) < 1e-6 and abs(ob.data.sensor_width - 36.0) < 1e-6
    unit = units.maya_unit(bpy.context.scene)
    assert (ob.matrix_world.translation - Vector((28.0, -28.0, 21.0)) * unit).length < 1e-4, ob.matrix_world
    aim = ob.matrix_world.to_3x3() @ Vector((0, 0, -1))
    to_origin = -ob.matrix_world.translation.normalized()
    assert aim.angle(to_origin) < 0.01, (aim, to_origin)                   # aimed at the origin like Maya's persp
    assert not startup_cameras.is_startup(ob) and not ob.hide_viewport
    assert bpy.context.view_layer.objects.active == ob and ob.select_get()
    _win, area, _region = _view3d()
    space = area.spaces.active
    assert space.camera == ob and space.region_3d.view_perspective == 'CAMERA'


def test_new_cameras_are_listed_and_numbered():
    assert _new() == {'FINISHED'}
    assert "persp2" in bpy.data.objects
    listed = [o.name for o in panel_menus._cameras(bpy.context, False)]
    assert listed == ["persp1", "persp2"], listed            # the startup persp is the menu's own persp row


def test_one_undo_removes_it():
    assert "persp2" in bpy.data.objects
    bpy.ops.ed.undo()
    assert "persp2" not in bpy.data.objects and "persp1" in bpy.data.objects, [o.name for o in bpy.data.objects]


def test_menu_has_new_under_the_cameras():
    src = panel_menus.ALLSET_MT_panel_perspective.draw.__code__.co_names
    assert "_draw_camera_list" in src
    assert panel_menus.ALLSET_OT_panel_new_persp.bl_label == "New"
    assert 'UNDO' in panel_menus.ALLSET_OT_panel_new_persp.bl_options
