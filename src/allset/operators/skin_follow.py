# SPDX-License-Identifier: GPL-3.0-or-later
"""A skinned mesh follows its skeleton's transform, like a Maya skin.

Maya's skin reads the joints' world matrices, so moving a skeleton's root joint or a group above it moves the skinned
mesh with it, while the mesh's own transform stays where it is in the hierarchy. Blender's Armature modifier reads
the bones relative to the armature object: moving the armature object (or a group the kit made above it) leaves an
unparented skin behind. The kit gives every skinned mesh a Child Of constraint on its skeleton object whose inverse
is the skeleton's world matrix at bind, so the mesh carries the skeleton's motion since the bind and the Armature
modifier only adds the joints' pose. A mesh that also sits under a moving parent of the skeleton moves twice, like
a Maya skin under a moving group.

The constraint is part of the skin (not a Maya constraint node): the Channel Box and the Attribute Editor don't list
it. Unbind Skin / Delete History remove it (Unbind with Keep / Delete history: the mesh goes back to its bind place;
Bake history and Delete History keep the skin's shape where it is, the mesh's channels unchanged).
"""

import bpy
from mathutils import Matrix

FOLLOW = "Skin Follow"      # constraint name prefix


def is_follow(con):
    return con.type == 'CHILD_OF' and con.name.startswith(FOLLOW)


def follows(mesh):
    return [c for c in getattr(mesh, "constraints", ()) if is_follow(c)]


def _skinned_to(mesh, arm):
    return any(m.type == 'ARMATURE' and m.object == arm for m in getattr(mesh, "modifiers", ()))


def attach(mesh, arm):
    """``mesh`` follows ``arm`` (an armature object) from its current place on. One follow per mesh."""
    have = follows(mesh)
    if have:
        return have[0]
    con = mesh.constraints.new('CHILD_OF')
    con.name = FOLLOW
    con.target = arm
    con.inverse_matrix = arm.matrix_world.inverted_safe()
    con.show_expanded = False
    # first in the stack: the user's own constraints act on the followed transform
    while mesh.constraints[0] != con:
        mesh.constraints.move(list(mesh.constraints).index(con), 0)
    return con


def ensure(arm):
    """Give every mesh skinned to ``arm`` that has no follow one (scenes bound before the kit made it)."""
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and _skinned_to(ob, arm) and not follows(ob):
            attach(ob, arm)


def _own_world(mesh):
    """The mesh's world matrix without its constraints (parent chain + channels)."""
    if mesh.parent is None:
        return mesh.matrix_basis.copy()
    return mesh.parent.matrix_world @ mesh.matrix_parent_inverse @ mesh.matrix_basis


def detach(mesh, keep_shape=False, only_unskinned=True):
    """Remove the mesh's follow. ``keep_shape``: the skeleton's motion since the bind goes into the points (the
    mesh's channels unchanged), so the mesh stays where it shows. ``only_unskinned``: keep a follow whose skeleton
    still deforms the mesh."""
    for con in follows(mesh):
        arm = con.target
        if only_unskinned and arm is not None and _skinned_to(mesh, arm):
            continue
        if keep_shape and arm is not None and mesh.data is not None and con.influence > 0.0:
            w0 = _own_world(mesh)
            f = arm.matrix_world @ con.inverse_matrix
            d = w0.inverted_safe() @ f @ w0
            if not _identity(d):
                from .freeze import bake_into_data
                bake_into_data(mesh, d)
        mesh.constraints.remove(con)


def _identity(m, eps=1e-6):
    i = Matrix.Identity(4)
    return all(abs(m[r][c] - i[r][c]) < eps for r in range(4) for c in range(4))
