"""Hypershade Browser swatch RMB in a real UI: pCube1 selected + a new material (no user) -> Hypershade -> RMB on
the material's swatch -> the button menu starts with Maya's swatch items for that material -> its Assign Material
To Viewport Selection assigns it to pCube1."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, run, setup, step, win, load_maya_layout, view3d  # noqa: E402

GUI_TIMEOUT = 180
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {"seen": []}


def mod(name):
    return import_module(MODULE + name)


def shot(name, window=None):
    if SHOTS:
        with bpy.context.temp_override(window=window or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def again(fn, cond, limit=60):
    C.setdefault(fn.__name__, 0)
    if not cond() and C[fn.__name__] < limit:
        C[fn.__name__] += 1
        sim._steps.insert(0, fn)
        redraw()
        return True
    return False


def hs_window():
    hs = mod(".ui.hypershade")
    for w in bpy.context.window_manager.windows[1:]:
        panes = {hs.pane(a): a for a in w.screen.areas if hs.pane(a)}
        if 'BROWSER' in panes and hs.graph_area(w.screen) is not None:
            return w, panes['BROWSER']
    return None, None


def browser():
    w, area = hs_window()
    return w, area, next(r for r in area.regions if r.type == 'WINDOW')


def command_under_mouse():
    w, area, region = browser()
    wm = bpy.context.window_manager
    wm.clipboard = ""
    try:
        with bpy.context.temp_override(window=w, screen=w.screen, area=area, region=region):
            bpy.ops.ui.copy_data_path_button(full_path=True)
    except RuntimeError:
        pass
    return wm.clipboard


def spy(_self, context):
    """Records the material the real button menu's context names (what the kit's items act on)."""
    mat = mod(".ui.hypershade_swatch").swatch_material(context)
    C["seen"].append(mat.name if mat is not None else None)


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_scene():
    m = mod(".operators.material")
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    cube = bpy.context.active_object
    C["cube"] = cube.name
    mat = m.new_material()
    mat.use_fake_user = True
    C["mat"] = mat.name
    bpy.context.window_manager.allset_hs_swatch = 'SMALL'
    bpy.types.UI_MT_button_context_menu.append(spy)
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.hypershade()


@step
def s_ready():
    if again(s_ready, lambda: hs_window()[0] is not None and len(hs_window()[0].screen.areas) >= 6):
        return
    w, _area = hs_window()
    check("Hypershade window open", w is not None)
    C["w"] = w
    redraw()


@step
def s_wait():
    redraw()


def find_swatch(name, key):
    """Sweep down the Browser grid column of ``name`` for its name button (one probe per tick)."""
    state = {}

    def look():
        w, area, region = browser()
        if not state:
            wm = bpy.context.window_manager
            s = bpy.context.preferences.system.ui_scale
            size = next(z for z in mod(".ui.hypershade").SWATCHES if z[0] == wm.allset_hs_swatch)
            cell = size[3] * 20 * s + 12
            names = sorted((m.name for m in bpy.data.materials), key=str.lower)
            cols = min(len(names), max(1, min(24, int(region.width // cell))))
            index = names.index(name)
            state["x"] = region.x + int(region.width / cols * (index % cols + 0.5))
            state["y"] = region.y + region.height - 4
            C[key] = None
        else:
            got = command_under_mouse()
            if got.endswith(f'materials["{name}"].allset_hs_pick'):
                state.setdefault("first", state["y"])
                state["last"] = state["y"]
            elif "first" in state:
                C[key] = (state["x"], (state["first"] + state["last"]) // 2)
                return
            state["y"] -= 6
            if state["y"] < region.y + 2:
                if "first" in state:
                    C[key] = (state["x"], (state["first"] + state["last"]) // 2)
                return
        w.event_simulate(type='MOUSEMOVE', value='NOTHING', x=state["x"], y=state["y"])
        sim._steps.insert(0, look)
    return look


@step
def s_find():
    sim._steps.insert(0, find_swatch(C["mat"], "btn"))


@step
def s_rmb():
    btn = C.get("btn")
    check(f"swatch name button found in the Browser ({btn})", btn is not None)
    if btn is None:
        sim._steps.clear()
        return
    w = C["w"]
    w.event_simulate(type='MOUSEMOVE', value='NOTHING', x=btn[0], y=btn[1])
    w.event_simulate(type='RIGHTMOUSE', value='PRESS', x=btn[0], y=btn[1])
    w.event_simulate(type='RIGHTMOUSE', value='RELEASE', x=btn[0], y=btn[1])


@step
def s_menu_open():
    if again(s_menu_open, lambda: bool(C["seen"]), limit=20):
        return
    shot("gui_hypershade_swatch_menu.png", C["w"])
    check(f"RMB on the swatch opens the button menu for {C['mat']} ({C['seen']})", C["mat"] in C["seen"])
    cube = bpy.data.objects[C["cube"]]
    check("pCube1 does not use the material yet", cube.active_material is None
          or cube.active_material.name != C["mat"])
    btn = C["btn"]
    C["w"].event_simulate(type='ESC', value='PRESS', x=btn[0], y=btn[1])
    C["w"].event_simulate(type='ESC', value='RELEASE', x=btn[0], y=btn[1])


@step
def s_assign():
    """The menu's Assign item = this call (the button menu's rows are drawn after Blender's own, so their place
    depends on the Blender version: the item runs here instead of by keyboard)."""
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.hs_swatch_cmd(material=C["mat"], action='ASSIGN')
    cube = bpy.data.objects[C["cube"]]
    check(f"Assign Material To Viewport Selection: pCube1 uses {C['mat']} "
          f"({cube.active_material.name if cube.active_material else None})",
          cube.active_material is not None and cube.active_material.name == C["mat"])


@step
def s_rename():
    w, area, region = browser()
    with bpy.context.temp_override(window=w, screen=w.screen, area=area, region=region):
        got = bpy.ops.allset.hs_swatch_cmd('INVOKE_DEFAULT', material=C["mat"], action='RENAME')
    check(f"Rename opens the name field ({got})", got in ({'FINISHED'}, {'INTERFACE'}))
    C["renamed"] = True


@step
def s_rename_shot():
    shot("gui_hypershade_swatch_rename.png", C["w"])
    btn = C["btn"]
    C["w"].event_simulate(type='ESC', value='PRESS', x=btn[0], y=btn[1])
    C["w"].event_simulate(type='ESC', value='RELEASE', x=btn[0], y=btn[1])


@step
def s_node_pick():
    """A texture node picked in the Graph: the Property Editor draws that node (Image Texture with its image)."""
    mat = bpy.data.materials[C["mat"]]
    bpy.ops.allset.ae_map_connect(material=mat.name, socket="Base Color", kind='FILE')
    tree = mat.node_tree
    tex = next(n for n in tree.nodes if n.type == 'TEX_IMAGE')
    for n in tree.nodes:
        n.select = n == tex
    tree.nodes.active = tex
    check("Property Editor node = the picked texture",
          mod(".ui.hypershade_panes").shown_node(mat) == tex)
    redraw()


@step
def s_node_shot():
    shot("gui_hypershade_property_node.png", C["w"])


@step
def s_close():
    bpy.types.UI_MT_button_context_menu.remove(spy)
    w = C.get("w")
    if w is not None:
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


run()
