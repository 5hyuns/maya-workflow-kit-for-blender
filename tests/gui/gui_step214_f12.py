"""Step 214 (#120) lane F12 in a real UI: Maya Workflow Kit layout, a cube, no lights, a camera -> F12 over the
Outliner = Blender's Render Image through ``allset.render_blender``: the Render window opens, the cube is lit by
the default light, like Maya (added on the main thread before the render job, operators/default_light.py) and the light is
gone after the job. F12 over the 3D View in object mode stays Maya's UV selection mask (no render).
Screenshots: gui_step214_f12_render.png (Render window), gui_step214_f12_main.png."""

import os
import sys
import tempfile
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

GUI_TIMEOUT = 240
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name, window=None):
    if SHOTS:
        with bpy.context.temp_override(window=window or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def biggest(kind):
    area = max((a for a in win().screen.areas if a.type == kind), key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def redraw_all():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def render_window():
    for w in bpy.context.window_manager.windows[1:]:
        for a in w.screen.areas:
            img = getattr(a.spaces.active, "image", None) if a.type == 'IMAGE_EDITOR' else None
            if img is not None and img.type == 'RENDER_RESULT':
                return w, a
    return None, None


def wait(fn, cond, limit=150):
    C.setdefault(fn.__name__, 0)
    if not cond() and C[fn.__name__] < limit:
        C[fn.__name__] += 1
        sys.modules["sim"]._steps.insert(0, fn)
        return True
    return False


def marked():
    return [o.name for o in bpy.data.objects if o.get("allset_default_light")] + \
        [d.name for d in bpy.data.lights if d.get("allset_default_light")]


def live_f12():
    """Keymap items on F12 (no modifiers) that are on: the add-on keyconfig (the Maya keys) and the active one."""
    kcs = bpy.context.window_manager.keyconfigs
    out = []
    for tag, kc in (("addon", kcs.addon), ("active", kcs.active)):
        for km in (kc.keymaps if kc else ()):
            for k in km.keymap_items:
                if k.active and k.type == 'F12' and not (k.shift or k.ctrl or k.alt or k.oskey):
                    out.append((tag, km.name, k.idname))
    return out


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    sc = bpy.context.scene
    area, region = biggest('VIEW_3D')
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    C["cube"] = bpy.context.active_object.name
    bpy.context.active_object.scale = (6.0, 6.0, 6.0)      # big enough to read in the screenshot
    # the render camera = Maya's startup persp (a kit new scene has it, hidden), as a user's "look through" would set
    persp = next((o for o in bpy.data.objects if o.get("allset_startup_camera") == "persp"), None)
    sc.camera = persp
    sc.render.resolution_percentage = 50
    C["lights"] = [o.name for o in sc.objects if o.type == 'LIGHT']
    C["f12"] = live_f12()
    print("STEP214_F12 live F12 items", C["f12"])
    redraw_all()


@step
def s_press_f12():
    check(f"scene: cube {C['cube']}, camera {bpy.context.scene.camera and bpy.context.scene.camera.name}, "
          f"no lights {C['lights']}", C["cube"] and bpy.context.scene.camera is not None and not C["lights"])
    f12 = C["f12"]
    blender_own = [it for it in f12 if it[0] == "active" and it[2] == "render.render"]
    check(f"Maya mode: Blender's own F12 render.render is off ({blender_own}); kit F12 items {f12}",
          not blender_own and ("addon", "Screen", "allset.render_blender") in f12
          and ("addon", "Object Mode", "allset.uv_component") in f12)
    bpy.app.handlers.render_pre.append(_seen)
    area, region = biggest('OUTLINER')
    x, y = region.x + region.width // 2, region.y + region.height // 2
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('F12', 'PRESS', x=x, y=y)
    ev('F12', 'RELEASE', x=x, y=y)


def _seen(scene, *_a):
    """render_pre (the job thread): the scene's lights the render sees."""
    C.setdefault("seen", []).append([o.name for o in scene.objects if o.type == 'LIGHT'])


@step
def s_during():
    C["during"] = (marked(), bpy.app.is_job_running('RENDER'))


@step
def s_rendered():
    if wait(s_rendered, lambda: not bpy.app.is_job_running('RENDER') and render_window()[0] is not None):
        redraw_all()
        return
    w, _a = render_window()
    check(f"F12 over the Outliner: the Render window opened ({w is not None})", w is not None)
    bpy.app.handlers.render_pre.remove(_seen)
    names, job = C["during"]
    check(f"the render saw the default light (render_pre: {C.get('seen')}; next tick: {names}, job {job})",
          C.get("seen") == [["defaultLight"]])
    path = os.path.join(SHOTS or tempfile.gettempdir(), "gui_step214_f12_result.png")
    stats = (0, 0.0)
    try:
        bpy.data.images["Render Result"].save_render(filepath=path)
        img = bpy.data.images.load(path)
        px = list(img.pixels)
        wd, ht = img.size
        bg = px[0:3]
        hits = [k for k in range(wd * ht) if max(abs(px[4 * k + c] - bg[c]) for c in range(3)) > 0.03]
        mean = sum(max(px[4 * k + c] for c in range(3)) for k in hits) / len(hits) if hits else 0.0
        stats = (len(hits), mean)
        bpy.data.images.remove(img)
    except (RuntimeError, KeyError) as ex:
        C["err"] = str(ex)
    print("STEP214_F12 render", stats, path)
    check(f"the cube is lit in the Render Result ({stats[0]} cube pixels, mean {stats[1]:.3f} > 0.15"
          f"{C.get('err', '')})", stats[0] > 300 and stats[1] > 0.15)
    C["rv"] = w
    redraw_all()


@step
def s_cleaned():
    if wait(s_cleaned, lambda: not marked(), limit=20):
        return
    check(f"the default light is gone after the render ({marked()})", not marked())
    redraw_all()


@step
def s_shots():
    shot("gui_step214_f12_render.png", C["rv"])
    shot("gui_step214_f12_main.png")
    for w in list(bpy.context.window_manager.windows[1:]):
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


@step
def s_f12_in_view():
    """F12 over the 3D View in object mode = Maya's UV selection mask, not a render."""
    C["mode_before"] = bpy.context.mode
    area, region = biggest('VIEW_3D')
    x, y = region.x + region.width // 2, region.y + region.height // 2
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('F12', 'PRESS', x=x, y=y)
    ev('F12', 'RELEASE', x=x, y=y)


@step
def s_view_result():
    running = bpy.app.is_job_running('RENDER')
    check(f"F12 over the 3D View: no render ({running}), Maya UV mask entered component mode "
          f"({C['mode_before']} -> {bpy.context.mode})", not running and bpy.context.mode == 'EDIT_MESH'
          and not marked())


run()
