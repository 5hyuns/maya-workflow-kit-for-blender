"""Step 137 (#67): Render > Render Current Frame / Render Sequence through the view's camera, else Maya's persp
camera made on demand (operators/render_persp.py). Plan: docs/steps/step_137.md; GUI: tests/gui/gui_step137_render.py."""

import math
import os
from importlib import import_module

import bpy
from mathutils import Euler, Vector

import kit

rp = import_module(kit.MODULE + ".operators.render_persp")
units = import_module(kit.MODULE + ".operators.units")
framing = import_module(kit.MODULE + ".operators.framing")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
shelf_map = import_module(kit.MODULE + ".ui.shelf_map")
outliner_sets = import_module(kit.MODULE + ".ui.outliner_sets")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.context.scene.camera = None


def _view():
    space, rv3d = rp.find_view(bpy.context)
    assert space is not None and rv3d is not None, "factory screen has a 3D View"
    return space, rv3d


def _aim(rv3d, space, persp=True, lens=70.0):
    rv3d.view_perspective = 'PERSP' if persp else 'ORTHO'
    rv3d.view_location = Vector((0.0, 0.0, 0.0))
    rv3d.view_rotation = Euler((math.radians(60), 0.0, math.radians(45))).to_quaternion()
    rv3d.view_distance = 8.0
    space.lens = lens


def _cam(rv3d):
    """World matrix of a camera seeing what the view sees (framing.view_matrix inverted)."""
    return framing.view_matrix(rv3d.view_location, rv3d.view_rotation, rv3d.view_distance).inverted()


def _close(a, b, eps=1e-4):
    return all(abs(x - y) < eps for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def test_persp_made_on_demand_matches_view_and_is_reused():
    _clear()
    assert rp.persp_camera(create=False) is None
    space, rv3d = _view()
    _aim(rv3d, space)
    ob = rp.render_camera(bpy.context)
    sc = bpy.context.scene
    assert ob.name == "persp" and ob.data.name == "perspShape" and ob.get(rp.PROP), ob.name
    assert sc.camera == ob
    assert _close(ob.matrix_world, _cam(rv3d)), "camera sees what the view sees"
    to_target = rv3d.view_location - ob.matrix_world.translation
    look = ob.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))
    assert abs(to_target.length - 8.0) < 1e-4 and look.angle(to_target) < 1e-4, "view distance in front of the camera"
    # viewport lens is on a 72 mm sensor: lens 70 = Maya's 35 mm persp on a 36 mm film back
    assert ob.data.type == 'PERSP' and abs(ob.data.sensor_width - 36.0) < 1e-6 and abs(ob.data.lens - 35.0) < 1e-6
    clip = units.clip(sc)
    assert abs(ob.data.clip_start - clip["clip_start"]) < 1e-6 and abs(ob.data.clip_end - clip["clip_end"]) < 1e-3
    # not a second Outliner row: linked to no collection (the kit's drawn persp row stands for it), kept by a fake user
    assert not ob.users_collection and ob.name not in sc.objects and ob.use_fake_user
    assert ('CAMERA', "persp", "") in outliner_sets.default_entries()
    # the view moves: same object, new matrix
    rv3d.view_distance = 20.0
    space.lens = 50.0
    again = rp.render_camera(bpy.context)
    assert again == ob and len([o for o in bpy.data.objects if o.get(rp.PROP)]) == 1
    assert _close(ob.matrix_world, _cam(rv3d)) and abs(ob.data.lens - 25.0) < 1e-6
    # orphan purge keeps it
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    assert rp.persp_camera(create=False) == ob


def test_ortho_view():
    _clear()
    space, rv3d = _view()
    _aim(rv3d, space, persp=False)
    ob = rp.render_camera(bpy.context)
    assert ob.data.type == 'ORTHO'
    assert abs(ob.data.ortho_scale - rv3d.view_distance * 72.0 / space.lens) < 1e-4
    _aim(rv3d, space)


def test_camera_view_renders_that_camera():
    _clear()
    sc = bpy.context.scene
    space, rv3d = _view()
    cam = bpy.data.objects.new("camera1", bpy.data.cameras.new("cameraShape1"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    rv3d.view_perspective = 'CAMERA'
    try:
        assert rp.render_camera(bpy.context) == cam and sc.camera == cam
        assert rp.persp_camera(create=False) is None, "looking through a camera makes no persp"
        cam2 = bpy.data.objects.new("camera2", bpy.data.cameras.new("cameraShape2"))
        sc.collection.objects.link(cam2)
        space.use_local_camera, space.camera = True, cam2
        assert rp.render_camera(bpy.context) == cam2 and sc.camera == cam2
    finally:
        space.use_local_camera = False
        rv3d.view_perspective = 'PERSP'
    # a user view renders persp even when the scene has another camera (Maya renders the active panel's camera)
    ob = rp.render_camera(bpy.context)
    assert ob.get(rp.PROP) and sc.camera == ob


def test_render_through_persp_writes_an_image():
    _clear()
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    space, rv3d = _view()
    _aim(rv3d, space)
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 64, 36, 100
    out = os.path.join(os.path.dirname(os.path.abspath(kit.__file__)), "..", "tmp", "test_env", "step137_render.png")
    out = os.path.normpath(out)
    sc.render.filepath = out
    if os.path.exists(out):
        os.remove(out)
    assert bpy.ops.allset.render_current_frame(write_still=True) == {'FINISHED'}
    assert sc.camera is not None and sc.camera.get(rp.PROP)
    assert os.path.exists(out), out
    img = bpy.data.images.load(out)
    try:
        reds = {round(v, 3) for v in list(img.pixels)[0::4]}
        assert len(reds) > 5, f"cube visible (distinct red values {len(reds)})"
    finally:
        bpy.data.images.remove(img)
    # the view looks away from the cube: background only
    rv3d.view_location = Vector((1000.0, 0.0, 0.0))
    os.remove(out)
    assert bpy.ops.allset.render_current_frame(write_still=True) == {'FINISHED'}
    img = bpy.data.images.load(out)
    try:
        reds = {round(v, 3) for v in list(img.pixels)[0::4]}
        assert len(reds) <= 2, f"camera follows the view (distinct red values {len(reds)})"
    finally:
        bpy.data.images.remove(img)
    rv3d.view_location = Vector((0.0, 0.0, 0.0))


def test_render_sequence_operator():
    assert rp.ALLSET_OT_render_sequence.bl_idname == "allset.render_sequence"
    assert rp.ALLSET_OT_render_sequence.ANIMATION and not rp.ALLSET_OT_render_current_frame.ANIMATION
    assert "write_still" in bpy.ops.allset.render_sequence.get_rna_type().properties


def test_maya_render_items_use_the_persp_operators():
    m = menu_map.MAP
    assert m["Render/Render Current Frame"] == "allset.render_current_frame"
    assert m["Render/Redo Previous Render"] == "allset.render_current_frame"
    assert m["Playback/Render Current Frame"] == "allset.render_current_frame"
    assert m["Render/Render Sequence"] == "allset.render_sequence"
    assert shelf_map.BY_COMMAND["RenderSequence"][0] == "allset.render_sequence"
    assert shelf_map.BY_COMMAND["BatchRender"][0] == "allset.render_sequence"
    # no Maya render item renders through Blender's render.render directly any more
    for path, action in m.items():
        if path.startswith(("Render/", "Playback/Render")):
            assert "render.render" not in repr(action), (path, action)
