"""View > Create Camera From View (Ctrl+Shift+C) and Panels > Orthographic > New, like Maya.

Create Camera From View copies the view's camera: every camera setting (Fit Resolution Gate, film back, focal length
or orthographic width, Overscan, clip planes, film offset, Renderable ...) and its place. The copy is named after that
camera (persp1, top1; from shot3 the next free shot number), the view then looks through it (its label names it),
the selection stays and the menu row is one undo step; after Ctrl+Z the view shows what it showed before. Blender's
persp / top / front / side views stand for the scene's startup cameras.
Panels > Orthographic ends with New > Front / Back / Right / Left / Top / Bottom: front1 ... 30 units wide."""

import json
import sys
from importlib import import_module

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

import kit

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from test_step106_tool_settings_ae import Recorder  # noqa: E402

panel_menus = import_module(kit.MODULE + ".ui.panel_menus")
pmd = import_module(kit.MODULE + ".ui.panel_menu_data")
key_batch = import_module(kit.MODULE + ".operators.key_batch")
startup_cameras = import_module(kit.MODULE + ".operators.startup_cameras")
units = import_module(kit.MODULE + ".operators.units")
undo_steps = import_module(kit.MODULE + ".undo_steps")
view_furniture = import_module(kit.MODULE + ".ui.view_furniture")

LABEL = "Create Camera From View"


def _view():
    area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return area, region


def _scene():
    """A Maya scene (startup cameras) with pCube1 selected and lead, the view a Blender persp view."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for data in list(bpy.data.cameras):
        bpy.data.cameras.remove(data)
    startup_cameras.ensure(bpy.context.scene)
    cube = bpy.data.objects.new("pCube1", bpy.data.meshes.new("pCubeShape1"))
    bpy.context.scene.collection.objects.link(cube)
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube
    area, region = _view()
    space = area.spaces.active
    space.use_local_camera, space.camera = False, None
    bpy.context.scene.camera = None
    space.region_3d.view_perspective = 'PERSP'
    return area, region, cube


def _run(area, region, idname="camera_from_view", *args, **kw):
    with bpy.context.temp_override(area=area, region=region):
        return getattr(bpy.ops.allset, idname)(*args, **kw)


def _startup(name):
    return next(o for o in startup_cameras.cameras(bpy.context.scene) if o.get(startup_cameras.MARK) == name)


def _close(a, b, eps=1e-4):
    return abs(a - b) <= eps * max(1.0, abs(a), abs(b))


def _same_matrix(a, b, eps=1e-4):
    return all(_close(x, y, eps) for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def _selection_kept(cube, *new):
    vl = bpy.context.view_layer
    return ([o.name for o in bpy.context.selected_objects] == [cube.name] and vl.objects.active == cube
            and not any(o.select_get() for o in new))


def _looks_through(area, ob):
    space = area.spaces.active
    return space.camera == ob and space.use_local_camera and space.region_3d.view_perspective == 'CAMERA'


# --- the menu row --------------------------------------------------------------------------------------------------

def test_view_menu_row_after_lock_camera():
    labels = [r[-1] if r[0] == "set" else r[1] for r in pmd.VIEW]
    i = labels.index("Lock Camera")
    assert pmd.VIEW[i + 1][0] == "sep", pmd.VIEW[i + 1]
    assert pmd.VIEW[i + 2] == ("run", LABEL, "allset.camera_from_view", {}), pmd.VIEW[i + 2]
    assert pmd.VIEW[i + 3][0] == "sep", pmd.VIEW[i + 3]
    assert (("Panel menus", pmd.item_path("ALLSET_MT_panel_view", LABEL), True) in pmd.leaves())


def test_operator_label_and_undo():
    assert bpy.ops.allset.camera_from_view.get_rna_type().name == LABEL
    assert 'UNDO' in key_batch.ALLSET_OT_camera_from_view.bl_options      # the hotkey: Blender pushes one step


def test_menu_row_is_one_undo_step():
    area, region, _cube = _scene()
    pushed, push = [], undo_steps.push
    undo_steps.push = pushed.append
    try:
        res = _run(area, region, "panel_run", op="allset.camera_from_view", props=json.dumps({}))
    finally:
        undo_steps.push = push
    assert res == {'FINISHED'} and "persp1" in bpy.data.objects, (res, list(bpy.data.objects.keys()))
    assert pushed == [LABEL], pushed


def test_one_undo_takes_the_copy_back():
    # the menu row (the hotkey's own undo step, Blender's for an UNDO operator, is checked in the GUI test: in
    # background Blender a registered operator called with undo crashes in its redo panel)
    area, region, _cube = _scene()
    bpy.ops.ed.undo_push(message="start")
    assert _run(area, region, "panel_run", op="allset.camera_from_view") == {'FINISHED'}
    assert "persp1" in bpy.data.objects
    bpy.ops.ed.undo()
    names = [o.name for o in bpy.data.objects]
    assert "persp1" not in names and "pCube1" in names, names
    assert [o.name for o in bpy.context.selected_objects] == ["pCube1"], "the selection is as it was"


def _undo_copy(area, region, name):
    bpy.ops.ed.undo_push(message="start")
    assert _run(area, region, "panel_run", op="allset.camera_from_view") == {'FINISHED'}
    assert name in bpy.data.objects, list(bpy.data.objects.keys())
    bpy.ops.ed.undo()
    assert name not in bpy.data.objects, list(bpy.data.objects.keys())


def test_undo_puts_the_view_back():
    # a persp view: back to the persp view it was (Blender would keep a camera view with no camera)
    area, region, _cube = _scene()
    space = area.spaces.active
    _undo_copy(area, region, "persp1")
    assert space.region_3d.view_perspective == 'PERSP' and space.camera is None, space.region_3d.view_perspective
    # an orthographic view stays orthographic
    _scene()
    space.region_3d.view_perspective = 'ORTHO'
    space.region_3d.view_rotation = Quaternion()
    _undo_copy(area, region, "top1")
    assert space.region_3d.view_perspective == 'ORTHO', space.region_3d.view_perspective
    # a view that looked through a camera looks through it again
    _scene()
    shot = bpy.data.objects.new("shot3", bpy.data.cameras.new("shotShape3"))
    bpy.context.scene.collection.objects.link(shot)
    panel_menus.look_through(bpy.context, area, shot)
    _undo_copy(area, region, "shot4")
    assert _looks_through(area, bpy.data.objects["shot3"]), (space.camera, space.region_3d.view_perspective)
    # views that look through a camera that is still there are left alone
    assert _run(area, region) == {'FINISHED'}
    panel_menus.restore_camera_less(bpy.context.window_manager)
    assert _looks_through(area, bpy.data.objects["shot4"])
    assert panel_menus._on_undo in bpy.app.handlers.undo_post


def test_view_label_names_the_camera_it_looks_through():
    area, region, _cube = _scene()
    space = area.spaces.active
    scene_cam = bpy.data.objects.new("camera1", bpy.data.cameras.new("cameraShape1"))
    bpy.context.scene.collection.objects.link(scene_cam)
    bpy.context.scene.camera = scene_cam
    assert _run(area, region) == {'FINISHED'}             # the view now looks through persp1 (its own camera)
    assert view_furniture.label_camera(space, bpy.context.scene).name == "persp1"
    assert view_furniture.label_for('CAMERA', False, (0, 0, -1), "persp1") == "persp1"
    space.use_local_camera = False
    assert view_furniture.label_camera(space, bpy.context.scene) == scene_cam


# --- copies --------------------------------------------------------------------------------------------------------

def test_persp_view_copies_the_persp_camera():
    area, region, cube = _scene()
    space = area.spaces.active
    rv3d = space.region_3d
    unit = units.maya_unit(bpy.context.scene)
    pd = _startup("persp").data
    pd.sensor_width, pd.sensor_height = 30.0, 20.0
    pd.allset_film_fit = 'VERTICAL'
    pd.allset_overscan = 1.3
    pd.shift_x, pd.shift_y = 0.05, -0.02
    space.lens = 100.0
    space.clip_start, space.clip_end = 0.5 * unit, 5000.0 * unit
    rot = Euler((1.0, 0.0, 0.6)).to_quaternion()
    rv3d.view_rotation, rv3d.view_location, rv3d.view_distance = rot, Vector((1.0, 2.0, 0.5)), 12.0
    assert _run(area, region) == {'FINISHED'}
    ob = bpy.data.objects.get("persp1")
    assert ob is not None and ob.type == 'CAMERA' and ob.data.name == "persp1Shape", list(bpy.data.objects.keys())
    d = ob.data
    assert d.type == 'PERSP' and _close(d.lens, 100.0 * 30.0 / key_batch.VIEW_SENSOR), d.lens
    assert _close(d.sensor_width, 30.0) and _close(d.sensor_height, 20.0)
    assert d.allset_film_fit == 'VERTICAL' and _close(d.allset_overscan, 1.3), (d.allset_film_fit, d.allset_overscan)
    assert _close(d.shift_x, 0.05) and _close(d.shift_y, -0.02)
    assert _close(d.clip_start, 0.5 * unit) and _close(d.clip_end, 5000.0 * unit), (d.clip_start, d.clip_end)
    assert d.allset_renderable, "a copy of persp renders, like persp"
    assert _close(d.display_size, unit), d.display_size
    eye = Vector((1.0, 2.0, 0.5)) + rot @ Vector((0.0, 0.0, 12.0))
    assert (ob.matrix_world.translation - eye).length < 1e-4, ob.matrix_world.translation
    assert ob.matrix_world.to_quaternion().rotation_difference(rot).angle < 1e-4
    assert not ob.hide_viewport and not ob.hide_get() and not ob.hide_render and not ob.get(startup_cameras.MARK)
    assert _looks_through(area, ob), (space.camera, rv3d.view_perspective)
    assert _selection_kept(cube, ob), [o.name for o in bpy.context.selected_objects]
    # again, now looking through persp1: persp2, a copy of persp1
    assert _run(area, region) == {'FINISHED'}
    ob2 = bpy.data.objects.get("persp2")
    assert ob2 is not None and ob2.data.name == "persp2Shape" and ob2.data != d, list(bpy.data.objects.keys())
    assert _same_matrix(ob2.matrix_world, ob.matrix_world)
    assert _close(ob2.data.lens, d.lens) and ob2.data.allset_film_fit == 'VERTICAL'
    assert _looks_through(area, ob2) and _selection_kept(cube, ob, ob2)


def test_camera_view_copies_every_setting():
    area, region, cube = _scene()
    data = bpy.data.cameras.new("shotShape3")
    shot = bpy.data.objects.new("shot3", data)
    bpy.context.scene.collection.objects.link(shot)
    data.lens, data.sensor_width, data.sensor_height = 50.0, 30.48, 22.86
    data.allset_film_fit = 'OVERSCAN'
    data.allset_overscan = 1.3
    data.clip_start, data.clip_end = 0.5, 5000.0
    data.shift_x, data.shift_y = 0.05, 0.03
    data.allset_renderable = False
    data.show_passepartout, data.show_sensor = False, True
    data.display_size = 2.0
    grp = bpy.data.objects.new("grp", None)
    bpy.context.scene.collection.objects.link(grp)
    grp.location = (1.0, 1.0, 1.0)
    shot.parent = grp
    shot.matrix_basis = Matrix.LocRotScale((3.0, -4.0, 5.0), Euler((0.4, 0.1, 0.8)).to_quaternion(), None)
    bpy.context.view_layer.update()
    panel_menus.look_through(bpy.context, area, shot)
    assert _run(area, region) == {'FINISHED'}
    ob = bpy.data.objects.get("shot4")
    assert ob is not None and ob.data.name == "shot4Shape" and ob.data != data, list(bpy.data.objects.keys())
    for attr in ("type", "lens", "sensor_width", "sensor_height", "sensor_fit", "allset_film_fit", "allset_overscan",
                 "clip_start", "clip_end", "shift_x", "shift_y", "show_passepartout", "show_sensor", "display_size",
                 "allset_renderable"):
        a, b = getattr(ob.data, attr), getattr(data, attr)
        assert (_close(a, b) if isinstance(a, float) else a == b), (attr, a, b)
    assert ob.parent is None and _same_matrix(ob.matrix_world, shot.matrix_world), "the same place in the world"
    assert _looks_through(area, ob) and _selection_kept(cube, ob)


def test_top_view_copies_the_top_camera():
    area, region, cube = _scene()
    space = area.spaces.active
    rv3d = space.region_3d
    unit = units.maya_unit(bpy.context.scene)
    space.lens = 70.0
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = Quaternion()                     # Blender's top view: down -Z, +Y up
    rv3d.view_location, rv3d.view_distance = Vector((2.0, 3.0, 0.7)), 29.0
    assert _run(area, region) == {'FINISHED'}
    ob = bpy.data.objects.get("top1")
    assert ob is not None and ob.data.name == "top1Shape", list(bpy.data.objects.keys())
    d, top = ob.data, _startup("top").data
    assert d.type == 'ORTHO' and _close(d.ortho_scale, 29.0 * key_batch.VIEW_SENSOR / 70.0), d.ortho_scale
    # Maya's top camera sits 1000.1 units up: nothing between it and the ground is clipped
    assert (ob.matrix_world.translation - Vector((2.0, 3.0, 1000.1 * unit))).length < 1e-3 * max(1.0, unit)
    q = ob.matrix_world.to_quaternion()
    assert (q @ Vector((0.0, 0.0, -1.0)) - Vector((0.0, 0.0, -1.0))).length < 1e-5
    assert (q @ Vector((0.0, 1.0, 0.0)) - Vector((0.0, 1.0, 0.0))).length < 1e-5
    assert not d.allset_renderable, "a copy of top doesn't render, like top"
    assert d.allset_film_fit == 'HORIZONTAL' and _close(d.clip_start, top.clip_start) and _close(d.clip_end, top.clip_end)
    assert _looks_through(area, ob) and _selection_kept(cube, ob)


def test_other_views_are_named_after_their_side():
    area, region, _cube = _scene()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = Euler((3.14159265, 0.0, 0.0)).to_quaternion()      # bottom: looks up +Z
    assert _run(area, region) == {'FINISHED'}
    assert "bottom1" in bpy.data.objects and bpy.data.objects["bottom1"].data.type == 'ORTHO'
    _scene()
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = Euler((0.7, 0.0, 0.4)).to_quaternion()            # no side: Maya's persp seen orthographic
    assert _run(area, region) == {'FINISHED'}
    assert "persp1" in bpy.data.objects and bpy.data.objects["persp1"].data.type == 'ORTHO'


# --- Panels > Orthographic > New -----------------------------------------------------------------------------------

def _menu(cls):
    rec = Recorder()
    cls.draw(type("Menu", (), {"layout": rec})(), bpy.context)
    return rec


def test_orthographic_menu_ends_with_new():
    rec = _menu(panel_menus.ALLSET_MT_panel_orthographic)
    menus = [(t, kw["_args"][0]) for k, t, kw in rec.log if k == "menu"]
    assert [t for t, _i in menus] == ["New"] and rec.log[-1][0] == "menu", rec.log
    sub = _menu(getattr(bpy.types, menus[0][1]))
    assert sub.texts("operator") == ["Front", "Back", "Right", "Left", "Top", "Bottom"], sub.texts("operator")
    kinds = [p.kind for p in sub.ops(panel_menus.ALLSET_OT_panel_new_ortho.bl_idname)]
    assert kinds == ['front', 'back', 'right', 'left', 'top', 'bottom'], kinds
    # the panel toolbar's camera list keeps Front / Side / Top
    assert _menu(panel_menus.ALLSET_MT_panel_new_ortho).texts("operator") == ["Front", "Side", "Top"]


# Maya place of each side (Blender world): eye, looking direction, up
SIDES = {
    'front': ((0.0, -1000.1, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    'back': ((0.0, 1000.1, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
    'right': ((1000.1, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    'left': ((-1000.1, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    'top': ((0.0, 0.0, 1000.1), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
    'bottom': ((0.0, 0.0, -1000.1), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0)),
}


def test_orthographic_new_six_sides():
    area, region, _cube = _scene()
    unit = units.maya_unit(bpy.context.scene)
    for kind, (eye, look, up) in SIDES.items():
        assert _run(area, region, "panel_new_ortho", kind=kind) == {'FINISHED'}, kind
        ob = bpy.context.view_layer.objects.active
        assert ob.name == f"{kind}1" and ob.data.name == f"{kind}Shape1", (kind, ob.name, ob.data.name)
        d = ob.data
        assert d.type == 'ORTHO' and _close(d.ortho_scale, 30.0 * unit), (kind, d.ortho_scale)
        assert d.allset_film_fit == 'HORIZONTAL' and not d.allset_renderable, (kind, d.allset_film_fit)
        assert (ob.matrix_world.translation - Vector(eye) * unit).length < 1e-3 * max(1.0, unit), kind
        q = ob.matrix_world.to_quaternion()
        assert (q @ Vector((0.0, 0.0, -1.0)) - Vector(look)).length < 1e-5, (kind, q @ Vector((0.0, 0.0, -1.0)))
        assert (q @ Vector((0.0, 1.0, 0.0)) - Vector(up)).length < 1e-5, (kind, q @ Vector((0.0, 1.0, 0.0)))
        assert ob.select_get() and [o.name for o in bpy.context.selected_objects] == [ob.name]
        assert area.spaces.active.camera == ob and area.spaces.active.region_3d.view_perspective == 'CAMERA'
    assert _run(area, region, "panel_new_ortho", kind='top') == {'FINISHED'}
    assert bpy.context.view_layer.objects.active.name == "top2"
