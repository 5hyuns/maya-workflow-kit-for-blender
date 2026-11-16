"""#374 and #365 in a real UI, the reporters' steps. #374: pick an object far from the view in the Maya Outliner,
move the mouse over the viewport and press F: the view frames that object (F over the Outliner is Reveal Selected,
like Maya). #365: a long joint chain, pick its last joint in the viewport, F over the Outliner opens the rows down to
it, then Alt held + middle drag sideways pans the rows so the deep row comes into the Outliner."""

import json
import os
import sys
from importlib import import_module

import bpy
from bpy_extras import view3d_utils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, tap, win  # noqa: E402

C = {}
CHAIN = 14              # joints in the long chain


def mod(name):
    return import_module(MODULE + name)


def tree():
    return mod(".ui.outliner_tree")


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def outliner():
    area = next(a for a in win().screen.areas if a.type == 'OUTLINER')
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def redraw_all():
    for area in win().screen.areas:
        area.tag_redraw()


def park_mouse():
    _a, r = main_view()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + 20, y=r.y + 20)


def rows():
    area, region = outliner()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return tree().rows_for(bpy.context, area.spaces.active)


def row_point(label):
    area, region = outliner()
    rs = rows()
    t = tree()
    u = t.unit(bpy.context.preferences)
    k = next(i for i, r in enumerate(rs) if r.label == label)
    y0, y1 = t.row_rect(area, region, k, u, len(rs))
    return region.x + int((rs[k].depth + 3.0) * u), region.y + int((y0 + y1) / 2)


def screen_point(world):
    area, region = main_view()
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, world)
    return None if p is None else (p.x / region.width, p.y / region.height)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    k = mod(".operators.units").maya_unit(bpy.context.scene)
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
        bpy.ops.allset.create(kind='CUBE')
        far = bpy.context.view_layer.objects.active
        far.location = (14.0 * k, 9.0 * k, 3.0 * k)
        C["far"] = far.name
        pts = [[(2.0 + 1.5 * i) * k, -2.0 * k, (1.0 + 0.6 * i) * k] for i in range(CHAIN)]
        bpy.ops.allset.joint_tool(points=json.dumps(pts))
        bpy.ops.object.mode_set(mode='OBJECT')
        for ob in list(bpy.context.selected_objects):
            ob.select_set(False)
        rv3d = area.spaces.active.region_3d
        rv3d.view_location = (0.0, 0.0, 0.0)
        rv3d.view_distance = 30.0 * k
    park_mouse()
    redraw_all()


@step
def s_wait():
    redraw_all()


@step
def s_pick_row():
    C["before"] = screen_point(bpy.data.objects[C["far"]].matrix_world.translation)
    x, y = row_point(C["far"])
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_f_over_view():
    sel = [o.name for o in bpy.context.selected_objects]
    check(f"#374: a click on the {C['far']} row picks it ({sel})", sel == [C["far"]])
    _a, r = main_view()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 3)
    tap('F')


@step
def s_wait_frame():
    redraw_all()


@step
def s_wait_frame2():
    redraw_all()


@step
def s_framed():
    ob = bpy.data.objects[C["far"]]
    centre = ob.matrix_world @ (sum((v.co for v in ob.data.vertices), ob.data.vertices[0].co * 0) / len(ob.data.vertices))
    p = screen_point(centre)
    corners = [screen_point(ob.matrix_world @ v.co) for v in ob.data.vertices]
    inside = all(c is not None and 0.0 <= c[0] <= 1.0 and 0.0 <= c[1] <= 1.0 for c in corners)
    big = max(c[0] for c in corners) - min(c[0] for c in corners) if inside else 0.0
    check(f"#374: F over the viewport frames the Outliner pick (centre {C['before']} -> {p}, all corners in the view "
          f"{inside}, width {big:.2f} of the view)",
          p is not None and abs(p[0] - 0.5) < 0.05 and abs(p[1] - 0.5) < 0.05 and inside and big > 0.3)
    # #365: pick the last joint in the viewport
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    C["rig"] = rig.name
    last = f"joint{CHAIN}"
    C["last"] = last
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.view3d.view_all()
    head = rig.matrix_world @ rig.data.bones[last].head_local
    C["head"] = head


@step
def s_pick_joint():
    area, region = main_view()
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, C["head"])
    x, y = int(region.x + p.x), int(region.y + p.y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_reveal():
    rig = bpy.data.objects[C["rig"]]
    act = rig.data.edit_bones.active if rig.mode == 'EDIT' else rig.data.bones.active
    check(f"#365: the last joint is picked in the viewport ({act and act.name}, {rig.mode})",
          act is not None and act.name == C["last"])
    _a, region = outliner()
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 2)
    tap('F')


@step
def s_wait_reveal():
    redraw_all()


@step
def s_alt_drag():
    names = [r.label for r in rows()]
    check(f"#365: F over the Outliner opens the rows down to {C['last']} ({len(names)} rows)", C["last"] in names)
    area, region = outliner()
    C["sx0"] = tree().SCROLL_X.get(area.as_pointer(), 0)
    x, y = region.x + region.width // 2, region.y + region.height // 2
    C["xy"] = x, y
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFT_ALT', 'PRESS', alt=True)            # a real Alt key held, then the middle button
    ev('MIDDLEMOUSE', 'PRESS', x=x, y=y, alt=True)


@step
def s_alt_moves():
    x, y = C["xy"]
    for i in range(1, 7):
        ev('MOUSEMOVE', 'NOTHING', x=x - 70 * i, y=y, alt=True)


@step
def s_alt_release():
    x, y = C["xy"]
    ev('MIDDLEMOUSE', 'RELEASE', x=x - 420, y=y, alt=True)
    ev('LEFT_ALT', 'RELEASE')
    redraw_all()


@step
def s_panned():
    area, region = outliner()
    t = tree()
    u = t.unit(bpy.context.preferences)
    sx = t.SCROLL_X.get(area.as_pointer(), 0)
    deep = next(r for r in rows() if r.label == C["last"])
    left = deep.depth * u - sx
    check(f"#365: Alt + middle drag left pans the rows sideways ({C['sx0']} -> {sx} px) so the deep row "
          f"{C['last']} (depth {deep.depth}) starts inside the Outliner ({left:.0f} px of {region.width})",
          sx > C["sx0"] and 0 <= left < region.width * 0.6)
    t.SCROLL_X.pop(area.as_pointer(), None)


run()
