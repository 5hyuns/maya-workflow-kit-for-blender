# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya option windows of the UV Editor's Cut/Sew menu (Auto Seams, Move and Sew, Merge, Stitch Together).

Same spec as operators/option_windows_spec.py; option_windows._extend appends ``WINDOWS``. Each window runs the
item's command with its values, and a plain menu click runs them once they are saved, like Maya. Defaults: Auto
Seams cuts automatic seams; Move and Sew moves shells of any size (Limit shell size off, 10 faces once it is on);
Merge UVs merges within 0.01; Stitch Together stitches the smaller shells onto the larger ones.
"""

import bpy

from .option_windows import F, Window


def _run_auto_seams(context, v):
    return bpy.ops.allset.uv_auto_seams('EXEC_DEFAULT', seams=v["seams"].upper(),
                                       method='AUTOMATIC' if v["method"] == "Automatic" else 'HARD_EDGES')


def _run_move_sew(context, v):
    return bpy.ops.allset.uv_move_sew('EXEC_DEFAULT', limit=v["limit"], faces=v["faces"])


def _run_merge(context, v):
    return bpy.ops.allset.uv_merge('EXEC_DEFAULT', distance=v["distance"])


def _run_stitch(context, v):
    return bpy.ops.uv.stitch('INVOKE_DEFAULT')      # the menu item's own command (Blender Stitch)


WINDOWS = [
    Window("uv_auto_seams", "Auto Seams Options", "Auto Seams", None, [
        F("seams", "Seams:", "enum", "Cut", items=("Cut", "Select")),
        F("method", "Method:", "enum", "Automatic", items=("Automatic", "Cut along hard edges")),
    ], _run_auto_seams, paths=("UV Editor/Cut/Sew/Auto Seams",),
        missing=("Fix non-manifold geometry", "Shell Splitting Tolerance, Connect Holes")),
    Window("uv_move_sew", "Move and Sew UVs Options", "Move and Sew", None, [
        F("limit", "", "bool", False, text="Limit shell size"),
        F("faces", "Number of faces:", "int", 10, lo=0, hi=100),
    ], _run_move_sew, paths=("UV Editor/Cut/Sew/Move and Sew",),
        enabled=lambda v, name: name != "faces" or v["limit"]),
    Window("uv_merge", "Merge UVs Options", "Merge UVs", None, [
        F("distance", "Threshold:", "float", 0.01, lo=0.0, hi=1.0),
    ], _run_merge, paths=("UV Editor/Cut/Sew/Merge",)),
    Window("uv_stitch_together", "Stitch Together Options", "Stitch Together", None, [],
           _run_stitch, paths=("UV Editor/Cut/Sew/Stitch Together",),
           missing=("Stitch Together: Smallest to Largest / Largest to Smallest",)),
]
