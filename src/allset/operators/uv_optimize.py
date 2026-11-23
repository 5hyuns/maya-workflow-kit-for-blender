# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya UV Editor > Modify > Optimize (``allset.uv_optimize``) on bmesh; the solver is uv_optimize_math.

Like Maya: the selected UVs (the UVs of the selected faces, or the selected UVs / vertices) relax against the 3D
surface; every other UV of their shells and every pinned UV stays where it is. Nothing selected = nothing to do.
A shell whose UVs are all selected keeps its UV area (and, in the kit, its centre and orientation). Options (the
Optimize UVs Options window, operators/option_windows_uv.py): Iterations 1, Surfangle 1, Power 100 (below 100
nothing moves), Prevent triangle flips on. The menu item, the UV Toolkit button and the marking menu items run with
the saved values.
"""

import json

import bmesh
import bpy
import numpy as np
from bpy.props import StringProperty

from .. import undo_steps
from . import uv_optimize_math
from .uv_islands import _edit_meshes, islands, sync
from .uv_shells import _loop_selected, uv_points


def _shell_problem(ob, bm, uv, faces, picked, tris):
    """(points, UVs, triangles, held, groups) of one shell: ``groups`` = the loops of each UV, ``tris`` = face ->
    its loop triangles."""
    groups = uv_points(bm, uv, [l for f in faces for l in f.loops])
    index = {l: i for i, ls in enumerate(groups) for l in ls}
    mw = ob.matrix_world
    P = np.array([tuple(mw @ ls[0].vert.co) for ls in groups], float)
    U = np.array([tuple(ls[0][uv].uv) for ls in groups], float)
    held = np.array([not any(l in picked for l in ls) or any(l[uv].pin_uv for l in ls) for ls in groups])
    T = np.array([[index[l] for l in tri] for f in faces for tri in tris.get(f, ())], int)
    return P, U, T.reshape(-1, 3), held, groups


def optimize_mesh(context, ob, values):
    """Optimize the selected UVs of ``ob`` with the option ``values``. Returns the number of shells changed."""
    if int(values["power"]) // 100 <= 0 or int(values["iterations"]) <= 0:
        return 0      # Power below 100 or no iterations: Maya leaves the UVs as they are
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    if uv is None:
        return 0
    synced = sync(context)
    bm.faces.index_update()
    loops = [l for f in bm.faces if not f.hide and (synced or f.select) for l in f.loops]
    picked = {l for l in loops if _loop_selected(l, uv, synced)}
    if not picked:
        return 0
    i = 0
    for f in bm.faces:            # uv_points orders the UVs by loop index
        for l in f.loops:
            l.index = i
            i += 1
    tris = {}
    for tri in bm.calc_loop_triangles():
        tris.setdefault(tri[0].face, []).append(tri)
    done = 0
    for isl in islands(bm, uv, [f for f in bm.faces if not f.hide]):
        if not any(l in picked for f in isl for l in f.loops):
            continue
        P, U, T, held, groups = _shell_problem(ob, bm, uv, isl, picked, tris)
        new = uv_optimize_math.optimize(P, U, T, held, iterations=int(values["iterations"]),
                                        surfangle=float(values["surfangle"]),
                                        prevent_flips=bool(values["prevent_flips"]))
        moved = False
        for ls, p in zip(groups, new):
            if abs(ls[0][uv].uv.x - p[0]) > 1e-9 or abs(ls[0][uv].uv.y - p[1]) > 1e-9:
                moved = True
            for l in ls:
                l[uv].uv = (float(p[0]), float(p[1]))
        done += moved
    bmesh.update_edit_mesh(ob.data)
    return done


def option_values():
    from . import option_windows
    return option_windows.current("uv_optimize")


@undo_steps.no_redo_panel      # no Adjust Last Operation (Maya has none)
class ALLSET_OT_uv_optimize(bpy.types.Operator):
    """Even out the UV distortion of the selected UVs against the 3D surface, with the Optimize options (Maya
    Optimize): pinned and unselected UVs stay, a fully selected shell keeps its size"""
    bl_idname = "allset.uv_optimize"
    bl_label = "Optimize"
    bl_options = {'REGISTER', 'UNDO'}

    # the option values as JSON (Optimize UVs Options window); empty = the saved ones
    options: StringProperty(default="", options={'SKIP_SAVE', 'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        v = {**option_values(), **(json.loads(self.options) if self.options else {})}
        obs = _edit_meshes(context)
        if not any(_has_pick(context, ob) for ob in obs):
            self.report({'WARNING'}, "Select UVs or faces to optimize")
            return {'CANCELLED'}
        for ob in obs:
            optimize_mesh(context, ob, v)
        return {'FINISHED'}


def _has_pick(context, ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    if uv is None:
        return False
    synced = sync(context)
    return any(_loop_selected(l, uv, synced) for f in bm.faces if not f.hide and (synced or f.select)
               for l in f.loops)


classes = (ALLSET_OT_uv_optimize,)
