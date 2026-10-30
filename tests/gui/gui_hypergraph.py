"""Hypergraph: Hierarchy in a real UI: group1 > pCube1, pSphere1 in a coloured display layer -> Windows > General
Editors > Hypergraph: Hierarchy opens a kit window with one marked Properties area -> a click on the pCube1 node
selects pCube1 (lead) -> MMB drag pCube1 onto pSphere1 parents it there (world position kept) -> MMB drag onto empty
space unparents it -> a marquee over every node selects them all -> a double-click on group1 collapses it; shots with
``--shots``."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, win  # noqa: E402

GUI_TIMEOUT = 220
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name, window=None):
    if SHOTS:
        with bpy.context.temp_override(window=window or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def v3d():
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def again(fn, cond, limit=40):
    C.setdefault(fn.__name__, 0)
    if not cond() and C[fn.__name__] < limit:
        C[fn.__name__] += 1
        import sim
        sim._steps.insert(0, fn)
        redraw()
        return True
    return False


def hg_area():
    mw = mod(".ui.marked_window")
    w = mw.find_window(bpy.context, "HYPERGRAPH")
    if w is None:
        return None, None, None
    area = next(a for a in w.screen.areas if mw.kind_of(a) == "HYPERGRAPH")
    return w, area, next(r for r in area.regions if r.type == 'WINDOW')


def node_point(name):
    """Window coordinates of the centre of ``name``'s node box."""
    hg = mod(".ui.hypergraph")
    _w, area, region = hg_area()
    view = hg.VIEWS[area.as_pointer()]
    cents, _n, _b = hg.centres(bpy.context.scene)
    rx, ry = view.to_region(*cents[bpy.data.objects[name].session_uid])
    return int(region.x + rx), int(region.y + ry)


def hev(type, value, x, y, **kw):
    w = C["w"]
    w.event_simulate(type=type, value=value, x=int(x), y=int(y), **kw)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    area, region = v3d()
    sc = bpy.context.scene
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
        cube = bpy.context.active_object
        bpy.ops.allset.create(kind='SPHERE')
        sphere = bpy.context.active_object
    group = bpy.data.objects.new("group1", None)
    sc.collection.objects.link(group)
    cube.parent = group
    sphere.location = (5.0, 0.0, 0.0)
    cube.location = (1.0, 2.0, 0.0)
    le = mod(".ui.layer_editor")
    layer = le.new_layer(sc, [sphere])
    layer.color_tag = 'COLOR_01'
    bpy.context.view_layer.update()
    C.update(cube=cube.name, sphere=sphere.name, group=group.name, world=tuple(cube.matrix_world.translation))
    for o in sc.objects:
        o.select_set(False)
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["open"] = bpy.ops.allset.menu_item(item="Windows/General Editors/Hypergraph: Hierarchy")


@step
def s_open():
    if again(s_open, lambda: hg_area()[0] is not None):
        return
    w, area, region = hg_area()
    check(f"Hypergraph: Hierarchy opens a kit window ({C['open']})", w is not None)
    C["w"] = w
    check("one marked area, no Blender header", w is not None and len(w.screen.areas) == 1
          and not area.spaces.active.show_region_header)
    redraw()


@step
def s_drawn():
    hg = mod(".ui.hypergraph")
    if again(s_drawn, lambda: hg_area()[1].as_pointer() in hg.VIEWS):
        return
    check("the view is framed on first draw", hg_area()[1].as_pointer() in hg.VIEWS)
    redraw()


@step
def s_shot_open():
    shot("gui_hypergraph_open.png", C["w"])
    x, y = node_point(C["cube"])
    hev('MOUSEMOVE', 'NOTHING', x, y)


@step
def s_click():
    x, y = node_point(C["cube"])
    hev('LEFTMOUSE', 'PRESS', x, y)
    hev('LEFTMOUSE', 'RELEASE', x, y)


@step
def s_click_check():
    cube = bpy.data.objects[C["cube"]]
    check("a click on the pCube1 node selects pCube1 as the lead",
          cube.select_get() and bpy.context.view_layer.objects.active == cube
          and not bpy.data.objects[C["sphere"]].select_get())
    x, y = node_point(C["cube"])
    hev('MOUSEMOVE', 'NOTHING', x, y)


@step
def s_mmb_press():
    x, y = node_point(C["cube"])
    C["to"] = node_point(C["sphere"])
    hev('MIDDLEMOUSE', 'PRESS', x, y)


@step
def s_mmb_move():
    x, y = C["to"]
    hev('MOUSEMOVE', 'NOTHING', x - 10, y)


@step
def s_mmb_move2():
    x, y = C["to"]
    hev('MOUSEMOVE', 'NOTHING', x, y)


@step
def s_mmb_shot():
    shot("gui_hypergraph_drag.png", C["w"])
    x, y = C["to"]
    hev('MIDDLEMOUSE', 'RELEASE', x, y)


@step
def s_parent_check():
    cube = bpy.data.objects[C["cube"]]
    bpy.context.view_layer.update()
    moved = (cube.matrix_world.translation - __import__("mathutils").Vector(C["world"])).length
    check("MMB drag pCube1 onto pSphere1 parents it there", cube.parent == bpy.data.objects[C["sphere"]])
    check(f"world position kept ({moved:.6f})", moved < 1e-4)
    redraw()


@step
def s_unparent_press():
    x, y = node_point(C["cube"])
    _w, _area, region = hg_area()
    C["empty"] = (region.x + region.width - 40, region.y + 40)
    hev('MOUSEMOVE', 'NOTHING', x, y)


@step
def s_unparent_press2():
    x, y = node_point(C["cube"])
    hev('MIDDLEMOUSE', 'PRESS', x, y)


@step
def s_unparent_move():
    hev('MOUSEMOVE', 'NOTHING', *C["empty"])


@step
def s_unparent_release():
    hev('MIDDLEMOUSE', 'RELEASE', *C["empty"])


@step
def s_unparent_check():
    cube = bpy.data.objects[C["cube"]]
    check("MMB drag onto empty space unparents to the world", cube.parent is None)
    _w, _area, region = hg_area()
    hev('MOUSEMOVE', 'NOTHING', region.x + 30, region.y + 30)


@step
def s_box_press():
    _w, _area, region = hg_area()
    hev('LEFTMOUSE', 'PRESS', region.x + 30, region.y + 30)


@step
def s_box_move():
    _w, _area, region = hg_area()
    hev('MOUSEMOVE', 'NOTHING', region.x + region.width - 30, region.y + region.height // 2)


@step
def s_box_move2():
    _w, _area, region = hg_area()
    hev('MOUSEMOVE', 'NOTHING', region.x + region.width - 30, region.y + region.height - 40)


@step
def s_box_release():
    _w, _area, region = hg_area()
    hev('LEFTMOUSE', 'RELEASE', region.x + region.width - 30, region.y + region.height - 40)


@step
def s_box_check():
    names = (C["cube"], C["sphere"], C["group"])
    check("a marquee over every node selects them all", all(bpy.data.objects[n].select_get() for n in names))
    hev('MOUSEMOVE', 'NOTHING', *node_point(C["group"]))


@step
def s_group_dbl():
    # pCube1 back under group1 first: group1 then has a child to collapse
    bpy.data.objects[C["cube"]].parent = bpy.data.objects[C["group"]]
    redraw()


@step
def s_group_dbl2():
    x, y = node_point(C["group"])
    hev('LEFTMOUSE', 'PRESS', x, y)
    hev('LEFTMOUSE', 'RELEASE', x, y)
    hev('LEFTMOUSE', 'PRESS', x, y)
    hev('LEFTMOUSE', 'RELEASE', x, y)


@step
def s_group_check():
    hg = mod(".ui.hypergraph")
    check("a double-click on group1 collapses it", bpy.data.objects[C["group"]].session_uid in hg.COLLAPSED)
    redraw()


@step
def s_final_shot():
    shot("gui_hypergraph_final.png", C["w"])


run()
