# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya's bend deformer (Deform > Nonlinear > Bend) on a mesh (#379).

Maya bends in its handle's space. The handle's Y axis is the length that bends and its X axis the side it bends to.
A point (x, y, z) of that space whose y, held between Low Bound and High Bound, is y_c turns by t = Curvature * y_c
around the centre (1 / Curvature, 0):

    x' = x cos t + (1 - cos t) / Curvature + (y - y_c) sin t
    y' = sin t / Curvature - x sin t + (y - y_c) cos t
    z' = z

and the result is blended in by Envelope times the point's weight. A line from -1 to 1 along the handle (the bounds
Maya starts with) bends into an arc of 2 * Curvature: Curvature 180 degrees closes a full circle, 90 a half circle.
The parts beyond the bounds go on straight from the bent ends. The handle is made at the centre of the deformed
points with a uniform scale of half their bounding box's longest side, so on a flat plane it stands upright and
bends nothing until it is turned to lie along the plane.

Blender's Simple Deform spreads its angle over the object's own extent between its limits (fractions of that extent),
so the kit bend on a mesh is a Geometry Nodes modifier named like the Maya node (``bend1``) on a shared node group.
The kit handle is an empty whose local +Z (its arrow) is Maya's Y, +X Maya's X and -Y Maya's Z. Curvature is held
in radians and shown in degrees. The weights are the vertex group ``bend1`` (weight 1 on the deformed points), which
Deform > Paint Weights > Nonlinear paints.
"""

import math

import bpy
from mathutils import Vector

GROUP = ".Allset Bend"           # leading dot: hidden in node menus
VERSION_PROP = "allset_bend_version"
VERSION = 1
INPUTS = (("Handle", 'NodeSocketObject', None), ("Curvature", 'NodeSocketFloat', 0.0),
          ("Low Bound", 'NodeSocketFloat', -1.0), ("High Bound", 'NodeSocketFloat', 1.0),
          ("Envelope", 'NodeSocketFloat', 1.0), ("Weight", 'NodeSocketFloat', 1.0))
TICK = 0.2      # the handle's side line: handle units per radian of Curvature


# --- node group -------------------------------------------------------------------------------------------------

def build_group():
    from .wire_deformer import _B
    ng = bpy.data.node_groups.new(GROUP, 'GeometryNodeTree')
    ng[VERSION_PROP] = VERSION
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    for name, stype, default in INPUTS:
        s = ng.interface.new_socket(name, in_out='INPUT', socket_type=stype)
        if default is not None:
            s.default_value = default
        if name == "Curvature":
            s.subtype = 'ANGLE'
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    b = _B(ng)
    gin = b.node("NodeGroupInput")
    gout = b.node("NodeGroupOutput")
    I = gin.outputs                                             # noqa: E741
    info = b.node("GeometryNodeObjectInfo", transform_space='RELATIVE')
    b.link(I["Handle"], info.inputs["Object"])
    to_handle = b.node("FunctionNodeInvertMatrix")
    b.link(info.outputs["Transform"], to_handle.inputs["Matrix"])
    p = b.node("GeometryNodeInputPosition").outputs[0]
    local = b.node("FunctionNodeTransformPoint")
    b.link(p, local.inputs["Vector"])
    b.link(to_handle.outputs["Matrix"], local.inputs["Transform"])
    sep = b.node("ShaderNodeSeparateXYZ")
    b.link(local.outputs["Vector"], sep.inputs[0])
    x, y = sep.outputs["X"], sep.outputs["Z"]                   # Maya X, Y of the handle
    c = I["Curvature"]
    yc = b.math('MINIMUM', b.math('MAXIMUM', y, I["Low Bound"]), I["High Bound"])
    t = b.math('MULTIPLY', c, yc)
    s, co = b.math('SINE', t), b.math('COSINE', t)
    half = b.math('SINE', b.math('MULTIPLY', t, 0.5))
    one_minus_cos = b.math('DIVIDE', b.math('MULTIPLY', b.math('MULTIPLY', half, half), 2.0), c)   # (1 - cos t) / c
    sin_over = b.math('DIVIDE', s, c)                                                               # sin t / c
    d = b.math('SUBTRACT', y, yc)
    x2 = b.math('ADD', b.math('ADD', b.math('MULTIPLY', x, co), one_minus_cos), b.math('MULTIPLY', d, s))
    y2 = b.math('ADD', b.math('SUBTRACT', sin_over, b.math('MULTIPLY', x, s)), b.math('MULTIPLY', d, co))
    comb = b.node("ShaderNodeCombineXYZ")
    b.link(x2, comb.inputs[0])
    b.link(sep.outputs["Y"], comb.inputs[1])
    b.link(y2, comb.inputs[2])
    back = b.node("FunctionNodeTransformPoint")
    b.link(comb.outputs[0], back.inputs["Vector"])
    b.link(info.outputs["Transform"], back.inputs["Transform"])
    bends = b.math('GREATER_THAN', b.math('ABSOLUTE', c), 1e-12)      # Curvature 0: the points stay
    amount = b.math('MULTIPLY', b.math('MULTIPLY', I["Envelope"], I["Weight"]), bends)
    offset = b.vmath('SCALE', b.vmath('SUBTRACT', back.outputs["Vector"], p), scale=amount)
    sp = b.node("GeometryNodeSetPosition")
    b.link(I["Geometry"], sp.inputs["Geometry"])
    b.link(offset, sp.inputs["Offset"])
    b.link(sp.outputs["Geometry"], gout.inputs[0])
    return ng


def group():
    ng = bpy.data.node_groups.get(GROUP)
    if ng is not None and ng.bl_idname == 'GeometryNodeTree' and ng.get(VERSION_PROP) == VERSION:
        return ng
    if ng is not None:
        ng.name = GROUP + ".old"
    return build_group()


# --- modifier inputs ------------------------------------------------------------------------------------------

def is_bend(md):
    return md.type == 'NODES' and md.node_group is not None and md.node_group.name.startswith(GROUP)


def get(md, name):
    from . import wire_deformer
    return wire_deformer.get(md, name)


def set_(md, name, value):
    from . import wire_deformer
    wire_deformer.set_(md, name, value)


def path(md, name):
    """The data path on modifier ``md`` of its input ``name`` (what a key on it animates), or None."""
    from . import wire_deformer
    from .. import compat
    key = wire_deformer.ident(md, name)
    return compat.gn_input_path(key) if key is not None else None


def handle_of(md):
    return get(md, "Handle") if is_bend(md) else None


def add(ob, name, handle, group_name, curvature=0.0, low=-1.0, high=1.0, envelope=1.0):
    """Kit bend ``name`` on mesh ``ob`` driven by empty ``handle`` (Curvature in radians), weights = vertex group
    ``group_name`` (none: every point at weight 1)."""
    md = ob.modifiers.new(name, 'NODES')
    md.node_group = group()
    set_(md, "Handle", handle)
    set_(md, "Curvature", float(curvature))
    set_(md, "Low Bound", min(0.0, float(low)))
    set_(md, "High Bound", max(0.0, float(high)))
    set_(md, "Envelope", float(envelope))
    if group_name:
        from . import wire_deformer
        from .. import compat
        compat.gn_input_attribute(md, wire_deformer.ident(md, "Weight"), group_name)
    return md


# --- the bend in the handle's space (also what the handle draws) -----------------------------------------------

def bent(x, y, curvature, low, high):
    """Maya's bend of handle-space point (x, y) (Maya axes, handle units) -> (x', y')."""
    yc = min(max(y, low), high)
    if abs(curvature) <= 1e-12:
        return x, y
    t = curvature * yc
    s, co = math.sin(t), math.cos(t)
    d = y - yc
    one_minus_cos = 2.0 * math.sin(t * 0.5) ** 2 / curvature
    return x * co + one_minus_cos + d * s, s / curvature - x * s + d * co


def to_kit(mx, my, mz=0.0):
    """A Maya handle-space point -> the kit handle's local space (Maya Y = local +Z, Maya Z = local -Y)."""
    return Vector((mx, -mz, my))


def handle_lines(curvature, low, high):
    """The lines Maya draws for a bend handle, in the kit handle's local space: [(a, b), ...] — the straight line from
    Low Bound to High Bound, the same line bent, and the short line towards the side it bends to."""
    low, high = min(low, 0.0), max(high, 0.0)
    out = [(to_kit(0.0, low), to_kit(0.0, high))]
    turns = abs(curvature) * (high - low)
    n = max(8, min(512, int(math.ceil(turns / (math.pi / 24.0)))))
    pts = [to_kit(*bent(0.0, low + (high - low) * i / n, curvature, low, high)) for i in range(n + 1)]
    out += list(zip(pts[:-1], pts[1:]))
    if abs(curvature) > 1e-12:
        out.append((to_kit(0.0, 0.0), to_kit(TICK * curvature, 0.0)))
    return out
