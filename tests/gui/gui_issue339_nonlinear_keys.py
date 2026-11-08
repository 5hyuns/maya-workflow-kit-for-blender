"""Issue #339 in a real UI: Deform > Nonlinear > Bend on a tall box; the handle is selected afterwards and bend1 is
expanded in its Channel Box INPUTS. RMB on Curvature's name > Key Selected (K) keys it at frame 1 (the row reads
keyed); at frame 10 type a Curvature and press S with the mouse over the Channel Box, at frame 20 type another and
press S over the viewport. Scrubbing the Time Slider plays the bend: Curvature follows its keys and the box bends with
it. Screenshots with ALLSET_GUI_SHOTS (or --shots)."""

import os
import re
import sys
from importlib import import_module

import bmesh
import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import (MODULE, check, dock_area, dock_region, ev, find_button, run, screenshot, scroll_channel_box,  # noqa: E402
                 setup, step, tap, view3d, win)

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
GUI_TIMEOUT = 300
KEY = "in:SIMPLE_DEFORM:0:maya:curvature"
LOW = "in:SIMPLE_DEFORM:0:maya:lowBound"


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def dock():
    return dock_area(), dock_region()


def cb():
    return import_module(MODULE + ".ui.channel_box")


def mesh():
    return bpy.data.objects[C["mesh"]]


def handle():
    return bpy.data.objects[C["handle"]]


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def bend():
    """How far the box's points moved from their rest place (0 = not bent)."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev_ob = mesh().evaluated_get(dg)
    me = ev_ob.to_mesh()
    d = max((v.co - C["rest"][i]).length for i, v in enumerate(me.vertices))
    ev_ob.to_mesh_clear()
    return d


def curve_keys(node, key):
    fc = cb().fcurve(node, key)
    return [(round(k.co.x), round(k.co.y, 5)) for k in fc.keyframe_points] if fc is not None else None


@step
def s_setup():
    setup()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        ob = bpy.context.view_layer.objects.active
        ob.name = "pCube1"
        ob.data.transform(Matrix.Diagonal((1.0, 1.0, 3.0, 1.0)))
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=5, use_grid_fill=True)
        bm.to_mesh(ob.data)
        bm.free()
        C["rest"] = [v.co.copy() for v in ob.data.vertices]
        res = bpy.ops.allset.menu_item('INVOKE_DEFAULT', item="Deform/Nonlinear/Bend")
    check(f"Deform > Nonlinear > Bend runs ({res})", res == {'FINISHED'})
    h = bpy.context.view_layer.objects.active
    check(f"the handle is selected afterwards ({h.name})", h.name == "bend1Handle" and "bend1" in ob.modifiers)
    C["mesh"], C["handle"] = ob.name, h.name
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 24
    sc.use_preview_range = False
    sc.frame_set(1)
    cb().set_selected_channels([])
    dock_area('CHANNEL_BOX')


@step
def s_wait():
    # a new lead starts with every node collapsed (Maya): expand bend1 once the lead has settled
    cb().set_open(handle(), cb().mod_node(mesh().modifiers["bend1"]))
    cb().rebuild_rows()
    redraw()


@step
def s_wait2():
    scroll_channel_box()       # INPUTS sit at the end of the Channel Box part
    redraw()


def _row_index(path, part):
    m = re.search(r"allset_cb\.rows\[(\d+)\]\." + part + "$", path or "")
    rows = bpy.context.scene.allset_cb.rows
    return int(m.group(1)) if m is not None and int(m.group(1)) < len(rows) else None


def _is_curvature(part):
    def match(path, _c=None):
        i = _row_index(path, part)
        return i is not None and bpy.context.scene.allset_cb.rows[i].name == "maya:curvature"
    return match


step(find_button(dock, _is_curvature("sel"), C, "name", x_frac=0.25, step_px=4))


@step
def s_hover():
    shot("gui_issue339_found.png")
    check(f"bend1's Curvature name is a channel button ({C.get('name')})", C.get("name") is not None)
    if not C.get("name"):
        raise RuntimeError("Curvature row not found")
    x, y = C["name"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_hover2():
    x, y = C["name"]
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)


@step
def s_rmb():
    ev('RIGHTMOUSE', 'PRESS')
    ev('RIGHTMOUSE', 'RELEASE')


@step
def s_menu():
    shot("gui_issue339_menu.png")
    sel = cb().selected_channels()
    check(f"RMB on Curvature selects its channel ({sel})", sel == [KEY])


@step
def s_pick():
    tap('K')      # Key Selected by its underlined letter (the menu may slide up)


@step
def s_picked():
    redraw()
    keys = curve_keys(handle(), KEY)
    fc = cb().fcurve(handle(), KEY)
    check(f"Channels > Key Selected keys Curvature at frame 1 ({keys}), on pCube1's bend1 "
          f"({fc.data_path if fc else None})", keys == [(1, 0.0)] and fc is not None
          and fc.data_path == 'modifiers["bend1"].angle')
    state = cb().channel_state(handle(), KEY)
    check(f"the Curvature row reads keyed ({state})", state == 'KEYED')
    check("only the selected channel: the handle's own channels stay unkeyed", handle().animation_data is None)
    cb().set_selected_channels([])


# --- frame 10: type, S over the Channel Box; frame 20: type, S over the viewport; scrub --------------------------

def timeline():
    for area in win().screen.areas:
        if area.type == 'DOPESHEET_EDITOR' and area.spaces.active.mode == 'TIMELINE':
            return area, next(r for r in area.regions if r.type == 'WINDOW')
    raise LookupError("no timeline")


def tx(frame):
    _area, r = timeline()
    x = r.view2d.view_to_region(frame, 0, clip=False)[0]
    return r.x + int(x), r.y + r.height // 2


def hover_view():
    _a, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


def type_text(text):
    ev('A', 'PRESS', ctrl=True)     # select the whole text, then type over it
    ev('A', 'RELEASE', ctrl=True)
    for ch in text:
        ev('TEXTINPUT', 'PRESS', unicode=ch)


@step
def s_range():
    area, r = timeline()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        bpy.ops.anim.scene_range_frame()
    redraw()


step(find_button(dock, _is_curvature("text"), C, "value", x_frac=0.72, step_px=4))


def goto(frame):
    def s_move():
        C["t"] = tx(frame)
        ev('MOUSEMOVE', 'NOTHING', x=C["t"][0], y=C["t"][1])

    def s_click():
        x, y = C["t"]
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)

    def s_at():
        sc = bpy.context.scene
        check(f"a click on the Time Slider goes to frame {frame} ({sc.frame_current})", sc.frame_current == frame)
        redraw()

    for fn in (s_move, s_click, s_at):
        step(fn)


def type_curvature(text, frame, where):
    """Steps: click Curvature's value field, type ``text``, Enter, then S with the mouse over the Channel Box
    (``where`` "cb") or over the viewport ("view")."""
    def s_click():
        check(f"Curvature's value field is found ({C.get('value')})", C.get("value") is not None)
        if not C.get("value"):
            raise RuntimeError("Curvature value field not found")
        x, y = C["value"]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)

    def s_press():
        x, y = C["value"]
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)

    def s_type():
        type_text(text)

    def s_enter():
        tap('RET')

    def s_typed():
        v = mesh().modifiers["bend1"].angle
        check(f"typing {text} at frame {frame} sets Curvature ({v:.3f}; the box bends {bend():.3f})",
              abs(v - float(text)) < 1e-5 and bend() > 0.01)
        if where == "view":
            hover_view()
        else:
            x, y = C["value"]       # the mouse stays over the Channel Box (the field, no longer typing)
            ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)

    def s_key():
        tap('S')

    def s_keyed():
        keys = curve_keys(handle(), KEY)
        over = "the viewport" if where == "view" else "the Channel Box"
        check(f"S over {over} keys the open bend1's Curvature at frame {frame} ({keys})",
              keys is not None and (frame, float(text)) in keys)
        low = curve_keys(handle(), LOW)
        check(f"... and its Low Bound ({low})", low is not None and frame in [f for f, _v in low])
        tx_keys = curve_keys(handle(), "tx") or []
        check(f"... and the handle's own channels, like S on a selection (Translate X keys {tx_keys})",
              frame in [f for f, _v in tx_keys])
        redraw()

    for fn in (s_click, s_press, s_type, s_enter, s_typed, s_key, s_keyed):
        step(fn)


goto(10)
type_curvature("1.5", 10, "cb")
goto(20)
type_curvature("0.5", 20, "view")

SCRUB = (1, 5, 10, 15, 20, 3, 1)


@step
def s_scrub_start():
    keys = curve_keys(handle(), KEY)
    check(f"Curvature's curve holds the three keys ({keys})", keys == [(1, 0.0), (10, 1.5), (20, 0.5)])
    C["scrub"] = [tx(f) for f in SCRUB]
    C["seen"] = []
    x, y = C["scrub"][0]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_scrub_press():
    x, y = C["scrub"][0]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


def scrub_to(i, frame):
    def s_move():
        x, y = C["scrub"][i]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        redraw()

    def s_check():
        sc = bpy.context.scene
        fc = cb().fcurve(handle(), KEY)
        want = fc.evaluate(sc.frame_current) if fc is not None else None
        v = mesh().modifiers["bend1"].angle
        row = next(r for r in bpy.context.scene.allset_cb.rows if r.name == "maya:curvature")
        b = bend()
        C["seen"].append((v, b))
        shot(f"gui_issue339_scrub_{i}_{frame}.png")
        check(f"scrubbing to frame {frame} ({sc.frame_current}): Curvature follows its keys ({v:.3f}, Channel Box "
              f"{row.text}, curve {want if want is None else round(want, 3)}) and the box bends {b:.3f}",
              sc.frame_current == frame and want is not None and abs(v - want) < 1e-5
              and abs(float(row.text) - want) < 1e-3 and ((b < 1e-4) == (abs(v) < 1e-6)))
        redraw()

    step(s_move)
    step(s_check)


for _i, _f in enumerate(SCRUB):
    if _i:
        scrub_to(_i, _f)


@step
def s_scrub_release():
    x, y = C["scrub"][-1]
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
    redraw()


@step
def s_scrub_done():
    seen = sorted(C["seen"])
    check(f"a larger Curvature bends the box more ({[(round(v, 3), round(b, 3)) for v, b in seen]})",
          all(b1 <= b2 + 1e-6 for (_v1, b1), (_v2, b2) in zip(seen, seen[1:])) and seen[-1][1] > seen[0][1] + 0.1)
    sc = bpy.context.scene
    check(f"the scrub ends at frame 1 ({sc.frame_current}) with the box straight ({bend():.4f})",
          sc.frame_current == 1 and bend() < 1e-4)


run()
