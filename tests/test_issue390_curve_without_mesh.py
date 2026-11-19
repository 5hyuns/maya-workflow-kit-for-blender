"""#390: an object-mode click with a curve object that draws no curve of its own in the scene (no splines, or a
Geometry Nodes modifier that outputs only instances) selects like any other click instead of raising
"'NoneType' object has no attribute 'vertices'"."""

import types
from importlib import import_module

import bpy
from mathutils import Matrix

import kit

sp = import_module(kit.MODULE + ".operators.select_priority")

W = H = 400


def _clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _view():
    # orthographic front view: x right, z up, 8 units across 400 px (50 px per unit)
    view = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, -10), (0, 0, 0, 1)))
    proj = Matrix(((0.25, 0, 0, 0), (0, 0.25, 0, 0), (0, 0, -0.01, 0), (0, 0, 0, 1)))
    rv3d = types.SimpleNamespace(perspective_matrix=proj @ view)
    region = types.SimpleNamespace(width=W, height=H)
    ctx = types.SimpleNamespace(space_data=None, view_layer=bpy.context.view_layer, scene=bpy.context.scene,
                                evaluated_depsgraph_get=bpy.context.evaluated_depsgraph_get)
    return ctx, region, rv3d


def _px(x, z):
    return (W / 2 + x * W / 8, H / 2 + z * H / 8)


def _best(mouse):
    ctx, region, rv3d = _view()
    best = sp.rank(sp.hits(ctx, region, rv3d, mouse), sp.RADIUS_PX)
    return best and best[0]


def _instances_only(ob):
    """A Geometry Nodes modifier that turns the curve into cube instances on its points (a scatter set-up)."""
    ng = bpy.data.node_groups.new("scatter", 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gin, gout = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
    points = ng.nodes.new("GeometryNodeCurveToPoints")
    inst = ng.nodes.new("GeometryNodeInstanceOnPoints")
    cube = ng.nodes.new("GeometryNodeMeshCube")
    cube.inputs["Size"].default_value = (0.1, 0.1, 0.1)
    ng.links.new(gin.outputs[0], points.inputs[0])
    ng.links.new(points.outputs[0], inst.inputs["Points"])
    ng.links.new(cube.outputs[0], inst.inputs["Instance"])
    ng.links.new(inst.outputs[0], gout.inputs[0])
    ob.modifiers.new("Scatter", 'NODES').node_group = ng


def _scene():
    _clear()
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    cube = bpy.context.active_object
    empty = bpy.data.objects.new("curve2", bpy.data.curves.new("curve2", 'CURVE'))     # no splines
    sc.collection.objects.link(empty)
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, -2, 0))
    scatter = bpy.context.active_object
    scatter.name = "Scatter_Tool"
    _instances_only(scatter)
    bpy.ops.curve.primitive_bezier_circle_add(radius=0.5, location=(3, -2, 0), rotation=(1.5708, 0, 0))
    circle = bpy.context.active_object
    bpy.context.view_layer.update()
    return cube, empty, scatter, circle


def test_curves_without_a_drawn_curve_have_no_evaluated_mesh():
    _cube, empty, scatter, _circle = _scene()
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in (empty, scatter):
        ev = ob.evaluated_get(dg)
        try:
            assert ev.to_mesh() is None, ob.name          # the case the click met
        finally:
            ev.to_mesh_clear()


def test_click_with_such_curves_in_the_scene():
    _cube, _empty, _scatter, circle = _scene()
    assert _best(_px(0.0, 0.0)) is None                    # on the cube: Blender's own pick, no error
    assert _best(_px(-1.0, 0.0)) is None                   # where the scatter curve's spline lies: not a curve hit
    assert _best(_px(3.5, 0.0)) == circle.name             # a curve that draws its wire still wins


def test_selected_wire_of_such_curves_is_empty():
    """The selected-object wire reads no edges from these curves instead of raising (which removed its draw handler)."""
    edges = import_module(kit.MODULE + ".ui.selection_wire_edges")
    _cube, empty, scatter, circle = _scene()
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in (empty, scatter):
        co, ed = edges.edges_of(ob, dg)
        if len(co) or len(ed):
            raise AssertionError(f"{ob.name}: expected no wire, got {len(co)} points {len(ed)} edges")
    co, ed = edges.edges_of(circle, dg)
    if not len(ed):
        raise AssertionError("a bezier circle still has its wire")
