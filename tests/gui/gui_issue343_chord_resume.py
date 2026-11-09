"""#343: during an Alt+MMB track, pressing LMB as well dollies, and letting go of LMB while MMB is still held goes
back to the track without letting go of MMB, like Maya. The same for the other button orders: letting go of one
button of the Alt+LMB+MMB dolly carries on with the button still held (LMB = tumble, MMB = track), as often as the
second button is pressed and let go again, also after Alt is let go, and also when looking through a camera.
Esc still cancels the dolly and nothing carries on."""

import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

C = {}
NAV_OPS = {"VIEW3D_OT_rotate", "VIEW3D_OT_move", "VIEW3D_OT_zoom", "ALLSET_OT_dolly", "ALLSET_OT_nav_chord"}
RUNS = {"TRACK": "VIEW3D_OT_move", "TUMBLE": "VIEW3D_OT_rotate", "DOLLY": "ALLSET_OT_dolly"}
NAMES = {'LEFTMOUSE': "LMB", 'MIDDLEMOUSE': "MMB"}
DRAG = 60          # px per drag, alternating right / left so the mouse stays in the view
GUI_TIMEOUT = 300


def main_view():
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D']
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def rv3d():
    return main_view()[1].data


def modal_names():
    return [op.bl_idname for op in win().modal_operators]


def camera():
    cam = bpy.data.objects.get("chord_cam")
    if cam is None:
        cam = bpy.data.objects.new("chord_cam", bpy.data.cameras.new("chord_cam"))
        bpy.context.scene.collection.objects.link(cam)
    return cam


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    rv3d().view_perspective = 'PERSP'
    _area, region = main_view()
    C["xy"] = (region.x + int(region.width * 0.4), region.y + int(region.height * 0.55))


def state():
    rv = rv3d()
    cam = camera()
    return {"dist": rv.view_distance, "rot": rv.view_rotation.copy(), "loc": rv.view_location.copy(),
            "offset": Vector(rv.view_camera_offset), "zoom": rv.view_camera_zoom,
            "cam": cam.matrix_world.copy()}


def changes(a, b, through_camera):
    """What a drag changed: (kind -> amount)."""
    if not through_camera:
        return {"turn": a["rot"].rotation_difference(b["rot"]).angle, "slide": (a["loc"] - b["loc"]).length,
                "dolly": abs(b["dist"] - a["dist"]) / max(a["dist"], 1e-6)}
    m0, m1 = a["cam"], b["cam"]
    local = m0.to_3x3().normalized().transposed() @ (m1.translation - m0.translation)
    turn = m0.to_quaternion().rotation_difference(m1.to_quaternion()).angle
    side = Vector((local.x, local.y)).length + (a["offset"] - b["offset"]).length
    along = abs(local.z) + abs(b["zoom"] - a["zoom"]) * 0.01
    if turn > 1e-4:                    # a tumble around the view centre moves the camera as well
        side = along = 0.0
    return {"turn": turn, "slide": side, "dolly": along}


def looks_like(kind, ch):
    small = 1e-4
    if kind == "NONE":
        return all(v < small for v in ch.values())
    if kind == "TUMBLE":
        return ch["turn"] > 0.02 and ch["dolly"] < small
    if kind == "TRACK":
        return ch["slide"] > 1e-3 and ch["turn"] < small and ch["dolly"] < max(small, ch["slide"] * 0.05)
    if kind == "DOLLY":
        return ch["dolly"] > 1e-3 and ch["turn"] < small and ch["slide"] < max(small, ch["dolly"] * 0.05)
    raise ValueError(kind)


def add_sequence(label, actions, through_camera=False):
    """``actions``: ('press' | 'release', button), ('alt_up',), ('esc',), ('drag', TRACK | TUMBLE | DOLLY | NONE)."""
    S = {"down": set(), "alt": True, "drags": 0, "pos": None, "done": []}

    def prepare():
        if any(n in NAV_OPS for n in modal_names()):        # a case before left something running
            ev('ESC', 'PRESS')
            ev('ESC', 'RELEASE')
        rv = rv3d()
        if through_camera:
            cam = camera()
            cam.location = (9.0, -9.0, 6.0)
            cam.rotation_euler = (1.1, 0.0, 0.785)
            bpy.context.scene.camera = cam
            main_view()[0].spaces.active.lock_camera = False
            rv.view_perspective = 'CAMERA'
            rv.view_camera_offset = (0.0, 0.0)
            rv.view_camera_zoom = 0.0
        else:
            rv.view_perspective = 'PERSP'
            rv.view_distance = 15.0
        S["pos"] = list(C["xy"])
        S["down"].clear()
        S["alt"], S["drags"] = True, 0
        S["done"] = []
        ev('MOUSEMOVE', 'NOTHING', x=S["pos"][0], y=S["pos"][1])
        ev('LEFT_ALT', 'PRESS', alt=True, x=S["pos"][0], y=S["pos"][1])

    def button(kind, which):
        def fn():
            ev(which, 'PRESS' if kind == 'press' else 'RELEASE', alt=S["alt"], x=S["pos"][0], y=S["pos"][1])
            (S["down"].add if kind == 'press' else S["down"].discard)(which)
            S["done"].append(("+" if kind == 'press' else "-") + NAMES[which])
        return fn

    def alt_up():
        ev('LEFT_ALT', 'RELEASE', x=S["pos"][0], y=S["pos"][1])
        S["alt"] = False
        S["done"].append("-Alt")

    def esc():
        ev('ESC', 'PRESS', alt=S["alt"], x=S["pos"][0], y=S["pos"][1])
        ev('ESC', 'RELEASE', alt=S["alt"], x=S["pos"][0], y=S["pos"][1])
        S["done"].append("Esc")

    def drag(kind):
        def start():
            S["before"] = state()
            S["sign"] = 1 if S["drags"] % 2 == 0 else -1
            S["drags"] += 1
            S["pos"][0] += S["sign"] * DRAG // 2
            S["pos"][1] += S["sign"] * 10
            ev('MOUSEMOVE', 'NOTHING', alt=S["alt"], x=S["pos"][0], y=S["pos"][1])

        def finish():
            S["pos"][0] += S["sign"] * DRAG // 2
            S["pos"][1] += S["sign"] * 10
            ev('MOUSEMOVE', 'NOTHING', alt=S["alt"], x=S["pos"][0], y=S["pos"][1])
            S["modals"] = modal_names()

        def verify():
            ch = changes(S["before"], state(), through_camera)
            nav = sorted(n for n in S["modals"] if n in NAV_OPS)
            runs = RUNS.get(kind)
            if through_camera and kind == "DOLLY":
                runs = "VIEW3D_OT_zoom"          # through a camera the dolly is Blender's zoom (it moves the camera)
            others = [n for n in nav if n != runs and n != "ALLSET_OT_nav_chord"]
            amounts = ", ".join(f"{k} {v:.4f}" for k, v in ch.items())
            after = " ".join(S["done"]) or "start"
            ok = looks_like(kind, ch) and (runs is None or runs in nav) and not others
            check(f"{label}: drag after {after} = {kind} ({amounts}; running {nav})", ok)
        return start, finish, verify

    def release_all():
        for which in ('LEFTMOUSE', 'MIDDLEMOUSE'):
            if which in S["down"]:
                ev(which, 'RELEASE', alt=S["alt"], x=S["pos"][0], y=S["pos"][1])
        S["down"].clear()
        if S["alt"]:
            ev('LEFT_ALT', 'RELEASE', x=S["pos"][0], y=S["pos"][1])

    def clean():
        check(f"{label}: nothing left running ({modal_names()})", not any(n in NAV_OPS for n in modal_names()))
        rv3d().view_perspective = 'PERSP'

    step(prepare)
    for act in actions:
        if act[0] in ('press', 'release'):
            step(button(act[0], act[1]))
        elif act[0] == 'alt_up':
            step(alt_up)
        elif act[0] == 'esc':
            step(esc)
        else:
            for fn in drag(act[1]):
                step(fn)
    step(release_all)
    step(clean)


L, M = 'LEFTMOUSE', 'MIDDLEMOUSE'
# the issue: Alt+MMB track, + LMB = dolly, - LMB = track again
add_sequence("Alt+MMB, +LMB, -LMB", [('press', M), ('drag', "TRACK"), ('press', L), ('drag', "DOLLY"),
                                     ('release', L), ('drag', "TRACK"), ('release', M), ('drag', "NONE")])
add_sequence("Alt+LMB, +MMB, -MMB", [('press', L), ('drag', "TUMBLE"), ('press', M), ('drag', "DOLLY"),
                                     ('release', M), ('drag', "TUMBLE"), ('release', L), ('drag', "NONE")])
add_sequence("Alt+MMB, +LMB, -MMB", [('press', M), ('drag', "TRACK"), ('press', L), ('drag', "DOLLY"),
                                     ('release', M), ('drag', "TUMBLE"), ('release', L), ('drag', "NONE")])
add_sequence("Alt+LMB, +MMB, -LMB", [('press', L), ('drag', "TUMBLE"), ('press', M), ('drag', "DOLLY"),
                                     ('release', L), ('drag', "TRACK"), ('release', M), ('drag', "NONE")])
add_sequence("Alt+MMB, LMB twice", [('press', M), ('press', L), ('drag', "DOLLY"), ('release', L), ('drag', "TRACK"),
                                    ('press', L), ('drag', "DOLLY"), ('release', L), ('drag', "TRACK"),
                                    ('release', M)])
add_sequence("Alt+MMB, +LMB, Alt up, -LMB", [('press', M), ('press', L), ('drag', "DOLLY"), ('alt_up',),
                                             ('drag', "DOLLY"), ('release', L), ('drag', "TRACK"), ('release', M)])
add_sequence("Alt+MMB, +LMB, Esc", [('press', M), ('press', L), ('drag', "DOLLY"), ('esc',), ('release', L),
                                    ('drag', "NONE"), ('release', M)])
add_sequence("camera: Alt+MMB, +LMB, -LMB", [('press', M), ('drag', "TRACK"), ('press', L), ('drag', "DOLLY"),
                                             ('release', L), ('drag', "TRACK"), ('release', M), ('drag', "NONE")],
             through_camera=True)
add_sequence("camera: Alt+LMB, +MMB, -LMB", [('press', L), ('drag', "TUMBLE"), ('press', M), ('drag', "DOLLY"),
                                             ('release', L), ('drag', "TRACK"), ('release', M), ('drag', "NONE")],
             through_camera=True)
run()
