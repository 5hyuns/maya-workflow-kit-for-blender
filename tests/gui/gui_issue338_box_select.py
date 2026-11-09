"""#338 follow-up in a real UI, the reporter's steps: click the cube, Shift+drag a box over the locator, Modify > Match
Transformations > Match All Transforms -> the cube takes the locator's transform and the locator stays; one Ctrl+Z
puts the cube back. Then the same through the Outliner: a click on the cube's row, Shift+click on the locator's row
(range), Match -> the cube again; a click on the locator's row, Ctrl+click on the cube's row, Match -> the locator
takes the cube's transform. A box leaves Blender's active object alone, so the active object isn't the last pick."""

import math
import os
import sys
from importlib import import_module

import bpy
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
KEYS = {"ctrl": "LEFT_CTRL", "shift": "LEFT_SHIFT"}
TOL = 1e-3


def mod(name):
    return import_module(MODULE + name)


def cube():
    return bpy.data.objects[C["cube"]]


def loc():
    return bpy.data.objects[C["loc"]]


def to_window(world):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    p = location_3d_to_region_2d(region, area.spaces.active.region_3d, world)
    return Vector((p.x + region.x, p.y + region.y))


def selected():
    return sorted(o.name for o in bpy.context.view_layer.objects if o is not None and o.select_get())


def same(m1, m2):
    t1, r1, s1 = m1.decompose()
    t2, r2, s2 = m2.decompose()
    return (t1 - t2).length < TOL and math.degrees(r1.rotation_difference(r2).angle) < 1e-2 and (s1 - s2).length < TOL


def wait(n=3):
    for _ in range(n):
        step(lambda: None)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    k = mod(".operators.units").maya_unit()
    for ob in list(bpy.context.view_layer.objects):
        if ob is not None:
            ob.select_set(False)
    me = bpy.data.meshes.new("pCube1")
    me.from_pydata([(x * k, y * k, z * k) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    c = bpy.data.objects.new("pCube1", me)
    lo = bpy.data.objects.new("locator1", None)
    lo.empty_display_type = 'PLAIN_AXES'
    lo.empty_display_size = 1.0 * k
    coll = bpy.context.scene.collection.children[0] if len(bpy.context.scene.collection.children) \
        else bpy.context.scene.collection
    for ob in (c, lo):
        coll.objects.link(ob)
    lo.matrix_world = Matrix.LocRotScale(Vector((8.0 * k, 0.0, 1.0 * k)), Euler((0.2, 0.4, 0.6)), Vector((1, 1, 1)))
    C["cube"], C["loc"] = c.name, lo.name
    area, _region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'PERSP'
    rv3d.view_rotation = Euler((math.radians(80), 0.0, 0.0)).to_quaternion()
    rv3d.view_location = (4.0 * k, 0.0, 0.5 * k)
    rv3d.view_distance = 30.0 * k
    bpy.context.view_layer.update()
    C["cube0"], C["loc0"] = c.matrix_world.copy(), lo.matrix_world.copy()
    redraw()


wait()


def click_cube(name):
    def press():
        p = to_window(cube().matrix_world.translation)
        ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))
        ev('LEFTMOUSE', 'PRESS', x=int(p.x), y=int(p.y))
        ev('LEFTMOUSE', 'RELEASE', x=int(p.x), y=int(p.y))
    press.__name__ = f"s_{name}"
    step(press)
    wait(2)


def shift_box_locator(name, half=45):
    def press():
        p = to_window(loc().matrix_world.translation)
        a = p - Vector((half, half))
        C["box"] = (a, p + Vector((half, half)))
        ev('MOUSEMOVE', 'NOTHING', x=int(a.x), y=int(a.y))
        ev('LEFT_SHIFT', 'PRESS', shift=True)
        ev('LEFTMOUSE', 'PRESS', x=int(a.x), y=int(a.y), shift=True)

    def move():
        a, b = C["box"]
        for i in range(1, 9):
            q = a + (b - a) * (i / 8)
            ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), shift=True)

    def release():
        _a, b = C["box"]
        ev('LEFTMOUSE', 'RELEASE', x=int(b.x), y=int(b.y), shift=True)
        ev('LEFT_SHIFT', 'RELEASE')
    for i, fn in enumerate((press, move, release)):
        fn.__name__ = f"s_{name}_{i}"
        step(fn)
    wait(3)


def match(name):
    def run_match():
        area, region = view3d()
        with bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region):
            # a menu item: one undo step
            C[name] = bpy.ops.allset.match_transform('INVOKE_DEFAULT', True, kind='ALL')
    run_match.__name__ = f"s_{name}"
    step(run_match)
    wait(2)


def ctrl_z(name):
    def press():
        _area, r = view3d()
        x, y = r.x + r.width // 2, r.y + 40
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFT_CTRL', 'PRESS', ctrl=True)
        ev('Z', 'PRESS', ctrl=True)
        ev('Z', 'RELEASE', ctrl=True)
        ev('LEFT_CTRL', 'RELEASE')
    press.__name__ = f"s_{name}"
    step(press)
    wait(3)


# --- the reporter's steps: click the cube, Shift+drag a box over the locator, Match --------------------------------

click_cube("click_cube")


@step
def s_cube_picked():
    check(f"a click picks the cube ({selected()})", selected() == [C["cube"]])


shift_box_locator("box_locator")


@step
def s_boxed():
    active = bpy.context.view_layer.objects.active
    check(f"Shift+drag box adds the locator ({selected()})", selected() == sorted((C["cube"], C["loc"])))
    print("GUI note: active object after the box =", active.name if active else None)
    C["active_after_box"] = active.name if active else None


match("match_box")


@step
def s_matched_box():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue338_box_match.png"))
    check(f"Match Transformations finished ({C['match_box']})", C["match_box"] == {'FINISHED'})
    check(f"#338: the cube (clicked first) takes the boxed locator's transform "
          f"({tuple(round(v, 3) for v in cube().matrix_world.translation)})", same(cube().matrix_world, C["loc0"]))
    check("#338: the locator (boxed last) does not move", same(loc().matrix_world, C["loc0"]))


ctrl_z("undo_match")


@step
def s_undone():
    check(f"one Ctrl+Z puts the cube back ({tuple(round(v, 3) for v in cube().matrix_world.translation)})",
          same(cube().matrix_world, C["cube0"]))
    check("the locator is where it was", same(loc().matrix_world, C["loc0"]))
    check(f"the selection stays after the undo ({selected()})", selected() == sorted((C["cube"], C["loc"])))


match("match_again")


@step
def s_matched_again():
    check("Match again after the undo: the cube takes the locator's transform again",
          C["match_again"] == {'FINISHED'} and same(cube().matrix_world, C["loc0"]) and
          same(loc().matrix_world, C["loc0"]))


ctrl_z("undo_again")


# --- the Outliner: find the rows, then click / Shift+click / Ctrl+click ----------------------------------------------

def outliner():
    return C["outliner"]


def ol_region():
    return next(r for r in outliner().regions if r.type == 'WINDOW')


@step
def s_outliner():
    C["outliner"] = max((a for a in win().screen.areas if a.type == 'OUTLINER'), key=lambda a: a.height)
    r = ol_region()
    row = round(20 * bpy.context.preferences.system.ui_scale)
    C["probe"] = [r.y + r.height - int(row * (i + 0.5)) for i in range(16)]
    C["rows"] = {}


def probe(i):
    def s_click():
        r = ol_region()
        y = C["probe"][i]
        x = r.x + int(r.width * 0.35)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)

    def s_look():
        sel = selected()
        if len(sel) == 1 and sel[0] not in C["rows"]:
            C["rows"][sel[0]] = C["probe"][i]
    step(s_click)
    step(s_look)


for _i in range(16):
    probe(_i)


@step
def s_rows_found():
    check(f"Outliner rows found ({sorted(C['rows'])})", C["cube"] in C["rows"] and C["loc"] in C["rows"])


def ol_click(name, obname, *mods):
    def s1():
        r = ol_region()
        x, y = r.x + int(r.width * 0.35), C["rows"].get(C[obname], r.y)
        C["xy"] = (x, y)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        for m in mods:
            ev(KEYS[m], 'PRESS', x=x, y=y, **{m: True})

    def s2():
        x, y = C["xy"]
        kw = {m: True for m in mods}
        ev('LEFTMOUSE', 'PRESS', x=x, y=y, **kw)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y, **kw)

    def s3():
        x, y = C["xy"]
        for m in mods:
            ev(KEYS[m], 'RELEASE', x=x, y=y)
    for i, fn in enumerate((s1, s2, s3)):
        fn.__name__ = f"s_{name}_{i}"
        step(fn)
    wait(12)                     # a second click on a row within the double-click time would rename it


@step
def s_reset_positions():
    cube().matrix_world = C["cube0"]
    loc().matrix_world = C["loc0"]
    bpy.context.view_layer.update()
    bpy.ops.ed.undo_push(message="positions")


wait(12)
ol_click("ol_cube", "cube")
ol_click("ol_range_locator", "loc", "shift")


@step
def s_range():
    active = bpy.context.view_layer.objects.active
    check(f"Outliner click cube, Shift+click locator = both ({selected()})",
          selected() == sorted((C["cube"], C["loc"])))
    print("GUI note: active object after the Outliner range =", active.name if active else None)
    C["active_after_range"] = active.name if active else None


match("match_range")


@step
def s_matched_range():
    check(f"Outliner Shift+click: the cube (clicked first) takes the locator's transform ({C['match_range']})",
          C["match_range"] == {'FINISHED'} and same(cube().matrix_world, C["loc0"]))
    check("Outliner Shift+click: the locator (picked last) does not move", same(loc().matrix_world, C["loc0"]))


ctrl_z("undo_range")
ol_click("ol_locator", "loc")
ol_click("ol_toggle_cube", "cube", "ctrl")


@step
def s_toggle():
    check(f"Outliner click locator, Ctrl+click cube = both ({selected()})",
          selected() == sorted((C["cube"], C["loc"])))
    check("the positions are back before this Match", same(cube().matrix_world, C["cube0"]) and
          same(loc().matrix_world, C["loc0"]))


match("match_toggle")


@step
def s_matched_toggle():
    check(f"Outliner Ctrl+click: the locator (clicked first) takes the cube's transform ({C['match_toggle']})",
          C["match_toggle"] == {'FINISHED'} and same(loc().matrix_world, C["cube0"]))
    check("Outliner Ctrl+click: the cube (picked last) does not move", same(cube().matrix_world, C["cube0"]))
    print("GUI note: active after box", C.get("active_after_box"), "after range", C.get("active_after_range"))


ctrl_z("undo_toggle")


# --- the Lasso Select tool: the cube picked, a Shift+lasso around the locator, Match ---------------------------------

def set_tool(name):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.tool_set_by_id(name=name)
        return bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname


def pick_only(*obs):
    """A plain click on the first object, (Ctrl+Shift) clicks on the rest: each becomes the active one in turn."""
    for o in bpy.context.view_layer.objects:
        if o is not None:
            o.select_set(False)
    for ob in obs:
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.context.view_layer.update()


@step
def s_lasso_setup():
    check("the positions are back before the lasso", same(cube().matrix_world, C["cube0"]) and
          same(loc().matrix_world, C["loc0"]))
    C["tool"] = set_tool("builtin.select_lasso")
    pick_only(cube())
    bpy.ops.ed.undo_push(message="cube picked")
    redraw()


wait(3)


def shift_lasso_locator(name, r=45):
    ring = [(math.cos(2 * math.pi * k / 12) * r, math.sin(2 * math.pi * k / 12) * r) for k in range(13)]

    def at(k):
        p = to_window(loc().matrix_world.translation) + Vector(ring[k])
        return int(p.x), int(p.y)

    def press():
        ev('MOUSEMOVE', 'NOTHING', x=at(0)[0], y=at(0)[1])
        ev('LEFT_SHIFT', 'PRESS', shift=True)
        ev('LEFTMOUSE', 'PRESS', x=at(0)[0], y=at(0)[1], shift=True)
    fns = [press]
    for k in range(1, 13):
        fns.append((lambda k: lambda: ev('MOUSEMOVE', 'NOTHING', x=at(k)[0], y=at(k)[1], shift=True))(k))

    def release():
        ev('LEFTMOUSE', 'RELEASE', x=at(12)[0], y=at(12)[1], shift=True)
        ev('LEFT_SHIFT', 'RELEASE')
    fns.append(release)
    for i, fn in enumerate(fns):
        f = (lambda fn: lambda: fn())(fn)
        f.__name__ = f"s_{name}_{i}"
        step(f)
    wait(3)


shift_lasso_locator("lasso_locator")


@step
def s_lassoed():
    active = bpy.context.view_layer.objects.active
    check(f"Lasso tool ({C['tool']}): Shift+lasso adds the locator ({selected()}), the cube stays the active object "
          f"({active.name if active else None})",
          selected() == sorted((C["cube"], C["loc"])) and active is not None and active.name == C["cube"])


match("match_lasso")


@step
def s_matched_lasso():
    check(f"Lasso: the cube (picked first) takes the lassoed locator's transform ({C['match_lasso']})",
          C["match_lasso"] == {'FINISHED'} and same(cube().matrix_world, C["loc0"]))
    check("Lasso: the locator (picked last) does not move", same(loc().matrix_world, C["loc0"]))


ctrl_z("undo_lasso")


@step
def s_lasso_undone():
    check("one Ctrl+Z after the lasso Match puts the cube back", same(cube().matrix_world, C["cube0"]))
    C["tool"] = set_tool("builtin.select_box")


# --- a rig: a root joint picked with a box (Pose mode), then a Shift+box over the locator, Match ---------------------

def arm():
    return bpy.data.objects[C["arm"]]


def joint_tip(i):
    a = arm()
    pb = a.pose.bones[C["names"][i]]
    return to_window(a.matrix_world @ pb.head)


def selected_joints():
    a = arm()
    return [pb.name for pb in a.pose.bones if pb.select]


@step
def s_rig_scene():
    joints = mod(".operators.joints")
    k = mod(".operators.units").maya_unit()
    pick_only()
    a = joints.new_skeleton(bpy.context)
    names, parent = [], None
    for x in (2.0, 5.0):
        parent = joints.add_joint(a, Vector((x, 0.0, 4.0)) * k, parent, length=1.0 * k)
        names.append(parent)
    joints.finish(bpy.context, a, names)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for n in names:
        a.data.bones[n][joints.RADIUS] = 2.0
    pick_only()
    bpy.context.view_layer.objects.active = None
    C["arm"], C["names"] = a.name, names
    bpy.context.view_layer.update()
    C["rig0"] = a.matrix_world.copy()
    bpy.ops.ed.undo_push(message="rig")
    redraw()


wait(3)


def box_at(name, where, half=30, shift=False):
    def press():
        p = where()
        a = p - Vector((half, half))
        C["box"] = (a, p + Vector((half, half)))
        ev('MOUSEMOVE', 'NOTHING', x=int(a.x), y=int(a.y))
        if shift:
            ev('LEFT_SHIFT', 'PRESS', shift=True)
        ev('LEFTMOUSE', 'PRESS', x=int(a.x), y=int(a.y), shift=shift)

    def move():
        a, b = C["box"]
        for i in range(1, 9):
            q = a + (b - a) * (i / 8)
            ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), shift=shift)

    def release():
        _a, b = C["box"]
        ev('LEFTMOUSE', 'RELEASE', x=int(b.x), y=int(b.y), shift=shift)
        if shift:
            ev('LEFT_SHIFT', 'RELEASE')
    for i, fn in enumerate((press, move, release)):
        fn.__name__ = f"s_{name}_{i}"
        step(fn)
    wait(4)                       # the joint rules run from a timer after the box ends


box_at("box_joint", lambda: joint_tip(0))


@step
def s_joint_boxed():
    check(f"a box over a joint picks it ({bpy.context.mode}, {selected_joints()})",
          bpy.context.mode == 'POSE' and selected_joints() == [C["names"][0]])


box_at("box_locator_after_joint", lambda: to_window(loc().matrix_world.translation), half=45, shift=True)


@step
def s_rig_boxed():
    active = bpy.context.view_layer.objects.active
    check(f"then a Shift+box over the locator adds it and keeps the joint ({bpy.context.mode}, {selected()}, "
          f"{selected_joints()}, active {active.name if active else None})",
          loc().select_get() and selected_joints() == [C["names"][0]])
    snap = mod(".operators.snap_align")
    C["joint_before"] = snap._maya_frame(arm().pose.bones[C["names"][0]])


match("match_rig")


@step
def s_matched_rig():
    snap = mod(".operators.snap_align")
    bpy.context.view_layer.update()
    pb = arm().pose.bones[C["names"][0]]
    check(f"Rig: Match finished ({C['match_rig']})", C["match_rig"] == {'FINISHED'})
    check(f"Rig: the joint (picked first) takes the boxed locator's transform "
          f"({tuple(round(v, 3) for v in snap._maya_frame(pb).translation)})",
          same(snap._maya_frame(pb), C["loc0"]))
    check("Rig: the locator (boxed last) does not move", same(loc().matrix_world, C["loc0"]))
    check("Rig: the skeleton object does not move", same(arm().matrix_world, C["rig0"]))
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue338_rig_match.png"))


ctrl_z("undo_rig")


@step
def s_rig_undone():
    snap = mod(".operators.snap_align")
    bpy.context.view_layer.update()
    pb = arm().pose.bones[C["names"][0]]
    check("one Ctrl+Z puts the joint back", same(snap._maya_frame(pb), C["joint_before"]))
    check("the locator is where it was", same(loc().matrix_world, C["loc0"]))


run()
