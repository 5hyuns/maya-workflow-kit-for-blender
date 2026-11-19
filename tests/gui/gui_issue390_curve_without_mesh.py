"""#390 in a real UI: with a curve that has no splines and a curve whose Geometry Nodes output is only instances in
the scene, an object-mode click on a mesh selects it (the click no longer stops on a Python error)."""

import os
import sys

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, view3d  # noqa: E402

C = {}


def screen_xy(co):
    area, region = view3d()
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, co)
    return region.x + int(round(p.x)), region.y + int(round(p.y))


def click(xy):
    x, y = xy
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


def selected():
    return sorted(o.name for o in bpy.context.selected_objects)


def scatter_nodes():
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
    return ng


@step
def s_setup():
    setup()
    for ob in list(bpy.data.objects):
        if ob.name != "Cube":
            bpy.data.objects.remove(ob)
    cube = bpy.data.objects["Cube"]
    cube.location = (0, 0, 0)
    sc = bpy.context.scene
    sc.collection.objects.link(bpy.data.objects.new("curve2", bpy.data.curves.new("curve2", 'CURVE')))
    cu = bpy.data.curves.new("scatter", 'CURVE')
    spline = cu.splines.new('POLY')
    spline.points.add(1)
    spline.points[0].co = (-3, 0, 2, 1)
    spline.points[1].co = (3, 0, 2, 1)
    ob = bpy.data.objects.new("Scatter_Tool", cu)
    sc.collection.objects.link(ob)
    ob.modifiers.new("Scatter", 'NODES').node_group = scatter_nodes()
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.update()


@step
def s_click():
    click(screen_xy(Vector((0.3, -1.0, 0.2))))      # on the cube's front face


@step
def s_check():
    check(f"a click on the cube selects it with curves that draw no curve in the scene ({selected()})",
          selected() == ["Cube"])


run()
