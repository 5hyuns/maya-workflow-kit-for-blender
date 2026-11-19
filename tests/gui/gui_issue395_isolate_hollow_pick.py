"""#395 in a real UI: a box with its front and back faces deleted is isolated (Ctrl+1) while another object stands
between it and the camera, and the view looks through the box's holes. RMB on the box's inner wall (its back side
seen through the hole) opens the box's marking menu, not one for the object Isolate Select hides; its Vertex item
puts the box in vertex mode, and a click on a vertex seen through the hole selects it. RMB over the hole names no
hidden object either. Screenshots with ALLSET_GUI_SHOTS (or --shots)."""

import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
SECTORS = {"N": (0, 1), "NE": (1, 1), "E": (1, 0), "SE": (1, -1), "S": (0, -1), "SW": (-1, -1), "W": (-1, 0),
           "NW": (-1, 1)}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def mod(name):
    return import_module(MODULE + name)


def draw():
    return mod(".marking.draw")


def session():
    return draw().ACTIVE.get("session")


def screen_xy(co):
    area, region = view3d()
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, Vector(co))
    return region.x + int(round(p.x)), region.y + int(round(p.y))


def target():
    return bpy.context.window_manager.allset_mm_target


def sector_point(s, key):
    eng = mod(".marking.engine")
    lay, (cx, cy) = s.stack[-1]
    ox, oy = draw().ACTIVE["origin"]
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


def close_menu():
    for _ in range(2):
        ev('ESC', 'PRESS')
        ev('ESC', 'RELEASE')


@step
def s_setup():
    setup()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("pCube6")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.normal.y) > 0.5], context='FACES_ONLY')
    bm.to_mesh(me)
    bm.free()
    box = bpy.data.objects.new("pCube6", me)
    sc = bpy.context.scene
    sc.collection.objects.link(box)
    me2 = bpy.data.meshes.new("pasted__Cylinder6")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me2)
    bm.free()
    blocker = bpy.data.objects.new("pasted__Cylinder6", me2)
    blocker.location = (0, -4, 0)
    blocker.scale = (6, 0.2, 6)                  # covers the whole box as seen from the camera
    sc.collection.objects.link(blocker)
    for o in sc.objects:
        o.select_set(o == box)
    bpy.context.view_layer.objects.active = box
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active):
        bpy.ops.allset.isolate()
    C["local"] = area.spaces.active.local_view is not None


@step
def s_view():
    area, _region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'PERSP'
    rv3d.view_rotation = Euler((math.radians(90), 0, 0)).to_quaternion()     # look along +Y through the holes
    rv3d.view_location = (0, 0, 0)
    rv3d.view_distance = 8.0
    for o in bpy.context.scene.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = None
    area.tag_redraw()


step(lambda: None)


@step
def s_rmb_wall():
    check("Isolate Select shows only the box (local view)", C["local"])
    shot("gui_issue395_isolated.png")
    C["wall"] = screen_xy((-1.0, 0.4, 0.0))            # the inner side of the -X wall, seen through the front hole
    ev('MOUSEMOVE', 'NOTHING', x=C["wall"][0], y=C["wall"][1])
    ev('RIGHTMOUSE', 'PRESS', x=C["wall"][0], y=C["wall"][1])


@step
def s_menu_wall():
    s = session()
    check(f"RMB on the box's inner wall opens the menu for the box ({target()!r})", target() == "pCube6")
    shot("gui_issue395_menu_wall.png")
    at = sector_point(s, "W") if s is not None and s.layout.radial.get("W") is not None else None
    C["at"] = at or C["wall"]
    ev('MOUSEMOVE', 'NOTHING', x=C["at"][0], y=C["at"][1])


@step
def s_release_wall():
    ev('RIGHTMOUSE', 'RELEASE', x=C["at"][0], y=C["at"][1])


step(lambda: None)


@step
def s_vertex_mode():
    ob = bpy.context.edit_object
    check(f"... its Vertex item puts the box in vertex mode ({ob and ob.name}, {bpy.context.mode})",
          ob is not None and ob.name == "pCube6" and tuple(bpy.context.scene.tool_settings.mesh_select_mode)
          == (True, False, False))
    if ob is not None and ob.name == "pCube6":
        bm = bmesh.from_edit_mesh(ob.data)
        for v in bm.verts:
            v.select_set(False)
        bm.select_flush(False)
        bmesh.update_edit_mesh(ob.data)
    xy = screen_xy((-1.0, 1.0, -1.0))                  # the far bottom-left corner, seen through the hole
    ev('MOUSEMOVE', 'NOTHING', x=xy[0], y=xy[1])
    ev('LEFTMOUSE', 'PRESS', x=xy[0], y=xy[1])
    ev('LEFTMOUSE', 'RELEASE', x=xy[0], y=xy[1])


step(lambda: None)


@step
def s_vertex_picked():
    ob = bpy.context.edit_object
    picked = []
    if ob is not None and ob.name == "pCube6":
        bm = bmesh.from_edit_mesh(ob.data)
        picked = [tuple(round(c, 3) for c in v.co) for v in bm.verts if v.select]
    check(f"a click on a vertex seen through the hole selects it ({picked})", picked == [(-1.0, 1.0, -1.0)])
    shot("gui_issue395_vertex.png")
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='OBJECT')


@step
def s_rmb_hole():
    C["hole"] = screen_xy((0.0, 1.5, 0.0))             # straight through both holes: nothing of the box there
    ev('MOUSEMOVE', 'NOTHING', x=C["hole"][0], y=C["hole"][1])
    ev('RIGHTMOUSE', 'PRESS', x=C["hole"][0], y=C["hole"][1])


@step
def s_menu_hole():
    check(f"RMB through the holes names no object Isolate Select hides ({target()!r})",
          target() != "pasted__Cylinder6")
    close_menu()
    ev('RIGHTMOUSE', 'RELEASE')


run()
