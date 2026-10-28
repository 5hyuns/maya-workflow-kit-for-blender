"""Reference mesh: a 2-unit cube with a top inset and a front inset, extruded along two axes.

The expected boundaries come from the starting mesh and geometric intersections,
not from the addon output's polygon count.
"""
import bmesh
from mathutils import Vector


def inset(bm, axis, sign, width):
    face = max((f for f in bm.faces if f.normal[axis]*sign > .99),
               key=lambda f: f.calc_center_median()[axis]*sign)
    bmesh.ops.inset_region(bm, faces=[face], thickness=width, depth=0, use_even_offset=True)
    bm.normal_update()
    bm.faces.index_update()
    return min((f for f in bm.faces if f.normal[axis]*sign > .99
                and f.calc_center_median()[axis]*sign > .99),
               key=lambda f: sum(f.calc_center_median()[i]**2 for i in range(3) if i != axis))


def mesh():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2)
    bm.normal_update()
    inset(bm, 2, 1, .5)   # top opening: 1 x 1
    inset(bm, 1, -1, .2)  # front opening: 1.6 x 1.6
    return bm


def patch(bm, axis, sign):
    bm.faces.index_update()
    return min((f for f in bm.faces if f.normal[axis]*sign > .99
                and f.calc_center_median()[axis]*sign > .99),
               key=lambda f: sum(f.calc_center_median()[i]**2 for i in range(3) if i != axis)).index


def covered(bm, p, q, eps=1e-5):
    p, q = Vector(p), Vector(q)
    d = q-p
    length = d.length
    axis = d/length
    intervals = []
    for edge in bm.edges:
        coords = [v.co-p for v in edge.verts]
        if any((v-axis*v.dot(axis)).length > eps for v in coords):
            continue
        a, b = sorted(v.dot(axis) for v in coords)
        if b >= -eps and a <= length+eps:
            intervals.append((max(0., a), min(length, b)))
    end = 0.
    for a, b in sorted(intervals):
        if a > end+eps:
            return False
        end = max(end, b)
    return end >= length-eps
