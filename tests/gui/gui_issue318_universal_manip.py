"""#318 Universal Manipulator in a real UI: Maya Workflow Kit layout, a 1 x 4 x 1 box, Ctrl+T.

- Ctrl+T picks the Universal Manipulator tool; the box, corner boxes, edge arrows, centre handles and lengths show.
- A corner drag along one box axis scales that axis only, the opposite face staying; Ctrl: about the box centre;
  Shift: evenly, the opposite corner staying. One Ctrl+Z after each drag gives the box back.
- An edge's arrows rotate about the edge's direction (0.2 degrees per px along the arrows).
- The centre X arrow moves along X.
- A click on the Y length turns it into a field: typing 2 and Enter makes the box 2 long on Y about its centre.
Screenshots: gui_issue318_um.png (the tool), gui_issue318_um_field.png (typing a length)."""

import math
import os
import sys
from importlib import import_module

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, screenshot, view3d, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
STEPS = 8


def mod(name):
    return import_module(f"{MODULE}.{name}")


def um():
    return mod("operators.universal_manip")


def ob1():
    return bpy.data.objects["pCube1"]


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def screen(world):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, world)
    return Vector((region.x + p.x, region.y + p.y))


def box():
    bpy.context.view_layer.update()
    with override():
        frame, lo, hi = um().box_of(bpy.context)
    return frame, lo.copy(), hi.copy()


def centre():
    return Vector((0, 2 * C["U"], 0))


def hover(p):
    ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))
    ev('MOUSEMOVE', 'NOTHING', x=int(p.x) + 1, y=int(p.y))
    ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))


def undo():
    hover(screen(centre()) + Vector((200, 120)))
    ev('LEFT_CTRL', 'PRESS')
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


def drag(name, start, path, ctrl=False, shift=False, shot=None):
    """Steps: hover, press (with modifiers), first stretch alone, the rest, release."""
    mods = {"ctrl": ctrl, "shift": shift}

    def s1():
        a = start()
        C[name + "_a"] = a
        C[name + "_pts"] = [a + d for d in path(a)]
        hover(a)
        for key, on in (('LEFT_CTRL', ctrl), ('LEFT_SHIFT', shift)):
            if on:
                ev(key, 'PRESS', **mods)

    def s2():
        a = C[name + "_a"]
        ev('LEFTMOUSE', 'PRESS', x=int(a.x), y=int(a.y), **mods)

    def s3():
        q = C[name + "_pts"][0]
        ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), **mods)

    def s4():
        for q in C[name + "_pts"][1:]:
            ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), **mods)

    def s5():
        if SHOTS and shot:
            screenshot(os.path.join(SHOTS, shot))
        C[name + "_modal"] = [op.bl_idname for op in win().modal_operators]
        q = C[name + "_pts"][-1]
        ev('LEFTMOUSE', 'RELEASE', x=int(q.x), y=int(q.y), **mods)
        for key, on in (('LEFT_CTRL', ctrl), ('LEFT_SHIFT', shift)):
            if on:
                ev(key, 'RELEASE')

    for s in (s1, s2, s3, s4, s5):
        step(s)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_cube():
    bpy.ops.allset.keymap_activate()
    ui = mod("ui.universal_manip")
    original = ui.ALLSET_GGT_universal_manip.draw_prepare

    def spy(self, context):
        original(self, context)
        C["group"] = self
    ui.ALLSET_GGT_universal_manip.draw_prepare = spy
    with override():
        bpy.ops.allset.create(kind='CUBE')
    ob = ob1()
    for o in bpy.context.view_layer.objects:
        o.select_set(o is ob)
    bpy.context.view_layer.objects.active = ob
    u = C["U"] = mod("operators.units").maya_unit(bpy.context.scene)     # the cube is 1 Maya unit
    ob.location = (0, 2 * u, 0)
    ob.scale = (1, 4, 1)
    _area, region = view3d()
    rv3d = region.data
    rv3d.view_perspective = 'PERSP'
    rv3d.view_location = (0, 2 * u, 0)
    rv3d.view_rotation = Euler((math.radians(65), 0, math.radians(35))).to_quaternion()
    rv3d.view_distance = 11.0 * u
    with override():
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    bpy.ops.ed.undo_push(message="box made")
    redraw()


@step
def s_ctrl_t():
    _area, region = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + 40)
    ev('LEFT_CTRL', 'PRESS')
    ev('T', 'PRESS', ctrl=True)
    ev('T', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


@step
def s_tool():
    with override():
        idname = bpy.context.workspace.tools.from_space_view3d_mode('OBJECT').idname
    check(f"Ctrl+T -> Universal Manipulator ({idname})", idname == um().TOOL)
    redraw()


@step
def s_shown():
    g = C.get("group")
    check("the box manipulator draws", g is not None)
    if g is None:
        return
    shown = [gz for gz in g.corners if not gz.hide]
    edges = [gz for gz in g.edges if not gz.hide]
    labels = [gz.text for gz in g.labels if not gz.hide]
    check(f"7 corners, 9 edge handles shown, the far ones hidden ({len(shown)}, {len(edges)})",
          len(shown) == 7 and len(edges) == 9)
    check(f"lengths 1 / 4 / 1 shown ({labels})", labels == ["1.000", "4.000", "1.000"])
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue318_um.png"))
    # the corner to drag: the visible one highest-right on screen
    corners = [(i, screen(gz.matrix_basis.translation)) for i, gz in enumerate(g.corners) if not gz.hide]
    i, p = max(corners, key=lambda c: c[1].x + c[1].y)
    frame, lo, hi = box()
    s = um().corner_signs(i)
    w = frame @ um().corner_point(lo, hi, i)
    dirs = [screen(w + frame.col[k] * s[k] * 0.2 * C["U"]) - p for k in range(3)]
    k = max(range(3), key=lambda a: dirs[a].length)        # the axis longest on screen
    C.update(corner=i, axis=k, dir=dirs[k].normalized(), lo=lo, hi=hi, w=w)
    print(f"UM318 corner {i} axis {k} dirs {[tuple(round(v, 1) for v in d) for d in dirs]}", flush=True)


def _corner_start():
    return screen(C["w"])


drag("plain", _corner_start, lambda _a: [C["dir"] * 40 * j / STEPS for j in range(1, STEPS + 1)], shot="gui_issue318_um_drag.png")


@step
def s_plain_check():
    ob, k = ob1(), C["axis"]
    _f, lo, hi = box()
    s = um().corner_signs(C["corner"])
    others = [a for a in range(3) if a != k]
    base = (1, 4, 1)
    check(f"plain corner drag: scale {tuple(round(v, 4) for v in ob.scale)} changes axis {k} only, bigger "
          f"(modal {C.get('plain_modal')})",
          ob.scale[k] > base[k] * 1.05 and all(abs(ob.scale[a] - base[a]) < 1e-5 for a in others))
    stay = lo[k] if s[k] > 0 else hi[k]
    was = C["lo"][k] if s[k] > 0 else C["hi"][k]
    check(f"the opposite face stays ({stay:.5f} = {was:.5f})", abs(stay - was) < 1e-4 * C["U"])
    undo()


@step
def s_plain_undo():
    check(f"one Ctrl+Z after the corner drag ({tuple(round(v, 4) for v in ob1().scale)})",
          all(abs(a - b) < 1e-5 for a, b in zip(ob1().scale, (1, 4, 1))))


drag("ctrl", _corner_start, lambda _a: [-C["dir"] * 25 * j / STEPS for j in range(1, STEPS + 1)], ctrl=True)


@step
def s_ctrl_check():
    ob, k = ob1(), C["axis"]
    _f, lo, hi = box()
    base = (1, 4, 1)
    others = [a for a in range(3) if a != k]
    check(f"Ctrl corner drag inward: axis {k} smaller only ({tuple(round(v, 4) for v in ob.scale)})",
          ob.scale[k] < base[k] * 0.95 and all(abs(ob.scale[a] - base[a]) < 1e-5 for a in others))
    mid, was = (lo[k] + hi[k]) / 2, (C["lo"][k] + C["hi"][k]) / 2
    check(f"about the box centre ({mid:.5f} = {was:.5f})", abs(mid - was) < 1e-4 * C["U"])
    undo()


@step
def s_ctrl_undo():
    check("Ctrl+Z", all(abs(a - b) < 1e-5 for a, b in zip(ob1().scale, (1, 4, 1))))


def _shift_path(a):
    frame, lo, hi = box()
    s = um().corner_signs(C["corner"])
    opp = frame @ Vector(tuple(lo[i] if s[i] > 0 else hi[i] for i in range(3)))
    d = (a - screen(opp)).normalized()
    return [d * 30 * j / STEPS for j in range(1, STEPS + 1)]


drag("shift", _corner_start, _shift_path, shift=True)


@step
def s_shift_check():
    ob = ob1()
    f = ob.scale[0]
    _fr, lo, hi = box()
    s = um().corner_signs(C["corner"])
    opp = [lo[i] if s[i] > 0 else hi[i] for i in range(3)]
    was = [C["lo"][i] if s[i] > 0 else C["hi"][i] for i in range(3)]
    check(f"Shift corner drag: even scale ({tuple(round(v, 4) for v in ob.scale)}), copies made "
          f"{len(bpy.data.objects)}",
          f > 1.02 and abs(ob.scale[1] - 4 * f) < 1e-4 and abs(ob.scale[2] - f) < 1e-4
          and len([o for o in bpy.data.objects if o.name.startswith("pCube")]) == 1)
    check(f"the opposite corner stays ({[round(v, 4) for v in opp]} = {[round(v, 4) for v in was]})",
          all(abs(a - b) < 1e-4 * C["U"] for a, b in zip(opp, was)))
    undo()


@step
def s_shift_undo():
    check("Ctrl+Z", all(abs(a - b) < 1e-5 for a, b in zip(ob1().scale, (1, 4, 1))))


def _edge_start():
    g = C["group"]
    frame, lo, hi = box()
    with override():
        pivot = um().rotate_pivot(bpy.context, frame, lo, hi)
    for e, gz in enumerate(g.edges):
        if gz.hide or um().edge_spec(e)[0] != 0:
            continue
        mid = gz.matrix_basis.translation.copy()
        t = um().tangent(frame.col[0], mid, pivot)
        d = screen(mid + t * 0.2 * C["U"]) - screen(mid)
        if d.length > 10:
            C["edge"], C["edge_dir"] = e, d.normalized()
            return screen(mid)
    C["edge"], C["edge_dir"] = None, Vector((1, 0))
    return screen(centre())


drag("rotate", _edge_start, lambda _a: [C["edge_dir"] * 50 * j / STEPS for j in range(1, STEPS + 1)])


@step
def s_rotate_check():
    r = ob1().rotation_euler
    want = math.radians(50 * um().ROTATE_DEG_PER_PX)
    check(f"edge {C.get('edge')} drag 50 px along its arrows: rotate X {math.degrees(r.x):.2f} (about "
          f"{math.degrees(want):.2f}), Y / Z 0", abs(r.x - want) < math.radians(1.5) and abs(r.y) < 1e-5
          and abs(r.z) < 1e-5)
    check(f"about the pivot: location stays ({tuple(round(v, 4) for v in ob1().location)})",
          (ob1().location - centre()).length < 1e-4 * C["U"])
    undo()


@step
def s_rotate_undo():
    check("Ctrl+Z", abs(ob1().rotation_euler.x) < 1e-6)


def _arrow_start():
    c = centre()
    d = (screen(c + Vector((0.3 * C["U"], 0, 0))) - screen(c)).normalized()
    manipulator = mod("ui.manipulator")
    length = (manipulator.ARROW_PX * bpy.context.preferences.view.gizmo_size / 75.0
              * bpy.context.preferences.system.ui_scale * mod("ui.universal_manip").MOVE_SCALE)
    C["arrow_dir"] = d
    return screen(c) + d * length * 0.6


drag("move", _arrow_start, lambda _a: [C["arrow_dir"] * 60 * j / STEPS for j in range(1, STEPS + 1)])


@step
def s_move_check():
    loc = ob1().location
    u = C["U"]
    check(f"centre X arrow: moves along X only ({tuple(round(v / u, 4) for v in loc)} units)",
          loc.x > 0.2 * u and abs(loc.y - 2 * u) < 1e-5 * u and abs(loc.z) < 1e-5 * u)
    undo()


@step
def s_move_undo():
    check("Ctrl+Z", (ob1().location - centre()).length < 1e-5 * C["U"])


@step
def s_label_hover():
    g = C["group"]
    _area, region = view3d()
    lab = g.labels[1]
    C["label"] = Vector((region.x + lab.xy[0], region.y + lab.xy[1]))
    hover(C["label"])


@step
def s_label_click():
    p = C["label"]
    ev('LEFTMOUSE', 'PRESS', x=int(p.x), y=int(p.y))
    ev('LEFTMOUSE', 'RELEASE', x=int(p.x), y=int(p.y))


@step
def s_type():
    edit = dict(um().EDIT)
    check(f"a click on the Y length makes it a field ({edit})", edit.get("axis") == 1 and edit.get("fresh"))
    ev('TWO', 'PRESS', unicode="2")
    ev('TWO', 'RELEASE')


@step
def s_typed():
    redraw()
    check(f"typed 2 ({um().EDIT.get('text')})", um().EDIT.get("text") == "2")


@step
def s_field_shot():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue318_um_field.png"))
    ev('RET', 'PRESS')
    ev('RET', 'RELEASE')


@step
def s_size_check():
    _f, lo, hi = box()
    ob = ob1()
    u = C["U"]
    check(f"Enter: Y length 2 about the centre ({tuple(round(v, 4) for v in ob.scale)}, y {lo[1] / u:.4f}.."
          f"{hi[1] / u:.4f} units)",
          abs(ob.scale[1] - 2) < 1e-4 and abs(lo[1] / u - 1) < 1e-4 and abs(hi[1] / u - 3) < 1e-4 and not um().EDIT)
    redraw()


@step
def s_size_label():
    labels = [gz.text for gz in C["group"].labels if not gz.hide]
    check(f"the length reads 2.000 ({labels})", "2.000" in labels)
    undo()


@step
def s_size_undo():
    check(f"Ctrl+Z gives the length back ({ob1().scale[1]:.4f})", abs(ob1().scale[1] - 4) < 1e-5)


run()
