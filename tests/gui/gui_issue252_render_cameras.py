"""Render Sequence with All Render-Enabled Cameras in a real UI: Maya Workflow Kit layout -> new Maya scene -> cube +
two cameras (one with Renderable off) -> Render Sequence (all cameras, INVOKE) -> one render job after another, each
camera's frames in its own folder (persp, camA), the off camera not rendered, output path / camera / size restored."""

import os
import shutil
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, win  # noqa: E402

GUI_TIMEOUT = 300
C = {}
OUT = os.path.join(os.environ.get("ALLSET_GUI_SHOTS") or os.path.join(os.getcwd(), "tmp"), "gui_issue252")


def mod(name):
    return import_module(MODULE + name)


def v3d():
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def wait(fn, cond, limit=600):
    C.setdefault(fn.__name__, 0)
    if not cond() and C[fn.__name__] < limit:
        C[fn.__name__] += 1
        sys.modules["sim"]._steps.insert(0, fn)
        return True
    return False


def _camera(name, x):
    ob = bpy.data.objects.new(name, bpy.data.cameras.new(name + "Shape"))
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (x, -30.0, 0.0)
    ob.rotation_euler = (1.5708, 0.0, 0.0)
    return ob


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)
    sc = bpy.context.scene
    area, region = v3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    _camera("camA", 0.0)
    off = _camera("camOff", 5.0)
    off.data.allset_renderable = False
    r = sc.render
    r.engine = 'BLENDER_WORKBENCH'
    r.resolution_x = r.resolution_y = 16
    r.resolution_percentage = 100
    r.image_settings.file_format = 'PNG'
    sc.frame_start, sc.frame_end = 1, 2
    r.filepath = os.path.join(OUT, "shot_")
    C["before"] = (r.filepath, sc.camera, r.resolution_x, r.resolution_y, r.resolution_percentage)
    names = [o.name for o in mod(".operators.render_cameras").renderable_cameras(sc)]
    check(f"renderable cameras: startup persp + camA ({names})", names == ["persp", "camA"])
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["ret"] = bpy.ops.allset.render_sequence('INVOKE_DEFAULT', all_cameras=True)


@step
def s_done():
    rc = mod(".operators.render_cameras")
    if wait(s_done, lambda: not rc._chain["jobs"] and not rc._chain["timer"] and not bpy.app.is_job_running('RENDER')):
        return
    sc = bpy.context.scene
    r = sc.render
    found = {d: sorted(os.listdir(os.path.join(OUT, d))) for d in sorted(os.listdir(OUT))
             if os.path.isdir(os.path.join(OUT, d))}
    want = ["shot_0001.png", "shot_0002.png"]
    check(f"Render Sequence all cameras ({C['ret']}): one folder per renderable camera ({found})",
          found == {"persp": want, "camA": want} and rc._chain["done"] == 2)
    after = (r.filepath, sc.camera, r.resolution_x, r.resolution_y, r.resolution_percentage)
    check(f"output path, camera and size restored ({after[0]}, {after[1]})", after == C["before"])
    left = [o.name for o in bpy.data.objects if o.get("allset_default_light")]
    check(f"no default light left ({left})", not left)
    for w in list(bpy.context.window_manager.windows[1:]):
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


run()
