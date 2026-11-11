"""#351 in a real UI: component pivot editing keeps the Move / Rotate / Scale tool and its manipulator (pivot handles
at the 3D cursor), the handles move and turn only the pivot, a click on empty space resets it, the Select tool has no
pivot edit; a placed pivot moves with Move drags of the components (soft selection too) while Rotate and Pin
Component Pivot leave it, and Ctrl+Z / Shift+Z take it back and forward with the move."""

import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + "." + name)


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def ob():
    return bpy.data.objects["Cube"]


def ts():
    return bpy.context.scene.tool_settings


def cursor():
    return bpy.context.scene.cursor


def hold():
    return mod("operators.hold")


def tool_id():
    with override():
        t = bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH', create=False)
    return t.idname if t else None


def selected_world():
    o = ob()
    return [o.matrix_world @ v.co for v in bmesh.from_edit_mesh(o.data).verts if v.select]


def all_world():
    o = ob()
    return [o.matrix_world @ v.co for v in bmesh.from_edit_mesh(o.data).verts]


def same(a, b, eps=1e-4):
    return len(a) == len(b) and all((p - q).length < eps for p, q in zip(a, b))


def r3(v):
    return tuple(round(x, 3) for x in v)


def frame():
    """(centre, axes) of the manipulator as drawn."""
    with override():
        centre, axes, _otype = mod("ui.manipulator").pivot_frame(bpy.context, 'TRANSLATE')
    return centre, axes


def region_xy(p):
    area, region = view3d()
    q = location_3d_to_region_2d(region, area.spaces.active.region_3d, p)
    return Vector((region.x + q.x, region.y + q.y))


def arrow_point(axis, frac=0.75):
    """Window point at ``frac`` of the manipulator's ``axis`` arrow, and the arrow's screen direction."""
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    centre, axes = frame()
    manip = mod("ui.manipulator")
    length = (manip.ARROW_PX * bpy.context.preferences.view.gizmo_size / 75.0
              * bpy.context.preferences.system.ui_scale * manip.SIZE[0])
    c2 = location_3d_to_region_2d(region, rv3d, centre)
    right = rv3d.view_rotation @ Vector((1.0, 0.0, 0.0))
    ppw = (location_3d_to_region_2d(region, rv3d, centre + right) - c2).length
    tip = location_3d_to_region_2d(region, rv3d, centre + axes.col['XYZ'.index(axis)] * (length / ppw))
    p = c2 + (tip - c2) * frac
    return Vector((region.x + p.x, region.y + p.y)), (tip - c2).normalized()


def ring_point(axis):
    """Window point on the pivot orientation ring of ``axis`` (from the projected rings the manipulator keeps), away
    from the arrows, and the screen tangent there."""
    area, region = view3d()
    cache = mod("ui.manipulator").PIVOT_RING_CACHE.get(region.as_pointer())
    paths = cache[1] if cache is not None else []
    xy = paths['XYZ'.index(axis)]
    centre, axes = frame()
    c = region_xy(centre) - Vector((region.x, region.y))
    others = [a for a in 'XYZ' if a != axis]
    want = region_xy(centre + (axes.col['XYZ'.index(others[0])] + axes.col['XYZ'.index(others[1])]) * 0.1)
    want = (want - Vector((region.x, region.y)) - c).normalized()
    pts = [Vector((float(x), float(y))) for x, y in xy]
    best = max(range(len(pts)), key=lambda i: (pts[i] - c).normalized().dot(want))
    p, q = pts[best], pts[(best + 1) % len(pts)]
    return Vector((region.x + p.x, region.y + p.y)), (q - p).normalized()


def drag(name, start, delta, button='LEFTMOUSE', moves=6):
    """Steps: hover, press, ``moves`` moves, release (separate steps: a transform started on a press misses moves
    queued in the same tick)."""
    def s_hover():
        a, d = start()
        C[name] = (a, d if delta is None else Vector(delta))
        ev('MOUSEMOVE', 'NOTHING', x=round(a.x), y=round(a.y))

    def s_press():
        a, _d = C[name]
        ev(button, 'PRESS', x=round(a.x), y=round(a.y))

    def s_move(i):
        a, d = C[name]
        p = a + d * (60.0 * i / moves if delta is None else i / moves)
        ev('MOUSEMOVE', 'NOTHING', x=round(p.x), y=round(p.y))

    def s_release():
        a, d = C[name]
        p = a + (d * 60.0 if delta is None else d)
        ev(button, 'RELEASE', x=round(p.x), y=round(p.y))

    step(s_hover)
    step(s_press)
    for i in range(1, moves + 1):
        if i == moves - 1:
            step(lambda: C.__setitem__(name + "_mid", (frame()[0], selected_world())))
        step(lambda i=i: s_move(i))
    step(s_release)


def select_top():
    o = ob()
    bm = bmesh.from_edit_mesh(o.data)
    for f in bm.faces:
        f.select = False
    for e in bm.edges:
        e.select = False
    for v in bm.verts:
        v.select = v.co.z > 0
    bm.select_flush(True)
    bmesh.update_edit_mesh(o.data)


# --- setup -------------------------------------------------------------------------------------------------------

@step
def s_setup():
    C["mouse"] = setup()
    o = ob()
    for other in bpy.context.view_layer.objects:
        other.select_set(other == o)
        if other != o:
            other.hide_set(True)
    bpy.context.view_layer.objects.active = o
    rv3d = view3d()[0].spaces.active.region_3d
    rv3d.view_location = (0, 0, 0.5)
    rv3d.view_distance = 9
    cursor().matrix = Matrix.Identity(4)
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
    select_top()
    ts().transform_pivot_point = 'BOUNDING_BOX_CENTER'
    ev('MOUSEMOVE', 'NOTHING', x=C["mouse"][0], y=C["mouse"][1])
    tap('W')


@step
def s_d_press():
    check(f"W: Move tool ({tool_id()})", tool_id() == "builtin.move")
    C["verts0"] = all_world()
    ev('D', 'PRESS')


@step
def s_d_held():
    check(f"D held: the Move tool stays ({tool_id()}), pivot edit on", tool_id() == "builtin.move" and hold().COMPONENT.on)
    with override():
        on = mod("ui.manipulator").pivot_edit(bpy.context)
        kind = mod("ui.manipulator").tool_kind(bpy.context)
    check(f"the manipulator shows the pivot handles ({on}, {kind})", on and kind == 'TRANSLATE')
    check(f"the pivot starts on the selection centre {r3(cursor().location)}", (cursor().location - Vector((0, 0, 1))).length < 1e-4)
    shot("gui_issue351_d_held.png")


drag("pivX", lambda: arrow_point('X'), None)


@step
def s_pivx():
    c = cursor().location
    check(f"X handle with D held moves only the pivot along X {r3(c)}", c.x > 0.2 and abs(c.y) < 1e-4 and abs(c.z - 1) < 1e-4)
    check("the components stay", same(C["verts0"], all_world()))
    C["loc_before_ring"] = cursor().location.copy()


drag("ringZ", lambda: ring_point('Z'), None)


@step
def s_ring():
    m = cursor().matrix.to_3x3()
    check(f"the Z ring turns the pivot about its Z axis (X axis {r3(m.col[0])})",
          abs(m.col[0].x - 1.0) > 1e-3 and (m.col[2] - Vector((0, 0, 1))).length < 1e-4)
    check("the ring doesn't move the pivot", (cursor().location - C["loc_before_ring"]).length < 1e-5)
    check("the components stay (ring)", same(C["verts0"], all_world()))
    shot("gui_issue351_ring.png")
    ev('D', 'RELEASE')


@step
def s_d_released():
    slot = bpy.context.scene.transform_orientation_slots[mod("operators.pivot").MOVE_SLOT].type
    check(f"D released: custom pivot kept ({ts().transform_pivot_point}), Move axes = the turned pivot ({slot}), "
          f"tool {tool_id()}", hold().COMPONENT.custom and ts().transform_pivot_point == 'CURSOR'
          and slot == "Maya Pivot" and tool_id() == "builtin.move")
    C["pivot1"] = cursor().location.copy()
    C["sel1"] = selected_world()


# --- the pivot follows Move drags ---------------------------------------------------------------------------------

drag("moveZ", lambda: arrow_point('Z'), None)


@step
def s_follow_wait():
    pass


@step
def s_moved():
    mid_centre, mid_sel = C["moveZ_mid"]
    d_mid = mid_sel[0] - C["sel1"][0]
    check(f"during the drag the manipulator goes with the components ({r3(mid_centre)} vs {r3(C['pivot1'] + d_mid)})",
          d_mid.length > 1e-3 and (mid_centre - (C["pivot1"] + d_mid)).length < 1e-4)
    d = selected_world()[0] - C["sel1"][0]
    c = cursor().location
    check(f"after the drag the pivot moved by the same vector ({r3(d)}; pivot {r3(C['pivot1'])} -> {r3(c)})",
          d.length > 0.05 and (c - (C["pivot1"] + d)).length < 1e-4)
    C["pivot2"] = c.copy()
    C["sel2"] = selected_world()
    ts().use_proportional_edit = True
    ts().proportional_size = 3.0


drag("softZ", lambda: arrow_point('Z'), None)


@step
def s_soft_wait():
    pass


@step
def s_soft():
    d = selected_world()[0] - C["sel2"][0]
    c = cursor().location
    check(f"soft selection: the pivot follows too ({r3(d)}; {r3(C['pivot2'])} -> {r3(c)})",
          d.length > 0.05 and (c - (C["pivot2"] + d)).length < 1e-4)
    ts().use_proportional_edit = False
    C["pivot3"] = c.copy()
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_undo():
    check(f"Ctrl+Z: components and pivot go back together ({r3(cursor().location)} vs {r3(C['pivot2'])})",
          same(selected_world(), C["sel2"]) and (cursor().location - C["pivot2"]).length < 1e-4)
    ev('LEFT_SHIFT', 'PRESS', shift=True)
    ev('Z', 'PRESS', shift=True)
    ev('Z', 'RELEASE', shift=True)
    ev('LEFT_SHIFT', 'RELEASE')


@step
def s_redo():
    check(f"Shift+Z: both forward again ({r3(cursor().location)} vs {r3(C['pivot3'])})",
          (cursor().location - C["pivot3"]).length < 1e-4)
    C["sel3"] = selected_world()
    area, region = view3d()
    C["mmb_at"] = Vector((region.x + region.width * 0.8, region.y + region.height * 0.3))
    tap('E')


drag("rotateMMB", lambda: (C["mmb_at"], Vector((1.0, 0.0))), (70, 30), button='MIDDLEMOUSE')


@step
def s_rotate_wait():
    pass


@step
def s_rotated():
    check(f"Rotate tool MMB drag turns the components ({tool_id()})", not same(selected_world(), C["sel3"]))
    check(f"... about the pivot, which stays ({r3(cursor().location)})", (cursor().location - C["pivot3"]).length < 1e-5)
    tap('W')
    bpy.context.window_manager.allset_pin_pivot = True
    C["sel4"] = selected_world()


drag("pinnedZ", lambda: arrow_point('Z'), None)


@step
def s_pin_wait():
    pass


@step
def s_pinned():
    check("Pin on: the components moved", not same(selected_world(), C["sel4"]))
    check(f"... and the pinned pivot stays ({r3(cursor().location)})", (cursor().location - C["pivot3"]).length < 1e-5)
    bpy.context.window_manager.allset_pin_pivot = False


# --- D + empty click, other tools ---------------------------------------------------------------------------------

@step
def s_d_again():
    ev('MOUSEMOVE', 'NOTHING', x=C["mouse"][0], y=C["mouse"][1])
    ev('D', 'PRESS')


@step
def s_empty_hover():
    area, region = view3d()      # lower right: empty grid (no toolbar, no Adjust Last Operation panel there)
    C["empty"] = (region.x + int(region.width * 0.85), region.y + int(region.height * 0.25))
    ev('MOUSEMOVE', 'NOTHING', x=C["empty"][0], y=C["empty"][1])


@step
def s_empty_press():
    ev('LEFTMOUSE', 'PRESS', x=C["empty"][0], y=C["empty"][1])


@step
def s_empty_release():
    ev('LEFTMOUSE', 'RELEASE', x=C["empty"][0], y=C["empty"][1])


@step
def s_empty_check():
    sel = selected_world()
    lo = Vector([min(p[i] for p in sel) for i in range(3)])
    hi = Vector([max(p[i] for p in sel) for i in range(3)])
    slot = bpy.context.scene.transform_orientation_slots[mod("operators.pivot").MOVE_SLOT].type
    check(f"D + click on empty space resets the pivot ({r3(cursor().location)}, axes {slot})",
          (cursor().location - (lo + hi) / 2).length < 1e-4
          and not hold().turned(Matrix.Identity(3), cursor().matrix.to_3x3()) and slot != "Maya Pivot")
    check(f"... the selection stays ({len(sel)} vertices)", len(sel) == 4)
    ev('D', 'RELEASE')


@step
def s_empty_released():
    check(f"D released after the reset: no custom pivot ({ts().transform_pivot_point})",
          not hold().COMPONENT.custom and ts().transform_pivot_point != 'CURSOR')
    ev('MOUSEMOVE', 'NOTHING', x=C["mouse"][0], y=C["mouse"][1])
    tap('Q')


@step
def s_select_tool_d():
    C["pivot_point_q"] = ts().transform_pivot_point
    ev('D', 'PRESS')


@step
def s_select_tool_held():
    check(f"Select tool ({tool_id()}) + D: no pivot edit, like Maya",
          tool_id() != "builtin.move" and not hold().COMPONENT.on
          and ts().transform_pivot_point == C["pivot_point_q"])
    ev('D', 'RELEASE')


for _tool_key, _tool in (('E', "builtin.rotate"), ('R', "builtin.scale")):
    @step
    def s_tool_key(key=_tool_key):
        tap(key)

    @step
    def s_tool_d():
        ev('D', 'PRESS')

    @step
    def s_tool_held(want=_tool):
        with override():
            kind = mod("ui.manipulator").tool_kind(bpy.context)
        check(f"{want} + D: the tool stays and shows the pivot handles ({tool_id()}, {kind})",
              tool_id() == want and hold().COMPONENT.on and kind == 'TRANSLATE')
        shot(f"gui_issue351_{want.split('.')[-1]}_d.png")
        ev('D', 'RELEASE')

    @step
    def s_tool_released(want=_tool):
        check(f"{want}: D released, the tool stays ({tool_id()})", tool_id() == want and not hold().COMPONENT.on)


# --- while the pivot is edited, middle drags and Shift+drags move the pivot, never the components -----------------

def faces():
    return len(bmesh.from_edit_mesh(ob().data).faces)


@step
def s_guard_rotate():
    ev('MOUSEMOVE', 'NOTHING', x=C["mouse"][0], y=C["mouse"][1])
    tap('E')


@step
def s_guard_d():
    ev('D', 'PRESS')


@step
def s_guard_d_held():
    C["verts_g"], C["faces_g"], C["cur_g"] = all_world(), faces(), cursor().location.copy()


drag("pivotMMB", lambda: (C["mmb_at"], Vector((1.0, 0.0))), (60, 20), button='MIDDLEMOUSE')


@step
def s_guard_mmb():
    check(f"Rotate tool + D + MMB drag moves the pivot ({r3(C['cur_g'])} -> {r3(cursor().location)})",
          (cursor().location - C["cur_g"]).length > 1e-3)
    check("... and not the components (MMB)", same(C["verts_g"], all_world()))
    ev('D', 'RELEASE')


@step
def s_guard_w():
    ev('MOUSEMOVE', 'NOTHING', x=C["mouse"][0], y=C["mouse"][1])
    tap('W')


@step
def s_guard_d2():
    ev('D', 'PRESS')


@step
def s_guard_d2_held():
    C["verts_g"], C["faces_g"], C["cur_g"] = all_world(), faces(), cursor().location.copy()


@step
def s_guard_shift():
    ev('LEFT_SHIFT', 'PRESS', shift=True)


drag("shiftX", lambda: arrow_point('X'), None)


@step
def s_guard_shift_drag():
    ev('LEFT_SHIFT', 'RELEASE')
    check(f"Shift+drag on a pivot handle: no extrude ({C['faces_g']} -> {faces()} faces), components stay",
          faces() == C["faces_g"] and same(C["verts_g"], all_world()))
    check(f"... the handle moved the pivot ({r3(C['cur_g'])} -> {r3(cursor().location)})",
          (cursor().location - C["cur_g"]).length > 1e-3)
    C["cur_g"] = cursor().location.copy()
    ev('LEFT_SHIFT', 'PRESS', shift=True)


drag("shiftMMB", lambda: (C["mmb_at"], Vector((1.0, 0.0))), (60, 0), button='MIDDLEMOUSE')


@step
def s_guard_shift_mmb():
    ev('LEFT_SHIFT', 'RELEASE')
    check(f"Shift+MMB drag while the pivot is edited moves the pivot ({r3(C['cur_g'])} -> {r3(cursor().location)})",
          (cursor().location - C["cur_g"]).length > 1e-3)
    check("... and not the components (Shift+MMB)", same(C["verts_g"], all_world()) and faces() == C["faces_g"])
    ev('D', 'RELEASE')


run()
