"""#582 in the UV Editor window (UV > UV Editor; Move tool, UV Sync Selection off, then on): single clicks on an edge, then on a face, then on
another face, then on UVs (plain, Shift, Ctrl+Shift, Ctrl) move the manipulator to the clicked components at once, like
a marquee selection does. The clicks run back to back with no other change in between, as a user clicks."""

import os
import sys
from importlib import import_module
from operator import attrgetter

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, setup, step, view3d, win  # noqa: E402

C = {}
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")


def mod(name):
    return import_module(MODULE + name)


def cube():
    return bpy.data.objects["Cube"]


def uv_window():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.ui_type == 'UV':
                return w, a
    return None, None


def uv_region():
    _w, area = uv_window()
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def in_uv(fn):
    w, _a = uv_window()
    area, region = uv_region()
    with bpy.context.temp_override(window=w, area=area, region=region):
        return fn()


def uev(type, value, x, y, **mods):
    """A mouse event in the UV Editor's own window."""
    w, _a = uv_window()
    w.event_simulate(type=type, value=value, x=x, y=y, **mods)


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def faces_uv():
    """[(face index, [loop UVs])] of the cube."""
    bm = bmesh.from_edit_mesh(cube().data)
    uv = bm.loops.layers.uv.active
    return [(f.index, [tuple(l[uv].uv) for l in f.loops]) for f in bm.faces]


def to_px(u, v):
    _area, region = uv_region()
    x, y = region.view2d.view_to_region(u, v, clip=False)
    return int(region.x + x), int(region.y + y)


def manip():
    _area, region = uv_region()
    return mod(".ui.uv_manipulator").LAST.get(region.as_pointer())


def want_centre():
    """Region pixels of the middle of the selected UVs' box, read from the BMesh here (what a marquee selection puts
    the manipulator on)."""
    ts = bpy.context.scene.tool_settings
    bm = bmesh.from_edit_mesh(cube().data)
    uv = bm.loops.layers.uv.active
    picked = attrgetter("uv_select_vert")
    sync = ts.use_uv_select_sync
    face_mode = tuple(ts.mesh_select_mode) == (False, False, True)
    pts = []
    for f in bm.faces:
        if f.hide or (not sync and not f.select):
            continue
        for l in f.loops:
            if not sync or getattr(bm, "uv_select_sync_valid", False):
                on = picked(l)
            else:
                on = f.select if face_mode else l.vert.select
            if on:
                pts.append(tuple(l[uv].uv))
    if not pts:
        return None
    us, vs = [p[0] for p in pts], [p[1] for p in pts]
    _area, region = uv_region()
    return region.view2d.view_to_region((min(us) + max(us)) / 2, (min(vs) + max(vs)) / 2, clip=False)


@step
def s_setup():
    setup()
    bpy.ops.allset.keymap_activate()
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set('EXEC_DEFAULT', True, mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        # UV > UV Editor: the UV Editor in its own window, like the report
        C["open"] = mod(".marking.modal").run_action(bpy.context, mod(".ui.menu_map").MAP["UV/UV Editor"])
    bpy.context.scene.tool_settings.use_uv_select_sync = False


@step
def s_wait_window():
    import sim
    C.setdefault("wait", 0)
    if uv_window()[1] is None and C["wait"] < 15:
        C["wait"] += 1
        sim._steps.insert(0, s_wait_window)


@step
def s_frame():
    in_uv(lambda: bpy.ops.image.view_all(fit_view=True))
    in_uv(lambda: bpy.ops.uv.select_all(action='SELECT'))
    in_uv(lambda: bpy.ops.wm.tool_set_by_id(name="builtin.move", space_type='IMAGE_EDITOR'))
    redraw()


def click_case(tag, sync, mode, point, **mods):
    @step
    def s_aim():
        # set only what changes: a settings write is a depsgraph update, which a run of plain clicks never sends
        ts = bpy.context.scene.tool_settings
        if ts.use_uv_select_sync != sync:
            ts.use_uv_select_sync = sync
        if sync:
            want = (mode == 'VERTEX', mode == 'EDGE', mode == 'FACE')
            if tuple(ts.mesh_select_mode) != want:
                ts.mesh_select_mode = want
        elif ts.uv_select_mode != mode:
            ts.uv_select_mode = mode
        C["before"] = manip()
        C["p"] = to_px(*point())
        uev('MOUSEMOVE', 'NOTHING', *C["p"])
        redraw()

    @step
    def s_click():
        for k in mods:
            uev({'shift': 'LEFT_SHIFT', 'ctrl': 'LEFT_CTRL'}[k], 'PRESS', *C["p"], **mods)
        uev('LEFTMOUSE', 'PRESS', *C["p"], **mods)
        uev('LEFTMOUSE', 'RELEASE', *C["p"], **mods)
        for k in mods:
            uev({'shift': 'LEFT_SHIFT', 'ctrl': 'LEFT_CTRL'}[k], 'RELEASE', *C["p"])

    step(lambda: None)

    @step
    def s_check():
        got, want = manip(), want_centre()
        check(f"{tag}: a component is selected ({want})", want is not None)
        check(f"{tag}: the manipulator moves to it at once ({C['before']} -> {got}, want {want})",
              got is not None and want is not None and abs(got[0] - want[0]) <= 2 and abs(got[1] - want[1]) <= 2)
        if SHOTS:
            w, _a = uv_window()
            with bpy.context.temp_override(window=w):
                bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, f"gui_issue582_{tag}.png"))


def edge_mid(face_no):
    def point():
        pts = faces_uv()[face_no][1]
        return ((pts[0][0] + pts[1][0]) / 2 + (pts[2][0] - pts[0][0]) * 0.02,
                (pts[0][1] + pts[1][1]) / 2 + (pts[2][1] - pts[0][1]) * 0.02)
    return point


def face_mid(face_no):
    def point():
        pts = faces_uv()[face_no][1]
        return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    return point


for sync in (False, True):
    s = "sync" if sync else "uv"
    click_case(f"{s}_edge", sync, 'EDGE', edge_mid(0))
    click_case(f"{s}_face_a", sync, 'FACE', face_mid(1))
    click_case(f"{s}_face_b", sync, 'FACE', face_mid(4))
    click_case(f"{s}_vertex", sync, 'VERTEX', lambda: faces_uv()[2][1][0])
    # the report: Shift (toggle) / Ctrl+Shift (add) clicks add UVs to the selection one at a time
    click_case(f"{s}_vertex_shift", sync, 'VERTEX', lambda: faces_uv()[2][1][2], shift=True)
    click_case(f"{s}_vertex_ctrl_shift", sync, 'VERTEX', lambda: faces_uv()[3][1][1], shift=True, ctrl=True)
    click_case(f"{s}_vertex_ctrl", sync, 'VERTEX', lambda: faces_uv()[2][1][2], ctrl=True)

run()
