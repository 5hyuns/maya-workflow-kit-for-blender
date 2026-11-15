"""In a real UI on every supported Blender: the Paint Skin Weights Tool Settings draw Blender's falloff, stroke and
cursor panels without errors, and strokes paint the tool's Value (Replace 0.3 from the option window; after Smooth,
Replace again with the 0.75 Value preset)."""

import os
import sys
from importlib import import_module

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, win, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 240
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {"errors": [], "drawn": set()}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def main_view():
    toolbox = import_module(MODULE + ".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def screen_of(world):
    _area, r = main_view()
    p = view3d_utils.location_3d_to_region_2d(r, r.data, world)
    return r.x + int(p.x), r.y + int(p.y)


def cyl():
    return bpy.data.objects["pCylinder1"]


def joint2_at(value):
    """How many vertices hold joint2 weight ``value``."""
    me = cyl()
    vg = me.vertex_groups["joint2"]
    return sum(1 for v in me.data.vertices for g in v.groups if g.group == vg.index and abs(g.weight - value) < 0.01)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    joints = import_module(MODULE + ".operators.joints")
    k = import_module(MODULE + ".operators.units").maya_unit()
    area, r = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        bpy.ops.allset.create(kind='CYLINDER')            # pCylinder1: radius 1, height 2 (Maya units)
        c = bpy.context.active_object
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(c.data)
        vertical = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-9]
        bmesh.ops.subdivide_edges(bm, edges=vertical, cuts=9, use_grid_fill=True)
        bm.to_mesh(c.data)
        bm.free()
        bpy.ops.object.select_all(action='DESELECT')
        sk = joints.new_skeleton(bpy.context)
        parent = None
        for z in (-1.0, 0.0, 1.0):
            parent = joints.add_joint(sk, Vector((0, 0, z * k)), parent, length=k)
        joints.finish(bpy.context, sk, ["joint1", "joint2", "joint3"])
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        sk.select_set(True)
        c.select_set(True)
        bpy.context.view_layer.objects.active = c
        bpy.ops.allset.bind_skin()
        bpy.ops.allset.frame(selected=False)
    C["k"] = k


@step
def s_paint_tool():
    area, r = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        # the option window: Replace, Value 0.3, Opacity 1, a Solid profile of radius 0.5
        bpy.ops.allset.paint_skin_weights(settings=True, operation='REPLACE', profile='SOLID', value=0.3,
                                          opacity=1.0, radius=0.5)
        bpy.ops.allset.weight_workspace()                 # its Tool Settings
    check(f"Paint Skin Weights: weight paint ({bpy.context.mode})", bpy.context.mode == 'PAINT_WEIGHT')
    c = cyl()
    c.vertex_groups.active_index = c.vertex_groups["joint2"].index
    pw = import_module(MODULE + ".ui.paint_weights")
    s = import_module(MODULE + ".operators.weight_paint").state(bpy.context)
    for flag in ("show_brush", "show_stroke", "show_display", "show_pressure"):
        setattr(s, flag, True)
    native, draw = pw._native, pw.draw

    def record_native(layout, context, cls):
        C["drawn"].add(cls.__name__)
        try:
            native(layout, context, cls)
        except Exception as ex:
            C["errors"].append(f"{cls.__name__}: {ex!r}")
            raise

    def record_draw(layout, context):
        try:
            draw(layout, context)
        except Exception as ex:
            C["errors"].append(f"draw: {ex!r}")
            raise
    pw._native, pw.draw = record_native, record_draw
    C["restore"] = (pw, native, draw)
    redraw()


@step
def s_wait_draw():
    redraw()


@step
def s_dock_drawn():
    from bl_ui import properties_paint_common as paint_common
    falloff = "ShapePanel" if hasattr(paint_common, "ShapePanel") else "FalloffPanel"
    want = {falloff, "StrokePanel", "DisplayPanel"}
    check(f"Tool Settings draw Blender's {sorted(want)} (drawn {sorted(C['drawn'])}) without errors {C['errors']}",
          want <= C["drawn"] and not C["errors"])
    shot("gui_paint_versions_dock.png")
    k = C["k"]
    C["before"] = joint2_at(0.3)
    C["stroke"] = [screen_of(Vector((x * k, -k, 0.0))) for x in (-0.5, -0.25, 0.0, 0.25, 0.5)]
    ev('MOUSEMOVE', 'NOTHING', x=C["stroke"][0][0], y=C["stroke"][0][1])


def stroke_steps():
    @step
    def s_press():
        x, y = C["stroke"][0]
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)

    @step
    def s_move():
        for x, y in C["stroke"][1:]:
            ev('MOUSEMOVE', 'NOTHING', x=x, y=y)

    @step
    def s_release():
        x, y = C["stroke"][-1]
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


stroke_steps()


@step
def s_painted_03():
    after = joint2_at(0.3)
    brush = bpy.context.tool_settings.weight_paint.brush
    check(f"a Replace stroke paints the tool's Value 0.3 ({C['before']} -> {after} vertices at 0.3, brush "
          f"{brush.name} {brush.blend})", after >= C["before"] + 4)
    shot("gui_paint_versions_painted.png")
    area, r = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        bpy.ops.allset.weight_tool(kind='BLUR')           # Maya Smooth
        bpy.ops.allset.weight_tool(kind='DRAW', blend='MIX')   # back to Replace
        bpy.ops.allset.weight_value(value=0.75)           # the dock's 0.75 Value preset
    brush = bpy.context.tool_settings.weight_paint.brush
    kind = import_module(MODULE + ".operators.weight_paint").brush_kind(brush)
    check(f"Replace after Smooth: a draw brush mixing ({brush.name}, {kind}, {brush.blend})",
          kind == 'DRAW' and brush.blend == 'MIX')
    k = C["k"]
    C["before"] = joint2_at(0.75)
    C["stroke"] = [screen_of(Vector((x * k, -k, 0.4 * k))) for x in (-0.5, -0.25, 0.0, 0.25, 0.5)]
    ev('MOUSEMOVE', 'NOTHING', x=C["stroke"][0][0], y=C["stroke"][0][1])


stroke_steps()


@step
def s_painted_075():
    after = joint2_at(0.75)
    check(f"after Smooth, Replace paints the 0.75 Value preset ({C['before']} -> {after} vertices at 0.75)",
          after >= C["before"] + 4)
    shot("gui_paint_versions_painted2.png")
    pw, native, draw = C["restore"]
    pw._native, pw.draw = native, draw
    check(f"no Tool Settings draw errors while painting {C['errors']}", not C["errors"])


run()
