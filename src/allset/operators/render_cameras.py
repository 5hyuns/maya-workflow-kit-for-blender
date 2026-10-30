# SPDX-License-Identifier: GPL-3.0-or-later
"""Renderable cameras and Skip existing frames, like Maya's Render Sequence.

- Each camera has Maya's Renderable check (``Camera.allset_renderable``, stored on the camera data like Maya's camera
  shape attribute; on by default, off for Maya's startup top / front / side cameras). It shows in the Attribute
  Editor camera tab (Output Settings) and in Render Settings > Common > Renderable Cameras.
- Render Sequence with All Render-Enabled Cameras renders the animation once per renderable camera. With more than
  one camera each camera's frames go into a folder named after the camera next to the usual output
  (``<folder>/<camera>/<file name>``); the output path, render camera and render size come back afterwards.
- Render Settings > Common > Render Options > Skip existing frames is Blender's Overwrite off + Placeholders on (the
  scene's own output options), so a stopped sequence picks up where it stopped and several computers rendering the
  same frame range into one folder share out the frames.
"""

import bpy
from bpy.props import BoolProperty

from .. import live_refs, results

PROP = "allset_renderable"
STORE = "allset_renderable_on"      # the stored value (ID property of the camera data); unset = the camera's default
_BAD = '<>:"/\\|?*'
_chain = {"jobs": [], "restore": None, "window": 0, "scene": "", "cancelled": False, "timer": False, "done": 0}


# --- renderable cameras ---------------------------------------------------------------------------------------

def default_renderable(cam):
    """Renderable of a camera never set: on, except Maya's startup top / front / side cameras."""
    from . import startup_cameras
    return not any(ob.data == cam and startup_cameras.is_startup(ob) and ob.get(startup_cameras.MARK) != "persp"
                   for ob in bpy.data.objects if ob.type == 'CAMERA')


def _renderable_get(cam):
    value = cam.get(STORE)
    return default_renderable(cam) if value is None else bool(value)


def _renderable_set(cam, value):
    cam[STORE] = bool(value)


def is_renderable(ob):
    return ob is not None and ob.type == 'CAMERA' and ob.data is not None and bool(getattr(ob.data, PROP, True))


def _order(ob):
    from . import render_persp, startup_cameras
    if startup_cameras.is_startup(ob):
        return (0, startup_cameras.NAMES.index(ob.get(startup_cameras.MARK)), "")
    if ob.get(render_persp.PROP):
        return (0, 0, "")
    return (1, 0, ob.name)


def renderable_cameras(scene):
    """The scene's renderable cameras: Maya's startup / persp camera first, then the others by name."""
    from . import render_persp
    obs = [ob for ob in scene.objects if is_renderable(ob)]
    persp = render_persp.persp_camera(create=False)
    if persp is not None and persp not in obs and is_renderable(persp):
        obs.append(persp)
    return sorted(obs, key=_order)


def folder_name(name):
    """A camera name usable as one folder name."""
    clean = "".join("_" if c in _BAD or ord(c) < 32 else c for c in name).strip(" .")
    return clean or "camera"


def camera_output(filepath, name):
    """Render output path ``filepath`` with a folder for camera ``name`` before its file name part."""
    i = max(filepath.rfind("/"), filepath.rfind("\\"))
    sep = filepath[i] if i >= 0 else "/"
    return f"{filepath[:i + 1]}{folder_name(name)}{sep}{filepath[i + 1:]}"


# --- render every renderable camera ------------------------------------------------------------------------------

def plan(scene, base_path):
    """[(camera, output path)] of an All Render-Enabled Cameras render."""
    cams = renderable_cameras(scene)
    if len(cams) <= 1:
        return [(ob, base_path) for ob in cams]
    return [(ob, camera_output(base_path, ob.name)) for ob in cams]


def _prepare(context, scene, cams):
    """Put the persp camera at the view (Maya's persp is the view) when it renders and the view isn't a camera's."""
    from . import render_persp
    space, rv3d = render_persp.find_view(context)
    if rv3d is None or render_persp.view_camera(space, rv3d, scene) is not None:
        return
    persp = render_persp.persp_camera(create=False)
    if persp is not None and persp in cams:
        render_persp.match_view(persp, space, rv3d, scene)


def _saver(scene, restore_size):
    old_path, old_cam = scene.render.filepath, scene.camera

    def restore():
        try:
            scene.render.filepath = old_path
            scene.camera = old_cam
        except ReferenceError:
            pass
        restore_size()
    return restore


def render_all(op, context, how, base_path=None):
    """Render the animation through every renderable camera (Render Sequence, All Render-Enabled Cameras)."""
    from . import default_light, render_batch
    scene = context.scene
    if _chain["jobs"] or default_light._render_running():
        op.report({'WARNING'}, "A render is already running")
        return {'CANCELLED'}
    cams = renderable_cameras(scene)
    if not cams:
        op.report({'WARNING'}, "No renderable cameras: turn on Renderable for a camera")
        return {'CANCELLED'}
    _prepare(context, scene, cams)
    restore = _saver(scene, render_batch.scaled(context))
    jobs = plan(scene, base_path if base_path is not None else scene.render.filepath)
    names = ", ".join(ob.name for ob, _p in jobs)
    if how != 'INVOKE_DEFAULT':
        try:
            for ob, path in jobs:
                _setup(scene, ob, path)
                try:
                    res = bpy.ops.render.render('EXEC_DEFAULT', animation=True)
                finally:
                    default_light.remove_all()
                if 'CANCELLED' in res:
                    return {'CANCELLED'}
        except RuntimeError as ex:
            op.report({'ERROR'}, str(ex))
            return {'CANCELLED'}
        finally:
            restore()
        results.result(op, f"Rendered through {names}")
        return {'FINISHED'}
    _chain.update(jobs=[(ob.name, path) for ob, path in jobs], restore=restore, scene=scene.name,
                  window=live_refs.pointer(context.window), cancelled=False, done=0)
    if not _start_next():
        return {'CANCELLED'}
    results.result(op, f"Rendering through {names}")
    return {'FINISHED'}


def _setup(scene, ob, path):
    from . import default_light
    scene.camera = ob
    scene.render.filepath = path
    default_light.add(scene, ob)


def _on_cancel(*_args):
    _chain["cancelled"] = True        # (render thread: only a flag)


def _start_next():
    """Start the next camera's INVOKE render; False when the chain is over."""
    from . import default_light
    scene = bpy.data.scenes.get(_chain["scene"])
    window = live_refs.window(_chain["window"]) or (live_refs.windows() or [None])[0]
    while _chain["jobs"]:
        name, path = _chain["jobs"].pop(0)
        ob = bpy.data.objects.get(name)
        if scene is None or window is None or ob is None:
            continue
        _setup(scene, ob, path)
        try:
            with bpy.context.temp_override(window=window, scene=scene):
                res = bpy.ops.render.render('INVOKE_DEFAULT', animation=True, scene=scene.name)
        except RuntimeError:
            res = {'CANCELLED'}
        if 'CANCELLED' in res:
            break
        _chain["done"] += 1
        _watch()
        return True
    _finish()
    return False


def _watch():
    if _on_cancel not in bpy.app.handlers.render_cancel:
        bpy.app.handlers.render_cancel.append(_on_cancel)
    if not _chain["timer"]:
        _chain["timer"] = True
        bpy.app.timers.register(_tick, first_interval=0.2, persistent=True)


def _tick():
    from . import default_light
    if default_light._render_running():
        return 0.2
    default_light.remove_all()
    if _chain["cancelled"] or not _chain["jobs"]:
        _chain["timer"] = False
        _finish()
        return None
    if _start_next():
        return 0.2
    _chain["timer"] = False
    return None


def _finish():
    from . import default_light
    _chain["jobs"] = []
    restore, _chain["restore"] = _chain["restore"], None
    if restore is not None:
        try:
            restore()
        except (ReferenceError, RuntimeError):
            pass
    default_light.remove_all()
    if _on_cancel in bpy.app.handlers.render_cancel:
        bpy.app.handlers.render_cancel.remove(_on_cancel)


# --- Skip existing frames ----------------------------------------------------------------------------------------

def _skip_get(scene):
    return not scene.render.use_overwrite


def _skip_set(scene, value):
    scene.render.use_overwrite = not value
    scene.render.use_placeholder = bool(value)


def register_props():
    bpy.types.Camera.allset_renderable = BoolProperty(
        name="Renderable", get=_renderable_get, set=_renderable_set,
        description="Render Sequence with All Render-Enabled Cameras renders this camera (like Maya)")
    bpy.types.Scene.allset_skip_existing = BoolProperty(
        name="Skip existing frames", get=_skip_get, set=_skip_set,
        description="Animation renders leave frames whose image already exists and mark the frame being rendered "
                    "with an empty file, so a render can resume and several computers can share a frame range "
                    "(Blender's Overwrite off, Placeholders on)")


def unregister_props():
    if _chain["timer"] and bpy.app.timers.is_registered(_tick):
        bpy.app.timers.unregister(_tick)
    _chain["timer"] = False
    try:
        _finish()
    except AttributeError:          # restricted context while Blender quits
        _chain.update(jobs=[], restore=None)
    del bpy.types.Scene.allset_skip_existing
    del bpy.types.Camera.allset_renderable
