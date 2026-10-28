"""#185: switching back to Blender shows the user's own workspaces, not Blender's factory Layout.

Maya mode starts Blender in a new Maya scene, which replaces the user's own startup file; a switch to Blender then
appended Blender's factory "Layout" and the user's custom workspace was gone until a restart. Now the switch brings
back the workspace the file already has, else the workspaces of the user's own startup file (read only)."""

import os
import tempfile
from importlib import import_module

import bpy

import kit

sw = import_module(kit.MODULE + ".switch")
first_start = import_module(kit.MODULE + ".first_start")

_shown = []
_REAL = sw.user_startup_file          # before the tests replace it


def _record_targets():
    """In -b a Window.workspace assignment waits for an event loop: record what the switch chose instead."""
    real = sw.blender_target

    def wrapped(window):
        ws = real(window)
        _shown.append(ws.name if ws is not None else None)
        return ws
    sw.blender_target = wrapped


def _user_startup():
    """A user startup file whose window shows a custom workspace "My Workspace" (plus Blender's other tabs)."""
    win = bpy.context.window_manager.windows[0]
    win.workspace.name = "My Workspace"
    path = os.path.join(tempfile.mkdtemp(prefix="allset185_"), "startup.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    with bpy.data.libraries.load(path) as (src, _dst):
        names = list(src.workspaces)
    return path, names


def test_switch_to_blender_brings_back_the_users_startup_workspaces():
    path, names = _user_startup()
    assert "My Workspace" in names and len(names) > 1, names
    sw.user_startup_file = lambda: path
    _record_targets()
    first_start.new_maya_scene()            # Maya mode at start: the user's file is replaced by a new Maya scene
    win = bpy.context.window_manager.windows[0]
    assert sw.is_maya_workspace(win.workspace)
    assert "My Workspace" not in bpy.data.workspaces
    assert sw.START_WORKSPACE["name"] == "My Workspace"
    sw.set_mode(False)
    assert _shown[-1] == "My Workspace", _shown
    back = sorted(w.name for w in bpy.data.workspaces if sw.BLENDER_LAYOUT_KEY in w)
    assert "My Workspace" in back and len(back) == len(names), (back, names)
    assert not any(sw.is_maya_workspace(bpy.data.workspaces[n]) for n in back)
    # Maya and back again: nothing appended twice
    n_ws = len(bpy.data.workspaces)
    sw.set_mode(True)
    sw.set_mode(False)
    assert len(bpy.data.workspaces) == n_ws and _shown[-1] == "My Workspace", (_shown, len(bpy.data.workspaces))


def test_a_workspace_already_in_the_file_wins():
    """A Maya template workspace shown, the user's own workspace in the file: that one, nothing appended."""
    win = bpy.context.window_manager.windows[0]
    maya = next(w for w in bpy.data.workspaces if sw.is_maya_workspace(w))
    mine = next(w for w in bpy.data.workspaces if not sw.is_maya_workspace(w))
    maya[sw.BLENDER_PREV_KEY] = mine.name
    with bpy.context.temp_override(window=win):
        n_ws = len(bpy.data.workspaces)
        assert sw._users_workspace(win) is not None
    assert len(bpy.data.workspaces) == n_ws


def test_no_user_startup_file_keeps_blenders_layout():
    sw.user_startup_file = lambda: None
    bpy.ops.wm.read_homefile()
    first_start.new_maya_scene()
    sw.START_WORKSPACE["name"] = None
    if not sw.is_on():
        sw.set_mode(True)
    sw.set_mode(False)
    assert _shown[-1] == "Layout", _shown


def test_user_startup_file_follows_blenders_config_folder():
    old = os.environ.get("BLENDER_USER_CONFIG")
    d = tempfile.mkdtemp(prefix="allset185cfg_")
    try:
        os.environ["BLENDER_USER_CONFIG"] = d
        assert _REAL() is None                                   # no startup file saved: nothing to read
        open(os.path.join(d, "startup.blend"), "wb").close()
        assert _REAL() == os.path.join(d, "startup.blend"), _REAL()
    finally:
        if old is None:
            os.environ.pop("BLENDER_USER_CONFIG", None)
        else:
            os.environ["BLENDER_USER_CONFIG"] = old
