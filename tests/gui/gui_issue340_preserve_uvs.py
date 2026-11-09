"""Issue #340 in a real UI: Preserve UVs and Transform Constraint Edge keep the UV layout in place.

UV Editing layout, a Maya sphere with a patch of side faces selected, Preserve UVs on:
- a released Scale tool drag on the centre handle gives the same UVs as one plain resize by the same amount;
- a Scale drag cancelled with RMB puts the faces back with fresh normals, and the Move drag on the X arrow after it
  gives the same UVs as one plain move (Blender's UV correction projects through the face normals);
- Transform Constraint Edge, one vertex, MMB drag: with Preserve UVs off the vertex slides and the UVs stay; with
  Preserve UVs on the slid vertex's UVs follow a little (no jump to (0, 0) or far away), the other UVs stay, and the
  UVs equal one plain vertex slide by the same amount;
- the UV Editor's Move tool, both options on: the U arrow drag moves only the selected UVs, along U, and no vertex.
"""

import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_location_3d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, load_maya_layout, scale, win, screenshot  # noqa: E402

GUI_TIMEOUT = 300
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
STEPS = 8
TOL = 1e-4


def mod(name):
    return import_module(MODULE + "." + name)


def view3d():
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def v3d_override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def uv_area():
    for a in win().screen.areas:
        if a.type == 'IMAGE_EDITOR' and a.ui_type == 'UV':
            return a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None


def ob():
    return bpy.data.objects["pSphere1"]


def state():
    bm = bmesh.from_edit_mesh(ob().data)
    uv = bm.loops.layers.uv.active
    return ([v.co.copy() for v in bm.verts],
            [(l.vert.index, l[uv].uv.copy()) for f in bm.faces for l in f.loops])


def put(st):
    """Back to ``st`` with fresh normals."""
    bm = bmesh.from_edit_mesh(ob().data)
    uv = bm.loops.layers.uv.active
    for v, co in zip(bm.verts, st[0]):
        v.co = co
    for l, (_i, u) in zip((l for f in bm.faces for l in f.loops), st[1]):
        l[uv].uv = u
    bm.normal_update()
    bmesh.update_edit_mesh(ob().data)


def uv_gap(a, b, skip=()):
    return max(((p[1] - q[1]).length for p, q in zip(a[1], b[1]) if p[0] not in skip), default=0.0)


def co_gap(a, b):
    return max((p - q).length for p, q in zip(a[0], b[0]))


def stale():
    bm = bmesh.from_edit_mesh(ob().data)
    fresh = bm.copy()
    fresh.normal_update()
    gap = max(max((a.normal - b.normal).length for a, b in zip(bm.faces, fresh.faces)),
              max((a.normal - b.normal).length for a, b in zip(bm.verts, fresh.verts)))
    fresh.free()
    return gap


def replay(before, after, idname):
    """UV gap between the GUI result ``after`` and the last registered ``idname`` run once from ``before`` (fresh
    normals) with the same settings. Leaves the mesh at ``after``."""
    ops = bpy.context.window_manager.operators
    op = ops[-1] if len(ops) else None
    if op is None or op.bl_idname != idname:
        put(after)
        return None, op and op.bl_idname
    props = op.properties
    kw = {k: getattr(props, k) for k in props.bl_rna.properties.keys()
          if k != "rna_type" and props.is_property_set(k)}
    for k in ("release_confirm", "use_accurate"):
        kw.pop(k, None)
    for k, v in list(kw.items()):
        if hasattr(v, "to_tuple") or hasattr(v, "__len__") and not isinstance(v, str):
            try:
                kw[k] = tuple(tuple(r) for r in v) if hasattr(v[0], "__len__") else tuple(v)
            except TypeError:
                pass
    put(before)
    with v3d_override():
        getattr(bpy.ops.transform, idname.split("_OT_")[1])(**kw)
    ref = state()
    put(after)
    return uv_gap(after, ref), co_gap(after, ref)


def px_world(at):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, at)
    w = region_2d_to_location_3d(region, region.data, p + Vector((1, 0)), at)
    return (w - at).length


def screen(world):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, world)
    return Vector((region.x + p.x, region.y + p.y))


def centre():
    with v3d_override():
        return mod("ui.manipulator").pivot_frame(bpy.context, 'TRANSLATE')[0]


def arrow_point(axis, frac):
    c = centre()
    length = (mod("ui.manipulator").ARROW_PX * bpy.context.preferences.view.gizmo_size / 75.0 * scale()
              * mod("ui.manipulator").SIZE[0])
    return screen(c + Vector(axis) * length * frac * px_world(c))


def set_tool(name):
    with v3d_override():
        bpy.ops.wm.tool_set_by_id(name=name)


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def add(fn, name):
    fn.__name__ = name
    step(fn)


def pauses(tag, n=3):
    for i in range(n):      # a press soon after the last one would be a double click
        add(lambda: None, f"s_{tag}_pause{i}")


def drag(tag, button, start, delta, cancel=False):
    """Steps: hover ``start()``, press, move by ``delta`` (first stretch in its own tick), release (RMB first when
    ``cancel``). C[tag] = {"p": press point, "before": state at the press, "after": state after the release}."""
    box = C.setdefault(tag, {})
    pauses(tag)

    def hover():
        box["p"] = p = start()
        ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))
        ev('MOUSEMOVE', 'NOTHING', x=int(p.x) + 1, y=int(p.y))
        ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))

    def press():
        box["before"] = state()
        ev(button, 'PRESS', x=int(box["p"].x), y=int(box["p"].y))

    def first():
        q = box["p"] + delta / STEPS
        ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y))

    def rest():
        box["modal"] = [o.bl_idname for o in win().modal_operators]
        for i in range(2, STEPS + 1):
            q = box["p"] + delta * (i / STEPS)
            ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y))

    def release():
        shot(f"gui_issue340_{tag}.png")
        q = box["p"] + delta
        if cancel:
            ev('RIGHTMOUSE', 'PRESS', x=int(q.x), y=int(q.y))
            ev('RIGHTMOUSE', 'RELEASE', x=int(q.x), y=int(q.y))
        ev(button, 'RELEASE', x=int(q.x), y=int(q.y))

    for fn, name in ((hover, "hover"), (press, "press"), (first, "first"), (rest, "rest"), (release, "release")):
        add(fn, f"s_{tag}_{name}")
    add(lambda: box.update(after=state()), f"s_{tag}_settle")
    return box


# --- UV Editing layout, a Maya sphere, side faces, Preserve UVs on ------------------------------------------

@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_workspace():
    C["ws"] = mod("switch").append_workspace(win(), "UV Editing")
    check("UV Editing workspace", C["ws"] is not None)


@step
def s_wait_ws():
    pass


@step
def s_sphere():
    with v3d_override():
        bpy.ops.allset.create(kind='SPHERE')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(ob().data)
    r = max(v.co.length for v in bm.verts)
    # side faces facing the persp camera
    cam = ob().matrix_world.inverted() @ view3d()[1].data.view_matrix.inverted().translation
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot((cam - c).normalized()) > 0.85 and abs(c.z) < 0.6 * r:
            f.select_set(True)
    bm.select_flush_mode()
    mod("compat").uv_sync_from_mesh(bm)
    bmesh.update_edit_mesh(ob().data)
    C["faces"] = sum(f.select for f in bm.faces)
    check(f"a patch of faces selected ({C['faces']})", 0 < C["faces"] < 30)
    with v3d_override():
        bpy.ops.view3d.view_selected()
    ts = bpy.context.scene.tool_settings
    ts.use_transform_correct_face_attributes = True
    ts.use_proportional_edit = False
    mod("preferences").get(bpy.context).transform_constraint = 'NONE'
    a, r = uv_area()
    with bpy.context.temp_override(window=win(), area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)


@step
def s_scale_tool():
    set_tool("builtin.scale")
    view3d()[0].tag_redraw()


@step
def s_scale_tool_check():
    tool = C["ws"].tools.from_space_view3d_mode('EDIT_MESH', create=False)
    check(f"Scale tool with the kit manipulator ({tool and (tool.idname, tool.widget)})",
          tool is not None and tool.idname == "builtin.scale" and tool.widget == "ALLSET_GGT_xform")


# --- Scale tool: a released drag, then a cancelled one -------------------------------------------------------

scaled = drag("scale", 'LEFTMOUSE', lambda: screen(centre()), Vector((45, 6)))


@step
def s_scale_check():
    b = C["scale"]
    check(f"the Scale drag ran the kit's scale ({b.get('modal')})", "ALLSET_OT_manip_scale" in (b.get("modal") or []))
    check(f"the faces were scaled ({co_gap(b['before'], b['after']):.5f})", co_gap(b["before"], b["after"]) > 1e-4)
    gap, cgap = replay(b["before"], b["after"], "TRANSFORM_OT_resize")
    check(f"released Scale drag with Preserve UVs: the UVs of one plain resize (UV gap {gap}, geometry gap {cgap})",
          gap is not None and gap < TOL and cgap < 1e-5)


cancelled = drag("scale_cancel", 'LEFTMOUSE', lambda: screen(centre()), Vector((60, -4)), cancel=True)


@step
def s_cancel_check():
    b = C["scale_cancel"]
    check(f"RMB cancels the Scale drag: the faces are back ({co_gap(b['before'], b['after']):.2e})",
          co_gap(b["before"], b["after"]) < 1e-6)
    check(f"... with fresh normals (stale by {stale():.4f})", stale() < 1e-4)
    set_tool("builtin.move")
    view3d()[0].tag_redraw()


@step
def s_move_tool_check():
    tool = C["ws"].tools.from_space_view3d_mode('EDIT_MESH', create=False)
    check(f"Move tool ({tool and tool.idname})", tool is not None and tool.idname == "builtin.move")


# --- Move tool: X arrow with Preserve UVs ---------------------------------------------------------------------

moved = drag("move", 'LEFTMOUSE', lambda: arrow_point((1, 0, 0), 0.6), Vector((50, 8)))


@step
def s_move_check():
    b = C["move"]
    check(f"the X arrow drag moved the faces ({co_gap(b['before'], b['after']):.5f})",
          co_gap(b["before"], b["after"]) > 1e-4)
    gap, cgap = replay(b["before"], b["after"], "TRANSFORM_OT_translate")
    check(f"Move with Preserve UVs after the cancelled Scale drag: the UVs of one plain move (UV gap {gap}, "
          f"geometry gap {cgap})", gap is not None and gap < TOL and cgap < 1e-5)


# --- Transform Constraint Edge, one vertex, MMB drag ---------------------------------------------------------

def pick_vertex():
    with v3d_override():
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(ob().data)
    cam = ob().matrix_world.inverted() @ view3d()[1].data.view_matrix.inverted().translation
    v = max((v for v in bm.verts if len(v.link_edges) == 4), key=lambda v: v.normal.dot((cam - v.co).normalized()))
    v.select_set(True)
    bm.select_history.add(v)
    bm.select_flush_mode()
    mod("compat").uv_sync_from_mesh(bm)
    bmesh.update_edit_mesh(ob().data)
    C["vi"] = v.index


def edge_on(preserve):
    def fn():
        bpy.context.scene.tool_settings.use_transform_correct_face_attributes = preserve
        mod("preferences").get(bpy.context).transform_constraint = 'EDGE'
        view3d()[0].tag_redraw()
    return fn


add(pick_vertex, "s_pick_vertex")
add(edge_on(False), "s_edge_off")


def near_vertex():
    # slides follow the mouse from the vertex: start a little off it on screen
    return screen(ob().matrix_world @ bmesh.from_edit_mesh(ob().data).verts[C["vi"]].co) + Vector((-12, -12))


slide_off = drag("slide_off", 'MIDDLEMOUSE', near_vertex, Vector((-40, -25)))


@step
def s_slide_off_check():
    b = C["slide_off"]
    vi = C["vi"]
    check(f"Edge constraint MMB drag slides ({b.get('modal')})",
          any(n in (b.get("modal") or []) for n in ("TRANSFORM_OT_vert_slide", "TRANSFORM_OT_edge_slide")))
    d = (b["after"][0][vi] - b["before"][0][vi]).length
    check(f"... the vertex slid ({d:.5f})", d > 1e-5)
    gap = uv_gap(b["before"], b["after"])
    check(f"Preserve UVs off: the UVs stay ({gap:.6f})", gap < 1e-7)
    put(b["before"])


add(edge_on(True), "s_edge_on")
slide_on = drag("slide_on", 'MIDDLEMOUSE', near_vertex, Vector((-40, -25)))


@step
def s_slide_on_check():
    b = C["slide_on"]
    vi = C["vi"]
    d = (b["after"][0][vi] - b["before"][0][vi]).length
    mine, other = uv_gap(b["before"], b["after"]), uv_gap(b["before"], b["after"], skip={vi})
    check(f"Preserve UVs on: the vertex slid ({d:.5f}) and its UVs follow a little ({mine:.5f}, no jump), "
          f"no other UV moves ({other:.2e})", d > 1e-5 and 1e-5 < mine < 0.05 and other < 1e-7)
    gap, cgap = replay(b["before"], b["after"], "TRANSFORM_OT_vert_slide")
    check(f"... the UVs of one plain vertex slide (UV gap {gap}, geometry gap {cgap})",
          gap is not None and gap < TOL and cgap < 1e-5)


# --- UV Editor Move tool, both options on ----------------------------------------------------------------------

@step
def s_uv_tool():
    a, r = uv_area()
    with bpy.context.temp_override(window=win(), area=a, region=r):
        bpy.ops.wm.tool_set_by_id(name="builtin.move", space_type='IMAGE_EDITOR')
    a.tag_redraw()


@step
def s_uv_wait():
    uv_area()[0].tag_redraw()


def uv_arrow():
    um = mod("ui.uv_manipulator")
    a, r = uv_area()
    with bpy.context.temp_override(window=win(), area=a, region=r):
        b = um.selected_uv_bounds(bpy.context)
        cx, cy = um.center_px(bpy.context, b)
        length = um.length_px(bpy.context)
    C["uv_bounds"] = b
    return Vector((r.x + cx + 0.6 * length, r.y + cy))


uv_drag = drag("uv", 'LEFTMOUSE', uv_arrow, Vector((40, 12)))


@step
def s_uv_check():
    b = C["uv"]
    vi = C["vi"]
    ts = bpy.context.scene.tool_settings
    check("both options on", ts.use_transform_correct_face_attributes
          and mod("preferences").get(bpy.context).transform_constraint == 'EDGE')
    check(f"the UV manipulator sat on the vertex's UVs ({C.get('uv_bounds')})", C.get("uv_bounds") is not None)
    du = [q[1] - p[1] for p, q in zip(b["before"][1], b["after"][1]) if p[0] == vi]
    other = uv_gap(b["before"], b["after"], skip={vi})
    check(f"the U arrow moves the selected UVs along U ({du[0].x:.4f}, {du[0].y:.6f})",
          du[0].x > 1e-3 and all((d - du[0]).length < 1e-6 for d in du) and abs(du[0].y) < 1e-6)
    check(f"... and no other UV ({other:.2e})", other < 1e-7)
    check(f"... and no vertex ({co_gap(b['before'], b['after']):.2e})", co_gap(b["before"], b["after"]) < 1e-7)


run()
