"""#422 in a real UI: Ctrl+1 (Isolate Select) on two of three cubes, then selection inside the isolated view works
like Maya: a click, Shift+click and a marquee pick the isolated objects (never the hidden one); in face mode a click and
a marquee pick the isolated object's faces; Ctrl+1 entered from face mode, or after RMB > Face on an unselected
object, keeps face selection working; a hidden object in front of the isolated one doesn't block a click (objects or
faces), also with the Move tool, in wireframe and with X-ray; z keeps Isolate Select. ALLSET_422_LAYOUT=maya runs the
same in the Maya layout. Screenshots with ALLSET_GUI_SHOTS (or --shots)."""

import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
MAYA_LAYOUT = os.environ.get("ALLSET_422_LAYOUT", "") == "maya"
C = {"u": 1.0}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def key(k, **mods):
    ev(k, 'PRESS', **mods)
    ev(k, 'RELEASE', **mods)


SECTORS = {"N": (0, 1), "NE": (1, 1), "E": (1, 0), "SE": (1, -1), "S": (0, -1), "SW": (-1, -1), "W": (-1, 0),
           "NW": (-1, 1)}


def mod(name):
    return import_module(MODULE + name)


def sector_point(key):
    """A point inside the open marking menu's ``key`` sector item, clear of the other items."""
    draw, eng = mod(".marking.draw"), mod(".marking.engine")
    s = draw.ACTIVE.get("session")
    if s is None or s.layout.radial.get(key) is None:
        return None
    lay, (cx, cy) = s.stack[-1]
    ox, oy = draw.ACTIVE["origin"]
    p = lay.params
    item = lay.radial[key]
    others = [it for it in lay.items if it is not item]

    def ok(dx, dy):
        return (math.hypot(dx, dy) >= p.radius + 2 and eng.direction(dx, dy, p.dead) == key
                and not any(eng._inside(it.rect, dx, dy) or (it.opt_rect and eng._inside(it.opt_rect, dx, dy))
                            for it in others))
    x0, y0, x1, y1 = item.rect
    cands = [(x, y) for x in range(int(x0) + 3, int(x1) - 2, 3) for y in range(int(y0) + 3, int(y1) - 2, 3)]
    sx, sy = SECTORS[key]
    n = math.hypot(sx, sy)
    cands += [(sx / n * d, sy / n * d) for d in range(int(p.radius) + 10, 300, 5)]
    for dx, dy in cands:
        if ok(dx, dy):
            return ox + round(cx + dx), oy + round(cy + dy)
    return None


def ctrl_one():
    """Ctrl+1 with the Ctrl key itself pressed and released (a modifier flag alone stays held in the window)."""
    ev('LEFT_CTRL', 'PRESS')
    key('ONE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


def screen_xy(co):
    area, region = view3d()
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, Vector(co) * C["u"])
    return region.x + int(round(p.x)), region.y + int(round(p.y))


def click(xy, **mods):
    ev('MOUSEMOVE', 'NOTHING', x=xy[0], y=xy[1])
    ev('LEFTMOUSE', 'PRESS', x=xy[0], y=xy[1], **mods)
    ev('LEFTMOUSE', 'RELEASE', x=xy[0], y=xy[1], **mods)


def drag(a, b):
    ev('MOUSEMOVE', 'NOTHING', x=a[0], y=a[1])
    ev('LEFTMOUSE', 'PRESS', x=a[0], y=a[1])
    n = 8
    for i in range(1, n + 1):
        ev('MOUSEMOVE', 'NOTHING', x=a[0] + (b[0] - a[0]) * i // n, y=a[1] + (b[1] - a[1]) * i // n)
    ev('LEFTMOUSE', 'RELEASE', x=b[0], y=b[1])


def rel(fx, fy):
    _a, r = view3d()
    return r.x + int(r.width * fx), r.y + int(r.height * fy)


def selected():
    return sorted(o.name for o in bpy.context.scene.objects if o.select_get() and o.type == 'MESH')


def picked_faces():
    ob = bpy.context.edit_object
    if ob is None:
        return None
    bm = bmesh.from_edit_mesh(ob.data)
    return sorted(f.index for f in bm.faces if f.select)


def clear_faces():
    ob = bpy.context.edit_object
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(False)
    bm.select_flush(False)
    bmesh.update_edit_mesh(ob.data)


@step
def s_setup():
    setup()
    if MAYA_LAYOUT:
        load_maya_layout()


step(lambda: None)


@step
def s_scene():
    for ob in list(bpy.data.objects):
        if ob.type == 'MESH':
            bpy.data.objects.remove(ob)
    sc = bpy.context.scene
    C["u"] = u = import_module(MODULE + ".operators.units").maya_unit(sc)
    for name, x in (("pCube1", -3.0), ("pCube2", 0.0), ("pCube3", 3.0)):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2.0 * u)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        ob.location.x = x * u
        sc.collection.objects.link(ob)
    area, _region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'PERSP'
    rv3d.view_rotation = Euler((math.radians(70), 0, math.radians(20))).to_quaternion()
    rv3d.view_location = (0, 0, 0)
    rv3d.view_distance = 16.0 * u
    for o in sc.objects:
        o.select_set(o.name in ("pCube1", "pCube2"))
    bpy.context.view_layer.objects.active = sc.objects["pCube2"]
    C["mid"] = screen_xy((0, 0, 5))
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])


step(lambda: None)


@step
def s_base_marquee():
    C["sel"] = selected()
    drag(rel(0.05, 0.95), rel(0.95, 0.05))


step(lambda: None)


@step
def s_base_marquee_done():
    check(f"before Isolate Select a marquee over everything picks all three cubes ({selected()})",
          selected() == ["pCube1", "pCube2", "pCube3"])
    for o in bpy.context.scene.objects:
        o.select_set(o.name in C["sel"])
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])


step(lambda: None)


@step
def s_isolate():
    ctrl_one()


step(lambda: None)


@step
def s_isolated():
    area, _r = view3d()
    space = area.spaces.active
    check(f"Ctrl+1 = local view ({space.local_view is not None})", space.local_view is not None)
    shot("gui_issue422_isolated.png")
    for o in bpy.context.scene.objects:
        o.select_set(False)


step(lambda: None)


@step
def s_iso_marquee_first():
    drag(rel(0.05, 0.95), rel(0.95, 0.05))


step(lambda: None)


@step
def s_iso_marquee_first_done():
    check(f"right after Ctrl+1 a marquee over everything picks the two isolated cubes ({selected()})",
          selected() == ["pCube1", "pCube2"])
    click(screen_xy((0, 0, 1)))        # top face of pCube2


step(lambda: None)


@step
def s_click_obj():
    check(f"a click on pCube2 selects it ({selected()})", selected() == ["pCube2"])
    click(screen_xy((-3, 0, 1)), shift=True)


step(lambda: None)


@step
def s_shift_click():
    check(f"shift+click adds pCube1 ({selected()})", selected() == ["pCube1", "pCube2"])
    click(rel(0.1, 0.9))                # empty space: deselect


step(lambda: None)


@step
def s_empty():
    check(f"a click on empty space clears the selection ({selected()})", selected() == [])


step(lambda: None)
step(lambda: None)


@step
def s_marquee_drag():
    a, b = rel(0.05, 0.95), rel(0.95, 0.05)
    ev('MOUSEMOVE', 'NOTHING', x=a[0], y=a[1])
    ev('LEFTMOUSE', 'PRESS', x=a[0], y=a[1])
    n = 8
    for i in range(1, n + 1):
        ev('MOUSEMOVE', 'NOTHING', x=a[0] + (b[0] - a[0]) * i // n, y=a[1] + (b[1] - a[1]) * i // n)


@step
def s_marquee_mid():
    b = rel(0.95, 0.05)
    ev('LEFTMOUSE', 'RELEASE', x=b[0], y=b[1])


step(lambda: None)


@step
def s_marquee():
    check(f"a marquee over everything picks the two isolated cubes, not the hidden one ({selected()})",
          selected() == ["pCube1", "pCube2"])
    shot("gui_issue422_marquee.png")
    click(screen_xy((0, 0, 1)))
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])


step(lambda: None)


@step
def s_face_mode():
    key('F11')


step(lambda: None)


@step
def s_face_mode_on():
    ob = bpy.context.edit_object
    check(f"F11 = face mode on pCube2 ({ob and ob.name}, {tuple(bpy.context.scene.tool_settings.mesh_select_mode)})",
          ob is not None and tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, False, True))
    if ob is not None:
        clear_faces()
    click(screen_xy((0, 0, 1)))


step(lambda: None)


@step
def s_face_click():
    f = picked_faces()
    check(f"a click on the top face selects one face ({f})", f is not None and len(f) == 1)
    shot("gui_issue422_face_click.png")
    a, b = screen_xy((-1.2, -1.2, 1.2)), screen_xy((1.2, 1.2, -1.2))
    drag((min(a[0], b[0]) - 30, max(a[1], b[1]) + 30), (max(a[0], b[0]) + 30, min(a[1], b[1]) - 30))


step(lambda: None)


@step
def s_face_marquee():
    f = picked_faces()
    check(f"a marquee over the cube selects its front faces ({f})", f is not None and len(f) >= 3)
    shot("gui_issue422_face_marquee.png")
    ctrl_one()                          # leave Isolate Select in face mode


step(lambda: None)


@step
def s_left_in_face_mode():
    area, _r = view3d()
    check(f"Ctrl+1 in face mode leaves Isolate Select ({area.spaces.active.local_view is None}, {bpy.context.mode})",
          area.spaces.active.local_view is None and bpy.context.mode == 'EDIT_MESH')
    clear_faces()
    ob = bpy.context.edit_object
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(f.normal.z > 0.5 or f.normal.x < -0.5)    # top and -X faces
    bm.select_flush(True)
    bmesh.update_edit_mesh(ob.data)
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])
    ctrl_one()                          # Isolate Select entered from face mode


step(lambda: None)


@step
def s_iso_from_faces():
    area, _r = view3d()
    space = area.spaces.active
    check(f"Ctrl+1 in face mode = Isolate Select, still in face mode ({space.local_view is not None}, "
          f"{bpy.context.mode})", space.local_view is not None and bpy.context.mode == 'EDIT_MESH')
    shot("gui_issue422_iso_faces.png")
    clear_faces()
    click(screen_xy((0, 0, 1)))


step(lambda: None)


@step
def s_iso_faces_click():
    f = picked_faces()
    check(f"... a click on the top face selects it ({f})", f is not None and len(f) == 1)
    shot("gui_issue422_iso_faces_click.png")


step(lambda: None)
step(lambda: None)


@step
def s_iso_faces_marquee():
    drag(rel(0.05, 0.95), rel(0.95, 0.05))


step(lambda: None)


@step
def s_iso_faces_marquee_done():
    f = picked_faces()
    check(f"... a marquee picks faces ({f})", f is not None and len(f) >= 2)
    shot("gui_issue422_iso_faces_marquee.png")
    ctrl_one()


step(lambda: None)


@step
def s_to_object_mode():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.scene.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = None
    C["at"] = screen_xy((-3, 0, 1))                  # pCube1, not selected
    ev('MOUSEMOVE', 'NOTHING', x=C["at"][0], y=C["at"][1])
    ev('RIGHTMOUSE', 'PRESS', x=C["at"][0], y=C["at"][1])


step(lambda: None)


@step
def s_rmb_face():
    C["mm"] = sector_point("S") or C["at"]
    ev('MOUSEMOVE', 'NOTHING', x=C["mm"][0], y=C["mm"][1])


@step
def s_rmb_face_release():
    ev('RIGHTMOUSE', 'RELEASE', x=C["mm"][0], y=C["mm"][1])


step(lambda: None)


@step
def s_rmb_face_mode():
    ob = bpy.context.edit_object
    check(f"RMB > Face on pCube1 = its face mode ({ob and ob.name})", ob is not None and ob.name == "pCube1")
    click(screen_xy((-3, 0, 1)))


step(lambda: None)


@step
def s_rmb_face_pick():
    f = picked_faces()
    check(f"... a click picks its top face ({f})", f is not None and len(f) == 1)
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])
    ctrl_one()


step(lambda: None)


@step
def s_rmb_iso():
    area, _r = view3d()
    space = area.spaces.active
    check(f"Ctrl+1 on the face of pCube1 = Isolate Select ({space.local_view is not None})",
          space.local_view is not None)
    check("... pCube1 is shown in it", space.local_view is not None and bpy.data.objects["pCube1"].local_view_get(space))
    shot("gui_issue422_rmb_iso.png")
    clear_faces()
    click(screen_xy((-3, 0, 1)))


step(lambda: None)


@step
def s_rmb_iso_click():
    f = picked_faces()
    check(f"... a click picks a face of pCube1 ({f})", f is not None and len(f) == 1)


step(lambda: None)
step(lambda: None)


@step
def s_rmb_iso_marquee():
    drag(rel(0.05, 0.95), rel(0.95, 0.05))


step(lambda: None)


@step
def s_rmb_iso_marquee_done():
    f = picked_faces()
    # the face was selected at Ctrl+1: only it is shown, like Maya (#427), so a marquee picks just that face
    check(f"... a marquee picks the isolated face ({f})", f is not None and len(f) == 1)
    shot("gui_issue422_rmb_iso_marquee.png")
    ctrl_one()


step(lambda: None)


# --- an object Isolate Select hides stands between the camera and the isolated one ---------------------------

@step
def s_occluder():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='OBJECT')
    rv3d = area.spaces.active.region_3d
    toward = rv3d.view_rotation @ Vector((0, 0, 1))
    c3 = bpy.data.objects["pCube3"]
    c3.location = (Vector((0, 0, 1)) + toward * 4.0) * C["u"]
    c3.scale = (0.6, 0.6, 0.6)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = None
    click(screen_xy((0, 0, 1)))


step(lambda: None)


@step
def s_occluder_hit():
    check(f"without Isolate Select a click there hits the cube in front ({selected()})", selected() == ["pCube3"])
    for o in bpy.context.scene.objects:
        o.select_set(o.name == "pCube2")
    bpy.context.view_layer.objects.active = bpy.data.objects["pCube2"]
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])
    ctrl_one()


step(lambda: None)


@step
def s_occ_iso():
    check(f"Ctrl+1 on pCube2 ({view3d()[0].spaces.active.local_view is not None})",
          view3d()[0].spaces.active.local_view is not None)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = None
    shot("gui_issue422_occ_iso.png")
    click(screen_xy((0, 0, 1)))


step(lambda: None)


@step
def s_occ_click():
    check(f"... a click through the hidden cube selects pCube2 ({selected()})", selected() == ["pCube2"])
    key('F11')


step(lambda: None)


@step
def s_occ_face_mode():
    ob = bpy.context.edit_object
    check(f"... F11 = face mode on pCube2 ({ob and ob.name})", ob is not None and ob.name == "pCube2")
    if ob is not None:
        clear_faces()
    click(screen_xy((0, 0, 1)))


step(lambda: None)


@step
def s_occ_face_click():
    f = picked_faces()
    check(f"... a click through the hidden cube selects pCube2's top face ({f})", f == [5])
    shot("gui_issue422_occ_face.png")
    clear_faces()


step(lambda: None)
step(lambda: None)


@step
def s_occ_face_marquee():
    a, b = screen_xy((-1.2, -1.2, 1.2)), screen_xy((1.2, 1.2, -1.2))
    drag((min(a[0], b[0]) - 30, max(a[1], b[1]) + 30), (max(a[0], b[0]) + 30, min(a[1], b[1]) - 30))


step(lambda: None)


@step
def s_occ_face_marquee_done():
    f = picked_faces()
    check(f"... a marquee there selects pCube2's faces ({f})", f is not None and 5 in f)
    shot("gui_issue422_occ_marquee.png")
    clear_faces()
    key('W')                            # Move tool


step(lambda: None)


@step
def s_move_tool_click():
    click(screen_xy((0, 0, 1)))


step(lambda: None)


@step
def s_move_tool_clicked():
    f = picked_faces()
    check(f"... with the Move tool a click selects the top face ({f})", f == [5])
    clear_faces()
    key('Q')
    space = view3d()[0].spaces.active
    space.shading.type = 'WIREFRAME'


step(lambda: None)


@step
def s_wire_click():
    click(screen_xy((0, 0, 1)))


step(lambda: None)


@step
def s_wire_clicked():
    f = picked_faces()
    check(f"... in wireframe a click selects a face ({f})", f is not None and len(f) == 1)
    shot("gui_issue422_wire.png")
    clear_faces()
    space = view3d()[0].spaces.active
    space.shading.type = 'SOLID'
    space.shading.show_xray = True


step(lambda: None)


@step
def s_xray_click():
    click(screen_xy((0, 0, 1)))


step(lambda: None)


@step
def s_xray_clicked():
    f = picked_faces()
    check(f"... with X-ray a click selects a face ({f})", f is not None and len(f) == 1)
    shot("gui_issue422_xray.png")
    view3d()[0].spaces.active.shading.show_xray = False
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.ed.undo_push(message="before move")
    bpy.data.objects["pCube2"].location.x += 0.5 * C["u"]
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.ed.undo_push(message="move")
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])


step(lambda: None)


@step
def s_undo():
    key('Z')


step(lambda: None)


@step
def s_undone():
    area, _r = view3d()
    space = area.spaces.active
    x = bpy.data.objects["pCube2"].location.x / C["u"]
    check(f"z undoes the move and Isolate Select stays ({x:.2f}, {space.local_view is not None})",
          abs(x) < 1e-4 and space.local_view is not None and bpy.data.objects["pCube2"].local_view_get(space))
    for o in bpy.context.scene.objects:
        o.select_set(False)
    shot("gui_issue422_undo.png")
    click(screen_xy((0, 0, 1)))


step(lambda: None)


@step
def s_undo_click():
    check(f"... a click after the undo picks pCube2 ({selected()})", selected() == ["pCube2"])


run()
