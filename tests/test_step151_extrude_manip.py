"""Step 151 lane B: Maya's polyExtrudeFace manipulator - three local
translate arrows, a scale cube per axis, three plane handles and the centre square (uniform scale) - and the
polyExtrudeFace values they drive (Local Translate X / Y, Local Scale X / Y / Z, operators/extrude.py).

MAYA = Maya 2022 (polyCube 1 x 1 x 1, polyExtrudeFacet, then setAttr on the node): faces by Blender side
(Maya f[0] +Z = -y,
f[1] top, f[2] -Z = +y, f[3] bottom, f[4] +x, f[5] -x), node values, mesh preparation, every vertex sorted
(Maya Y-up -> Blender (x, -z, y)). "slant" = Maya vtx[2:3] (top front edge) moved +0.4 up, "trap" = vtx[3] / vtx[5]
(top right edge) +0.25 X, "rot" = the cube rotated 30 deg about Maya Y (Blender Z). Maya's rules: each face's local
Z = its normal, X = Maya world X projected into the face (Maya world Z for faces looking along X: f[4] / f[5]),
Y = Z x X; Local Scale scales about the face's vertex mean (a 5-sided cap: the mean, not the bbox centre = the
node's pivot); a shared vertex takes the mean of its faces' moves (Keep Faces Together); rings take the level
fraction; Offset adds after the scale; Local Direction is in world space (the rotated cube moves along world X)."""

import math
from importlib import import_module
from types import SimpleNamespace

import bmesh
import bpy
from mathutils import Matrix, Vector

import kit

ex = import_module(kit.MODULE + ".operators.extrude")
in_view = import_module(kit.MODULE + ".ui.in_view")

SIDES = {"top": Vector((0, 0, 1)), "bottom": Vector((0, 0, -1)), "+x": Vector((1, 0, 0)), "-x": Vector((-1, 0, 0)),
         "+y": Vector((0, 1, 0)), "-y": Vector((0, -1, 0))}

MAYA = {
    'top_ltx': (['top'], {'local_translate_x': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.2, -0.5, 0.5), (-0.2, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.8, -0.5, 0.5), (0.8, 0.5, 0.5)]),
    'top_lty': (['top'], {'local_translate_y': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, -0.2, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.5, 0.8, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, -0.2, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.5, 0.8, 0.5)]),
    'top_lsx': (['top'], {'local_scale_x': 0.5}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.25, -0.5, 0.5), (-0.25, 0.5, 0.5), (0.25, -0.5, 0.5), (0.25, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'top_lsy': (['top'], {'local_scale_y': 0.5}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, -0.25, 0.5), (-0.5, 0.25, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, -0.25, 0.5), (0.5, 0.25, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'top_lsz_ltz': (['top'], {'local_scale_z': 2.0, 'local_translate_z': 0.5}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, -0.5, 1.0), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.5, 0.5, 1.0), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, -0.5, 1.0), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.5, 0.5, 1.0)]),
    'top_ls_all_ltz': (['top'], {'local_scale_x': 0.5, 'local_scale_y': 0.5, 'local_scale_z': 0.5, 'local_translate_z': 0.5}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.25, -0.25, 1.0), (-0.25, 0.25, 1.0), (0.25, -0.25, 1.0), (0.25, 0.25, 1.0), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'top_ls_offset': (['top'], {'local_scale_x': 0.5, 'offset': 0.1}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.15, -0.4, 0.5), (-0.15, 0.4, 0.5), (0.15, -0.4, 0.5), (0.15, 0.4, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'top_ls_thick': (['top'], {'local_scale_x': 0.5, 'thickness': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.25, -0.5, 0.8), (-0.25, 0.5, 0.8), (0.25, -0.5, 0.8), (0.25, 0.5, 0.8), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'ltx_offset': (['top'], {'local_translate_x': 0.3, 'offset': 0.1}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.1, -0.4, 0.5), (-0.1, 0.4, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.7, -0.4, 0.5), (0.7, 0.4, 0.5)]),
    'two_kft_ltx': (['top', '+y'], {'local_translate_x': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.2, -0.5, 0.5), (-0.2, 0.5, -0.5), (-0.2, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.8, -0.5, 0.5), (0.8, 0.5, -0.5), (0.8, 0.5, 0.5)]),
    'two_kft_lty': (['top', '+y'], {'local_translate_y': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, -0.2, 0.5), (-0.5, 0.5, -0.8), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.5, 0.65, 0.35), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, -0.2, 0.5), (0.5, 0.5, -0.8), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.5, 0.65, 0.35)]),
    'two_kft_lsx': (['top', '+y'], {'local_scale_x': 0.5}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.25, -0.5, 0.5), (-0.25, 0.5, -0.5), (-0.25, 0.5, 0.5), (0.25, -0.5, 0.5), (0.25, 0.5, -0.5), (0.25, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'two_kft_lsz': (['top', '+y'], {'local_scale_z': 2.0, 'local_translate_z': 0.5}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, -0.5, 1.0), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.5, 0.75, 0.75), (-0.5, 1.0, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, -0.5, 1.0), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.5, 0.75, 0.75), (0.5, 1.0, -0.5)]),
    'two_kft_ls_all': (['top', '+y'], {'local_scale_x': 0.5, 'local_scale_y': 0.5, 'local_scale_z': 0.5}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.25, -0.25, 0.5), (-0.25, 0.375, 0.375), (-0.25, 0.5, -0.25), (0.25, -0.25, 0.5), (0.25, 0.375, 0.375), (0.25, 0.5, -0.25), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'two_sep_ltx': (['top', '+y'], {'local_translate_x': 0.3, 'keep_faces_together': False}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.2, -0.5, 0.5), (-0.2, 0.5, -0.5), (-0.2, 0.5, 0.5), (-0.2, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.8, -0.5, 0.5), (0.8, 0.5, -0.5), (0.8, 0.5, 0.5), (0.8, 0.5, 0.5)]),
    'two_sep_lsx': (['top', '+y'], {'local_scale_x': 0.5, 'keep_faces_together': False}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.25, -0.5, 0.5), (-0.25, 0.5, -0.5), (-0.25, 0.5, 0.5), (-0.25, 0.5, 0.5), (0.25, -0.5, 0.5), (0.25, 0.5, -0.5), (0.25, 0.5, 0.5), (0.25, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'two_sep_ls_all': (['top', '+y'], {'local_scale_x': 0.5, 'local_scale_y': 0.5, 'local_scale_z': 0.5, 'keep_faces_together': False}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.25, -0.25, 0.5), (-0.25, 0.25, 0.5), (-0.25, 0.5, -0.25), (-0.25, 0.5, 0.25), (0.25, -0.25, 0.5), (0.25, 0.25, 0.5), (0.25, 0.5, -0.25), (0.25, 0.5, 0.25), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'topright_kft_ltx': (['top', '+x'], {'local_translate_x': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.2, -0.5, 0.5), (-0.2, 0.5, 0.5), (0.5, -0.8, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.2, -0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.65, -0.65, 0.5), (0.65, 0.35, 0.5)]),
    'topright_kft_lsx': (['top', '+x'], {'local_scale_x': 0.5}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.25, -0.5, 0.5), (-0.25, 0.5, 0.5), (0.375, -0.375, 0.5), (0.375, 0.375, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, -0.25, -0.5), (0.5, 0.25, -0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'div2_ltx': (['top'], {'local_translate_x': 0.3, 'local_translate_z': 0.4, 'divisions': 2}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.35, -0.5, 0.7), (-0.35, 0.5, 0.7), (-0.2, -0.5, 0.9), (-0.2, 0.5, 0.9), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.65, -0.5, 0.7), (0.65, 0.5, 0.7), (0.8, -0.5, 0.9), (0.8, 0.5, 0.9)]),
    'div2_lsx': (['top'], {'local_scale_x': 0.5, 'local_translate_z': 0.4, 'divisions': 2}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.375, -0.5, 0.7), (-0.375, 0.5, 0.7), (-0.25, -0.5, 0.9), (-0.25, 0.5, 0.9), (0.25, -0.5, 0.9), (0.25, 0.5, 0.9), (0.375, -0.5, 0.7), (0.375, 0.5, 0.7), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'face0_ltx': (['-y'], {'local_translate_x': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.2, -0.5, -0.5), (-0.2, -0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.8, -0.5, -0.5), (0.8, -0.5, 0.5)]),
    'face0_lty': (['-y'], {'local_translate_y': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, -0.2), (-0.5, -0.5, 0.5), (-0.5, -0.5, 0.8), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, -0.2), (0.5, -0.5, 0.5), (0.5, -0.5, 0.8), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'face1_ltx': (['top'], {'local_translate_x': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.2, -0.5, 0.5), (-0.2, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.8, -0.5, 0.5), (0.8, 0.5, 0.5)]),
    'face1_lty': (['top'], {'local_translate_y': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, -0.2, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.5, 0.8, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, -0.2, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.5, 0.8, 0.5)]),
    'face2_ltx': (['+y'], {'local_translate_x': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.2, 0.5, -0.5), (-0.2, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.8, 0.5, -0.5), (0.8, 0.5, 0.5)]),
    'face2_lty': (['+y'], {'local_translate_y': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.8), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.2), (-0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.8), (0.5, 0.5, -0.5), (0.5, 0.5, 0.2), (0.5, 0.5, 0.5)]),
    'face3_ltx': (['bottom'], {'local_translate_x': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.2, -0.5, -0.5), (-0.2, 0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.8, -0.5, -0.5), (0.8, 0.5, -0.5)]),
    'face3_lty': (['bottom'], {'local_translate_y': 0.3}, None,
        [(-0.5, -0.8, -0.5), (-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.2, -0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, -0.8, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.2, -0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'face4_ltx': (['+x'], {'local_translate_x': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, -0.8, -0.5), (0.5, -0.8, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.2, -0.5), (0.5, 0.2, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'face4_lty': (['+x'], {'local_translate_y': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, -0.5, -0.8), (0.5, -0.5, -0.5), (0.5, -0.5, 0.2), (0.5, -0.5, 0.5), (0.5, 0.5, -0.8), (0.5, 0.5, -0.5), (0.5, 0.5, 0.2), (0.5, 0.5, 0.5)]),
    'face5_ltx': (['-x'], {'local_translate_x': 0.3}, None,
        [(-0.5, -0.8, -0.5), (-0.5, -0.8, 0.5), (-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.2, -0.5), (-0.5, 0.2, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'face5_lty': (['-x'], {'local_translate_y': 0.3}, None,
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, -0.2), (-0.5, -0.5, 0.5), (-0.5, -0.5, 0.8), (-0.5, 0.5, -0.5), (-0.5, 0.5, -0.2), (-0.5, 0.5, 0.5), (-0.5, 0.5, 0.8), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'slant_ltx': (['top'], {'local_translate_x': 0.3}, 'slant',
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.9), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.2, -0.5, 0.9), (-0.2, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.9), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.8, -0.5, 0.9), (0.8, 0.5, 0.5)]),
    'slant_lty': (['top'], {'local_translate_y': 0.3}, 'slant',
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.9), (-0.5, -0.2215, 0.7886), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.5, 0.7785, 0.3886), (0.5, -0.5, -0.5), (0.5, -0.5, 0.9), (0.5, -0.2215, 0.7886), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.5, 0.7785, 0.3886)]),
    'slant_lsx': (['top'], {'local_scale_x': 0.5}, 'slant',
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.9), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.25, -0.5, 0.9), (-0.25, 0.5, 0.5), (0.25, -0.5, 0.9), (0.25, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.9), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'slant_lsy': (['top'], {'local_scale_y': 0.5}, 'slant',
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.9), (-0.5, -0.25, 0.8), (-0.5, 0.25, 0.6), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.9), (0.5, -0.25, 0.8), (0.5, 0.25, 0.6), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]),
    'trap_lsx': (['top'], {'local_scale_x': 0.5}, 'trap',
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.1875, -0.5, 0.5), (-0.1875, 0.5, 0.5), (0.4375, -0.5, 0.5), (0.4375, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (0.75, -0.5, 0.5), (0.75, 0.5, 0.5)]),
    'trap_lsy': (['top'], {'local_scale_y': 0.5}, 'trap',
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, -0.25, 0.5), (-0.5, 0.25, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (0.75, -0.5, 0.5), (0.75, -0.25, 0.5), (0.75, 0.25, 0.5), (0.75, 0.5, 0.5)]),
    'trap_ltx': (['top'], {'local_translate_x': 0.3}, 'trap',
        [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.2, -0.5, 0.5), (-0.2, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (0.75, -0.5, 0.5), (0.75, 0.5, 0.5), (1.05, -0.5, 0.5), (1.05, 0.5, 0.5)]),
    'rot_ltx': (['top'], {'local_translate_x': 0.3}, 'rot',
        [(-0.683, 0.183, -0.5), (-0.683, 0.183, 0.5), (-0.383, 0.183, 0.5), (-0.183, -0.683, -0.5), (-0.183, -0.683, 0.5), (0.117, -0.683, 0.5), (0.183, 0.683, -0.5), (0.183, 0.683, 0.5), (0.483, 0.683, 0.5), (0.683, -0.183, -0.5), (0.683, -0.183, 0.5), (0.983, -0.183, 0.5)]),
    'rot_lsx': (['top'], {'local_scale_x': 0.5}, 'rot',
        [(-0.683, 0.183, -0.5), (-0.683, 0.183, 0.5), (-0.3415, 0.183, 0.5), (-0.183, -0.683, -0.5), (-0.183, -0.683, 0.5), (-0.0915, -0.683, 0.5), (0.0915, 0.683, 0.5), (0.183, 0.683, -0.5), (0.183, 0.683, 0.5), (0.3415, -0.183, 0.5), (0.683, -0.183, -0.5), (0.683, -0.183, 0.5)]),
}


def _prep(bm, prep):
    if prep == "slant":
        for v in bm.verts:
            if v.co.y < 0 and v.co.z > 0:
                v.co.z += 0.4
    elif prep == "trap":
        for v in bm.verts:
            if v.co.x > 0 and v.co.z > 0:
                v.co.x += 0.25
    elif prep == "rot":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(30), 3, 'Z'))
    bm.normal_update()


def _pick(bm, sides):
    return [f for f in bm.faces if any(f.normal.dot(SIDES[s]) > 0.7 for s in sides)]


def _points(coords):
    return sorted(tuple(round(c, 4) + 0.0 for c in co) for co in coords)


def _close(got, want, tol=2e-4):
    return len(got) == len(want) and all(max(abs(a - b) for a, b in zip(g, w)) <= tol for g, w in zip(got, want))


def test_geometry_matches_maya():
    bad = []
    for case, (sides, params, prep, want) in MAYA.items():
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        _prep(bm, prep)
        ex.extrude(bm, _pick(bm, sides), **params)
        got = _points(v.co for v in bm.verts)
        if not _close(got, want):
            bad.append((case, got, want))
        bm.free()
    assert not bad, bad


def test_fast_path_equals_rebuild():
    """A drag previews by moving the vertices (rec.moved); the edit rebuilds: both give the same mesh."""
    params = dict(local_translate_x=0.2, local_translate_y=-0.1, local_scale_x=0.7, local_scale_y=1.3,
                  local_scale_z=0.9, thickness=0.1, local_translate_z=0.3, offset=0.05)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.normal_update()
    _caps, moved = ex.extrude(bm, _pick(bm, ["top", "+x"]), divisions=3)
    ex.place(moved, 0.1, 0.3, 0.05, **{k: params[k] for k in ex.MANIP_FIELDS})
    fast = _points(v.co for v in bm.verts)
    bm.free()
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.normal_update()
    ex.extrude(bm, _pick(bm, ["top", "+x"]), divisions=3, **params)
    assert _points(v.co for v in bm.verts) == fast
    bm.free()


def test_face_axes():
    x, y = ex.face_axes(Vector((0, 0, 1)))
    assert (x - Vector((1, 0, 0))).length < 1e-9 and (y - Vector((0, 1, 0))).length < 1e-9
    x, y = ex.face_axes(Vector((1, 0, 0)))          # looks along X: Maya world Z (Blender -Y)
    assert (x - Vector((0, -1, 0))).length < 1e-9 and (y - Vector((0, 0, -1))).length < 1e-9, (x, y)


# --- the record, the operators, undo ---------------------------------------------------------------

def _cube(rot_z=0.0):
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.context.scene.pop(ex.COUNTER, None)
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    ob.rotation_euler.z = math.radians(rot_z)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(False)
    for f in bm.faces:
        if f.normal.z > 0.9:
            f.select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    bpy.ops.ed.undo_push(message="test start")
    assert bpy.ops.allset.extrude('EXEC_DEFAULT', True) == {'FINISHED'}
    return ob


def _world(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return _points(ob.matrix_world @ v.co for v in bm.verts)


def test_record_keeps_the_manipulator_values():
    ob = _cube()
    _o, rec = ex.active(bpy.context)
    assert rec.params == ex.DEFAULTS and set(ex.MANIP_FIELDS) <= set(rec.params)
    # In-View Editor / Channel Box rows stay Maya's five (modeling_03.png)
    assert rec.spec.fields == ex.FIELDS and rec.spec.manip == ex.MANIP_FIELDS
    assert ex.set_params(bpy.context, local_scale_x=0.5) == {'FINISHED'}
    assert ex.set_params(bpy.context, local_translate_y=0.3) == {'FINISHED'}     # keeps the scale
    _o, rec = ex.active(bpy.context)
    assert abs(rec.params["local_scale_x"] - 0.5) < 1e-6 and abs(rec.params["local_translate_y"] - 0.3) < 1e-6
    caps = sorted({(round(p[0], 4), round(p[1], 4)) for p in _world(ob) if p[2] > 0.4})
    assert caps == [(-0.5, -0.5), (-0.5, 0.5), (-0.25, -0.2), (-0.25, 0.8), (0.25, -0.2), (0.25, 0.8),
                    (0.5, -0.5), (0.5, 0.5)], caps


def test_rotated_object_uses_world_x_and_one_undo_step():
    """Maya's Local Direction is world X: on a cube turned 30 deg the faces still move along world X (rot_ltx)."""
    ob = _cube(rot_z=30.0)
    assert ex.set_params(bpy.context, local_translate_x=0.3) == {'FINISHED'}
    assert _close(_world(ob), MAYA["rot_ltx"][3]), _world(ob)
    assert ex.set_params(bpy.context, local_translate_x=0.0, local_scale_x=0.5) == {'FINISHED'}
    assert _close(_world(ob), MAYA["rot_lsx"][3]), _world(ob)
    bpy.ops.ed.undo()                         # one step: back to Local Translate X 0.3
    _o, rec = ex.active(bpy.context)
    assert rec is not None and rec.params["local_scale_x"] == 1.0 and abs(rec.params["local_translate_x"] - 0.3) < 1e-6, \
        rec and rec.params
    assert _close(_world(ob), MAYA["rot_ltx"][3])


# --- the manipulator ----------------------------------------------------------------------------------

def test_handles_and_what_they_drive():
    assert set(in_view.HANDLES) == {"TX", "TY", "TZ", "SX", "SY", "SZ", "PXY", "PYZ", "PXZ", "S"}
    _cube()
    _o, rec = ex.active(bpy.context)
    drive = {h: in_view.handle_fields(rec, h) for h in in_view.HANDLES}
    assert drive["TZ"] == ("local_translate_z",) and drive["SZ"] == ("local_scale_z",)
    assert drive["PYZ"] == ("local_translate_y", "local_translate_z")
    assert drive["S"] == ("local_scale_x", "local_scale_y", "local_scale_z")
    assert all(set(f) <= set(rec.params) for f in drive.values())
    # edge / vertex extrusions, bevels: only their own arrow
    edge = ex.Record("polyExtrudeEdge1", None, ex.EDGE.defaults, ex.EDGE)
    assert {h: in_view.handle_fields(edge, h) for h in in_view.HANDLES if in_view.handle_fields(edge, h)} == \
        {"TZ": ("local_translate_z",)}
    vert = ex.Record("polyExtrudeVertex1", None, ex.VERTEX.defaults, ex.VERTEX)
    assert in_view.handle_fields(vert, "TZ") == ("length",) and in_view.handle_fields(vert, "SX") == ()


def test_shapes_follow_maya_layout():
    for role in ('ARROW', 'CUBE', 'PLANE', 'CENTER'):
        draw, pick = in_view.handle_shapes(role)
        assert draw and pick[1], role
    zs = [p[2] for _t, verts, _f in in_view.handle_shapes('ARROW')[0] for p in verts]
    assert max(zs) == in_view.CONE_TIP and in_view.CONE_TIP < in_view.CUBE_AT - in_view.CUBE_HALF
    cube = [p for _t, verts, _f in in_view.handle_shapes('CUBE')[0] for p in verts]
    assert max(p[2] for p in cube) == in_view.CUBE_AT + in_view.CUBE_HALF
    plane = in_view.handle_shapes('PLANE')[0]
    assert [fill for _t, _v, fill in plane] == [True, False]       # translucent fill + full-colour rim
    rim = plane[1][1]
    assert min(p[0] for p in rim) == in_view.PLANE_AT - in_view.PLANE_HALF


def test_frame_is_maya_local():
    ob = _cube(rot_z=30.0)
    _o, rec = ex.active(bpy.context)
    centre, axes, k = in_view.manip_frame(ob, rec)
    assert (centre - Vector((0, 0, 0.5))).length < 1e-6
    for i, want in enumerate(((1, 0, 0), (0, 1, 0), (0, 0, 1))):    # world X even on the turned cube
        assert (axes.col[i] - Vector(want)).length < 1e-6, (i, axes)
    assert all(abs(x - 1.0) < 1e-6 for x in k)


def _fake(role, fields, idx, **kw):
    f = SimpleNamespace(_role=role, _fields=fields, _idx=idx, _axes=[Vector((1, 0, 0)), Vector((0, 1, 0)),
                        Vector((0, 0, 1))], _k=(1.0, 2.0, 1.0), _unit=0.01, _start=dict(ex.DEFAULTS), _last={},
                        _mouse0=Vector((100, 100)), _sdir=Vector((0.6, 0.8)))
    f.__dict__.update(kw)
    return f


def test_drag_maths():
    values = in_view.ALLSET_OT_extrude_drag.values
    ev = SimpleNamespace(mouse_region_x=150, mouse_region_y=100)
    # arrow: world distance along the axis / (world length of a mesh unit) / Maya unit
    f = _fake('ARROW', ("local_translate_y",), [1], _t0=0.1, _along=lambda c, e, a: 0.5)
    assert values(f, None, ev) == {"local_translate_y": round(0.4 / 2.0 / 0.01, 4)}
    f = _fake('ARROW', ("local_translate_x",), [0], _t0=0.1, _along=lambda c, e, a: None)
    assert values(f, None, ev) == {}                                   # no checked: the press values
    # plane: the hit on the plane split onto its two axes
    f = _fake('PLANE', ("local_translate_x", "local_translate_z"), [0, 2], _h0=Vector((0, 0, 0)),
              _normal=Vector((0, 1, 0)), _on_plane=lambda c, e, n: Vector((0.03, 5.0, -0.02)))
    assert values(f, None, ev) == {"local_translate_x": 3.0, "local_translate_z": -2.0}
    # scale cube: mouse travel along the handle's screen direction, SCALE_PX doubles
    f = _fake('CUBE', ("local_scale_x",), [0], _start=dict(ex.DEFAULTS, local_scale_x=0.5))
    s = bpy.context.preferences.system.ui_scale or 1.0
    want = round(0.5 * (1 + 50 * 0.6 / (in_view.SCALE_PX * s)), 4)
    assert values(f, None, ev) == {"local_scale_x": want}
    # centre: uniform, horizontal drag
    f = _fake('CENTER', ("local_scale_x", "local_scale_y", "local_scale_z"), [])
    want = round(1 + 50 / (in_view.SCALE_PX * s), 4)
    assert values(f, None, ev) == {"local_scale_x": want, "local_scale_y": want, "local_scale_z": want}


def test_registered_without_tooltips():
    assert "bl_rna" in in_view.ALLSET_GT_extrude_handle.__dict__
    assert "bl_rna" in in_view.ALLSET_GGT_extrude.__dict__
    assert bpy.ops.allset.extrude_drag.get_rna_type().properties["handle"].is_hidden
    # Blender would show the target operator's description over a gizmo (#98); 4.5 has Gizmo.use_tooltip
    assert "use_tooltip" in bpy.types.Gizmo.bl_rna.properties
