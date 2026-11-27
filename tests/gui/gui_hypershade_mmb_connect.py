"""Hypershade Graph middle-mouse drag in a real UI: a material with a Checker and a Noise texture node left of its
Principled BSDF -> Hypershade -> Ctrl+MMB drag Checker onto the shader = Checker Color -> Base Color (no list);
MMB drag Noise onto the shader = the input list opens (screenshot), ESC = no link; Alt+MMB drag starting on a node =
the view pans (as in Maya), nothing links."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, run, setup, step, win, load_maya_layout, view3d  # noqa: E402

GUI_TIMEOUT = 180
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


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
        if hs.graph_area(w.screen) is not None and len(w.screen.areas) >= 6:
            return w
    return None


def graph():
    w = C["w"]
    area = mod(".ui.hypershade").graph_area(w.screen)
    return w, area, next(r for r in area.regions if r.type == 'WINDOW')


def node_point(node):
    """Window coordinates of a point inside ``node``'s header (below its top edge, right of its left edge)."""
    w, area, region = graph()
    left, bottom, right, top = mod(".ui.hypershade_hands").node_rect(node)
    x, y = region.view2d.view_to_region((left + right) / 2, top - 10, clip=False)
    return region.x + x, region.y + y


def ev(type, value, x, y, **kw):
    if value == 'PRESS':
        sim._down.add(type)
    elif value == 'RELEASE':
        sim._down.discard(type)
    C["w"].event_simulate(type=type, value=value, x=int(x), y=int(y), **kw)


def tree():
    return bpy.data.materials[C["mat"]].node_tree


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_scene():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    mat = mod(".operators.material").new_material()
    bpy.context.active_object.data.materials.append(mat)
    C["mat"] = mat.name
    t = mat.node_tree
    shader = next(n for n in t.nodes if n.type == 'BSDF_PRINCIPLED')
    for idname, dy, key in (("ShaderNodeTexChecker", 150, "checker"), ("ShaderNodeTexNoise", -150, "noise")):
        n = t.nodes.new(idname)
        n.location = (shader.location.x - 320, shader.location.y + dy)
        C[key] = n.name
    for n in t.nodes:
        n.select = False
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.hypershade()


@step
def s_ready():
    if again(s_ready, lambda: hs_window() is not None):
        return
    C["w"] = hs_window()
    check("Hypershade window open", C["w"] is not None)


@step
def s_frame():
    w, area, region = graph()
    with bpy.context.temp_override(window=w, area=area, region=region):
        bpy.ops.node.view_all()
    redraw()


@step
def s_wait():
    redraw()


@step
def s_ctrl_press():
    t = tree()
    C["dims"] = all(n.dimensions.x > 0 for n in t.nodes)
    check("graph nodes drawn", C["dims"])
    shader = next(n for n in t.nodes if n.type == 'BSDF_PRINCIPLED')
    C["src"] = node_point(t.nodes[C["checker"]])
    C["dst"] = node_point(shader)
    ev('MOUSEMOVE', 'NOTHING', *C["src"])
    ev('LEFT_CTRL', 'PRESS', *C["src"])
    ev('MIDDLEMOUSE', 'PRESS', *C["src"], ctrl=True)


@step
def s_ctrl_move():
    sx, sy = C["src"]
    dx, dy = C["dst"]
    for i in range(1, 6):
        ev('MOUSEMOVE', 'NOTHING', sx + (dx - sx) * i / 5, sy + (dy - sy) * i / 5, ctrl=True)


@step
def s_ctrl_release():
    ev('MIDDLEMOUSE', 'RELEASE', *C["dst"], ctrl=True)
    ev('LEFT_CTRL', 'RELEASE', *C["dst"])


@step
def s_ctrl_check():
    t = tree()
    shader = next(n for n in t.nodes if n.type == 'BSDF_PRINCIPLED')
    links = [(l.from_node.name, l.from_socket.name, l.to_socket.name) for l in shader.inputs["Base Color"].links]
    check(f"Ctrl+MMB drop: Checker Color -> Base Color ({links})", links == [(C["checker"], "Color", "Base Color")])
    C["n_links"] = len(t.links)
    C["src"] = node_point(t.nodes[C["noise"]])
    ev('MOUSEMOVE', 'NOTHING', *C["src"])
    ev('MIDDLEMOUSE', 'PRESS', *C["src"])


@step
def s_plain_move():
    sx, sy = C["src"]
    dx, dy = C["dst"]
    for i in range(1, 6):
        ev('MOUSEMOVE', 'NOTHING', sx + (dx - sx) * i / 5, sy + (dy - sy) * i / 5)


@step
def s_plain_release():
    ev('MIDDLEMOUSE', 'RELEASE', *C["dst"])


@step
def s_list_shot():
    redraw()


@step
def s_list_shot2():
    shot("gui_hypershade_mmb_list.png", C["w"])
    check("plain MMB drop links nothing before a choice", len(tree().links) == C["n_links"])
    ev('ESC', 'PRESS', *C["dst"])
    ev('ESC', 'RELEASE', *C["dst"])


@step
def s_pan_press():
    check("ESC closes the list: no new link", len(tree().links) == C["n_links"])
    w, area, region = graph()
    C["empty"] = node_point(tree().nodes[C["noise"]])        # Alt: a press on a node pans too
    C["view0"] = region.view2d.region_to_view(10, 10)
    ev('MOUSEMOVE', 'NOTHING', *C["empty"])
    ev('LEFT_ALT', 'PRESS', *C["empty"])
    ev('MIDDLEMOUSE', 'PRESS', *C["empty"], alt=True)


def _pan_move(i):
    def move():
        x, y = C["empty"]
        ev('MOUSEMOVE', 'NOTHING', x - 12 * i, y, alt=True)
    return move


for _i in range(1, 6):
    step(_pan_move(_i))


@step
def s_pan_release():
    x, y = C["empty"]
    ev('MIDDLEMOUSE', 'RELEASE', x - 60, y, alt=True)
    ev('LEFT_ALT', 'RELEASE', x - 60, y)


@step
def s_pan_wait():
    redraw()


@step
def s_pan_check():
    w, area, region = graph()
    v1 = region.view2d.region_to_view(10, 10)
    moved = abs(v1[0] - C["view0"][0]) > 1.0
    check(f"Alt+MMB on a node pans the view ({C['view0']} -> {v1})", moved)
    check("pan links nothing", len(tree().links) == C["n_links"])


@step
def s_close():
    w = C.get("w")
    if w is not None:
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


run()
