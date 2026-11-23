"""In a real UI (#524): the UV Editor's Shift selection toggles like Maya (and like the kit's 3D View): Shift+click on a
selected face / UV deselects it, on an unselected one adds it; Shift+marquee toggles every face / UV it catches
against the selection before. Checked with UV Sync Selection on (face mode) and off (face and UV / vertex mode)."""
import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
N = 4


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def grid():
    return bpy.data.objects[C["grid"]]


def uv_window():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.ui_type == 'UV':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


def redraw_all():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def bm():
    return bmesh.from_edit_mesh(grid().data)


def face_uv_centre(b, f):
    uv = b.loops.layers.uv.active
    pts = [lp[uv].uv for lp in f.loops]
    return sum(p.x for p in pts) / len(pts), sum(p.y for p in pts) / len(pts)


def cell(b, f):
    u, v = face_uv_centre(b, f)
    return int(u * N), int(v * N)          # (column, row) of the face in the 0-1 square


def face_at(col, row):
    b = bm()
    return next(f.index for f in b.faces if cell(b, f) == (col, row))


def to_region(u, v):
    _w, _a, r = uv_window()
    x, y = r.view2d.view_to_region(u, v, clip=False)
    return x, y


def sync():
    return bpy.context.scene.tool_settings.use_uv_select_sync


def picked_faces():
    """Faces shown selected in the UV Editor: mesh faces with UV Sync Selection on, the UV face flag (all corners
    picked) with it off."""
    b = bm()
    compat = mod(".compat")
    uv = b.loops.layers.uv.active
    if sync():
        if compat.uv_selection_on_loops(b, True):
            return {f.index for f in b.faces if f.select and all(compat.uv_vert_selected(lp, uv) for lp in f.loops)}
        return {f.index for f in b.faces if f.select}
    return {f.index for f in b.faces if all(compat.uv_vert_selected(lp, uv) for lp in f.loops)}


def picked_uvs():
    """(column, row) corners of picked UVs (sync off)."""
    b = bm()
    compat = mod(".compat")
    uv = b.loops.layers.uv.active
    return {(round(lp[uv].uv.x * N), round(lp[uv].uv.y * N)) for f in b.faces for lp in f.loops
            if compat.uv_vert_selected(lp, uv)}


def picked_uv_edges():
    """UV edges picked (sync off), as pairs of (column, row) corners."""
    b = bm()
    compat = mod(".compat")
    uv = b.loops.layers.uv.active

    def at(lp):
        return round(lp[uv].uv.x * N), round(lp[uv].uv.y * N)
    return {frozenset((at(lp), at(lp.link_loop_next))) for f in b.faces for lp in f.loops
            if compat.uv_edge_selected(lp, uv)}


def picked_verts():
    """(column, row) of the selected mesh vertices (sync on), by their UV position."""
    b = bm()
    uv = b.loops.layers.uv.active
    return {(round(v.link_loops[0][uv].uv.x * N), round(v.link_loops[0][uv].uv.y * N)) for v in b.verts if v.select}


def set_faces(cells):
    """Select exactly the faces at ``cells`` ((col, row)), in the current sync state."""
    b = bm()
    compat = mod(".compat")
    uv = b.loops.layers.uv.active
    want = {f.index for f in b.faces if cell(b, f) in cells}
    if sync():
        for seq in (b.faces, b.edges, b.verts):
            for el in seq:
                el.select = False
        for f in b.faces:            # (unselecting a face unselects its corners too: wanted faces go last)
            if f.index in want:
                f.select = True
        b.select_flush_mode()
        compat.uv_sync_from_mesh(b)
    else:
        for v in b.verts:
            v.select = True
        for f in b.faces:
            f.select = True
        for f in b.faces:
            compat.set_uv_face_selected(f, uv, f.index in want)
    bmesh.update_edit_mesh(grid().data)
    redraw_all()


def cells_of(faces):
    b = bm()
    b.faces.ensure_lookup_table()
    return {cell(b, b.faces[i]) for i in faces}


KEYS = {"ctrl": "LEFT_CTRL", "shift": "LEFT_SHIFT"}


def wait(n=12):
    for _ in range(n):            # a second press within the double-click time is a DOUBLE_CLICK (no CLICK)
        step(lambda: None)


def click_cell(col, row, *mods):
    wait()

    def xy():
        x, y = to_region((col + 0.5) / N, (row + 0.5) / N)
        _w, _a, r = uv_window()
        return r.x + int(x), r.y + int(y)

    def s1():
        w = uv_window()[0]
        x, y = xy()
        w.event_simulate(type='MOUSEMOVE', value='NOTHING', x=x, y=y)
        for m in mods:
            w.event_simulate(type=KEYS[m], value='PRESS', x=x, y=y)

    def s2():
        w = uv_window()[0]
        x, y = xy()
        kw = {m: True for m in mods}
        w.event_simulate(type='LEFTMOUSE', value='PRESS', x=x, y=y, **kw)
        w.event_simulate(type='LEFTMOUSE', value='RELEASE', x=x, y=y, **kw)

    def s3():
        w = uv_window()[0]
        x, y = xy()
        for m in mods:
            w.event_simulate(type=KEYS[m], value='RELEASE', x=x, y=y)
    step(s1)
    step(s2)
    step(s3)
    wait(4)


# Simulated drags carry no modifier into CLICK_DRAG, so a Shift+marquee is driven the way its keymap runs it: the kit's
# allset.select_2d_box first (PASS_THROUGH), then Blender's box as mode SET (see the keymap test for the bindings).
def shift_box(u0, v0, u1, v1):
    def s():
        w, a, r = uv_window()
        x0, y0 = to_region(u0, v0)
        x1, y1 = to_region(u1, v1)
        with bpy.context.temp_override(window=w, area=a, region=r):
            bpy.ops.allset.select_2d_box('INVOKE_DEFAULT', editor='UV')
            bpy.ops.uv.select_box('EXEC_DEFAULT', True, mode='SET', xmin=int(min(x0, x1)), xmax=int(max(x0, x1)),
                                  ymin=int(min(y0, y1)), ymax=int(max(y0, y1)), wait_for_input=False)
    wait(2)
    step(s)
    wait(6)


@step
def s_setup():
    C["x"], C["y"] = setup()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for ob in list(bpy.data.objects):
            ob.select_set(False)
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=N, y_subdivisions=N, size=2.0)
        C["grid"] = bpy.context.active_object.name
        C["open"] = mod(".marking.modal").run_action(bpy.context, mod(".ui.menu_map").MAP["UV/UV Editor"])


@step
def s_wait_uv_window():
    import sim
    C.setdefault("wait_uv", 0)
    if uv_window()[1] is None and C["wait_uv"] < 15:
        C["wait_uv"] += 1
        sim._steps.insert(0, s_wait_uv_window)


@step
def s_opened():
    w, a, r = uv_window()
    check(f"UV > UV Editor opens a UV Editor window, grid in edit mode ({C['open']}, {a is not None})",
          a is not None and grid().mode == 'EDIT')
    if a is None:
        return
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (False, False, True)
    set_faces({(0, 3), (1, 3), (3, 3), (0, 0)})


# --- UV Sync Selection on, face mode -------------------------------------------------------------------------------

shift_box(0.02, 0.77, 0.98, 0.98)                 # the top row


@step
def s_sync_box():
    got = cells_of(picked_faces())
    check(f"sync, faces: Shift+marquee over the top row toggles it: (2, 3) + (0, 0) ({sorted(got)})",
          got == {(2, 3), (0, 0)})
    set_faces({(0, 0), (1, 1)})


click_cell(0, 0, "shift")


@step
def s_sync_click_off():
    got = cells_of(picked_faces())
    check(f"sync, faces: Shift+click on a selected face deselects it: (1, 1) ({sorted(got)})", got == {(1, 1)})


click_cell(2, 2, "shift")


@step
def s_sync_click_on():
    got = cells_of(picked_faces())
    check(f"sync, faces: Shift+click on an unselected face adds it: (1, 1) + (2, 2) ({sorted(got)})",
          got == {(1, 1), (2, 2)})
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = False
    ts.uv_select_mode = 'FACE'
    set_faces({(0, 3), (1, 3), (3, 3), (0, 0)})


# --- UV Sync Selection off, face mode ------------------------------------------------------------------------------

shift_box(0.02, 0.77, 0.98, 0.98)


@step
def s_uv_face_box():
    got = cells_of(picked_faces())
    check(f"UV faces: Shift+marquee over the top row toggles it: (2, 3) + (0, 0) ({sorted(got)})",
          got == {(2, 3), (0, 0)})
    set_faces({(0, 0), (1, 1)})


click_cell(0, 0, "shift")


@step
def s_uv_face_click_off():
    got = cells_of(picked_faces())
    check(f"UV faces: Shift+click on a selected face deselects it: (1, 1) ({sorted(got)})", got == {(1, 1)})


click_cell(2, 2, "shift")


@step
def s_uv_face_click_on():
    got = cells_of(picked_faces())
    check(f"UV faces: Shift+click on an unselected face adds it: (1, 1) + (2, 2) ({sorted(got)})",
          got == {(1, 1), (2, 2)})
    ts = bpy.context.scene.tool_settings
    ts.uv_select_mode = 'VERTEX'
    set_faces({(0, 0)})                    # UVs (0,0) (1,0) (0,1) (1,1)


# --- UV Sync Selection off, UV (vertex) mode -----------------------------------------------------------------------

shift_box(0.12, 0.12, 0.38, 0.38)                 # catches the UVs (1, 1)


@step
def s_uv_vert_box():
    got = picked_uvs()
    check(f"UVs: Shift+marquee over a picked UV unpicks it ({sorted(got)})",
          got == {(0, 0), (1, 0), (0, 1)})


shift_box(0.37, 0.37, 0.63, 0.63)                 # catches the UV (2, 2) only


@step
def s_uv_vert_box_add():
    got = picked_uvs()
    check(f"UVs: Shift+marquee over an unpicked UV picks it ({sorted(got)})",
          got == {(0, 0), (1, 0), (0, 1), (2, 2)})
    ts = bpy.context.scene.tool_settings
    ts.uv_select_mode = 'EDGE'
    set_faces({(0, 0)})


# --- UV Sync Selection off, UV edge mode ---------------------------------------------------------------------------

shift_box(-0.02, -0.02, 0.27, 0.03)               # the bottom UV edge of the face (0, 0)


@step
def s_uv_edge_box():
    got = picked_uv_edges()
    want = {frozenset(((0, 0), (0, 1))), frozenset(((0, 1), (1, 1))), frozenset(((1, 1), (1, 0)))}
    check(f"UV edges: Shift+marquee over a picked UV edge unpicks it, the others stay ({len(got)} edges)",
          got == want)
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (True, False, False)


# --- UV Sync Selection on, vertex mode -----------------------------------------------------------------------------

@step
def s_sync_vert_ready():
    set_faces({(0, 0)})


@step
def s_sync_vert_before():
    got = picked_verts()
    check(f"sync, vertices: the face (0, 0)'s four vertices selected to start ({sorted(got)})",
          got == {(0, 0), (1, 0), (0, 1), (1, 1)})


shift_box(0.2, 0.2, 0.3, 0.3)                     # the vertex at (1, 1)


@step
def s_sync_vert_box():
    got = picked_verts()
    check(f"sync, vertices: Shift+marquee over a selected vertex deselects it ({sorted(got)})",
          got == {(0, 0), (1, 0), (0, 1)})


shift_box(0.45, 0.45, 0.55, 0.55)                 # the vertex at (2, 2)


@step
def s_sync_vert_box_add():
    got = picked_verts()
    check(f"sync, vertices: Shift+marquee over an unselected vertex adds it ({sorted(got)})",
          got == {(0, 0), (1, 0), (0, 1), (2, 2)})
    if SHOTS:
        w = uv_window()[0]
        with bpy.context.temp_override(window=w):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, "gui_issue524_uv_shift_toggle.png"))


run()
