"""#348 in a real UI: Display > Shapes in the Maya Outliner shows the joints under the skeleton and keeps the Maya
header (Display / Show / Help, dock handle, search) so Shapes can be switched off where it was switched on; while
Shapes is on, picking a joint in the viewport opens the Outliner tree down to that joint; Shapes off brings back the
DAG-only rows with the skeleton row reading its root joint (joint1).

Rows are read from screenshots with the kit's own row-name matcher (ui/outliner_joints.find_rows)."""

import json
import os
import sys
from importlib import import_module

import bpy
import numpy as np
from bpy_extras import view3d_utils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
POINTS = ((3.0, -1.0, 2.0), (3.0, -1.0, 6.0), (5.0, -1.0, 9.0))
C = {}


def mod(name):
    return import_module(MODULE + name)


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def outliner():
    area = next(a for a in win().screen.areas if a.type == 'OUTLINER')
    return area, next(r for r in area.regions if r.type == 'WINDOW'), \
        next(r for r in area.regions if r.type == 'HEADER')


def redraw_all():
    for area in win().screen.areas:
        area.tag_redraw()


def park_mouse():
    """Mouse in the viewport: no hover highlight in the Outliner header or rows."""
    _a, r = main_view()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + 20, y=r.y + 20)


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_issue348_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)          # bottom line first, like a framebuffer read


def crop(px, region):
    return px[region.y:region.y + region.height, region.x:region.x + region.width, :3]


def row_names(px, names):
    """[(name, row, depth)] of the Outliner rows whose text reads one of ``names``: each row's ink at the name column
    of each depth (the icon on its left and anything right of the name masked off) against the UI font's picture of
    each name (the kit's row-name matcher, ui/outliner_joints.match); the best name and depth per row wins
    (joint1 / joint2 / joint3 differ in one glyph)."""
    ol = mod(".ui.outliner_joints")
    area, region, _h = outliner()
    sp = area.spaces.active
    prefs = bpy.context.preferences
    u = ol._unit(prefs)
    lead = 0.0 if not sp.show_mode_column else u
    size = ol._font_size(prefs)
    img = (px[region.y:region.y + region.height, region.x:region.x + region.width] * 255.0 + 0.5).astype(np.int16)
    found = []
    for k in range(0, 60):
        y0 = int(round(region.view2d.view_to_region(0, -(k + 1) * u, clip=False)[1]))
        if y0 < 0 or y0 + u > region.height:
            continue
        lines = img[y0:y0 + u]
        ink = ol._ink(lines, ol._background(lines))
        best = None
        for name in names:
            w, _base, ref = ol._ref(name, size, u)
            for depth in range(0, 8):
                x = int(lead + (depth + 2.25) * u)
                if x + w + u > region.width:
                    break
                part = ink.copy()
                part[:, :max(0, x - 2)] = False                  # the row's icon / disclosure triangle
                part[:, x + w + u // 2:] = False                 # restriction toggles, child counts
                if not part.any():
                    continue
                score = ol.match(part, ref, x)[0]
                if score >= ol.MATCH and (best is None or score > best[0]):
                    best = (score, name, depth)
        if best is not None:
            found.append((best[1], k, best[2]))
    return found


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_joints():
    bpy.ops.allset.keymap_activate()
    k = mod(".operators.units").maya_unit(bpy.context.scene)
    pts = [[c * k for c in p] for p in POINTS]
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        for ob in list(bpy.context.selected_objects):
            ob.select_set(False)
        bpy.ops.allset.joint_tool(points=json.dumps(pts))
    park_mouse()
    redraw_all()


@step
def s_wait():
    redraw_all()


@step
def s_shapes_off():
    px = shot("1_shapes_off")
    mo, ol = mod(".ui.maya_outliner"), mod(".ui.outliner_joints")
    area, region, header = outliner()
    sp = area.spaces.active
    ob = bpy.data.objects.get("skeleton1")
    check(f"skeleton1 made, in Pose Mode ({ob.mode if ob else None})", ob is not None and ob.mode == 'POSE')
    check("Maya Outliner, Shapes off", mo.is_maya_outliner(sp) and not sp.use_filter_object_content)
    seen = ol.SEEN.get(region.as_pointer())
    check(f"Shapes off: the skeleton row reads joint1 ({seen})", seen == [("skeleton1", "joint1")])
    C["header"] = crop(px, header).copy()
    C["header_size"] = (header.width, header.height)
    sp.use_filter_object_content = True          # Display > Shapes (the menu item is this property)
    redraw_all()


@step
def s_wait_on():
    redraw_all()


@step
def s_shapes_on():
    px = shot("2_shapes_on")
    mo, ol = mod(".ui.maya_outliner"), mod(".ui.outliner_joints")
    area, region, header = outliner()
    sp = area.spaces.active
    check("Shapes on: still a Maya Outliner", mo.is_maya_outliner(sp))
    same_size = (header.width, header.height) == C["header_size"]
    diff = np.abs(crop(px, header) - C["header"]).max(axis=-1) if same_size else None
    changed = float((diff > 0.06).mean()) if diff is not None else 1.0
    check(f"Shapes on: the header is the same Maya header (Display / Show / Help, handle, search; "
          f"{changed:.1%} of its pixels changed)", changed < 0.02)
    check(f"Shapes on: no root-joint label over Blender's rows ({ol.SEEN.get(region.as_pointer())})",
          ol.SEEN.get(region.as_pointer()) is None)
    rows = row_names(px, ["skeleton1", "joint1"])
    C["rows_on"] = rows
    check(f"Shapes on: the skeleton row shows Blender's name, nothing reads joint1 yet ({rows})",
          any(n == "skeleton1" and d == 0 for n, _k, d in rows) and not any(n == "joint1" for n, _k, _d in rows))
    # pick joint3 in the viewport
    rig = bpy.data.objects["skeleton1"]
    area3, r3 = main_view()
    head = rig.matrix_world @ rig.data.bones["joint3"].head_local
    p = view3d_utils.location_3d_to_region_2d(r3, area3.spaces.active.region_3d, head)
    x, y = int(r3.x + p.x), int(r3.y + p.y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_wait_pick():
    park_mouse()
    redraw_all()


@step
def s_wait_pick2():
    redraw_all()


@step
def s_picked():
    px = shot("3_joint3_picked")
    rig = bpy.data.objects["skeleton1"]
    act = rig.data.bones.active
    check(f"joint3 picked in the viewport (active {act.name if act else None}, mode {rig.mode})",
          act is not None and act.name == "joint3" and rig.mode == 'POSE')
    rows = row_names(px, ["joint1", "joint2", "joint3"])
    names = [n for n, _k, _d in rows]
    check(f"the Outliner opened down to joint3: joint1 > joint2 > joint3 rows, one each ({rows})",
          names == ["joint1", "joint2", "joint3"] and [d for _n, _k, d in rows] == sorted(d for _n, _k, d in rows)
          and len({d for _n, _k, d in rows}) == 3)
    _area, region, _h = outliner()
    check("Shapes on: still no root-joint label after the pick",
          mod(".ui.outliner_joints").SEEN.get(region.as_pointer()) is None)
    revealed = getattr(mod(".ui.maya_outliner"), "STATS", {}).get("revealed", 0)
    check(f"one Outliner opened for the pick ({revealed})", revealed == 1)
    C["rows_picked"], C["revealed"] = rows, revealed
    # click joint2's row in the Outliner: selected there, so the tree must not jump
    row = next((r for r in rows if r[0] == "joint2"), None)
    if row is not None:
        _n, k, depth = row
        u = mod(".ui.outliner_joints")._unit(bpy.context.preferences)
        x = region.x + int((depth + 2.25) * u) + u
        y = region.y + int(round(region.view2d.view_to_region(0, -(k + 0.5) * u, clip=False)[1]))
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_wait_row():
    park_mouse()
    redraw_all()


@step
def s_wait_row2():
    redraw_all()


@step
def s_row_clicked():
    px = shot("4_outliner_row_clicked")
    rig = bpy.data.objects["skeleton1"]
    act = rig.data.bones.active
    check(f"joint2 picked in the Outliner (active {act.name if act else None})", act is not None and act.name == "joint2")
    revealed = getattr(mod(".ui.maya_outliner"), "STATS", {}).get("revealed", 0)
    check(f"a pick made in the Outliner runs no reveal ({revealed} after, {C['revealed']} before)",
          revealed == C["revealed"])
    rows = row_names(px, ["joint1", "joint2", "joint3"])
    check(f"the rows stay where they were ({rows})", rows == C["rows_picked"])
    # collapse the tree, back to Object Mode: the next pick must open it again after the switch to Pose Mode
    area, region, _h = outliner()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        for _ in range(8):
            bpy.ops.outliner.show_one_level(open=False)
    area3, r3 = main_view()
    with bpy.context.temp_override(window=win(), area=area3, region=r3):
        bpy.ops.object.mode_set(mode='OBJECT')
        for ob in list(bpy.context.selected_objects):
            ob.select_set(False)
    redraw_all()


@step
def s_wait_collapse():
    redraw_all()


@step
def s_collapsed():
    px = shot("5_collapsed_object_mode")
    rig = bpy.data.objects["skeleton1"]
    check(f"Object Mode, collapsed: no joint rows ({rig.mode}, {row_names(px, ['joint1', 'joint2', 'joint3'])})",
          rig.mode == 'OBJECT' and row_names(px, ["joint1", "joint2", "joint3"]) == [])
    area3, r3 = main_view()
    head = rig.matrix_world @ rig.data.bones["joint2"].head_local
    p = view3d_utils.location_3d_to_region_2d(r3, area3.spaces.active.region_3d, head)
    x, y = int(r3.x + p.x), int(r3.y + p.y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_wait_obj():
    park_mouse()
    redraw_all()


@step
def s_wait_obj2():
    redraw_all()


@step
def s_wait_obj3():
    redraw_all()


@step
def s_object_pick():
    px = shot("6_joint2_picked_from_object_mode")
    rig = bpy.data.objects["skeleton1"]
    act = rig.data.bones.active
    check(f"a joint picked in Object Mode: Pose Mode, joint2 active ({rig.mode}, {act.name if act else None})",
          rig.mode == 'POSE' and act is not None and act.name == "joint2")
    rows = row_names(px, ["joint1", "joint2", "joint3"])
    check(f"the Outliner opened down to joint2 after the switch to Pose Mode (joint3 stays inside it) ({rows})",
          [(n, d) for n, _k, d in rows] == [("joint1", 2), ("joint2", 3)])
    area, _r, _h = outliner()
    area.spaces.active.use_filter_object_content = False      # Display > Shapes off, same menu
    redraw_all()


@step
def s_wait_off():
    redraw_all()


@step
def s_back_off():
    px = shot("7_shapes_off_again")
    mo, ol = mod(".ui.maya_outliner"), mod(".ui.outliner_joints")
    area, region, header = outliner()
    sp = area.spaces.active
    dag_only = getattr(mo, "shows_dag_only", lambda _sp: False)
    check("Shapes off again: Maya Outliner, DAG rows only", mo.is_maya_outliner(sp) and dag_only(sp))
    same_size = (header.width, header.height) == C["header_size"]
    diff = np.abs(crop(px, header) - C["header"]).max(axis=-1) if same_size else None
    changed = float((diff > 0.06).mean()) if diff is not None else 1.0
    check(f"Shapes off again: the same Maya header ({changed:.1%} of its pixels changed)", changed < 0.02)
    seen = ol.SEEN.get(region.as_pointer())
    check(f"Shapes off again: the skeleton row reads joint1 again ({seen})", seen == [("skeleton1", "joint1")])
    rows = row_names(px, ["joint1", "joint2", "joint3"])
    check(f"Shapes off again: no bone rows, only the skeleton row reading joint1 ({rows})",
          [(n, d) for n, _k, d in rows] == [("joint1", 0)])


run()
