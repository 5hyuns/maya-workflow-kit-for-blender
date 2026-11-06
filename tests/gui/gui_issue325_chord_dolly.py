"""#325: with Alt held, pressing the middle button during a left-button tumble (or the left button during a
middle-button track) dollies the view like Maya; letting go of a button ends it. Plain Alt+LMB tumble and Alt+MMB
track still work, and Maya mode off leaves the modal keys as they were."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

C = {}


def main_view():
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D']
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def rv3d():
    return main_view()[1].data


def modal_names():
    return [op.bl_idname for op in win().modal_operators]


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    rv = rv3d()
    rv.view_perspective = 'PERSP'
    _area, region = main_view()
    C["xy"] = (region.x + int(region.width * 0.3), region.y + int(region.height * 0.6))


def add_case(label, first, second, chord=True):
    names = {'LEFTMOUSE': "LMB", 'MIDDLEMOUSE': "MMB"}

    def prepare():
        rv = rv3d()
        rv.view_distance = 15.0
        C["d0"], C["rot0"], C["loc0"] = rv.view_distance, rv.view_rotation.copy(), rv.view_location.copy()
        x, y = C["xy"]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFT_ALT', 'PRESS', alt=True, x=x, y=y)

    def press1():
        x, y = C["xy"]
        ev(first, 'PRESS', alt=True, x=x, y=y)

    def move1():
        x, y = C["xy"]
        ev('MOUSEMOVE', 'NOTHING', alt=True, x=x + 30, y=y + 10)

    def press2():
        if not chord:
            return
        rv = rv3d()
        C["d1"], C["rot1"], C["loc1"] = rv.view_distance, rv.view_rotation.copy(), rv.view_location.copy()
        x, y = C["xy"]
        ev(second, 'PRESS', alt=True, x=x + 30, y=y + 10)

    def move2():
        x, y = C["xy"]
        ev('MOUSEMOVE', 'NOTHING', alt=True, x=x + 130, y=y + 10)

    def move3():
        x, y = C["xy"]
        ev('MOUSEMOVE', 'NOTHING', alt=True, x=x + 190, y=y + 10)

    def during():
        C["modals"] = modal_names()

    def release():
        x, y = C["xy"]
        if chord:
            ev(second, 'RELEASE', alt=True, x=x + 190, y=y + 10)
        ev(first, 'RELEASE', alt=True, x=x + 190, y=y + 10)
        ev('LEFT_ALT', 'RELEASE', x=x + 190, y=y + 10)

    def verify():
        rv = rv3d()
        tag = f"Alt+{names[first]}" + (f"+{names[second]}" if chord else "")
        if chord:
            turned = C["rot1"].rotation_difference(rv.view_rotation).angle
            moved = (C["loc1"] - rv.view_location).length
            check(f"{tag}: dollies in ({C['d1']:.2f} -> {rv.view_distance:.2f}), modals {C['modals']}",
                  rv.view_distance < C["d1"] * 0.8 and "ALLSET_OT_dolly" in C["modals"])
            check(f"{tag}: view no longer turns / slides after the second button "
                  f"(turned {turned:.4f}, slid {moved:.4f})", turned < 1e-4 and moved < 1e-4)
        elif first == 'LEFTMOUSE':
            diff = C["rot0"].rotation_difference(rv.view_rotation).angle
            check(f"{label}: tumbles ({diff:.3f} rad), distance kept", diff > 0.05 and abs(rv.view_distance - C["d0"]) < 1e-4)
        else:
            moved = (C["loc0"] - rv.view_location).length
            check(f"{label}: tracks ({moved:.3f}), distance kept", moved > 0.05 and abs(rv.view_distance - C["d0"]) < 1e-4)
        check(f"{label}: nothing left running ({modal_names()})",
              not any(n in {"VIEW3D_OT_rotate", "VIEW3D_OT_move", "ALLSET_OT_dolly", "ALLSET_OT_nav_chord"}
                      for n in modal_names()))

    for fn in (prepare, press1, move1, press2, move2, move3, during, release, verify):
        step(fn)


add_case("Alt+LMB tumble", 'LEFTMOUSE', None, chord=False)
add_case("Alt+MMB track", 'MIDDLEMOUSE', None, chord=False)
add_case("Alt+LMB then MMB", 'LEFTMOUSE', 'MIDDLEMOUSE')
add_case("Alt+MMB then LMB", 'MIDDLEMOUSE', 'LEFTMOUSE')
run()
