"""In a real UI (#544): the mouse wheel zooms the 3D View in Maya mode also when the user's preferences carry their own
edits of the 3D View keymap (preferences brought over from an older Blender): an edit of another item, an edited
wheel zoom item, and a switched-off wheel zoom item. Each case: the edit made in Blender mode, the wheel checked in
Blender mode, Maya mode turned on, the wheel checked again (it zooms: a Blender-mode edit stays off the Maya keys),
Maya mode off, the edit is there again; then it is undone."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, win  # noqa: E402

S = {}


def main_view():
    return max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)


def rv3d():
    return main_view().spaces.active.region_3d


def park():
    r = next(r for r in main_view().regions if r.type == 'WINDOW')
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


def user_km():
    return bpy.context.window_manager.keyconfigs.user.keymaps["3D View"]


def wheel_item(km):
    return next(k for k in km.keymap_items if k.idname == "view3d.zoom" and k.type == 'WHEELINMOUSE'
                and not (k.shift or k.ctrl or k.alt or k.oskey))


def edit_other(on):
    kmi = next(k for k in user_km().keymap_items if k.idname == "view3d.view_all")
    kmi.active = not on


def edit_wheel(on):
    wheel_item(user_km()).properties.delta = 2 if on else 1


def wheel_off(on):
    wheel_item(user_km()).active = not on


CASES = (("another 3D View item edited", edit_other), ("the wheel zoom item edited", edit_wheel),
         ("the wheel zoom item switched off by the user", wheel_off))


def mode(on):
    import_module(MODULE + ".switch").set_mode(on, layout=False)


def wheel_steps(tag, expect=True):
    def s_wheel():
        park()
        S[tag] = rv3d().view_distance
        for _ in range(3):
            ev('WHEELUPMOUSE', 'PRESS')

    def s_check():
        before, after = S[tag], rv3d().view_distance
        changed = abs(after - before) > 1e-4
        print("WHEEL", tag, before, after, flush=True)
        if expect is not None:
            check(f"{tag}: the wheel {'zooms' if expect else 'does not zoom'} ({before:.3f} -> {after:.3f})",
                  changed == expect)
    return s_wheel, s_check


@step
def s_setup():
    setup()
    mode(False)


for _name, _edit in CASES:
    _wheel_works = _edit is not wheel_off
    step(lambda e=_edit: e(True))
    step(lambda: None)
    for f in wheel_steps(f"{_name}, Blender mode", _wheel_works):
        step(f)
    step(lambda: mode(True))
    step(lambda: None)
    for f in wheel_steps(f"{_name}, Maya mode", True):
        step(f)
    step(lambda: mode(False))
    step(lambda: None)
    for f in wheel_steps(f"{_name}, Blender mode again", _wheel_works):
        step(f)
    step(lambda e=_edit: e(False))
    step(lambda: None)

run()
