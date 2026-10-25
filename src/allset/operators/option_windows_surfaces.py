# SPDX-License-Identifier: GPL-3.0-or-later
"""Step 181: Maya option windows of the Surfaces menu (same spec as operators/option_windows.py; option_windows._extend
appends ``WINDOWS``). Titles, field labels and factory values:  (each option var with
its $M file:line) and the Maya 2022 option window procs ($M\\others\\perform<X>.mel, cited per window; labels resolved
through $M\\..\\resources\\Maya). Fields Blender / the kit can't follow are listed as ``missing``. Operators:
operators/surfaces_maya.py. Values are Maya values (lengths in Maya units)."""

import bpy

from .option_windows import F, Window

_OUTPUT = "Output geometry: NURBS only (Polygons / Bezier not made)"
_RANGE = "Curve range: Complete only (Partial not supported)"


def _degree(label):
    # "Linear" / "Cubic" / "1 Linear" / "3 Cubic" / "2" ... -> the operator's '1' / '3' / ...
    return {"Linear": "1", "Cubic": "3"}.get(label, label.split()[0])


def _run_loft(context, v):
    return bpy.ops.allset.loft('EXEC_DEFAULT', uniform=v["parameterization"] == "Uniform",
                               auto_reverse=v["auto_reverse"], close=v["close"], degree=_degree(v["degree"]),
                               section_spans=v["section_spans"])


def _run_revolve(context, v):
    return bpy.ops.allset.revolve('EXEC_DEFAULT', axis=v["axis"], pivot=v["pivot"].upper(),
                                  pivot_point=tuple(v["pivot_point"]), start_sweep=v["start_sweep"],
                                  end_sweep=v["end_sweep"], degree=_degree(v["degree"]), segments=v["segments"])


_STYLES = {"Distance": 'DISTANCE', "Flat": 'FLAT', "Tube": 'TUBE'}


def _run_extrude(context, v):
    direction = 'NORMAL' if v["direction"] == "Profile normal" else v["direction_vector"][0]   # "X axis" -> 'X'
    return bpy.ops.allset.surface_extrude(
        'EXEC_DEFAULT', style=_STYLES[v["style"]], length=v["length"], direction=direction,
        result_position='PROFILE' if v["result_position"] == "At profile" else 'PATH',
        pivot='CLOSEST' if v["pivot"] == "Closest end point" else 'COMPONENT')


def _run_birail1(context, v):
    return bpy.ops.allset.birail1('EXEC_DEFAULT', proportional=v["transform_control"] == "Proportional")


def _boundary(kind):
    def run(context, v):
        return bpy.ops.allset.surface_boundary('EXEC_DEFAULT', kind=kind)
    return run


def _run_attach(context, v):
    return bpy.ops.allset.surface_attach('EXEC_DEFAULT', method=v["method"].upper(), bias=v["bias"],
                                         keep_originals=v["keep_originals"])


def _run_detach(context, v):
    return bpy.ops.allset.surface_detach('EXEC_DEFAULT', keep_original=v["keep_original"])


_REVERSE = {"U": 'U', "V": 'V', "Swap": 'SWAP', "Both": 'BOTH'}


def _run_reverse(context, v):
    return bpy.ops.allset.surface_reverse('EXEC_DEFAULT', direction=_REVERSE[v["direction"]])


def _run_rebuild(context, v):
    return bpy.ops.allset.surface_rebuild('EXEC_DEFAULT', spans_u=v["spans_u"], spans_v=v["spans_v"],
                                          degree_u=_degree(v["degree_u"]), degree_v=_degree(v["degree_v"]))


REBUILD_DEGREES = ("1 Linear", "2", "3 Cubic", "5", "7")    # Maya-665 (Original: missing)

WINDOWS = [
    # Surfaces > Loft (Maya-302, title :392; option vars :33-51: Uniform, auto reverse, cubic, 1 span)
    Window("loft", "Loft Options", "Loft", ("allset.loft", {}), [
        F("parameterization", "Parameterization:", "enum", "Uniform", items=("Uniform", "Chord length")),
        F("auto_reverse", "", "bool", True, text="Auto reverse"),
        F("close", "", "bool", False, text="Close"),
        F("degree", "Surface degree:", "enum", "Cubic", items=("Linear", "Cubic")),
        F("section_spans", "Section spans:", "int", 1, lo=1, hi=500),
    ], _run_loft, paths=("Surfaces/Loft",), missing=(_RANGE, _OUTPUT)),
    # Surfaces > Revolve (Maya-376, title :492; Maya-131: axis Y, Object
    # pivot, 0 - 360, cubic, segments 8)
    Window("revolve", "Revolve Options", "Revolve", ("allset.revolve", {}), [
        F("axis", "Axis preset:", "enum", "Y", items=("X", "Y", "Z")),
        F("pivot", "Pivot:", "enum", "Object", items=("Object", "Preset")),
        F("pivot_point", "Pivot point:", "vec3", (0.0, 0.0, 0.0)),
        F("degree", "Surface degree:", "enum", "Cubic", items=("Linear", "Cubic")),
        F("start_sweep", "Start sweep angle:", "float", 0.0, lo=0.0, hi=360.0),
        F("end_sweep", "End sweep angle:", "float", 360.0, lo=0.0, hi=360.0),
        F("segments", "Segments:", "int", 8, lo=1, hi=1000),
    ], _run_revolve, paths=("Surfaces/Revolve",),
        missing=("Axis preset: Free / Axis (X, Y, Z only)", "Use tolerance: Local / Global (None = Segments only)",
                 _RANGE, _OUTPUT)),
    # Surfaces > Extrude (Maya-342, title :420; Maya-125: Tube, At profile,
    # Closest end point, Profile normal, X axis, length 1)
    Window("surface_extrude", "Extrude Options", "Extrude", ("allset.surface_extrude", {}), [
        F("style", "Style:", "enum", "Tube", items=("Distance", "Flat", "Tube")),
        F("length", "Extrude length:", "float", 1.0, lo=0.0, hi=10.0),
        F("direction", "Direction:", "enum", "Profile normal", items=("Specify", "Profile normal")),
        F("direction_vector", "Direction vector:", "enum", "X axis", items=("X axis", "Y axis", "Z axis")),
        F("result_position", "Result position:", "enum", "At profile", items=("At profile", "At path")),
        F("pivot", "Pivot:", "enum", "Closest end point", items=("Closest end point", "Component")),
    ], _run_extrude, paths=("Surfaces/Extrude",),
        missing=("Direction vector: Free", "Orientation: Path direction (Profile normal only)",
                 "Surface degree along the length (Distance: always Linear, as Maya makes it)",
                 "Rotation (0) / Scale (1): Maya's rule not reproduced", _RANGE, _OUTPUT)),
    # Surfaces > Birail > Birail 1 Tool (Maya-344, 364-369, 405-444; title "Birail 1 Options" :528-530,
    # button "Birail 1 Tool" :490; option vars :31-59: Proportional, no continuity, no rebuild)
    Window("birail1", "Birail 1 Options", "Birail 1 Tool", ("allset.birail1", {}), [
        F("transform_control", "Transform control:", "enum", "Proportional",
          items=("Non proportional", "Proportional")),
    ], _run_birail1, paths=("Surfaces/Birail/Birail 1 Tool",),
        missing=("Continuity: Profile (off)", "Rebuild: Profile / First rail / Second rail (off)", _OUTPUT,
                 "Tool behavior: picks from the selection (profile = the curve touching both rails)")),
    # Surfaces > Boundary (Maya-380, title :471; option vars :33-50: Automatic, Optional)
    Window("surface_boundary", "Boundary Options", "Boundary", ("allset.surface_boundary", {"kind": 'BOUNDARY'}), [],
           _boundary('BOUNDARY'), paths=("Surfaces/Boundary",),
           missing=("Curve ordering: Automatic only (As selected not supported)",
                    "Common end points: Optional only", "End point tolerance: Global", _RANGE, _OUTPUT)),
    # Surfaces > Square (Maya-417, title :508; option vars :33-59: Tangent, 5 checkpoints)
    Window("surface_square", "Square Surface Options", "Square Surface",
           ("allset.surface_boundary", {"kind": 'SQUARE'}), [], _boundary('SQUARE'), paths=("Surfaces/Square",),
           missing=("Continuity type: Fixed boundary / Tangent / Implied tangent (no neighbour surfaces: one patch)",
                    "Curve fit checkpoints (5)", "End point tolerance: Global", "Rebuild: Curve 1 - 4 (off)",
                    _OUTPUT)),
    # Surfaces > Attach (Maya-249, title :383; option vars :30-60: Blend, bias 0.5, keep originals)
    Window("surface_attach", "Attach Surfaces Options", "Attach", ("allset.surface_attach", {}), [
        F("method", "Attach method:", "enum", "Blend", items=("Connect", "Blend")),
        F("bias", "Blend bias:", "float", 0.5, lo=0.0, hi=1.0),
        F("keep_originals", "", "bool", True, text="Keep originals"),
    ], _run_attach, paths=("Surfaces/Attach",),
        missing=("Multiple knots: Keep / Remove (Keep)", "Insert knot / Insert parameter (off, 0.1)")),
    # Surfaces > Detach (Maya, title :276; Keep original off :34)
    Window("surface_detach", "Detach Surfaces Options", "Detach", ("allset.surface_detach", {}), [
        F("keep_original", "", "bool", False, text="Keep original"),
    ], _run_detach, paths=("Surfaces/Detach",)),
    # Surfaces > Reverse Direction (Maya-147, title :212; Maya-39: U)
    Window("surface_reverse", "Reverse Surface Direction Options", "Reverse", ("allset.surface_reverse", {}), [
        F("direction", "Surface direction:", "enum", "U", items=("U", "V", "Swap", "Both")),
    ], _run_reverse, paths=("Surfaces/Reverse Direction",), missing=("Keep original (off)",)),
    # Surfaces > Rebuild (Maya-686, title :819; Maya-100:
    # Uniform, 4 x 4 spans, cubic both ways, U and V)
    Window("surface_rebuild", "Rebuild Surface Options", "Rebuild", ("allset.surface_rebuild", {}), [
        F("spans_u", "Number of spans U:", "int", 4, lo=1, hi=5000),
        F("spans_v", "Number of spans V:", "int", 4, lo=1, hi=5000),
        F("degree_u", "Degree U:", "enum", "3 Cubic", items=REBUILD_DEGREES),
        F("degree_v", "Degree V:", "enum", "3 Cubic", items=REBUILD_DEGREES),
    ], _run_rebuild, paths=("Surfaces/Rebuild",),
        missing=("Rebuild type: Reduce / Match knots / No multiple knots / Non-rational / End conditions / Trim convert "
                 "/ Bezier (Uniform only)", "Parameter range: Keep / 0 to #spans (0 to 1 only)",
                 "Direction: U / V (U and V only)", "Keep: Corners / CVs / NumSpans", "Degree: Original",
                 "Keep original (off)", "Use tolerance", _OUTPUT)),
]
