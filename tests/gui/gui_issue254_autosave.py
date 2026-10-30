"""Issue #254: the project autosave timer writes a copy into <project>/autosave in a GUI session; the open scene keeps
its (empty) path and its unsaved state."""

import os
import sys
import tempfile
import time
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, step, setup, view3d, win  # noqa: E402

MODULE = "bl_ext.user_default.allset"
_S = {}


def _mods():
    return (import_module(MODULE + ".operators.autosave"), import_module(MODULE + ".operators.project"),
            import_module(MODULE + ".preferences"))


@step
def s_setup():
    setup()


@step
def s_edit():
    autosave, project, preferences = _mods()
    root = os.path.join(tempfile.mkdtemp(prefix="as254g_"), "proj")
    project.create_project(root)
    _S["root"] = root
    p = preferences.get()
    p.project_root = root
    p.autosave_enable = True
    p.autosave_interval = 1.0
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.mesh.primitive_cube_add()
        bpy.ops.ed.undo_push(message="cube")


@step
def s_wait():
    autosave = _mods()[0]
    check(f"the scene is modified (dirty {bpy.data.is_dirty}, changed {autosave._state['changed']})",
          bpy.data.is_dirty and autosave._state["changed"])
    autosave._state["last"] = time.monotonic() - 120.0     # the interval has passed


@step
def s_tick():
    autosave = _mods()[0]
    mods = [op.bl_idname for w in bpy.context.window_manager.windows for op in w.modal_operators]
    check(f"the kit's click watchers don't block it ({mods})", not autosave.busy())
    autosave._timer()          # the timer callback itself, from a timer like Blender runs it


@step
def s_check():
    autosave, _project, preferences = _mods()
    folder = os.path.join(_S["root"], "autosave")
    names = sorted(os.listdir(folder))
    check(f"one copy in the project's autosave folder ({names})", names == ["untitled.0001.blend"])
    check(f"the open scene is still untitled ({bpy.data.filepath!r})", bpy.data.filepath == "")
    check("the open scene still has unsaved changes", bpy.data.is_dirty)
    p = preferences.get()
    for attr in ("autosave_enable", "autosave_interval", "project_root"):
        p.property_unset(attr)


run()
