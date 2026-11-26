"""#546 in a real UI: pick the top face in face mode (F11), go to edge mode (F10) and Shift+click one of the face's
edges; Edit Mesh > Wedge then turns the face around that edge (each edge gives its own result). The other order works
too: an edge clicked in edge mode, then the face Shift+clicked in face mode; and in Multi-Component mode (F7) the
edge and the face picked in either order."""

import os
import sys

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, step, setup, screenshot, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def screen(co):
    area, region = view3d()
    ob = bpy.data.objects["Cube"]
    p = location_3d_to_region_2d(region, region.data, ob.matrix_world @ Vector(co))
    return int(region.x + p.x), int(region.y + p.y)


def click(co, shift=False):
    x, y = screen(co)
    ev('MOUSEMOVE', 'NOTHING', x=x - 1, y=y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    if shift:
        ev('LEFT_SHIFT', 'PRESS', shift=True)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y, shift=shift)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y, shift=shift)
    if shift:
        ev('LEFT_SHIFT', 'RELEASE')


def state():
    ob = bpy.data.objects["Cube"]
    if ob.mode != 'EDIT':
        return ("mode", ob.mode)
    bm = bmesh.from_edit_mesh(ob.data)
    act = bm.select_history.active
    return (tuple(bpy.context.tool_settings.mesh_select_mode), sum(f.select for f in bm.faces),
            sum(e.select for e in bm.edges), type(act).__name__)


def wedge_case(name, edge_mid, hinge_axis, hinge_value):
    @step
    def s_reset():
        ob = bpy.data.objects["Cube"]
        if ob.mode == 'EDIT':
            area, region = view3d()
            with bpy.context.temp_override(window=win(), area=area, region=region):
                bpy.ops.object.mode_set(mode='OBJECT')
        me = bpy.data.meshes.new("cube546")
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2)
        bm.to_mesh(me)
        bm.free()
        ob.data = me
        tap('F11')                      # face mode (enters Edit Mode)

    @step
    def s_face():
        click((0, 0, 1))                # the top face

    @step
    def s_edge_mode():
        C[name + "after_face"] = state()
        tap('F10')

    @step
    def s_edge():
        C[name + "after_f10"] = state()
        click(edge_mid, shift=True)

    @step
    def s_picked_shot():
        if SHOTS:
            screenshot(os.path.join(SHOTS, f"546_{name}_picked.png"))

    @step
    def s_wedge():
        C[name + "after_shift"] = state()
        ob = bpy.data.objects["Cube"]
        bm = bmesh.from_edit_mesh(ob.data)
        act = bm.select_history.active
        C[name + "faces"] = sum(f.select for f in bm.faces)
        C[name + "active"] = (isinstance(act, bmesh.types.BMEdge)
                              and all(abs(getattr(v.co, hinge_axis) - hinge_value) < 1e-4 for v in act.verts)
                              and all(abs(v.co.z - 1) < 1e-4 for v in act.verts))
        area, region = view3d()
        with bpy.context.temp_override(window=win(), area=area, region=region):
            C[name + "result"] = bpy.ops.allset.wedge()

    @step
    def s_check():
        ob = bpy.data.objects["Cube"]
        bm = bmesh.from_edit_mesh(ob.data)
        top = [v.co for v in bm.verts if v.co.z > 2.99]
        if SHOTS:
            screenshot(os.path.join(SHOTS, f"546_{name}.png"))
        check(f"{name}: the top face stays selected with the clicked edge active "
              f"(faces {C[name + 'faces']}, active edge {C[name + 'active']})",
              C[name + "faces"] == 1 and C[name + "active"])
        check(f"{name}: Wedge stands the face up on the clicked edge ({C[name + 'result']}, top {len(top)})",
              C[name + "result"] == {'FINISHED'} and len(top) == 2
              and all(abs(getattr(v, hinge_axis) - hinge_value) < 1e-3 for v in top))


def edge_first_case(name, edge_mid, hinge_axis, hinge_value, header=False):
    """Edge mode (F10): click a top edge; face mode (F11, or ``header``: the header's mode button, which sets the
    select mode directly): Shift+click the top face; Wedge turns about that edge."""
    @step
    def s_reset():
        ob = bpy.data.objects["Cube"]
        if ob.mode == 'EDIT':
            area, region = view3d()
            with bpy.context.temp_override(window=win(), area=area, region=region):
                bpy.ops.object.mode_set(mode='OBJECT')
        me = bpy.data.meshes.new("cube546e")
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2)
        bm.to_mesh(me)
        bm.free()
        ob.data = me
        tap('F10')                      # edge mode (enters Edit Mode)

    @step
    def s_edge():
        click(edge_mid)

    @step
    def s_face_mode():
        C[name + "after_edge"] = state()
        if header:
            bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
        else:
            tap('F11')

    @step
    def s_face():
        click((0, 0, 1), shift=True)

    @step
    def s_picked_shot():
        C[name + "after_face"] = state()
        if SHOTS:
            screenshot(os.path.join(SHOTS, f"546_{name}_picked.png"))

    @step
    def s_wedge():
        area, region = view3d()
        with bpy.context.temp_override(window=win(), area=area, region=region):
            C[name + "result"] = bpy.ops.allset.wedge()

    @step
    def s_check():
        ob = bpy.data.objects["Cube"]
        bm = bmesh.from_edit_mesh(ob.data)
        top = [v.co for v in bm.verts if v.co.z > 2.99]
        check(f"{name}: edge picked, then the face added in face mode ({C[name + 'after_edge']} -> "
              f"{C[name + 'after_face']})",
              C[name + "after_edge"][2] == 1 and C[name + "after_face"][1] == 1)
        check(f"{name}: Wedge stands the face up on the edge picked first ({C[name + 'result']}, top {len(top)})",
              C[name + "result"] == {'FINISHED'} and len(top) == 2
              and all(abs(getattr(v, hinge_axis) - hinge_value) < 1e-3 for v in top))


def multi_case(name, edge_mid, hinge_axis, hinge_value, edge_first):
    """Multi-Component mode (F7): the edge and the top face picked together (either order, the second with Shift);
    Wedge turns about that edge, and the edge is drawn as the hinge."""
    @step
    def s_reset():
        ob = bpy.data.objects["Cube"]
        if ob.mode == 'EDIT':
            area, region = view3d()
            with bpy.context.temp_override(window=win(), area=area, region=region):
                bpy.ops.object.mode_set(mode='OBJECT')
        me = bpy.data.meshes.new("cube546m")
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2)
        bm.to_mesh(me)
        bm.free()
        ob.data = me
        tap('F7')                       # Multi-Component (enters Edit Mode)

    @step
    def s_first():
        C[name + "mode"] = tuple(bpy.context.tool_settings.mesh_select_mode)
        click(edge_mid if edge_first else (0, 0, 1))

    @step
    def s_second():
        C[name + "first"] = state()
        click((0, 0, 1) if edge_first else edge_mid, shift=True)

    @step
    def s_hinge():
        from importlib import import_module
        from sim import MODULE
        hinge = import_module(MODULE + ".operators.wedge_hinge")
        ob = bpy.data.objects["Cube"]
        bm = bmesh.from_edit_mesh(ob.data)
        e = hinge.shown_hinge(ob, bm)
        C[name + "picked"] = state()
        C[name + "shown"] = e is not None and all(abs(getattr(v.co, hinge_axis) - hinge_value) < 1e-4
                                                  and abs(v.co.z - 1) < 1e-4 for v in e.verts)
        if SHOTS:
            screenshot(os.path.join(SHOTS, f"546_{name}_picked.png"))

    @step
    def s_wedge():
        area, region = view3d()
        with bpy.context.temp_override(window=win(), area=area, region=region):
            C[name + "result"] = bpy.ops.allset.wedge()

    @step
    def s_check():
        ob = bpy.data.objects["Cube"]
        bm = bmesh.from_edit_mesh(ob.data)
        top = [v.co for v in bm.verts if v.co.z > 2.99]
        check(f"{name}: Multi-Component, the edge and the face picked ({C[name + 'mode']}, {C[name + 'first']} -> "
              f"{C[name + 'picked']}); "
              f"the hinge drawn on the picked edge ({C[name + 'shown']})",
              C[name + "mode"] == (True, True, True) and C[name + "picked"][1] == 1 and C[name + "shown"])
        check(f"{name}: Wedge stands the face up on the picked edge ({C[name + 'result']}, top {len(top)})",
              C[name + "result"] == {'FINISHED'} and len(top) == 2
              and all(abs(getattr(v, hinge_axis) - hinge_value) < 1e-3 for v in top))


@step
def s_setup():
    C["x"], C["y"] = setup()
    cube = bpy.data.objects["Cube"]
    for o in bpy.context.view_layer.objects:
        o.select_set(o is cube)
    bpy.context.view_layer.objects.active = cube
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])


wedge_case("front", (0, -1, 1), "y", -1.0)
wedge_case("right", (1, 0, 1), "x", 1.0)
edge_first_case("edge_first_front", (0, -1, 1), "y", -1.0)
edge_first_case("edge_first_right", (1, 0, 1), "x", 1.0)
edge_first_case("header_front", (0, -1, 1), "y", -1.0, header=True)
edge_first_case("header_right", (1, 0, 1), "x", 1.0, header=True)
multi_case("multi_edge_first_front", (0, -1, 1), "y", -1.0, True)
multi_case("multi_edge_first_right", (1, 0, 1), "x", 1.0, True)
multi_case("multi_face_first_front", (0, -1, 1), "y", -1.0, False)
multi_case("multi_face_first_right", (1, 0, 1), "x", 1.0, False)

run()
