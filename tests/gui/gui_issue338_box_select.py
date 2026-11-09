"""#338 follow-up in a real UI, the reporter's steps: click the cube, Shift+drag a box over the locator, Modify > Match
Transformations > Match All Transforms -> the cube takes the locator's transform and the locator stays; one Ctrl+Z
puts the cube back. Then the same through the Outliner: a click on the cube's row, Shift+click on the locator's row
(range), Match -> the cube again; a click on the locator's row, Ctrl+click on the cube's row, Match -> the locator
takes the cube's transform. A box leaves Blender's active object alone, so the active object isn't the last pick.

The lead is the last pick in the kit's displays too, like Maya: after the box the Channel Box shows the locator's name
and values; with a second cube boxed after the clicked one, the selection wire draws the clicked cube white and the boxed
one in the lead green. One Ctrl+Z takes back the box with its lead, one Shift+Z brings both back."""

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


def cube2():
    return bpy.data.objects[C["cube2"]]


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
    c2 = bpy.data.objects.new("pCube2", me.copy())
    c2.location = (-4.0 * k, 0.0, 0.0)
    lo = bpy.data.objects.new("locator1", None)
    lo.empty_display_type = 'PLAIN_AXES'
    lo.empty_display_size = 1.0 * k
    coll = bpy.context.scene.collection.children[0] if len(bpy.context.scene.collection.children) \
        else bpy.context.scene.collection
    for ob in (c, lo, c2):          # Outliner rows pCube1, locator1 next to each other (a range of two)
        coll.objects.link(ob)
    lo.matrix_world = Matrix.LocRotScale(Vector((8.0 * k, 0.0, 1.0 * k)), Euler((0.2, 0.4, 0.6)), Vector((1, 1, 1)))
    C["cube"], C["loc"], C["cube2"] = c.name, lo.name, c2.name
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


def lead_shown(name, what):
    """The kit's lead displays show ``name``: the active object, the Channel Box name line and Translate values (the
    Attribute Editor reads the same lead)."""
    area, region = view3d()
    with bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region):
        cb = mod(".ui.channel_box")
        entry = mod(".ui.cb_entry")
        active = bpy.context.view_layer.objects.active
        lead = cb.lead(bpy.context)
        props = bpy.context.scene.allset_cb
        ob = bpy.data.objects[name]
        want = [entry.format_value(cb.get_value(ob, k), cb.entry_kind(ob, k), bpy.context.scene)
                for k in ("tx", "ty", "tz")]
        shown = [props.tx_text, props.ty_text, props.tz_text]
        check(f"{what}: {name} is the lead (active {active.name if active else None}, Channel Box "
              f"{props.lead_name!r} {shown})",
              active is not None and active.name == name and lead is not None and lead.name == name
              and props.lead_name == name and shown == want)


def wire_leads():
    """{object name: drawn in the lead colour} of the kit's selection wire in the 3D View."""
    area, region = view3d()
    with bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region):
        return {ob.name: lead for ob, lead in mod(".ui.selection_wire").highlighted(bpy.context)}


def green_pixels(path, ob):
    """Pixels in the lead green (#43ffa3) inside ``ob``'s screen box on a window screenshot."""
    img = bpy.data.images.load(path)
    w, h = img.size
    px = img.pixels[:]
    pts = [to_window(ob.matrix_world @ Vector(c)) for c in ob.bound_box]
    x0, x1 = max(0, int(min(p.x for p in pts)) - 2), min(w - 1, int(max(p.x for p in pts)) + 2)
    y0, y1 = max(0, int(min(p.y for p in pts)) - 2), min(h - 1, int(max(p.y for p in pts)) + 2)
    n = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            i = (y * w + x) * 4
            r, g, b = px[i], px[i + 1], px[i + 2]
            if g > 0.75 and g - r > 0.3 and g - b > 0.15:
                n += 1
    bpy.data.images.remove(img)
    return n


def shift_z(name):
    def press():
        _area, r = view3d()
        x, y = r.x + r.width // 2, r.y + 40
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFT_SHIFT', 'PRESS', shift=True)
        ev('Z', 'PRESS', shift=True)
        ev('Z', 'RELEASE', shift=True)
        ev('LEFT_SHIFT', 'RELEASE')
    press.__name__ = f"s_{name}"
    step(press)
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
    lead_shown(C["loc"], "Shift+box")
    leads = wire_leads()
    check(f"Shift+box: the selection wire draws the cube (picked first) in the non-lead colour ({leads})",
          leads.get(C["cube"]) is False)


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
ctrl_z("undo_box")


@step
def s_box_undone():
    check(f"one Ctrl+Z after the box takes it back: the cube alone ({selected()})", selected() == [C["cube"]])
    lead_shown(C["cube"], "Ctrl+Z after the box")


shift_z("redo_box")


@step
def s_box_redone():
    check(f"one Shift+Z brings the box back ({selected()})", selected() == sorted((C["cube"], C["loc"])))
    lead_shown(C["loc"], "Shift+Z after the box")


# --- the lead colour on screen: the cube clicked, a second cube boxed after it ---------------------------------------

click_cube("click_cube_wire")


def shift_box_cube2(name, half=45):
    def press():
        p = to_window(cube2().matrix_world.translation)
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


def wire_shot(name):
    def again():
        redraw()
    again.__name__ = f"s_{name}_redraw"
    step(again)
    wait(2)

    def take():
        C[name] = os.path.join(SHOTS or bpy.app.tempdir, f"gui_issue338_{name}.png")
        screenshot(C[name])
    take.__name__ = f"s_{name}"
    step(take)


shift_box_cube2("box_cube2")
wire_shot("wire_boxed")


@step
def s_wire_boxed():
    check(f"click pCube1, Shift+box pCube2: both selected ({selected()})",
          selected() == sorted((C["cube"], C["cube2"])))
    lead_shown(C["cube2"], "Shift+box over a second cube")
    leads = wire_leads()
    check(f"the wire: pCube2 (boxed last) in the lead colour, pCube1 not ({leads})",
          leads.get(C["cube2"]) is True and leads.get(C["cube"]) is False)
    g1, g2 = green_pixels(C["wire_boxed"], cube()), green_pixels(C["wire_boxed"], cube2())
    check(f"on screen: lead green on pCube2 ({g2} px), none on pCube1 ({g1} px)", g2 > 20 and g1 < 3)


ctrl_z("undo_box_cube2")
wire_shot("wire_undone")


@step
def s_wire_undone():
    check(f"one Ctrl+Z takes the box back ({selected()})", selected() == [C["cube"]])
    lead_shown(C["cube"], "Ctrl+Z after the box over pCube2")
    g1, g2 = green_pixels(C["wire_undone"], cube()), green_pixels(C["wire_undone"], cube2())
    check(f"on screen: lead green back on pCube1 ({g1} px), none on pCube2 ({g2} px)", g1 > 20 and g2 < 3)


shift_z("redo_box_cube2")
wire_shot("wire_redone")


@step
def s_wire_redone():
    check(f"one Shift+Z brings the box back ({selected()})", selected() == sorted((C["cube"], C["cube2"])))
    lead_shown(C["cube2"], "Shift+Z after the box over pCube2")
    g1, g2 = green_pixels(C["wire_redone"], cube()), green_pixels(C["wire_redone"], cube2())
    check(f"on screen: lead green on pCube2 again ({g2} px), none on pCube1 ({g1} px)", g2 > 20 and g1 < 3)


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
    lead_shown(C["loc"], "Outliner Shift+click range")
    C["range_shot"] = os.path.join(SHOTS or bpy.app.tempdir, "gui_issue338_outliner_range.png")
    screenshot(C["range_shot"])


@step
def s_range_rows():
    # the Outliner draws the active (lead) row in its brighter active highlight, the other selected rows darker
    img = bpy.data.images.load(C["range_shot"])
    w = img.size[0]
    px = img.pixels[:]
    r = ol_region()
    x = r.x + int(r.width * 0.85)

    def light(name):
        i = (C["rows"][C[name]] * w + x) * 4
        return round(sum(px[i:i + 3]) / 3, 3)
    bpy.data.images.remove(img)
    lo, cu = light("loc"), light("cube")
    check(f"Outliner: the locator's row (the lead) has the active highlight, brighter than the cube's ({lo} > {cu})",
          lo > cu + 0.01)


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
    lead_shown(C["cube"], "Outliner Ctrl+click")


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
    check(f"Lasso tool ({C['tool']}): Shift+lasso adds the locator ({selected()})",
          selected() == sorted((C["cube"], C["loc"])))
    lead_shown(C["loc"], "Shift+lasso")


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
    lead_shown(C["loc"], "Rig: Shift+box over the locator after the joint")


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
