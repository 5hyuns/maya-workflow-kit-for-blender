"""In a real UI (#525): the component and UV marking menus show their pictures, submenus too (Shift+RMB with a vertex /
an edge, its Merge submenu; the object menu's Booleans and Mapping lists; the UV Editor's UV menu with its Rotate,
Tools and Pinning submenus, the face menu) and the UV Toolkit's Pin / Unpin / Invert buttons
(screenshots)."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, screenshot, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
N = 4


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def draw():
    return mod(".marking.draw")


def session():
    return draw().ACTIVE.get("session")


def shot(name, window=None):
    if SHOTS:
        if window is None:
            screenshot(os.path.join(SHOTS, name))
        else:
            with bpy.context.temp_override(window=window):
                bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def uv_window():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.ui_type == 'UV':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


def uv_ev(type, value, x, y, **kw):
    down = sys.modules["sim"]._down
    if value == 'PRESS':
        down.add(type)
    elif value == 'RELEASE':
        down.discard(type)
    uv_window()[0].event_simulate(type=type, value=value, x=x, y=y, **kw)


def redraw_all():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def open_sub(label):
    """Open the submenu ``label`` of the open menu as the pointer would (a radial one in place, a list row's beside
    it) and redraw."""
    s = session()
    item = next((it for it in s.layout.items if it.label == label), None) if s else None
    check(f"{label} in the open menu", item is not None and item.sub is not None)
    if item is None:
        return
    if item.kind == "radial":
        at = (s.center[0] + (item.rect[0] + item.rect[2]) / 2, s.center[1] + (item.rect[1] + item.rect[3]) / 2)
        s._push(item, at)
    else:
        s._push(item, (s.center[0] + item.rect[2], s.center[1] + item.rect[3]), cascade=True)
    draw().redraw()


def back():
    s = session()
    if s is not None and len(s.stack) > 1:
        s._pop_to(len(s.stack) - 2)
    draw().redraw()


def pictured(labels):
    s = session()
    have = {it.label for lay, _c, _h in s.layers() for it in lay.items if it.icon} if s else set()
    missing = sorted(set(labels) - have)
    check(f"pictures on {sorted(labels)} (missing {missing})", not missing)


def cube():
    return bpy.data.objects["Cube"]


def select_component(kind):
    bpy.context.scene.tool_settings.mesh_select_mode = (kind == 'VERT', kind == 'EDGE', kind == 'FACE')
    b = bmesh.from_edit_mesh(cube().data)
    for el in (*b.verts, *b.edges, *b.faces):
        el.select = False
    seq = {"VERT": b.verts, "EDGE": b.edges, "FACE": b.faces}[kind]
    seq.ensure_lookup_table()
    seq[0].select_set(True)
    bmesh.update_edit_mesh(cube().data)


def press():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('LEFT_SHIFT', 'PRESS', x=C["x"], y=C["y"])
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"], shift=True)


def close():
    tap('ESC')
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"], y=C["y"], shift=True)
    ev('LEFT_SHIFT', 'RELEASE', x=C["x"], y=C["y"])


@step
def s_setup():
    C["x"], C["y"] = setup()
    tk = mod(".ui.uv_toolkit")
    original = tk._section

    def opened(layout, idname, label, default_closed=True):     # Pinning and Transform shown open
        return original(layout, idname, label,
                        default_closed=default_closed and idname not in ("ALLSET_uvtk_pin", "ALLSET_uvtk_transform"))
    tk._section = opened
    area, region = view3d()
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='EDIT')
    select_component('VERT')
    press()


@step
def s_vertex_shown():
    pass        # the first menu draws after the timer's next ticks


@step
def s_vertex():
    pictured({"Extrude Vertex", "Delete Vertex", "Paint Select Vertices"})
    shot("gui_issue525b_vertex.png")
    open_sub("Merge Vertices")


@step
def s_vertex_merge():
    pictured({"Merge Vertices", "Target Weld Tool"})
    shot("gui_issue525b_vertex_merge.png")
    close()


@step
def s_edge_press():
    select_component('EDGE')
    press()


@step
def s_edge():
    pictured({"Extrude Edge", "Delete Edge", "Paint Select Edges"})
    shot("gui_issue525b_edge.png")
    open_sub("Merge/Collapse Edges")


@step
def s_edge_merge():
    pictured({"Merge Border Edges", "Collapse Edge"})
    shot("gui_issue525b_edge_merge.png")
    close()


@step
def s_object_press():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='OBJECT')
    press()


@step
def s_object():
    pictured({"Unsmooth"})
    open_sub("Booleans")


@step
def s_booleans():
    pictured({"Difference (B - A)", "Slice", "Hole Punch", "Cut Out", "Split Edges"})
    shot("gui_issue525b_booleans.png")
    back()
    open_sub("Mapping")


@step
def s_mapping():
    pictured({"Camera-Based Map"})
    shot("gui_issue525b_mapping.png")
    close()


@step
def s_uv_open():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        for ob in list(bpy.data.objects):
            ob.select_set(False)
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=N, y_subdivisions=N, size=2.0)
        C["grid"] = bpy.context.active_object.name
        mod(".marking.modal").run_action(bpy.context, mod(".ui.menu_map").MAP["UV/UV Editor"])


@step
def s_wait_uv_window():
    import sim
    C["wait_uv"] = C.get("wait_uv", 0) + 1
    if uv_window()[1] is None and C["wait_uv"] < 15:
        sim._steps.insert(0, s_wait_uv_window)


@step
def s_uv_ready():
    w, a, r = uv_window()
    check("a UV Editor window", a is not None)
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
    a.spaces.active.show_region_ui = True
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (False, True, False)
    b = bmesh.from_edit_mesh(bpy.data.objects[C["grid"]].data)
    for el in (*b.verts, *b.edges, *b.faces):
        el.select = False
    b.edges.ensure_lookup_table()
    b.edges[len(b.edges) // 2].select_set(True)
    bmesh.update_edit_mesh(bpy.data.objects[C["grid"]].data)
    redraw_all()


@step
def s_toolkit():
    w, _a, _r = uv_window()
    shot("gui_issue525b_toolkit.png", w)        # Pinning: Pin / Unpin / Invert


def _uv_press():
    _w, _a, r = uv_window()
    C["uv"] = x, y = r.x + r.width // 3, r.y + r.height // 2
    uv_ev('MOUSEMOVE', 'NOTHING', x, y)
    uv_ev('LEFT_SHIFT', 'PRESS', x, y)
    uv_ev('RIGHTMOUSE', 'PRESS', x, y, shift=True)


def _uv_close():
    x, y = C["uv"]
    uv_ev('ESC', 'PRESS', x, y)
    uv_ev('ESC', 'RELEASE', x, y)
    uv_ev('RIGHTMOUSE', 'RELEASE', x, y, shift=True)
    uv_ev('LEFT_SHIFT', 'RELEASE', x, y)


@step
def s_uv_press():
    _uv_press()


@step
def s_uv_menu():
    s = session()
    name = getattr(s.stack[0][0].sub, "name", None) if s else None
    check(f"the UV menu ({name})", name == "SHIFT_UV")
    pictured({"Distribute", "Flip", "Map Border", "Symmetrize", "Measure Pixel Distance"})
    shot("gui_issue525b_uv.png", uv_window()[0])
    open_sub("Rotate UVs")


@step
def s_uv_rotate():
    pictured({"Rotate Clockwise", "Rotate Counterclockwise"})
    shot("gui_issue525b_uv_rotate.png", uv_window()[0])
    back()
    open_sub("Tools")


@step
def s_uv_tools():
    pictured({"Cut Tool", "Sew Tool", "Optimize Tool", "Unfold Tool", "Grab Tool", "Lattice Tool", "Pin Tool",
              "Pinch Tool", "Smear Tool", "Symmetrize Tool"})
    shot("gui_issue525b_uv_tools.png", uv_window()[0])
    back()
    open_sub("Pinning")


@step
def s_uv_pinning():
    pictured({"Pin Selection", "Inverse Pinning", "Unpin Selection", "Unpin All"})
    shot("gui_issue525b_uv_pinning.png", uv_window()[0])
    _uv_close()


@step
def s_uv_face_press():
    check("menu closed", not draw().ACTIVE)
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    b = bmesh.from_edit_mesh(bpy.data.objects[C["grid"]].data)
    for f in b.faces:
        f.select_set(True)
    bmesh.update_edit_mesh(bpy.data.objects[C["grid"]].data)
    _uv_press()


@step
def s_uv_face():
    s = session()
    name = getattr(s.stack[0][0].sub, "name", None) if s else None
    check(f"the UV face menu ({name})", name == "SHIFT_UV_FACE")
    pictured({"Cycle", "Flip", "Symmetrize"})
    shot("gui_issue525b_uv_face.png", uv_window()[0])
    _uv_close()


@step
def s_end():
    check("menu closed at the end", not draw().ACTIVE)


run()
