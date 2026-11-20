"""#398 in a real UI: the panel toolbar's Image Plane button in a top view of the Maya layout.

- The view has no image plane: the button opens a file browser; picking an image there makes imagePlane1 showing it,
  facing up (the top view) at the origin.
- The next click opens the file browser again (the top view's planes aren't tied to it, every click imports one
  more image); imagePlane1 stays shown."""

import os
import sys
import tempfile
from importlib import import_module

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, setup, step, view3d, win, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 240
FOLDER = tempfile.mkdtemp(prefix="gui398_")
PNG = "ref398.png"
C = {}


def steps():
    return sys.modules["sim"]._steps


def again(fn, cond, limit=40):
    """Run ``fn`` again next tick while ``cond()`` is false (at most ``limit`` times); True = waiting."""
    n = C.setdefault("wait_" + fn.__name__, 0)
    if not cond() and n < limit:
        C["wait_" + fn.__name__] = n + 1
        steps().insert(0, fn)
        return True
    return False


def file_browser():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type == 'FILE_BROWSER' and a.spaces.active.params is not None \
                    and a.spaces.active.active_operator is not None:
                return w, a
    return None, None


def planes():
    return [ob for ob in bpy.data.objects if ob.type == 'EMPTY' and ob.empty_display_type == 'IMAGE']


def click_button():
    """What the toolbar button runs: allset.panel_run with its row's operator, in the view."""
    pmd = import_module(MODULE + ".ui.panel_menu_data")
    _g, _kind, (op_id, props), _label = next(i for g in pmd.TOOLBAR for i in g if i[3] == "Image Plane")
    area, region = view3d()
    import json
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return bpy.ops.allset.panel_run('INVOKE_DEFAULT', op=op_id, props=json.dumps(props))


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_top():
    img = bpy.data.images.new(PNG, 300, 150)
    img.filepath_raw = os.path.join(FOLDER, PNG)
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    area, _region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = (1.0, 0.0, 0.0, 0.0)          # top
    C["n"] = len(bpy.data.objects)


@step
def s_click():
    C["res"] = click_button()


@step
def s_browser():
    if again(s_browser, lambda: file_browser()[0] is not None):
        return
    w, a = file_browser()
    check(f"a view without an image plane: the button opens a file browser ({C['res']})", a is not None)
    check("nothing is made before an image is picked", len(bpy.data.objects) == C["n"])
    if a is None:
        return
    params = a.spaces.active.params
    params.directory = FOLDER.encode() if isinstance(params.directory, bytes) else FOLDER
    params.filename = PNG
    region = next(r for r in a.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=w, area=a, region=region):
        C["exec"] = bpy.ops.file.execute()


@step
def s_made():
    if again(s_made, lambda: bool(planes())):
        return
    found = planes()
    check(f"picking the image makes one image plane ({[o.name for o in found]}, {C.get('exec')})", len(found) == 1)
    if not found:
        return
    ob = found[0]
    path = bpy.path.abspath(ob.data.filepath) if ob.data else ""
    check(f"{ob.name} shows the picked image ({path})",
          os.path.normcase(path) == os.path.normcase(os.path.join(FOLDER, PNG)))
    normal = ob.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))
    check(f"{ob.name} faces the top view: facing up ({tuple(round(c, 4) for c in normal)})",
          (normal - Vector((0.0, 0.0, 1.0))).length < 1e-4)
    check(f"{ob.name} is at the origin ({tuple(ob.matrix_world.translation)})", ob.matrix_world.translation.length < 1e-6)
    check("the file browser closed", file_browser()[0] is None)
    C["plane"], C["n"] = ob.name, len(bpy.data.objects)


@step
def s_again():
    click_button()


@step
def s_again_browser():
    if again(s_again_browser, lambda: file_browser()[0] is not None):
        return
    w, a = file_browser()
    ob = bpy.data.objects.get(C.get("plane", ""))
    check("the next click in the top view opens the file browser again", a is not None)
    check("... and imagePlane1 stays shown", ob is not None and not ob.hide_get())
    if a is not None:
        r = next(r for r in a.regions if r.type == 'WINDOW')
        x, y = r.x + r.width // 2, r.y + r.height // 2
        w.event_simulate(type='MOUSEMOVE', value='NOTHING', x=x, y=y)
        w.event_simulate(type='ESC', value='PRESS', x=x, y=y)
        w.event_simulate(type='ESC', value='RELEASE', x=x, y=y)


@step
def s_cancelled():
    if again(s_cancelled, lambda: file_browser()[0] is None):
        return
    check("cancelling the browser makes nothing", file_browser()[0] is None and len(bpy.data.objects) == C["n"])


run()
