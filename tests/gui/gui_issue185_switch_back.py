"""#185 in a real UI: the user's own startup file has a custom workspace "My Workspace"; a new Maya scene replaces the
file (what starting in the Maya layout does), then the Maya | Blender switch shows "My Workspace" again — and again
after a second round trip. The startup file is written into the test sandbox's config folder only."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, setup, step, win, load_maya_layout  # noqa: E402

C = {}


def sw():
    return import_module(MODULE + ".switch")


@step
def s_setup():
    setup()
    path = os.path.join(os.environ["BLENDER_USER_CONFIG"], "startup.blend")
    tmp = os.path.normcase(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tmp")))
    assert os.path.normcase(os.path.abspath(path)).startswith(tmp), path      # never the user's real config
    win().workspace.name = "My Workspace"
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    C["path"] = path
    check(f"the user's startup file is found ({sw().user_startup_file()})", sw().user_startup_file() == path)


@step
def s_maya():
    load_maya_layout()


@step
def s_maya_shown():
    check(f"a new Maya scene in the Maya layout ({win().workspace.name})", sw().is_maya_workspace(win().workspace))
    check("the user's workspace went with the old file", "My Workspace" not in bpy.data.workspaces)


@step
def s_wait():
    pass


@step
def s_blender():
    sw().set_mode(False)


@step
def s_blender_shown():
    check(f"Blender mode shows the user's workspace ({win().workspace.name})", win().workspace.name == "My Workspace")
    C["n"] = len(bpy.data.workspaces)
    sw().set_mode(True)


@step
def s_maya_again():
    check(f"Maya mode shows the Maya layout again ({win().workspace.name})", sw().is_maya_workspace(win().workspace))
    sw().set_mode(False)


@step
def s_blender_again():
    check(f"and back to the user's workspace, nothing appended twice ({win().workspace.name}, "
          f"{C['n']} -> {len(bpy.data.workspaces)})",
          win().workspace.name == "My Workspace" and len(bpy.data.workspaces) == C["n"])
    os.remove(C["path"])


run()
