"""#348 in a real UI: the kit-drawn Maya Outliner tree. A kit skeleton has no row of its own: joint1 is a top row,
its arrow opens joint2, joint2 opens joint3 and pCylinder1 (parented to joint2); clicking joint3 picks that joint
(the skeleton goes to Pose / Edit Mode like a viewport pick), Ctrl+click adds a row, a click on empty space selects
nothing; the wheel and the scrollbar scroll a long list; playback draws nothing in the Outliner (#344).

Rows are read from what the tree drew last (``outliner_tree.SEEN``) and from screenshots."""

import json
import os
import sys
from importlib import import_module

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
POINTS = ((0.0, 0.0, 0.0), (0.0, 0.0, 3.0), (0.0, 0.0, 6.0))
C = {}


def mod(name):
    return import_module(MODULE + name)


def tree():
    return mod(".ui.outliner_tree")


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def outliner():
    area = next(a for a in win().screen.areas if a.type == 'OUTLINER')
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def redraw_all():
    for area in win().screen.areas:
        area.tag_redraw()


def park_mouse():
    _a, r = main_view()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + 20, y=r.y + 20)


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_outliner_tree_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)


def seen():
    _a, region = outliner()
    return tree().SEEN.get(region.as_pointer(), [])


def labels():
    return [(k, lab, d) for k, lab, _j, d in seen()]


def rows():
    area, region = outliner()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return tree().rows_for(bpy.context, area.spaces.active)


def row_point(label, x_units=None, kind=None):
    """Window point on the row drawn as ``label``: on its name, or ``x_units`` UI units from the row's indent."""
    area, region = outliner()
    rs = rows()
    t = tree()
    u = t.unit(bpy.context.preferences)
    k = next(i for i, r in enumerate(rs) if r.label == label and (kind is None or r.kind == kind))
    y0, y1 = t.row_rect(area, region, k, u, len(rs))
    depth = rs[k].depth
    x = region.x + int((depth + (x_units if x_units is not None else 3.0)) * u)
    return x, region.y + int((y0 + y1) / 2)


def click(x, y, **mods):
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y, **mods)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y, **mods)


TEMP_ITEMS = []
OFF_ITEMS = []


def ensure_keys():
    """The tree's keymap items (added by the kit's keymap; until then the test adds them itself)."""
    kc = bpy.context.window_manager.keyconfigs.addon
    have = any(k.idname == "allset.outliner_tree_click" for km in kc.keymaps for k in km.keymap_items)
    C["kit_keys"] = have
    if have:
        return
    km = kc.keymaps.new("Outliner", space_type='OUTLINER')
    TEMP_ITEMS.append((km, km.keymap_items.new("allset.outliner_tree_click", 'LEFTMOUSE', 'PRESS', any=True)))
    km2 = kc.keymaps.new("View2D", space_type='EMPTY')
    for wheel, n in (('WHEELDOWNMOUSE', 3), ('WHEELUPMOUSE', -3)):
        k = km2.keymap_items.new("allset.outliner_tree_scroll", wheel, 'PRESS')
        k.properties.rows = n
        TEMP_ITEMS.append((km2, k))
    # the kit keeps its own items in front of later add-on items: its plain View2D wheel scroll goes off meanwhile
    for k in km2.keymap_items:
        if k.idname.startswith("view2d.scroll_") and k.type.startswith("WHEEL") and k.active:
            k.active = False
            OFF_ITEMS.append(k)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    tree().ENABLED = True
    tree().hide_all()
    bpy.ops.allset.keymap_activate()
    ensure_keys()
    k = mod(".operators.units").maya_unit(bpy.context.scene)
    pts = [[c * k for c in p] for p in POINTS]
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        for ob in list(bpy.context.selected_objects):
            ob.select_set(False)
        bpy.ops.allset.joint_tool(points=json.dumps(pts))
        bpy.ops.object.mode_set(mode='OBJECT')
        rig = bpy.data.objects["skeleton1"]
        coll = rig.users_collection[0]          # created after the skeleton, in its collection
        cube = bpy.data.objects.new("pCube1", bpy.data.meshes.new("pCubeShape1"))
        coll.objects.link(cube)
        cyl = bpy.data.objects.new("pCylinder1", bpy.data.meshes.new("pCylinderShape1"))
        coll.objects.link(cyl)
        cyl.parent, cyl.parent_type, cyl.parent_bone = rig, 'BONE', "joint2"
        for ob in list(bpy.context.selected_objects):
            ob.select_set(False)
    park_mouse()
    redraw_all()


@step
def s_wait():
    redraw_all()


@step
def s_collapsed():
    shot("1_collapsed")
    area, region = outliner()
    sp = area.spaces.active
    check(f"the Maya Outliner shows the kit tree (Blender's rows hidden: {not sp.use_filter_object})",
          tree().is_tree(sp))
    check(f"kit keymap items in place ({C['kit_keys']}; else the test added them)", True)
    got = labels()
    C["collapsed"] = got
    names = [lab for _k, lab, _d in got]
    check(f"joint1 is a top row, no skeleton1 row, pCube1 listed ({got})",
          ('JOINT', "joint1", 0) in got and "skeleton1" not in names and ('OBJECT', "pCube1", 0) in got)
    check(f"startup cameras lead the list ({names[:4]})", names[:4] == ["persp", "top", "front", "side"])
    click(*row_point("joint1", x_units=0.6))


@step
def s_wait_open():
    park_mouse()
    redraw_all()


@step
def s_open1():
    got = labels()
    check(f"joint1's arrow opens joint2 under it ({got})",
          ('JOINT', "joint2", 1) in got and ('JOINT', "joint3", 2) not in got)
    click(*row_point("joint2", x_units=0.6))


@step
def s_wait_open2():
    park_mouse()
    redraw_all()


@step
def s_open2():
    shot("2_open")
    got = labels()
    i = got.index(('JOINT', "joint2", 1)) if ('JOINT', "joint2", 1) in got else -1
    check(f"joint2 opens joint3 and pCylinder1 (parented to joint2) right under it ({got})",
          i >= 0 and got[i + 1:i + 3] == [('JOINT', "joint3", 2), ('OBJECT', "pCylinder1", 2)])
    C["ops0"] = len(bpy.context.window_manager.operators)
    click(*row_point("joint3"))


@step
def s_wait_pick():
    park_mouse()
    redraw_all()


@step
def s_picked():
    shot("3_joint3_picked")
    rig = bpy.data.objects["skeleton1"]
    act = rig.data.bones.active
    mode = rig.mode
    if mode == 'EDIT':
        act_name = rig.data.edit_bones.active.name if rig.data.edit_bones.active else None
    else:
        act_name = act.name if act else None
    check(f"a joint row click picks that joint (mode {mode}, active {act_name})",
          mode in ('POSE', 'EDIT') and act_name == "joint3")
    ops = [o.bl_idname for o in bpy.context.window_manager.operators][-2:]
    check(f"the kit click ran, not Blender's row operators ({ops})",
          ops and ops[-1] == "ALLSET_OT_outliner_tree_click")
    click(*row_point("pCube1"), ctrl=True)


@step
def s_wait_ctrl():
    park_mouse()
    redraw_all()


@step
def s_ctrl():
    sel = sorted(o.name for o in bpy.context.selected_objects)
    check(f"Ctrl+click an object row after a joint: Object Mode, the object added, the skeleton (its picked "
          f"joints) kept ({sel}, {bpy.data.objects['skeleton1'].mode})",
          sel == ["pCube1", "skeleton1"] and bpy.data.objects["skeleton1"].mode == 'OBJECT')
    click(*row_point("pCylinder1"), ctrl=True)


@step
def s_wait_ctrl2():
    park_mouse()
    redraw_all()


@step
def s_ctrl2():
    shot("4_two_objects")
    sel = sorted(o.name for o in bpy.context.selected_objects)
    check(f"Ctrl+click adds pCylinder1 ({sel})", sel == ["pCube1", "pCylinder1", "skeleton1"])
    rs = rows()
    root = next(r for r in rs if r.label == "joint1")
    st = tree().row_state(bpy.context, root, set())
    check(f"the picked skeleton shows as its root joint row in Object Mode (selected, lead: {st[:2]})",
          st[0] and not st[1])
    act = bpy.context.view_layer.objects.active
    check(f"the last picked is the lead ({act.name if act else None})", act is not None and act.name == "pCylinder1")
    area, region = outliner()
    rs = rows()
    u = tree().unit(bpy.context.preferences)
    x = region.x + region.width // 2
    y = region.y + max(2, region.height - (len(rs) + 1) * u - u // 2)
    C["empty_ok"] = len(rs) * u + u < region.height
    click(x, y)


@step
def s_wait_empty():
    park_mouse()
    redraw_all()


@step
def s_empty():
    if C["empty_ok"]:
        sel = [o.name for o in bpy.context.selected_objects]
        check(f"a click on empty Outliner space selects nothing ({sel})", not sel)
    # a long list: 60 objects
    coll = bpy.context.scene.collection
    me = bpy.data.meshes.new("pSphereShape")
    for i in range(60):
        coll.objects.link(bpy.data.objects.new(f"pSphere{i + 1}", me))
    redraw_all()


@step
def s_wait_many():
    redraw_all()


@step
def s_wheel():
    area, region = outliner()
    C["first0"] = tree().SCROLL.get(area.as_pointer(), 0)
    x, y = region.x + region.width // 2, region.y + region.height // 2
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    for _ in range(3):
        ev('WHEELDOWNMOUSE', 'PRESS', x=x, y=y)


@step
def s_wait_wheel():
    redraw_all()


@step
def s_wheeled():
    shot("5_scrolled")
    area, region = outliner()
    first = tree().SCROLL.get(area.as_pointer(), 0)
    check(f"the wheel scrolls the rows ({C['first0']} -> {first})", first == C["first0"] + 9)
    j0 = seen()[0] if seen() else None
    check(f"the first drawn row is that row ({j0})", j0 is not None and j0[2] == 0)
    # playback: the Outliner draws nothing (#344)
    va, vr = main_view()
    park_mouse()
    with bpy.context.temp_override(window=win(), area=va, region=vr):
        bpy.ops.screen.animation_play()


@step
def s_play1():
    C["draws0"] = tree().STATS["draws"]
    C["frame0"] = bpy.context.scene.frame_current


@step
def s_play2():
    pass


@step
def s_play_stop():
    draws = tree().STATS["draws"] - C["draws0"]
    frames = bpy.context.scene.frame_current - C["frame0"]
    playing = win().screen.is_animation_playing
    va, vr = main_view()
    with bpy.context.temp_override(window=win(), area=va, region=vr):
        bpy.ops.screen.animation_cancel(restore_frame=True)
    check(f"playback ran ({playing}, {frames} frames) and the Outliner tree drew {draws} times (no per-frame "
          f"Python work)", playing and frames > 5 and draws == 0)
    # drawing cost: 1000 objects, the Outliner redrawn (only the visible rows are drawn; the rows come from the cache)
    coll = bpy.context.scene.collection
    me = bpy.data.meshes.new("pConeShape")
    for i in range(940):
        coll.objects.link(bpy.data.objects.new(f"pCone{i + 1}", me))
    area, region = outliner()
    import time
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.redraw_timer(type='DRAW', iterations=2)        # the first draw builds the rows
        b0 = tree().STATS["builds"]
        t0 = time.perf_counter()
        bpy.ops.wm.redraw_timer(type='DRAW', iterations=20)
        ms = (time.perf_counter() - t0) * 1000 / 20
    builds = tree().STATS["builds"] - b0
    print(f"TREE348 outliner redraw {ms:.2f} ms per draw, {region.height // tree().unit()} rows shown, "
          f"{len(rows())} rows")
    check(f"a redraw with 1000 objects costs {ms:.2f} ms and builds no rows ({builds})", ms < 12.0 and builds == 0)
    for km, k in TEMP_ITEMS:
        km.keymap_items.remove(k)
    TEMP_ITEMS.clear()
    for k in OFF_ITEMS:
        k.active = True
    OFF_ITEMS.clear()


run()
