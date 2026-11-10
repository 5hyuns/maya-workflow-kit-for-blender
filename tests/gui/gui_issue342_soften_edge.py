"""#342 in a real UI: a kit cube whose side edges are bevelled in two segments (polyBevel1) and that carries Blender's
Shade Auto Smooth ("Smooth by Angle" modifier) shows hard edges. A click on Mesh Display > Soften Edge in the Maya menu
bar shades every edge soft (the modifier is gone); Ctrl+Z brings the hard edges and the modifier back. Shift+RMB >
Soften/Harden Edges > Soften Edge on the object does the same; in edge mode the edge marking menu's Soften Edge
shades the selected rim edges soft (the modifier gives way) and leaves the others as they were. There one Ctrl+Z
brings back the edges and the modifier together (every setting, its place in the stack), the selection and component
mode; one Shift+Z the result, in component mode; the next Ctrl+Z takes back the selection. Screenshots with
ALLSET_GUI_SHOTS (or --shots)."""

import math
import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
GUI_TIMEOUT = 240
C = {"calls": []}
ITEM = "Mesh Display/Soften Edge"


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def mod(name):
    return import_module(MODULE + name)


def oc():
    return mod(".ui.option_click")


def draw():
    return mod(".marking.draw")


def session():
    return draw().ACTIVE.get("session")


def ob():
    return bpy.data.objects[C["name"]]


def v3d_ctx():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def sba():
    return [m.name for m in ob().modifiers if m.type == 'NODES' and m.node_group
            and m.node_group.name.startswith("Smooth by Angle")]


def shown():
    """{edge index: soft} for edges between two faces at an angle, from the evaluated mesh's corner normals."""
    dg = bpy.context.evaluated_depsgraph_get()
    eo = ob().evaluated_get(dg)
    me = eo.to_mesh()
    normal, faces = {}, {}
    for p in me.polygons:
        for li in p.loop_indices:
            normal[(me.loops[li].vertex_index, p.index)] = me.corner_normals[li].vector.copy()
        for key in p.edge_keys:
            faces.setdefault(key, []).append(p.index)
    out = {}
    for e in me.edges:
        fs = faces.get(e.key, [])
        if len(fs) == 2 and me.polygons[fs[0]].normal.angle(me.polygons[fs[1]].normal, 0.0) > math.radians(1.0):
            out[e.index] = all((normal[(v, fs[0])] - normal[(v, fs[1])]).length < 1e-4 for v in e.vertices)
    eo.to_mesh_clear()
    return out


def hard_count():
    s = shown()
    return sum(1 for v in s.values() if not v), len(s)


def _plain(v):
    if isinstance(v, (str, bool, int, float)) or v is None:
        return v
    if isinstance(v, set):
        return tuple(sorted(v))
    try:
        return tuple(_plain(x) for x in v)
    except TypeError:
        return getattr(v, "name", repr(v))


def modifier(md):
    """Every setting of a modifier and a Geometry Nodes modifier's inputs."""
    out = {"name": md.name, "type": md.type}
    for p in md.bl_rna.properties:
        if p.identifier in ("rna_type", "execution_time") or p.type == 'COLLECTION':
            continue
        v = getattr(md, p.identifier, None)
        out[p.identifier] = getattr(v, "name", None) if p.type == 'POINTER' else _plain(v)
    if md.type == 'NODES' and md.node_group is not None:
        compat = mod(".compat")
        out["inputs"] = {it.identifier: _plain(compat.gn_input_get(md, it.identifier))
                         for it in md.node_group.interface.items_tree
                         if getattr(it, "in_out", None) == 'INPUT'
                         and getattr(it, "socket_type", "") != 'NodeSocketGeometry'}
    return out


def edge_selection():
    o = ob()
    if o.mode == 'EDIT':
        return tuple(e.select for e in bmesh.from_edit_mesh(o.data).edges)
    return tuple(e.select for e in o.data.edges)


def state():
    """Mode, selection, edge / face shading flags, the modifier stack with every setting, the object's custom
    property and what the evaluated mesh shows."""
    o = ob()
    if o.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(o.data)
    else:
        bm = bmesh.new()
        bm.from_mesh(o.data)
    out = {"mode": bpy.context.mode,
           "edges": tuple(e.select for e in bm.edges),
           "verts": tuple(v.select for v in bm.verts),
           "faces": tuple(f.select for f in bm.faces),
           "soft": tuple(e.smooth for e in bm.edges),
           "face_smooth": tuple(f.smooth for f in bm.faces),
           "modifiers": [modifier(md) for md in o.modifiers],
           "session": o.get("session"),
           "shown": shown()}
    if o.mode != 'EDIT':
        bm.free()
    return out


def unit():
    return mod(".ui.toolbar_fit").unit(bpy.context.preferences.system.ui_scale,
                                       bpy.context.preferences.system.pixel_size)


def top_area():
    return mod(".ui.status_line")._top_bars.get(win().as_pointer())


def top_region():
    return next(r for r in top_area().regions if r.type == 'HEADER')


def button_point(label):
    """Centre of a Maya menu bar button (the kit's own layout model of the bar)."""
    sl = mod(".ui.status_line")
    ms = mod(".ui.menu_sets")
    names, _n = sl.shown_menus(win())
    labels = [getattr(bpy.types, ms.menu_idname(nm)).bl_label for nm in names]
    with bpy.context.temp_override(window=win()):
        widths, _f, _m = sl.menu_bar_widths(bpy.context, list(names), False)
    i = labels.index(label)
    r = top_region()
    left = r.x + int(oc().LEAD_UNITS * unit()) + sum(widths[:i])
    return left + widths[i] // 2, r.y + r.height // 2


def object_point():
    from bpy_extras import view3d_utils
    area, region = view3d()
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, ob().matrix_world.translation)
    return region.x + round(p.x), region.y + round(p.y)


def press_release(x, y):
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


SECTORS = {"N": (0, 1), "NE": (1, 1), "E": (1, 0), "SE": (1, -1), "S": (0, -1), "SW": (-1, -1), "W": (-1, 0),
           "NW": (-1, 1)}


def sector_point(s, key):
    """A window point that picks radial item ``key`` of the open (sub)menu by its direction, past the ring and on no
    other box (a radial submenu opens there): inside its own box when part of the box lies in its sector, else
    further out along the sector."""
    eng = mod(".marking.engine")
    lay, (cx, cy) = s.stack[-1]
    ox, oy = draw().ACTIVE["origin"]
    p = lay.params
    target = lay.radial[key]
    others = [it for it in lay.items if it is not target]

    def ok(dx, dy):
        return (math.hypot(dx, dy) >= p.radius + 2 and eng.direction(dx, dy, p.dead) == key
                and not any(eng._inside(it.rect, dx, dy) or (it.opt_rect and eng._inside(it.opt_rect, dx, dy))
                            for it in others))
    x0, y0, x1, y1 = target.rect
    cands = [(x, y) for x in range(int(x0) + 3, int(x1) - 2, 3) for y in range(int(y0) + 3, int(y1) - 2, 3)]
    sx, sy = SECTORS[key]
    n = math.hypot(sx, sy)
    cands += [(sx / n * d, sy / n * d) for d in range(int(p.radius) + 10, 300, 5)]
    for dx, dy in cands:
        if ok(dx, dy):
            return ox + round(cx + dx), oy + round(cy + dy)
    return None


def release_marking():
    """Release the held Shift+RMB on the picked item; without one, Esc closes the menu first (nothing runs)."""
    del C["calls"][:]
    at = C.pop("release", None)
    if at is None:
        for _ in range(2):
            ev('ESC', 'PRESS')
            ev('ESC', 'RELEASE')
        at = C["pt"]
    ev('RIGHTMOUSE', 'RELEASE', x=at[0], y=at[1], shift=True)


def vertical(e):
    a, b = e.verts
    return abs(a.co.x - b.co.x) < 1e-6 and abs(a.co.y - b.co.y) < 1e-6


def select_edges(pick):
    bpy.context.scene.tool_settings.mesh_select_mode = (False, True, False)
    bm = bmesh.from_edit_mesh(ob().data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    for e in bm.edges:
        if pick(e):
            e.select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob().data)
    return {e.index for e in bm.edges if e.select}


def _spy():
    cls = mod(".ui.menu_sets").ALLSET_OT_menu_item
    orig = cls.execute

    def execute(self, context):
        C["calls"].append(self.item)
        return orig(self, context)
    cls.execute = execute
    C["restore"] = (cls, orig)


@step
def s_setup():
    C["x"], C["y"] = setup()
    load_maya_layout()


@step
def s_build():
    bpy.ops.allset.keymap_activate()
    bpy.context.preferences.view.show_tooltips = False
    mod(".ui.status_line").redraw_top_bars()
    _spy()
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    with v3d_ctx():
        bpy.ops.allset.create(kind='CUBE')
        C["name"] = bpy.context.view_layer.objects.active.name
        bpy.ops.object.mode_set(mode='EDIT')
        select_edges(vertical)
        res = bpy.ops.allset.bevel(segments=2)
        bpy.ops.object.mode_set(mode='OBJECT')
        for o in bpy.context.view_layer.objects:
            o.select_set(o.name == C["name"])
        bpy.context.view_layer.objects.active = ob()
        bpy.ops.object.shade_auto_smooth()
        bpy.ops.view3d.view_selected()                    # the cube fills the view (screenshots)
        bpy.ops.ed.undo_push(message="history cube")      # Ctrl+Z later comes back here
    check(f"history cube: polyBevel1 ({res}) and Smooth by Angle ({sba()})", res == {'FINISHED'} and len(sba()) == 1)
    C["before"] = shown()
    hard, n = hard_count()
    check(f"before: {hard} of {n} edges shade hard", hard > 0)
    redraw()


@step
def s_shot_before():
    shot("gui_issue342_before.png")
    x, y = button_point("Mesh Display")
    C["bar"] = (x, y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_open_menu():
    press_release(*C["bar"])


step(lambda: None)
step(lambda: None)


@step
def s_menu_open():
    with bpy.context.temp_override(window=win(), area=None, region=None):
        left = oc().top_left(bpy.context, "Mesh Display")     # the menu's left edge (it drew from the menu bar)
    check(f"Mesh Display opened from the menu bar (menu left {left})", left is not None)
    if left is None:
        raise RuntimeError("Mesh Display menu not open")
    u = unit()
    C["probe"] = [int(left + 3 * u), top_region().y - int(1.2 * u)]
    C["probe_end"] = top_region().y - int(14 * u)
    ev('MOUSEMOVE', 'NOTHING', x=int(left + 2 * u), y=C["probe"][1])


def s_find_row():
    """Move down the menu one probe per tick until the item under the mouse is Mesh Display > Soften Edge."""
    if "row" not in C:
        C["row"] = None
    x, y = C["probe"]
    _path, cmd = sim.button_under_mouse(top_area(), top_region())
    if f'item="{ITEM}"' in cmd:      # the open menu's item under the mouse (Blender follows the bar button's menu)
        C["row"] = (x, y - int(unit() * 0.3))        # a little into the row (the probe enters it from the top)
        return
    if y < C["probe_end"]:
        return
    C["probe"][1] = y - max(2, int(unit() * 0.25))
    ev('MOUSEMOVE', 'NOTHING', x=x, y=C["probe"][1])
    sim._steps.insert(0, s_find_row)


step(s_find_row)


@step
def s_click_item():
    check(f"Soften Edge row found in the open menu ({C['row']})", C["row"] is not None)
    if C["row"] is None:
        raise RuntimeError("Soften Edge row not found")
    shot("gui_issue342_menu.png")
    del C["calls"][:]
    press_release(*C["row"])


@step
def s_wait_click():
    redraw()


@step
def s_menu_result():
    hard, n = hard_count()
    check(f"the click ran Mesh Display > Soften Edge ({C['calls']})", C["calls"] == [ITEM])
    check(f"after Soften Edge: {hard} of {n} edges shade hard (want 0)", n > 0 and hard == 0)
    check(f"the Smooth by Angle modifier gave way ({sba()})", not sba())
    shot("gui_issue342_soft.png")
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])


@step
def s_undo():
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_undone():
    redraw()
    ok = C["name"] in bpy.data.objects
    check(f"Ctrl+Z: Smooth by Angle is back ({ok and sba()})", ok and len(sba()) == 1)
    check("Ctrl+Z: every edge shades as before", ok and shown() == C["before"])
    shot("gui_issue342_undo.png")


# --- Shift+RMB > Soften/Harden Edges > Soften Edge on the object ---------------------------------------------------

@step
def s_mm_press():
    C["pt"] = object_point()
    ev('MOUSEMOVE', 'NOTHING', x=C["pt"][0], y=C["pt"][1])
    ev('RIGHTMOUSE', 'PRESS', x=C["pt"][0], y=C["pt"][1], shift=True)


@step
def s_mm_se():
    s = session()
    ok = s is not None and s.layout.radial.get("SE") is not None
    check(f"Shift+RMB on the object opens the object marking menu ({ok and s.layout.radial['SE'].label})", ok)
    at = sector_point(s, "SE") if ok else None
    if at is not None:
        ev('MOUSEMOVE', 'NOTHING', x=at[0], y=at[1], shift=True)


step(lambda: None)


@step
def s_mm_ne():
    s = session()
    ok = s is not None and len(s.stack) == 2 and s.layout.radial.get("NE") is not None
    check("dragging onto Soften/Harden Edges opens its submenu", ok)
    at = sector_point(s, "NE") if ok else None
    if at is not None:
        C["release"] = at
        ev('MOUSEMOVE', 'NOTHING', x=at[0], y=at[1], shift=True)


@step
def s_mm_release():
    shot("gui_issue342_marking.png")
    release_marking()


@step
def s_mm_result():
    redraw()
    hard, n = hard_count()
    check(f"the marking menu ran Mesh Display > Soften Edge ({C['calls']})", C["calls"] == [ITEM])
    check(f"after the marking menu's Soften Edge: {hard} of {n} edges shade hard (want 0)", n > 0 and hard == 0)
    check(f"... and Smooth by Angle gave way ({sba()})", not sba())
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


# --- edge mode: Shift+RMB > Soften/Harden Edges > Soften Edge on selected rim edges --------------------------------

@step
def s_edges():
    check(f"Ctrl+Z again: Smooth by Angle back ({sba()})", len(sba()) == 1 and shown() == C["before"])
    top = max(v.co.z for v in ob().data.vertices)
    with v3d_ctx():
        bpy.ops.object.editmode_toggle('EXEC_DEFAULT', True)          # Tab, with its undo step
        bpy.context.scene.tool_settings.mesh_select_mode = (False, True, False)
        C["entered"] = edge_selection()
        C["picked"] = select_edges(lambda e: all(abs(v.co.z - top) < 1e-6 for v in e.verts)
                                   and len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(80.0))
        bpy.ops.ed.undo_push(message="Select")                        # a selection is an undo step of its own
    ob()["session"] = 1        # a change in component mode that only object-mode undo steps hold
    ob().update_tag()
    check(f"edge mode with the top rim edges selected ({len(C['picked'])})", len(C["picked"]) == 12)
    C["edit_before"] = state()
    C["pt"] = object_point()
    ev('MOUSEMOVE', 'NOTHING', x=C["pt"][0], y=C["pt"][1])
    redraw()


@step
def s_edge_press():
    ev('RIGHTMOUSE', 'PRESS', x=C["pt"][0], y=C["pt"][1], shift=True)


@step
def s_edge_se():
    s = session()
    ok = s is not None and s.layout.radial.get("SE") is not None
    check(f"Shift+RMB on edges opens the edge marking menu ({ok and s.layout.radial['SE'].label})", ok)
    at = sector_point(s, "SE") if ok else None
    if at is not None:
        ev('MOUSEMOVE', 'NOTHING', x=at[0], y=at[1], shift=True)


step(lambda: None)


@step
def s_edge_ne():
    s = session()
    ok = s is not None and len(s.stack) == 2 and s.layout.radial.get("NE") is not None
    check("... its Soften/Harden Edges submenu opens", ok)
    at = sector_point(s, "NE") if ok else None
    if at is not None:
        C["release"] = at
        ev('MOUSEMOVE', 'NOTHING', x=at[0], y=at[1], shift=True)


@step
def s_edge_release():
    shot("gui_issue342_marking_edges.png")
    release_marking()


@step
def s_edge_result():
    check(f"the edge marking menu ran Mesh Display > Soften Edge ({C['calls']})", C["calls"] == [ITEM])
    check("still in component mode", bpy.context.mode == 'EDIT_MESH')
    C["edit_after"] = st = state()
    check(f"... the Smooth by Angle modifier gave way ({sba()}), same selection",
          not sba() and st["edges"] == C["edit_before"]["edges"])
    shot("gui_issue342_edges_edit.png")


# --- component mode: Ctrl+Z / Shift+Z take the whole Soften Edge, in component mode ---------------------------------

def press(shift, ctrl, label):
    def s_press():
        x, y = C["x"], C["y"]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('Z', 'PRESS', ctrl=ctrl, shift=shift)
        ev('Z', 'RELEASE', ctrl=ctrl, shift=shift)
        ev('LEFT_CTRL', 'RELEASE')           # simulated modifiers stay down otherwise
        ev('LEFT_SHIFT', 'RELEASE')
    s_press.__name__ = f"s_{label}"
    step(s_press)
    step(lambda: None)                         # the kit's extra step runs from a timer
    step(lambda: redraw())


def expect(label, want, text):
    def s_expect():
        got = state()
        diff = {k: (got[k], want()[k]) for k in got if got[k] != want()[k]}
        check(f"{text} ({sorted(diff)})", not diff)
        if label:
            shot(f"gui_issue342_{label}.png")
    step(s_expect)


press(False, True, "edit_undo1")
expect("edit_undo", lambda: C["edit_before"],
       "Ctrl+Z: component mode, the rim selected, the edges and Smooth by Angle as before (settings, place)")
press(True, False, "edit_redo1")
expect("edit_redo", lambda: C["edit_after"], "Shift+Z: the result again, in component mode")
press(False, True, "edit_undo2")
expect(None, lambda: C["edit_before"], "Ctrl+Z again: the state before")
press(False, True, "edit_undo3")


@step
def s_edit_undo3():
    st = state()
    check(f"the next Ctrl+Z takes back the selection, still in component mode ({st['mode']}, {sum(st['edges'])})",
          st["mode"] == 'EDIT_MESH' and st["edges"] == C["entered"] and len(sba()) == 1)


press(True, False, "edit_redo2")


@step
def s_edit_redo2():
    st = state()
    check("Shift+Z: the selection is back", st["mode"] == 'EDIT_MESH' and st["edges"] == C["edit_before"]["edges"])


press(True, False, "edit_redo3")
expect(None, lambda: C["edit_after"], "Shift+Z from the selection: the result, in component mode")


# --- Edit > Undo History: each line lands on what it names ----------------------------------------------------------

def undo_steps():
    """(name, active) of every undo step, oldest first (Blender prints them to the C stdout only)."""
    import ctypes
    import tempfile
    crt = ctypes.cdll.ucrtbase
    crt.fflush(None)
    sys.stdout.flush()
    fd, path = tempfile.mkstemp(suffix=".txt")
    saved = os.dup(1)
    try:
        os.dup2(fd, 1)
        bpy.context.window_manager.print_undo_steps()
        crt.fflush(None)
    finally:
        os.dup2(saved, 1)
        os.close(saved)
        os.close(fd)
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = [ln for ln in f.read().splitlines() if "name=" in ln]
    os.remove(path)
    return [(ln.split("name='", 1)[1].rstrip("'"), "*" in ln[:6]) for ln in lines]


@step
def s_history_lines():
    steps = undo_steps()
    active = next((i for i, s in enumerate(steps) if s[1]), None)
    names = [n for n, _a in steps[active - 2:active + 1]] if active is not None else []
    check(f"Undo History: the command's lines are Object Mode, Edit Mode, Soften Edge ({names})",
          names == ["Object Mode", "Edit Mode", "Soften Edge"])
    C["lines"] = (active - 2, active - 1, active) if active is not None else None


def history(index, label):
    def s_jump():
        if C.get("lines"):
            with bpy.context.temp_override(window=win()):
                bpy.ops.ed.undo_history('INVOKE_DEFAULT', item=C["lines"][index])
    s_jump.__name__ = f"s_{label}"
    step(s_jump)
    step(lambda: None)                         # the kit's extra step runs from a timer
    step(lambda: redraw())


history(0, "history_object_mode")


@step
def s_history_object_mode_check():
    want = {**C["edit_before"], "mode": 'OBJECT'}
    got = state()
    diff = sorted(k for k in got if got[k] != want[k])
    check(f"Undo History > Object Mode (from the result): the state before, in object mode ({diff})", not diff)
    shot("gui_issue342_history_object_mode.png")


history(1, "history_edit_mode")
expect(None, lambda: C["edit_before"], "Undo History > Edit Mode: the state before, in component mode")
history(2, "history_result")
expect("history_result", lambda: C["edit_after"], "Undo History > Soften Edge: the result, in component mode")


@step
def s_edge_object_mode():
    with v3d_ctx():
        bpy.ops.object.mode_set(mode='OBJECT')
    s = shown()
    picked = C["picked"]
    check("the selected rim edges shade soft", all(s.get(i) for i in picked))
    changed = [i for i in s if i not in picked and s[i] != C["before"].get(i)]
    check(f"the other edges look as before ({changed})", not changed)
    redraw()


@step
def s_end():
    shot("gui_issue342_edges.png")
    cls, orig = C["restore"]
    cls.execute = orig
    check("done", True)


run()
