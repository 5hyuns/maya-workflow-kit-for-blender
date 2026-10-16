"""Helpers for GUI event-simulation tests (run inside Blender by tests/gui/run.py).

Blender must run with ``--enable-event-simulate``: real input is ignored and
``Window.event_simulate`` feeds events. Gotchas found in step 3:
- key events carry a position (default 0,0 = status bar), so ``ev`` reuses
  the last mouse position;
- the factory-startup splash popup eats events until ESC;
- simulated keys never reach the OS, so the add-on's ``keystate.is_down``
  (missed-RELEASE fallback) is replaced by the simulated key state.
"""

import json
import os
import sys
from importlib import import_module

import addon_utils
import bpy

MODULE = os.environ.get("MAYA_KIT_MODULE", "bl_ext.user_default.maya_kit")
RESULT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None

_pos = [0, 0]
_down = set()
_steps = []
results = []


def win():
    return bpy.context.window_manager.windows[0]


def view3d():
    area = next(a for a in win().screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return area, region


def ev(type, value, **kw):
    if value == 'PRESS':
        _down.add(type)
    elif value == 'RELEASE':
        _down.discard(type)
    if "x" in kw:
        _pos[:] = [kw["x"], kw["y"]]
    else:
        kw.update(x=_pos[0], y=_pos[1])
    win().event_simulate(type=type, value=value, **kw)


def tap(type):
    ev(type, 'PRESS')
    ev(type, 'RELEASE')


def check(name, cond):
    results.append({"name": name, "ok": bool(cond)})
    print("GUI", "PASS" if cond else "FAIL", name)


def screenshot(path):
    with bpy.context.temp_override(window=win()):
        bpy.ops.screen.screenshot(filepath=path)


def step(fn):
    _steps.append(fn)
    return fn


def setup():
    """Close the splash, enable the add-on, fake key state, park the mouse mid-viewport."""
    tap('ESC')
    addon_utils.enable(MODULE, default_set=True)
    import_module(MODULE + ".operators.keystate").is_down = lambda t: t in _down
    _area, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    return r.x + r.width // 2, r.y + r.height // 2


def _finish():
    if RESULT:
        with open(RESULT, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=1)
    bpy.ops.wm.quit_blender()


def run(interval=0.4, first=2.0):
    """Run registered steps one per timer tick, then write results and quit."""
    def tick():
        if _steps:
            try:
                _steps.pop(0)()
            except Exception as ex:  # report and stop
                import traceback
                traceback.print_exc()
                check(f"step raised {ex!r}", False)
                _steps.clear()
            return interval
        _finish()
        return None
    # persistent: survive wm.read_homefile (loading the app template)
    bpy.app.timers.register(tick, first_interval=first, persistent=True)
