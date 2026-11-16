"""#350: in a real UI the Modify > Match Transformations option boxes open Maya's option windows, and the window's
command button (Enter) runs the match with the window's values:

1. Match Translation ❒ with X only checked: the source moves along X onto the target, its Y / Z stay.
2. Match All Transforms ❒ (all on): the source takes the target's translation, rotation and scale.
3. Match Pivots ❒ with Orientation on: the source's pivot moves onto the target's and it turns to the target's
   orientation, its points staying where they are.
Screenshots (ALLSET_GUI_SHOTS): the three windows."""

import os
import sys
from importlib import import_module

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
MENU = "Modify/Match Transformations/"
C = {}
TOL = 1e-4


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def mod(name):
    return import_module(f"{MODULE}.{name}")


def key(k):
    ev(k, 'PRESS')
    ev(k, 'RELEASE')


def _cube(name, loc, rot=(0, 0, 0), scale=(1, 1, 1)):
    a, r = view3d()
    with bpy.context.temp_override(window=win(), area=a, region=r):
        bpy.ops.allset.create(kind='CUBE')
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.location, ob.rotation_euler, ob.scale = loc, rot, scale
    return ob


def _scene():
    for ob in list(bpy.context.scene.objects):
        bpy.data.objects.remove(ob)
    src = _cube("src", (-3, 0.5, 0.25), (0.2, -0.3, 0.4), (0.5, 1.5, 2.0))
    lead = _cube("lead", (2, 1, 0.5), (0.5, 0.6, 0.7), (1.5, 0.5, 2.0))
    order = mod("operators.pick_order")
    for o in bpy.context.scene.objects:
        o.select_set(False)
    order._sync(bpy.context.scene, bpy.context.view_layer)
    for o in (src, lead):          # the target is picked last (the kit keeps the pick order)
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        order._sync(bpy.context.scene, bpy.context.view_layer)
    bpy.context.view_layer.update()
    check("the target is the last pick", order.last(bpy.context) == lead)
    C["before"] = (Vector(src.location), Vector(src.rotation_euler), Vector(src.scale))


def _open(label):
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])
    path = MENU + label
    with bpy.context.temp_override(window=win()):
        res = bpy.ops.allset.menu_option_box('INVOKE_DEFAULT', item=path)
    check(f"{path} option box opens its window ({mod('ui.menu_sets').option_kind(path)}, {res})",
          mod("ui.menu_sets").option_kind(path) == "window" and res in ({'FINISHED'}, {'RUNNING_MODAL'}))


def _dialog_shown(name):
    """The option window darkens the middle of the viewport (a dialog under the pointer)."""
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
    box = a[y - 60:y + 60, x - 120:x + 120]
    return float((box < 45 / 255).mean())


@step
def s_setup():
    C["x"], C["y"] = setup()
    key('ESC')
    a, r = view3d()
    C["mid"] = (a.x + a.width // 2, a.y + a.height // 2)
    ow = mod("operators.option_windows")
    for k in ("match_all", "match_translation", "match_rotation", "match_scaling", "match_pivots"):
        ow.store(k, None)


# --- 1. Match Translation, X only ---------------------------------------------------------------------------------

@step
def s1_open():
    _scene()
    mod("operators.option_windows").store("match_translation", {"all": False, "x": True, "y": False, "z": False})
    _open("Match Translation")


@step
def s1_away():
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0] + 30, y=C["mid"][1] - 10)


@step
def s1_shot():
    share = _dialog_shown("350_match_translation_window.png")
    check(f"Match Translation Options is shown (dark share {share:.2f})", share > 0.3)
    key('RET')                                   # the window's command button: Match Translation


@step
def s1_done():
    src, lead = bpy.data.objects["src"], bpy.data.objects["lead"]
    t0 = C["before"][0]
    got = Vector(src.location)
    check(f"X only: the source's Translate X takes the target's, Y / Z stay ({tuple(got)})",
          abs(got.x - lead.location.x) < TOL and abs(got.y - t0.y) < TOL and abs(got.z - t0.z) < TOL)


# --- 2. Match All Transforms, defaults ---------------------------------------------------------------------------

@step
def s2_open():
    _scene()
    _open("Match All Transforms")


@step
def s2_away():
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0] + 30, y=C["mid"][1] - 10)


@step
def s2_shot():
    share = _dialog_shown("350_match_all_window.png")
    check(f"Match All Transforms Options is shown (dark share {share:.2f})", share > 0.3)
    key('RET')


@step
def s2_done():
    src, lead = bpy.data.objects["src"], bpy.data.objects["lead"]
    bpy.context.view_layer.update()
    ok = all(abs(a - b) < TOL for a, b in zip(src.matrix_world.col[3], lead.matrix_world.col[3]))
    t1, r1, s1 = src.matrix_world.decompose()
    t2, r2, s2 = lead.matrix_world.decompose()
    check(f"all on: the source takes the target's transforms (scale {tuple(s1)} / {tuple(s2)})",
          ok and r1.rotation_difference(r2).angle < 1e-4 and (s1 - s2).length < TOL)
    saved = mod("operators.option_windows").saved("match_all")
    check(f"the window's values are kept ({saved})",
          saved == {"translate": True, "rotate": True, "scale": True, "box": False})


# --- 3. Match Pivots with Orientation ----------------------------------------------------------------------------

@step
def s3_open():
    _scene()
    src = bpy.data.objects["src"]
    C["verts"] = [src.matrix_world @ v.co for v in src.data.vertices]
    mod("operators.option_windows").store("match_pivots", {"rotate": True, "scale": True, "orient": True})
    _open("Match Pivots")


@step
def s3_away():
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0] + 30, y=C["mid"][1] - 10)


@step
def s3_shot():
    share = _dialog_shown("350_match_pivots_window.png")
    check(f"Match Pivots Options is shown (dark share {share:.2f})", share > 0.3)
    key('RET')


@step
def s3_done():
    src, lead = bpy.data.objects["src"], bpy.data.objects["lead"]
    bpy.context.view_layer.update()
    at = (src.matrix_world.translation - lead.matrix_world.translation).length
    turn = src.matrix_world.to_quaternion().rotation_difference(lead.matrix_world.to_quaternion()).angle
    moved = max((p - src.matrix_world @ v.co).length for p, v in zip(C["verts"], src.data.vertices))
    check(f"pivot on the target's ({at:.5f}), turned to its orientation ({turn:.5f}), points stay ({moved:.5f})",
          at < TOL and turn < 1e-4 and moved < TOL)
    ow = mod("operators.option_windows")
    for k in ("match_all", "match_translation", "match_pivots"):
        ow.store(k, None)


run()
