"""#418: in a real UI the Edit Mesh > Extrude option box opens Extrude Face Options with Maya's Curve rows
(Curve: None / Selected / Generated, Taper, Twist), and its command button (Enter) with Curve: Generated and
Taper 0.5 makes the path curve and extrudes the selected face along it, tapered.
Screenshot (ALLSET_GUI_SHOTS): the window."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
PATH = "Edit Mesh/Extrude"
C = {}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def key(k):
    ev(k, 'PRESS')
    ev(k, 'RELEASE')


def _box(name):
    import numpy as np
    import tempfile
    path = os.path.join(SHOTS or tempfile.gettempdir(), name)
    screenshot(path)
    img = bpy.data.images.load(path)
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    a = a.reshape(h, w, 4)[:, :, :3].mean(axis=2)
    x, y = C["mid"]
    return a[y - 60:y + 60, x - 120:x + 120]


@step
def s_setup():
    C["x"], C["y"] = setup()
    key('ESC')
    a, r = view3d()
    C["mid"] = (a.x + a.width // 2, a.y + a.height // 2)
    for ob in list(bpy.context.scene.objects):
        bpy.data.objects.remove(ob)
    with bpy.context.temp_override(window=win(), area=a, region=r):
        bpy.ops.mesh.primitive_plane_add(size=2)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    ob = bpy.context.active_object
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(True)
    bmesh.update_edit_mesh(ob.data)
    C["ob"] = ob.name
    ow = mod("operators.option_windows")
    ow.store("extrude", {"divisions": 2, "offset": 0.0, "thickness": 0.0, "curve": "Generated", "taper": 0.5,
                         "twist": 0.0})


@step
def s_base():
    C["base"] = _box("418_extrude_before.png")
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])
    with bpy.context.temp_override(window=win()):
        res = bpy.ops.allset.menu_option_box('INVOKE_DEFAULT', item=PATH)
    check(f"{PATH} option box opens its window ({res})",
          mod("ui.menu_sets").option_kind(PATH) == "window" and res in ({'FINISHED'}, {'RUNNING_MODAL'}))


@step
def s_away():
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0] + 30, y=C["mid"][1] - 10)


@step
def s_shot():
    import numpy as np
    share = float((np.abs(_box("418_extrude_window.png") - C["base"]) > 8 / 255).mean())
    check(f"Extrude Face Options is shown (changed share {share:.2f})", share > 0.3)
    window = mod("operators.option_windows")._BY_KEY["extrude"]
    names = [f.name for f in window.fields]
    check(f"the window has Maya's Curve rows ({names})", names[3:] == ["curve", "taper", "twist"])
    key('RET')


@step
def s_done():
    ob = bpy.data.objects[C["ob"]]
    path = bpy.data.objects.get("polyExtrudeFace1Curve")
    check("Curve: Generated made the path curve", path is not None and path.type == 'CURVE')
    rec = mod("operators.extrude").current(ob)
    params = rec.params if rec is not None else {}
    check(f"the face went along it with the window's Taper / Divisions ({params})",
          rec is not None and rec.spec.kind == 'FACE_CURVE' and params.get("taper") == 0.5
          and params.get("divisions") == 2)
    bm = bmesh.from_edit_mesh(ob.data)
    caps = [f for f in bm.faces if f.select]
    size = max(abs(v.co.x) for f in caps for v in f.verts) if caps else 0.0
    check(f"the end face is half size ({size:.4f})", len(caps) == 1 and abs(size - 0.5) < 1e-4)


run()
