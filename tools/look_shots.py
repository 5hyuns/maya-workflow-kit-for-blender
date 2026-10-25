"""In-Blender part of tools/look_compare.py: Blender shots of the states research/maya/screens/ shows.

Runs in a GUI Blender (1600x900, --enable-event-simulate) on a clean sandbox config with the
extension installed and enabled. Shot names match the Maya shots (research/scripts/maya_shots/
shots.py) so look_compare.py can pair them. ``00_first_start`` is the layout before Maya mode
(what a new user sees). The kit ships no theme (step 130, #40): every shot is in Blender's factory theme.

Same scene as Maya (docs/steps/step_41.md): pCube1 1 cm at the origin (decision 8), pCube2/3 at
x = +-2 cm, Maya's persp view direction, Maya's focal length in screen pixels and the distance that
gives pCube1 the height it has in the Maya shot (look_data.CUBE_FITS). ``01_layout_empty`` keeps
the Maya layout file's own view (what the user gets; bundled startup.blend, step 130).

Besides the PNGs it writes ``geometry.json``: per shot the kit anchor rectangles (areas, regions,
top bar, status bar) and, for the fitted shots, pCube1's projected bounding box and the view's
pixel focal length.
"""

import json
import math
import os
import sys
from importlib import import_module
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests" / "gui"))
sys.path.insert(0, str(ROOT / "tools"))
import look_data as L  # noqa: E402
import sim  # noqa: E402
from sim import MODULE, check, ev, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ["ALLSET_LOOK_SHOTS"]
C = {}
GEOM = {"rects": {}, "cubes": {}}


# ---------------------------------------------------------------- geometry
def _img_rect(x, y, w, h):
    return [x, win().height - (y + h), w, h]


def anchor_rects():
    """Kit anchors in screenshot coordinates (origin top-left), see look_data."""
    rects = {}
    areas = list(win().screen.areas)
    outliners = sorted((a for a in areas if a.type == 'OUTLINER'), key=lambda a: a.x)
    names = {}
    toolbox = import_module(MODULE + ".ui.toolbox")
    dock = import_module(MODULE + ".ui.maya_dock")
    tool_dock = import_module(MODULE + ".ui.tool_dock")
    views = sorted((a for a in areas if a.type == 'VIEW_3D'), key=lambda a: -a.width * a.height)
    for a in areas:
        if a.type == 'IMAGE_EDITOR' and getattr(a.spaces.active.mask, "name", "") == ".AllsetStrip":
            names[a] = "strip"
        elif a.type == 'IMAGE_EDITOR' and getattr(a.spaces.active.mask, "name", "") == ".AllsetShelf":
            names[a] = "shelf"              # the Shelf row (step 49; header-less since step 113)
        elif a.type == 'VIEW_3D' and toolbox.is_toolbox(a.spaces.active):
            names[a] = "toolbox"            # the Tool Box column (step 49)
        elif a.type == 'VIEW_3D' and a == views[0]:
            names[a] = "view3d"
        elif a.type == 'DOPESHEET_EDITOR' and a.ui_type == 'TIMELINE':
            names[a] = "timeline"
        elif a.type == 'PROPERTIES' and dock.role(a) in ('STACK', 'CHANNEL_BOX'):
            names[a] = "dock"               # Channel Box / Layer Editor: its own area since step 116
        elif a.type == 'PROPERTIES' and tool_dock.is_dock(a):
            names[a] = "tooldock"           # Tool Settings (step 106)
        elif a.type == 'PROPERTIES':
            names[a] = "properties"
    if outliners:
        names[outliners[0]] = "outliner"
        for i, a in enumerate(outliners[1:]):
            names[a] = "outliner_right" if i == 0 else f"outliner_{i + 1}"
    for a, name in names.items():
        if name in rects:
            continue
        rects[name] = _img_rect(a.x, a.y, a.width, a.height)
        for r in a.regions:
            key = f"{name}.{r.type}"
            if r.width > 1 and r.height > 1 and key not in rects:
                rects[key] = _img_rect(r.x, r.y, r.width, r.height)
    # visible part of the main 3D view (sidebar / toolbar / headers excluded), for the view furniture (step 46)
    v3 = max((a for a in areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height, default=None)
    if v3 is not None:
        reg = next(r for r in v3.regions if r.type == 'WINDOW')
        x0, y0, x1, y1 = import_module(MODULE + ".operators.view").visible_bounds(v3, reg)
        rects["view3d.visible"] = _img_rect(reg.x + x0, reg.y + y0, x1 - x0, y1 - y0)
        # the viewport pane without a sidebar (= Maya MainPane; since step 116 the dock is its own area anyway)
        ui = next((r for r in v3.regions if r.type == 'UI' and r.width > 1), None)
        rects["view3d.pane"] = _img_rect(v3.x, v3.y, v3.width - (ui.width if ui else 0), v3.height)
    # Header-less shelf row (step 113): the kit draws the tab strip (top TAB_PX) and the icon row in one WINDOW region.
    s = bpy.context.preferences.system.ui_scale or 1.0
    shelf_mod = import_module(MODULE + ".ui.shelf")
    if "shelf.WINDOW" in rects and "shelf.HEADER" not in rects:
        x, y, w, h = rects["shelf.WINDOW"]
        th = round(shelf_mod.TAB_PX * s)
        rects["shelf.tabs"] = [x, y, w, th]
        rects["shelf.icons"] = [x, y + th, w, h - th]
    elif "shelf.HEADER" in rects:           # older layout: tab buttons in the header
        rects["shelf.tabs"] = rects["shelf.HEADER"]
        rects["shelf.icons"] = rects["shelf.WINDOW"]
    # the current frame's cell on the Time Slider ruler (step 202): it moves with the timeline view, so a fixed offset
    # from the region edge missed it at UI 1.25 (ui/time_slider.py _draw_ruler: cell = [f - 0.5, f + 0.5])
    tl = next((a for a in areas if names.get(a) == "timeline"), None)
    reg = next((r for r in tl.regions if r.type == 'WINDOW'), None) if tl is not None else None
    if reg is not None and reg.width > 1:
        cur = bpy.context.scene.frame_current
        x0 = reg.view2d.view_to_region(cur - 0.5, 0, clip=False)[0]
        x1 = reg.view2d.view_to_region(cur + 0.5, 0, clip=False)[0]
        rects["timeline.current"] = _img_rect(reg.x + round(x0), reg.y, max(1, round(x1) - round(x0)), reg.height)
    # editor gap between the Outliner and the viewport (Maya: the viewport frame line)
    if "outliner" in rects and "view3d" in rects:
        ox, oy, ow, oh = rects["outliner"]
        rects["gap.outliner_view"] = [ox + ow, oy, rects["view3d"][0] - (ox + ow), oh]
    tops = [_img_rect(a.x, a.y, a.width, a.height) for a in areas]
    top = min(r[1] for r in tops)
    bottom = max(r[1] + r[3] for r in tops)
    rects["topbar"] = [0, 0, win().width, top]
    rects["statusbar"] = [0, bottom, win().width, win().height - bottom]
    # Help Line | Command Line: rows of the status bar shared out by its width (command_line.units_for, step 161)
    cl = import_module(MODULE + ".command_line")
    unit = 20 * bpy.context.preferences.system.ui_scale
    help_u, cmd_u, _input_u = cl.units_for(win().width, bpy.context.preferences.system.ui_scale)
    help_w, cmd_w = help_u * unit, cmd_u * unit
    rects["statusbar.help"] = [0, bottom, help_w, win().height - bottom]
    rects["statusbar.command"] = [help_w, bottom, cmd_w, win().height - bottom]
    rects["window"] = [0, 0, win().width, win().height]
    return rects


def shot(name):
    sim.screenshot(os.path.join(SHOTS, name + ".png"))
    GEOM["rects"][name] = anchor_rects()


def record_press(name, x, y):
    """Anchor ``press`` = where the menu key/button went down (window coords -> screenshot)."""
    GEOM["rects"][name]["press"] = [x, win().height - y, 0, 0]


def record_cube(name, cube="pCube1"):
    """pCube1's projected bbox + the view's pixel focal length, from the last drawn matrices."""
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    ob = bpy.data.objects[cube]
    pts = [location_3d_to_region_2d(region, rv3d, ob.matrix_world @ Vector(c)) for c in ob.bound_box]
    xs = [region.x + p.x for p in pts]
    ys = [win().height - (region.y + p.y) for p in pts]
    GEOM["cubes"][name] = {"bbox": [min(xs), min(ys), max(xs), max(ys)],
                           "f_px": rv3d.window_matrix[0][0] * region.width / 2,
                           "lens": area.spaces.active.lens}


def record_grid(name):
    """Projected Maya grid points (step 45): points on minor / major / axis lines between crossings
    and the four corners (ui/maya_grid.py maths, the view's own matrices)."""
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    grid = import_module(MODULE + ".ui.maya_grid")
    unit = import_module(MODULE + ".operators.units").maya_unit()
    area, region = view3d()
    rv3d = area.spaces.active.region_3d

    def img(p):
        q = location_3d_to_region_2d(region, rv3d, Vector(p))
        return None if q is None else [region.x + q.x, win().height - (region.y + q.y)]

    pts = {}
    for kind, lines in grid.segments().items():
        out = []
        for (u0, v0), (u1, v1) in lines:
            for f in (0.104, 0.354, 0.604, 0.854):     # between the unit crossings
                u, v = u0 + (u1 - u0) * f, v0 + (v1 - v0) * f
                out.append(img(grid.PLANES["FLOOR"](u * unit, v * unit)))
        pts[f"grid.{kind}"] = out
    pts["grid.corners"] = [img(c) for c in grid.corners("FLOOR", unit)]
    pts["grid.centre"] = [img((0.0, 0.0, 0.0))]
    GEOM["grid_ms"] = grid.frame_ms()
    pts["grid.matrix"] = [[list(r) for r in rv3d.perspective_matrix], [region.x, region.y, region.width,
                                                                        region.height]]
    GEOM.setdefault("points", {})[name] = {k: ([p for p in v if p] if k != "grid.matrix" else v)
                                           for k, v in pts.items()}


def save_geometry():
    with open(os.path.join(SHOTS, "geometry.json"), "w", encoding="utf-8") as fh:
        json.dump(GEOM, fh, indent=1)


# ---------------------------------------------------------------- Maya camera
def maya_camera(shot_name, cube="pCube1"):
    """Maya persp direction + Maya pixel focal length; distance so ``cube`` is as tall on screen
    as in the Maya shot; view centred on the cube (Maya viewFit centres the fitted box)."""
    area, region = view3d()
    space = area.spaces.active
    rv3d = space.region_3d
    x0, y0, x1, y1 = L.maya_cube_bbox(shot_name)
    target_h = y1 - y0
    f_px = L.maya_f_px()
    # Blender viewport: tan(fov_h / 2) = 36 / lens on the wider side ($S-independent: C
    # BKE_camera_params_compute_viewplane, sensor 36 mm x zoom 2) -> f_px = width * lens / 72.
    space.lens = 72.0 * f_px / region.width
    rot = Vector(L.MAYA_EYE_BLENDER).normalized().to_track_quat('Z', 'Y')
    ob = bpy.data.objects[cube]
    corners = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    centre = sum(corners, Vector()) / 8
    inv = rot.inverted()

    def height(d):
        cam = centre + rot @ Vector((0.0, 0.0, d))
        ys = []
        for p in corners:
            c = inv @ (p - cam)
            ys.append(f_px * c.y / -c.z)
        return max(ys) - min(ys)

    lo, hi = 1e-4, 1e3
    for _ in range(80):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if height(mid) > target_h else (lo, mid)
    rv3d.view_perspective = 'PERSP'
    rv3d.view_rotation = rot
    rv3d.view_location = centre
    rv3d.view_distance = lo


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def v3d_override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region)


def park_mouse():
    """Mouse to an empty corner of the view: no tooltip, no gizmo highlight in the shots."""
    area, region = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 3, y=region.y + 30)


def centre():
    area, region = view3d()
    return region.x + region.width // 2, region.y + region.height // 2


def select_only(*names, active=None):
    bpy.ops.object.select_all(action='DESELECT')
    for n in names:
        bpy.data.objects[n].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[active or names[-1]]


# ---------------------------------------------------------------- steps
@step
def s_start():
    # First GUI start after a clean `install-file --enable` (docs/steps/step_42.md): the
    # welcome dialog is up (over Blender's splash). Shot, then one action: Return = its
    # "Make Blender Maya" button.
    import_module(MODULE + ".operators.keystate").is_down = lambda t: t in sim._down
    redraw()


@step
def s_first_start():
    shot("00_first_start")
    x, y = win().width // 2, win().height // 2
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('RET', 'PRESS')
    ev('RET', 'RELEASE')
    park_mouse()


@step
def s_wait():
    redraw()


@step
def s_wait2():
    # Step 130 (#40): no app template and no preference writes (Blender's splash stays Blender's). The Maya layout is
    # the bundled startup.blend read as a new untitled file (first_start.new_maya_scene).
    switch = import_module(MODULE + ".switch")
    check("one Return in the welcome dialog turns Maya mode on", switch.is_on())
    check("... and opens the Maya layout as a new untitled file",
          switch.is_maya_workspace(win().workspace) and not bpy.data.filepath)
    kc = bpy.context.window_manager.keyconfigs.active
    check(f"Maya keymap on (active keyconfig {kc.name if kc else None} unchanged, step 130)",
          kc is not None and import_module(MODULE + ".keymap").is_applied())
    # The template opened under the factory scale and the shot scale came after it: the header-only
    # Status Line row shrank and gave its pixels to the middle row. toolbox.fit_columns (0.5 s timer)
    # puts the shelf row back to 64 px, but screen.area_move polls False while the mouse is over a
    # region: hold the mouse on the shelf row's bottom edge (step 51).
    row = import_module(MODULE + ".ui.shelf").shelf_row_area(win().screen)
    if row is not None:
        # left end: no shelf icon there (mid-row, a shelf tooltip stayed up in the 1.25 shots, step 134)
        ev('MOUSEMOVE', 'NOTHING', x=row.x + 3, y=row.y - 1)
    redraw()


@step
def s_wait2b():
    redraw()


@step
def s_shelf_fit():
    row = import_module(MODULE + ".ui.shelf").shelf_row_area(win().screen)
    want = round(64 * bpy.context.preferences.system.ui_scale)
    check(f"shelf row {want} px after the fit (got {row.height if row else None})",
          row is not None and abs(row.height - want) <= 2)
    GEOM["ui_scale"] = bpy.context.preferences.system.ui_scale
    reg = next((r for r in row.regions if r.type == 'WINDOW'), None) if row else None
    if reg is not None:
        GEOM["shelf_icon"] = import_module(MODULE + ".ui.shelf").icon_rect(reg, 0, GEOM["ui_scale"])[2]
    park_mouse()
    redraw()


@step
def s_layout():
    shot("01_layout_empty")
    record_grid("01_layout_empty")
    with v3d_override():
        bpy.ops.allset.create(kind='CUBE')
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
    maya_camera("02_cube_selected_move")
    redraw()


@step
def s_wait3():
    redraw()


@step
def s_cube_sel():
    shot("02_cube_selected_move")
    record_cube("02_cube_selected_move")
    record_points("02_cube_selected_move")
    bpy.ops.object.select_all(action='DESELECT')
    redraw()


@step
def s_wait3b():
    redraw()


@step
def s_cube_unsel():
    shot("03_cube_unselected")
    k = import_module(MODULE + ".operators.units").maya_unit()
    with v3d_override():
        for name, x in (("pCube2", 2), ("pCube3", -2)):
            bpy.ops.allset.create(kind='CUBE')
            ob = bpy.context.active_object
            ob.location.x = x * k
            check(f"{name} named like Maya", ob.name == name)
    select_only("pCube2", "pCube1")          # Maya: select pCube2 pCube1 -> pCube1 lead
    view3d()[0].spaces.active.shading.type = 'WIREFRAME'
    maya_camera("04_wire_selected_lead")
    redraw()


@step
def s_wait4():
    redraw()


@step
def s_wire():
    shot("04_wire_selected_lead")
    record_cube("04_wire_selected_lead")
    record_points("04_wire_selected_lead")
    view3d()[0].spaces.active.shading.type = 'SOLID'
    # kit-only shot (step 47): the same view shaded, pCube1 lead + pCube2 selected -> selection wires
    # over shading (lead green, other white); Maya has no shaded shot with two selected.
    select_only("pCube2", "pCube1", active="pCube1")
    redraw()


@step
def s_wait4b():
    redraw()


@step
def s_two_selected():
    shot("02b_two_selected_shaded")
    record_points("02b_two_selected_shaded")
    select_only("pCube1")
    with v3d_override():     # without a 3D View context the tool didn't change (05/06 showed Move, step 59)
        bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
    redraw()


@step
def s_wait5():
    redraw()


@step
def s_rotate():
    shot("05_rotate_manip")
    with v3d_override():     # without a 3D View context the tool didn't change (05/06 showed Move, step 59)
        bpy.ops.wm.tool_set_by_id(name="builtin.scale")
    redraw()


@step
def s_wait6():
    redraw()


# Maya polyCube numbering (Y-up): vertex signs, edges as vertex pairs, faces by normal. Blender
# position of a Maya point (x, y, z) = (x, -z, y). Used to select the same components as the
# Maya shots (research/scripts/maya_shots/shots.py) whatever order the kit's mesh has.
MAYA_VTX = ((-1, -1, 1), (1, -1, 1), (-1, 1, 1), (1, 1, 1), (-1, 1, -1), (1, 1, -1), (-1, -1, -1), (1, -1, -1))
MAYA_EDGES = ((0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 7), (6, 0), (7, 1))
MAYA_FACE_NORMALS = ((0, 0, 1), (0, 1, 0), (0, 0, -1), (0, -1, 0), (1, 0, 0), (-1, 0, 0))


def _to_blender(v):
    x, y, z = v
    return (x, -z, y)


def _sign(v):
    return tuple((c > 0) - (c < 0) for c in v)


def maya_vertex(me, i):
    want = _to_blender(MAYA_VTX[i])
    return next(v for v in me.vertices if _sign(v.co) == want)


def maya_edge(me, i):
    pair = {maya_vertex(me, j).index for j in MAYA_EDGES[i]}
    return next(e for e in me.edges if set(e.vertices) == pair)


def maya_face(me, i):
    want = _to_blender(MAYA_FACE_NORMALS[i])
    return next(f for f in me.polygons if _sign(f.normal) == want)


def edit_select(mode, verts=(), edges=(), faces=()):
    """Select Maya's pCube1.vtx[..] / e[..] / f[..] (Maya numbers) in edit mode."""
    bpy.ops.object.mode_set(mode='OBJECT')
    me = bpy.data.objects["pCube1"].data
    keep_v = {maya_vertex(me, i).index for i in verts}
    keep_e = {maya_edge(me, i).index for i in edges}
    keep_f = {maya_face(me, i).index for i in faces}
    for seq, keep in ((me.vertices, keep_v), (me.edges, keep_e), (me.polygons, keep_f)):
        for el in seq:
            el.select = el.index in keep
    bpy.ops.object.mode_set(mode='EDIT')
    with v3d_override():
        bpy.ops.mesh.select_mode(type=mode)


def record_points(name, sel_verts=(), sel_edges=()):
    """Projected points the viewport pixel table samples around (look_data.VIEW_SAMPLES)."""
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    rv3d = area.spaces.active.region_3d

    def img(p):
        q = location_3d_to_region_2d(region, rv3d, p)
        return None if q is None else [region.x + q.x, win().height - (region.y + q.y)]

    pts = {}
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or not ob.name.startswith("pCube"):
            continue
        mw, me = ob.matrix_world, ob.data
        pts[f"{ob.name}.edges"] = [img(mw @ ((me.vertices[e.vertices[0]].co + me.vertices[e.vertices[1]].co) / 2))
                                   for e in me.edges]
        pts[f"{ob.name}.verts"] = [img(mw @ v.co) for v in me.vertices]
        pts[f"{ob.name}.origin"] = [img(mw.translation)]
    me, mw = bpy.data.objects["pCube1"].data, bpy.data.objects["pCube1"].matrix_world
    # Halfway between the top face centre and its back-left corner: the manipulator's Z line
    # crosses the centre on screen (step 43).
    top = maya_face(me, 1)
    corner = next(me.vertices[i].co for i in top.vertices
                  if me.vertices[i].co.x < 0 and me.vertices[i].co.y > 0)
    pts["pCube1.top_face"] = [img(mw @ ((top.center + corner) / 2))]
    pts["pCube1.sel_verts"] = [img(mw @ maya_vertex(me, i).co) for i in sel_verts]
    pts["pCube1.sel_edges"] = [img(mw @ ((me.vertices[e.vertices[0]].co + me.vertices[e.vertices[1]].co) / 2))
                               for e in (maya_edge(me, i) for i in sel_edges)]
    GEOM.setdefault("points", {})[name] = {k: [p for p in v if p] for k, v in pts.items()}


@step
def s_scale():
    shot("06_scale_manip")
    record_points("06_scale_manip")
    with v3d_override():
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
    edit_select('FACE', faces=(1, 4))        # Maya: pCube1.f[1], f[4]
    redraw()


@step
def s_wait7():
    redraw()


@step
def s_faces():
    shot("07_faces_selected")
    record_cube("07_faces_selected")
    record_points("07_faces_selected")
    edit_select('VERT', verts=(0, 1, 2))     # Maya: pCube1.vtx[0:2]
    redraw()


@step
def s_wait8():
    redraw()


@step
def s_verts():
    shot("08_verts_selected")
    record_points("08_verts_selected", sel_verts=(0, 1, 2))
    edit_select('EDGE', edges=(0, 5))        # Maya: pCube1.e[0], e[5]
    redraw()


@step
def s_wait9():
    redraw()


@step
def s_edges():
    shot("09_edges_selected")
    record_points("09_edges_selected", sel_edges=(0, 5))
    bpy.ops.object.mode_set(mode='OBJECT')
    select_only("pCube1")
    redraw()


@step
def s_wait10():
    redraw()


@step
def s_cb():
    shot("11_channel_box")
    # Maya opens Create from the menu bar: click the top bar's Create (global area: hover first)
    tb = GEOM["rects"]["11_channel_box"]["topbar"]
    x, y = sim.px(150), tb[1] + tb[3] // 2   # "Create" (x measured at scale 1.25; Maya density = 1.0)
    C["menu_xy"] = (x, win().height - y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=win().height - y)


@step
def s_menu_click():
    x, y = C["menu_xy"]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_wait11():
    pass


@step
def s_menu():
    shot("12_create_menu")
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')
    x, y = centre()
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('SPACE', 'PRESS')


@step
def s_wait12():
    redraw()


@step
def s_hotbox():
    shot("13_hotbox")
    record_press("13_hotbox", *centre())
    ev('SPACE', 'RELEASE')
    x, y = centre()                          # view centred on pCube1 (Maya: RMB over the cube)
    C["rmb"] = (x, y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('RIGHTMOUSE', 'PRESS', x=x, y=y)


@step
def s_wait13():
    redraw()


@step
def s_mm():
    shot("14_marking_menu_object")
    x, y = C["rmb"]
    record_press("14_marking_menu_object", x, y)
    # step 185: the drawn ring centre (step 184 draws the whole menu higher near the window bottom; the press stays)
    act = import_module(MODULE + ".marking.draw").ACTIVE
    sess = act.get("session")
    if sess is not None:
        ox, oy = act["origin"]
        GEOM["rects"]["14_marking_menu_object"]["mm_centre"] = [ox + sess.center[0], win().height - (oy + sess.center[1]),
                                                               0, 0]
    ev('RIGHTMOUSE', 'RELEASE', x=x, y=y)
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')
    park_mouse()
    with v3d_override():
        bpy.ops.screen.region_quadview()
    redraw()


@step
def s_wait14():
    redraw()


@step
def s_four():
    shot("16_four_view")
    with v3d_override():
        bpy.ops.screen.region_quadview()
    save_geometry()


run(interval=0.6, first=3.0)
