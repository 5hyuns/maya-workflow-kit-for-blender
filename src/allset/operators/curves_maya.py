# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya 2022 curve commands on Blender curves (step 156; rules + Maya ground truth  / .json).

Representation: a Maya uniform-knot NURBS curve = a Blender NURBS spline with
``use_endpoint_u`` and order = degree + 1 (Blender's endpoint knots are the clamped uniform vector, checked).
"""

import bpy
from mathutils import Vector

from . import units


def _new_object(context, name, cvs, degree=3, closed=False):
    data = bpy.data.curves.new(name + "Shape", 'CURVE')
    data.dimensions = '3D'
    sp = data.splines.new('NURBS')
    sp.points.add(len(cvs) - 1)
    for p, c in zip(sp.points, cvs):
        p.co = (c[0], c[1], c[2], 1.0)
    sp.order_u = min(degree + 1, len(cvs))
    sp.use_endpoint_u = not closed
    sp.use_cyclic_u = closed
    sp.resolution_u = 12
    ob = bpy.data.objects.new(name, data)
    context.collection.objects.link(ob)
    for o in context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    context.view_layer.objects.active = ob
    return ob


def make_cv_curve(context, points, degree=3):
    """Maya CV Curve Tool: the clicked points are the CVs (world space, already in scene units)."""
    return _new_object(context, "curve", [Vector(p) for p in points], degree)


def make_ep_curve(context, points, degree=3):
    """Maya EP Curve Tool: the curve passes through the clicked edit points (filled in from lane M's rule)."""
    return _new_object(context, "curve", [Vector(p) for p in points], degree)


def make_arc3(context, p1, p2, p3):
    """Maya Three Point Circular Arc through p1, p2, p3 (filled in from lane M's rule)."""
    return _new_object(context, "curve", [Vector(p1), Vector(p2), Vector(p3)], 2)


def make_arc2(context, p1, p2):
    """Maya Two Point Circular Arc from p1 to p2 (filled in from lane M's rule)."""
    return _new_object(context, "curve", [Vector(p1), Vector(p2)], 1)


classes = ()
