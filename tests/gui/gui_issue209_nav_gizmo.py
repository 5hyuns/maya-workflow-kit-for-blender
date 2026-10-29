"""Issue #209 in a real UI: add-on preference Viewport Navigation = Blender Navigation Gizmo shows Blender's
navigation gizmo instead of the Maya ViewCube in the Maya Workflow Kit layout, and the ViewCube comes back when the
preference goes back (screenshots)."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, step, setup, screenshot, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def area3d():
    return max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)


def prefs():
    return bpy.context.preferences.addons[MODULE].preferences


def vf():
    return import_module(MODULE + ".ui.view_furniture")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_viewcube():
    bpy.ops.allset.keymap_activate()
    space = area3d().spaces.active
    check("default: Maya ViewCube, Blender navigation gizmo off",
          prefs().view_navigation == 'VIEWCUBE' and not space.show_gizmo_navigate)
    redraw()


@step
def s_viewcube_shot():
    shot("gui_issue209_viewcube.png")


@step
def s_blender():
    prefs().view_navigation = 'BLENDER'
    space = area3d().spaces.active
    check("Blender Navigation Gizmo: the gizmo is on in the Maya view", space.show_gizmo_navigate)
    check("... it stays a Maya view (camera name / view axis)", vf().maya_view(space))
    tb = [a.spaces.active for a in win().screen.areas if a.type == 'VIEW_3D'
          and import_module(MODULE + ".ui.toolbox").is_toolbox(a.spaces.active)]
    check("... the Tool Box column is left alone", all(not sp.show_gizmo_navigate for sp in tb))
    redraw()


@step
def s_wait():
    redraw()


@step
def s_blender_shot():
    shot("gui_issue209_blender.png")


@step
def s_back():
    prefs().view_navigation = 'VIEWCUBE'
    check("back to the Maya ViewCube: navigation flag given back", not area3d().spaces.active.show_gizmo_navigate)
    redraw()


@step
def s_back_shot():
    shot("gui_issue209_back.png")


run()
