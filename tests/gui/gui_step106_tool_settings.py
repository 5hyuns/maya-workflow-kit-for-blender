"""In a real UI: the Maya Workflow Kit layout, pCube1 with its top face extruded, Move tool. Windows > General Editors >
Tool Settings opens Maya's floating Tool Settings window with Maya's Move Settings, the item again brings it to the
front, the Status Line button closes it (the old popup stayed open) and opens it again; Rotate / Scale show their
sections;
the Attribute Editor shows the history / material tabs, menu bar, buttons and Notes (screenshots beside audit-7
pairs c02 / c03)."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, setup, step, win, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 240
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    if SHOTS:
        # the floating Tool Settings window while it is open, else the main window
        with bpy.context.temp_override(window=mod(".ui.tool_dock").find_any()[0] or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def v3d():
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def in_v3d(fn, *a, **kw):
    area, region = v3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return fn(*a, **kw)


def menu(path):
    return in_v3d(bpy.ops.allset.menu_item, item=path)


def dock():
    """The Tool Settings area in any window (floating or docked), or None."""
    return mod(".ui.tool_dock").find_any()[1]


def ts_window():
    return mod(".ui.tool_dock").find_any()[0]


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


for _i in range(8):        # the layout is fitted to the UI scale in the first seconds after a load
    step(redraw)


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    in_v3d(bpy.ops.allset.create, kind='CUBE')
    ob = bpy.context.active_object
    ob.data.materials.append(mod(".operators.material").new_material())
    C["ob"] = ob.name
    in_v3d(bpy.ops.object.mode_set, mode='EDIT')
    import bmesh
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(False)
    for f in bm.faces:   # deselect first: a later face's select_set(False) would drop shared verts
        if f.normal.z > 0.9:
            f.select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    in_v3d(bpy.ops.allset.extrude, local_translate_z=0.5)


step(redraw)          # the mode change's tool carry runs from a timer (operators/tool_keys)


@step
def s_move_tool():
    # a tick after the mode change: Edit Mode first takes Object Mode's tool (Maya's one tool, operators/tool_keys)
    in_v3d(bpy.ops.wm.tool_set_by_id, name="builtin.move")
    C["areas"] = len(win().screen.areas)
    C["main_w"] = v3d()[0].width
    menu("Windows/General Editors/Tool Settings")


step(redraw)          # the window opens over a few timer ticks (its place is carved out first)


@step
def s_opened():
    redraw()


@step
def s_opened_check():
    d, w = dock(), ts_window()
    check("toggle 1: the Tool Settings window is open", d is not None)
    if d is None:
        return
    sp = d.spaces.active
    nav = next((r for r in d.regions if r.type == 'NAVIGATION_BAR'), None)
    check(f"a floating window of its own ({len(w.screen.areas)} area), the layout unchanged "
          f"({len(win().screen.areas)} areas vs {C['areas']}, viewport {v3d()[0].width} px vs {C['main_w']})",
          w != win() and len(w.screen.areas) == 1 and len(win().screen.areas) == C["areas"]
          and v3d()[0].width >= C["main_w"] - 4)
    check(f"Properties Tool tab, no header / tab column ({sp.context}, header {sp.show_region_header})",
          sp.context == 'TOOL' and not sp.show_region_header and (nav is None or nav.width <= 1))
    check(f"window width {w.width} px (280 x UI scale, narrower than the viewport {C['main_w']})",
          150 <= w.width <= 0.5 * C["main_w"])
    ts = mod(".ui.tool_settings")
    with bpy.context.temp_override(window=w, area=d, region=next(r for r in d.regions if r.type == 'WINDOW'),
                                   space_data=sp):
        kind = ts.tool_kind(bpy.context)
        hidden = ts.hides_blender_panels(bpy.context)
    check(f"Move tool: Maya sections ({kind}), Blender's tool panels hidden there", kind == 'TRANSLATE' and hidden)
    shot("gui_step106_ts_move.png")


@step
def s_menu_again():
    C["ts"] = ts_window().as_pointer()
    menu("Windows/General Editors/Tool Settings")


@step
def s_menu_again_check():
    redraw()
    w = ts_window()
    check("the menu item again only shows it (Maya's Tool Settings item): it comes to the front in a new window",
          dock() is not None and w is not None and w.as_pointer() != C["ts"]
          and len(bpy.context.window_manager.windows) == 2)
    in_v3d(bpy.ops.allset.editor_toggle, editor='TOOL_SETTINGS')     # the Status Line button


@step
def s_toggle2_check():
    redraw()
    check(f"toggle 2 (Status Line button): the window is closed, the layout as it was ({len(win().screen.areas)} areas vs {C['areas']}, "
          f"viewport {v3d()[0].width} px vs {C['main_w']}, {len(bpy.context.window_manager.windows)} windows)",
          dock() is None and len(win().screen.areas) == C["areas"] and v3d()[0].width >= C["main_w"] - 4
          and len(bpy.context.window_manager.windows) == 1)
    # (wider is fine: the Tool Box column may have been fitted to one toolbar column meanwhile, toolbox_column.settle)
    in_v3d(bpy.ops.allset.editor_toggle, editor='TOOL_SETTINGS')     # the Status Line button


step(redraw)


@step
def s_toggle3_check():
    redraw()
    check("toggle 3 (Status Line button): open again", dock() is not None)
    # an option box of a tool (toolPropertyWindow) only shows it
    in_v3d(bpy.ops.allset.editor_toggle, editor='TOOL_SETTINGS', show=True)
    check("show-only (tool option box) keeps it open", dock() is not None)
    in_v3d(bpy.ops.wm.tool_set_by_id, name="builtin.rotate")
    redraw()


@step
def s_rotate_shot():
    shot("gui_step106_ts_rotate.png")
    in_v3d(bpy.ops.wm.tool_set_by_id, name="builtin.select_box")
    redraw()


@step
def s_select_shot():
    shot("gui_step106_ts_select.png")
    check("Select tool: Tool Settings still open (Blender's tool panels under the head row)", dock() is not None)
    in_v3d(bpy.ops.wm.tool_set_by_id, name="builtin.move")
    in_v3d(bpy.ops.object.mode_set, mode='OBJECT')
    in_v3d(bpy.ops.wm.tool_set_by_id, name="builtin.move")
    redraw()


@step
def s_object_move_shot():
    shot("gui_step106_ts_move_object.png")      # pair with audit-7 c02 (object mode Move tool)
    in_v3d(bpy.ops.allset.editor_toggle, editor='TOOL_SETTINGS')
    in_v3d(bpy.ops.allset.dock_show, dock='ATTRIBUTE_EDITOR')
    ae = mod(".ui.attribute_editor")
    ae.set_tab(bpy.context, "S")
    redraw()


@step
def s_ae_wait():
    redraw()


@step
def s_ae_shot():
    check("Tool Settings closed before the AE shot", dock() is None)
    shot("gui_step106_ae.png")        # pair with audit-7 c03
    ob = bpy.data.objects[C["ob"]]
    ae = mod(".ui.attribute_editor")
    tabs = [t[1] for t in ae.tabs(ob)]
    mat = ob.active_material.name
    check(f"AE tabs {tabs}: transform, shape, {mat}SG, {mat}",
          tabs[:2] == [ob.name, ob.data.name] and f"{mat}SG" in tabs and mat in tabs)
    in_v3d(bpy.ops.object.mode_set, mode='EDIT')
    redraw()


@step
def s_ae_edit_wait():
    redraw()


@step
def s_ae_edit_shot():
    ob = bpy.data.objects[C["ob"]]
    ae = mod(".ui.attribute_editor")
    tabs = [t[1] for t in ae.tabs(ob)]
    check(f"edit mode: the kit extrusion is a polyExtrudeFace1 tab ({tabs})", "polyExtrudeFace1" in tabs)
    ae.set_tab(bpy.context, "H")
    redraw()


@step
def s_ae_history_shot():
    shot("gui_step106_ae_history.png")
    in_v3d(bpy.ops.object.mode_set, mode='OBJECT')
    in_v3d(bpy.ops.allset.dock_show, dock='CHANNEL_BOX')
    check("session ran", True)


run()
