"""In-Blender part of tools/make_listing_media.py: the extensions.blender.org preview images (step 117).

One screenshot per workflow group of the listing (docs/distribution/listing.md), Blender's own window only
(no Maya capture, no logo): Navigate & Select, Hotbox & Marking Menus, Channel Box & Attribute Editor,
Menu Sets & Shelves, Maya concepts, Option windows. Runs in a GUI Blender on a clean sandbox with the
extension installed and enabled from the command line, with --enable-event-simulate (tests/gui/sim.py);
each screenshot is taken one tick after the UI change (``screen.screenshot`` shows the previous frame).
The Maya theme ("Studio Grey (Maya-inspired)") is applied the way Make Blender feel like Maya does.
"""

import os
import sys
from importlib import import_module
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests" / "gui"))
import sim  # noqa: E402
from sim import MODULE, check, ev, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_SHOTS", str(ROOT / "docs" / "distribution" / "media"))
C = {}


def shot(name):
    path = os.path.join(SHOTS, name)
    sim.screenshot(path)
    hide_logo(path)


def hide_logo(path):
    """Paint the top bar's Blender menu icon over with the bar colour: preview images must not show the Blender
    logo (extensions.blender.org terms of service 2.2). The icon sits in the top-left corner of the window."""
    import numpy as np
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)                       # rows bottom-up
    size = round(30 * bpy.context.preferences.system.ui_scale)   # effective scale; "File" starts at 32 px x scale
    px[h - size:, :size] = px[h - 2, size]          # a top bar pixel right of the icon, left of "File"
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def v3d_override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region)


def mid():
    _area, region = view3d()
    return region.x + region.width // 2, region.y + region.height // 2


def esc():
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')


def call_menu(maya_name, x_frac=0.35, top=None):
    """Open a Maya menu from mid-window (a popup opened near the window top is missing from screenshots).
    A menu taller than the room below the mouse is moved up to fit: ``top`` = the mouse's distance from the window
    top in px, so it rests on a chosen row of such a menu."""
    _area, region = view3d()
    y = win().height - top if top else region.y + int(region.height * 0.8)
    ev('MOUSEMOVE', 'NOTHING', x=region.x + int(region.width * x_frac), y=y)
    name = import_module(MODULE + ".ui.menu_sets").menu_idname(maya_name)
    with bpy.context.temp_override(window=win()):
        bpy.ops.wm.call_menu(name=name)


def prefs():
    return bpy.context.preferences.addons[MODULE].preferences


def wait():
    redraw()


@step
def s_first_start():
    setup()   # closes the splash, opts in to Maya mode
    check("install the Maya layout template", bpy.ops.allset.layout_install() == {'FINISHED'})
    bpy.ops.wm.read_homefile(app_template="Allset")


@step
def s_scene():
    kc = bpy.context.window_manager.keyconfigs.active
    check("Maya keymap active in the Allset layout", kc is not None and kc.name == "Maya-style")
    import_module(MODULE + ".theme").apply()   # what Make Blender feel like Maya does (welcome.opt_in)
    # Maya 2022 factory background (flat #5c5c5c) in every view, whatever an earlier Alt+B left (step 120)
    import_module(MODULE + ".operators.key_batch3").reset_background()
    bpy.context.preferences.view.show_tooltips = False   # sandbox prefs: no tooltip over the pictures
    prefs().in_view_messages = False                     # no "group1 grouped." in every shot
    k = import_module(MODULE + ".operators.units").maya_unit()   # Maya lengths ()
    with v3d_override():
        bpy.ops.allset.create(kind='SPHERE')
        bpy.context.active_object.location = (4 * k, 0, k)
        bpy.ops.allset.create(kind='CYLINDER')
        bpy.context.active_object.location = (-4 * k, 0, k)
        bpy.data.objects["pSphere1"].select_set(True)
        bpy.ops.allset.group()
        bpy.ops.allset.create(kind='CUBE')
        cube = bpy.context.active_object
        cube.scale = (2, 2, 2)
        cube.location = (0, 0, k)
        cube.keyframe_insert("location")     # keyed channels draw red in the Channel Box
        bpy.ops.allset.shelf_material(kind='LAMBERT')
        bpy.ops.view3d.view_all(center=False)
    check("Maya names (pCube1, pSphere1, pCylinder1, group1)",
          all(n in bpy.data.objects for n in ("pCube1", "pSphere1", "pCylinder1", "group1")))
    ev('MOUSEMOVE', 'NOTHING', x=mid()[0], y=mid()[1])
    redraw()


# --- 1 Navigate & Select: component mode, Maya selection colours, Move manipulator --------------------

@step
def s_components():
    cube = bpy.data.objects["pCube1"]
    with v3d_override():
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bm = bmesh.from_edit_mesh(cube.data)
        for f in bm.faces:
            f.select_set(f.normal.z > 0.5 or f.normal.y < -0.5)
        bmesh.update_edit_mesh(cube.data)
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
        bpy.ops.view3d.view_selected()
        bpy.ops.view3d.zoom(delta=-3)
    _area, region = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 5, y=region.y + region.height // 5)
    redraw()


step(wait)


@step
def s_components_shot():
    shot("1_navigate_select.png")
    with v3d_override():
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        bpy.ops.view3d.view_all(center=False)
    redraw()


# --- 2 Hotbox & Marking Menus -------------------------------------------------------------------------------

@step
def s_hotbox_press():
    ev('MOUSEMOVE', 'NOTHING', x=mid()[0], y=mid()[1])
    ev('SPACE', 'PRESS')


step(wait)


@step
def s_hotbox_shot():
    shot("2_hotbox_marking_menus.png")
    ev('SPACE', 'RELEASE')


# --- 3 Channel Box & Attribute Editor: the tab stack split, AE above the Channel Box ------------------------

@step
def s_cb_ae():
    md = import_module(MODULE + ".ui.maya_dock")
    stack = sim.dock_area('CHANNEL_BOX')
    before = set(win().screen.areas[:])
    with bpy.context.temp_override(window=win(), screen=win().screen, area=stack):
        bpy.ops.screen.area_split(direction='HORIZONTAL', factor=0.55)
    new = [a for a in win().screen.areas if a not in before]
    check("split the tab stack for the Attribute Editor", len(new) == 1)
    C["ae"] = new[0] if new else None
    if C["ae"]:
        md.set_role(C["ae"], 'ATTRIBUTE_EDITOR', win())
    with v3d_override():
        bpy.ops.allset.ae_tab(key="T")
    redraw()


step(wait)
step(wait)


@step
def s_cb_ae_shot():
    shot("3_channel_box_attribute_editor.png")
    md = import_module(MODULE + ".ui.maya_dock")
    md.close_area(bpy.context, win(), C.get("ae"))
    redraw()


# --- 4 Menu Sets & Shelves: Rigging menu set + Rigging shelf, Skeleton menu ---------------------------------

@step
def s_rigging():
    prefs().menu_set = 'riggingMenuSet'
    bpy.ops.allset.shelf_select(shelf="Rigging")
    redraw()


@step
def s_rig_menu():
    call_menu("mainRigSkeletonsMenu", x_frac=0.2)


step(wait)


@step
def s_rig_shot():
    shot("4_menu_sets_shelves.png")
    esc()
    prefs().menu_set = 'modelingMenuSet'
    bpy.ops.allset.shelf_select(shelf="Polygons")


# --- 5 Maya concepts: group1 / shapes in the Outliner, Freeze (pivot kept), Modify menu ---------------------

@step
def s_concepts():
    wm = bpy.context.window_manager
    wm.allset_outliner_shapes = True
    for name in ("group1", "pCube1"):
        bpy.data.objects[name].allset_expanded = True
    outl = [a for a in win().screen.areas if a.type == 'OUTLINER']
    if outl:
        with bpy.context.temp_override(window=win(), area=outl[0],
                                       region=next(r for r in outl[0].regions if r.type == 'WINDOW')):
            bpy.ops.outliner.expanded_toggle()
    with v3d_override():
        bpy.ops.object.select_all(action='DESELECT')
        sphere = bpy.data.objects["pSphere1"]
        sphere.select_set(True)
        bpy.context.view_layer.objects.active = sphere
        bpy.ops.allset.freeze_transform()
    check("Freeze Transformations: channels 0 / 0 / 1, pivot kept",
          tuple(sphere.location) == (0, 0, 0) and sphere.delta_location.length > 0)
    redraw()


@step
def s_concepts_menu():
    call_menu("mainModifyMenu", x_frac=0.3, top=189)   # rests on Freeze Transformations


step(wait)


@step
def s_concepts_shot():
    shot("5_maya_concepts.png")
    esc()


# --- 6 Option windows: Duplicate Special Options with Maya's factory values -------------------------------

@step
def s_option_window():
    _area, region = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=mid()[0], y=region.y + int(region.height * 0.75))
    with bpy.context.temp_override(window=win()):
        res = bpy.ops.allset.opt_duplicate_special('INVOKE_DEFAULT')
    check("Duplicate Special Options opens", res == {'RUNNING_MODAL'})


step(wait)


@step
def s_option_shot():
    shot("6_option_windows.png")
    esc()


run(interval=0.6, first=3.0)
