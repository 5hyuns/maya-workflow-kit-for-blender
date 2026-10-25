"""Step 214 (#120) lane F12: Blender's own render keys lit by Maya's default light.

A UI render's render_* handlers run on the job thread (checked, operators/default_light.py docstring), so the kit
wraps the keys with ``allset.render_blender`` (light added on the main thread, render.render, light removed when the
render ends). Maya mode binds F12 / Ctrl+F12 in "Screen" and wraps IC's Ctrl+Alt+Enter; F12 stays Maya's UV mask in
the 3D View (object / edit mesh) and the UV Editor. The GUI side (F12 opens the Render window, lit cube, light gone
afterwards) is tests/gui/gui_step214_f12.py."""

import os
import threading
from importlib import import_module

import bpy
from mathutils import Vector

import kit

dl = import_module(kit.MODULE + ".operators.default_light")
sw = import_module(kit.MODULE + ".switch")


def _scene():
    """A cube at the origin, a camera looking at it, no lights, no world: Cycles, tiny, black background."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.lights, bpy.data.cameras):
        for d in list(coll):
            coll.remove(d)
    sc = bpy.context.scene
    sc.world = None
    sc.allset_default_light = True
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    cam = bpy.data.objects.new("camera1", bpy.data.cameras.new("camera1"))
    sc.collection.objects.link(cam)
    cam.location = (5.0, -5.0, 4.0)
    cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    r = sc.render
    r.engine = 'CYCLES'
    sc.cycles.samples, sc.cycles.use_denoising, sc.cycles.device = 4, False, 'CPU'
    r.resolution_x, r.resolution_y, r.resolution_percentage = 32, 32, 100
    r.film_transparent = False
    return sc


def _centre():
    """Mean RGB of the Render Result's 4 x 4 centre pixels (the cube fills the middle)."""
    path = os.path.join(bpy.app.tempdir, "step214_f12.png")
    bpy.data.images["Render Result"].save_render(path)
    img = bpy.data.images.load(path)
    try:
        w, h = img.size
        px = img.pixels[:]
        vals = [px[(y * w + x) * 4 + c] for y in range(h // 2 - 2, h // 2 + 2) for x in range(w // 2 - 2, w // 2 + 2)
                for c in range(3)]
    finally:
        bpy.data.images.remove(img)
    return sum(vals) / len(vals)


class _Seen:
    def __init__(self):
        self.log = []

    def __call__(self, scene, *_a):
        self.log.append({"main": threading.current_thread() is threading.main_thread(),
                         "lights": [(o.name, bool(o.get(dl.MARK)), o.parent.name if o.parent else "")
                                    for o in scene.objects if o.type == 'LIGHT']})

    def __enter__(self):
        bpy.app.handlers.render_pre.append(self)
        return self

    def __exit__(self, *_a):
        bpy.app.handlers.render_pre.remove(self)


def _no_marked():
    assert not [o.name for o in bpy.data.objects if o.get(dl.MARK)], "default light object left behind"
    assert not [d.name for d in bpy.data.lights if d.get(dl.MARK)], "default light data left behind"


def _render(**kw):
    with _Seen() as seen:
        res = bpy.ops.allset.render_blender('EXEC_DEFAULT', **kw)
    assert res == {'FINISHED'}, res
    return seen.log


def test_render_blender_lights_the_scene_during_the_render_only():
    _scene()
    log = _render(use_viewport=True)
    assert len(log) == 1 and log[0]["main"], log
    assert log[0]["lights"] == [("defaultLight", True, "camera1")], log
    lit = _centre()
    _no_marked()
    assert not [o for o in bpy.context.scene.objects if o.type == 'LIGHT']
    print("STEP214_F12 lit centre", round(lit, 4))
    assert lit > 0.15, lit


def test_enable_default_light_off_renders_black():
    sc = _scene()
    sc.allset_default_light = False
    log = _render()
    assert log[0]["lights"] == [], log
    dark = _centre()
    print("STEP214_F12 off centre", round(dark, 4))
    assert dark < 0.02, dark
    _no_marked()


def test_a_scene_light_turns_it_off():
    sc = _scene()
    lamp = bpy.data.objects.new("pointLight1", bpy.data.lights.new("pointLight1", 'POINT'))
    sc.collection.objects.link(lamp)
    lamp.location = Vector((0, 0, 10))
    log = _render()
    assert log[0]["lights"] == [("pointLight1", False, "")], log
    _no_marked()


def test_plain_render_render_has_no_default_light():
    """Blender's own render.render (the top bar Render > Render Image) is not wrapped: no light."""
    _scene()
    with _Seen() as seen:
        assert bpy.ops.render.render() == {'FINISHED'}
    assert seen.log[0]["lights"] == [], seen.log
    assert _centre() < 0.02


def test_no_camera_cancels_and_leaves_nothing():
    sc = _scene()
    sc.camera = None
    for ob in [o for o in sc.objects if o.type == 'CAMERA']:
        bpy.data.objects.remove(ob)
    try:
        res = bpy.ops.allset.render_blender('EXEC_DEFAULT')
    except RuntimeError:
        res = {'CANCELLED'}
    assert res == {'CANCELLED'}, res
    _no_marked()


def _items(km_name, idname):
    km = kit.maya_kc().keymaps.get(km_name)
    return [k for k in (km.keymap_items if km else ()) if k.idname == idname]


def _ev(k):
    return (k.type, k.value, k.shift, k.ctrl, k.alt)


def test_keys_in_maya_mode():
    screen = {_ev(k): dict(animation=k.properties.animation, use_viewport=k.properties.use_viewport)
              for k in _items("Screen", "allset.render_blender")}
    assert screen == {("F12", 'PRESS', False, False, False): {"animation": False, "use_viewport": True},
                      ("F12", 'PRESS', False, True, False): {"animation": True, "use_viewport": True}}, screen
    # first in Screen (effective order): nothing with the same event before it
    km = kit.maya_kc().keymaps["Screen"]
    first_f12 = next(k for k in km.keymap_items if (k.type, k.ctrl, k.alt, k.shift) == ("F12", False, False, False))
    assert first_f12.idname == "allset.render_blender"
    # IC's Ctrl+Alt+Enter render animation is wrapped, no plain render.render left on it
    se = _items("Screen Editing", "allset.render_blender")
    assert [(_ev(k), k.properties.animation) for k in se] == [(("RET", 'PRESS', False, True, True), True)], se
    assert not [k for k in _items("Screen Editing", "render.render") if (k.type, k.ctrl, k.alt) == ("RET", True, True)]
    # Maya's F12 UV mask keeps the 3D View (object / edit mesh) and the UV Editor (their keymaps run before Screen)
    for km_name in ("Object Mode", "Mesh", "UV Editor"):
        uv = [k for k in _items(km_name, "allset.uv_component") if _ev(k) == ("F12", 'PRESS', False, False, False)]
        assert uv and uv[0].properties.mode == 'UV', km_name


def test_no_keys_or_operator_without_maya_mode():
    sw.set_mode(False, layout=False)
    try:
        assert not _items("Screen", "allset.render_blender")
        assert not _items("Screen Editing", "allset.render_blender")
        assert not hasattr(bpy.types, "ALLSET_OT_render_blender")
    finally:
        sw.set_mode(True, layout=False)
    assert _items("Screen", "allset.render_blender")


def test_disable_removes_the_keys():
    kit.disable()
    try:
        kcs = bpy.context.window_manager.keyconfigs
        left = [k.idname for km in (kcs.addon.keymaps if kcs.addon else ()) for k in km.keymap_items
                if k.idname == "allset.render_blender"]
        assert not left, left
    finally:
        kit.enable()
    assert _items("Screen", "allset.render_blender")
