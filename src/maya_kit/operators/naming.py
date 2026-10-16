# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-style names: ``pCube1`` / ``pCubeShape1`` ().

Maya numbers a new node with a trailing integer and renames the shape to match
the transform. Blender names are unique per datablock type, so the number is
the lowest one free for both the object and its data.
"""

import re

import bpy

_TRAIL = re.compile(r"^(.*?)(\d+)$")


def base_name(name):
    """``pCube12`` -> ``pCube``; ``Cube.001`` -> ``Cube``; ``foo`` -> ``foo``."""
    name = re.sub(r"\.\d{3,}$", "", name)
    m = _TRAIL.match(name)
    return m.group(1) if m and m.group(1) else name


def next_number(base, taken, shape_taken=(), shape_base=None):
    """Lowest N >= 1 with ``base+N`` not in ``taken`` and ``shape_base+N`` not in ``shape_taken``."""
    shape_base = shape_base or f"{base}Shape"
    n = 1
    while f"{base}{n}" in taken or f"{shape_base}{n}" in shape_taken:
        n += 1
    return n


def _collection_for(data):
    if isinstance(data, bpy.types.Mesh):
        return bpy.data.meshes
    if isinstance(data, bpy.types.Curve):
        return bpy.data.curves
    if isinstance(data, bpy.types.Light):
        return bpy.data.lights
    if isinstance(data, bpy.types.Camera):
        return bpy.data.cameras
    return None


def apply_maya_name(ob, base, rename_data=True):
    """Rename ``ob`` to ``base<N>`` and its (single-user) data to ``base Shape<N>``."""
    data = ob.data if rename_data and ob.data is not None and ob.data.users == 1 else None
    coll = _collection_for(data) if data is not None else None
    taken = {o.name for o in bpy.data.objects if o is not ob}
    shape_taken = {d.name for d in coll if d is not data} if coll is not None else ()
    n = next_number(base, taken, shape_taken)
    ob.name = f"{base}{n}"
    if coll is not None:
        data.name = f"{base}Shape{n}"
    return n
