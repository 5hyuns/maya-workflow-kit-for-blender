# SPDX-License-Identifier: GPL-3.0-or-later
"""Step 144 (#34) Maya option windows of the Deform menu: same spec as operators/option_windows.py (``F`` fields,
``Window`` = one ``allset.opt_<key>`` operator; option_windows._extend appends ``WINDOWS``).

Titles, buttons, Basic tab fields in screen order and factory defaults:  "Deform
option windows" (shots <key>.png). Every Python-built deformer box also has an
Advanced tab (Deformation order / Exclusive / Partition, options_144.md "Common frame"): Blender's modifier stack
has none of them, so they and every Basic field Blender can't honour are listed as ``missing``, never faked.
The deformers themselves: operators/deformers.py.
"""

import bpy
from bpy.props import IntVectorProperty

from .option_windows import F, Window


class FDivisions(F):
    """Maya's three-int field (Lattice Divisions S T U)."""

    def __init__(self, name, label, default):
        super().__init__(name, label, "vec3int", default)

    def prop(self):
        return IntVectorProperty(name=self.label.rstrip(":"), default=self.default, size=3, min=2, soft_max=50)


ADVANCED = ("Deformation order (Advanced tab: Blender evaluates the modifier stack top to bottom)",
            "Exclusive / Partition to use / Partition name (Advanced tab)")
ENVELOPE = "Envelope (the modifier has no strength)"


def _create(kind):
    def run(context, v):
        from . import deformers
        deformers.create(context, kind, v)
        return {'FINISHED'}
    return run


def _cluster(context, v):
    return bpy.ops.allset.cluster('EXEC_DEFAULT', envelope=float(v["envelope"]))


def _soft_mod(context, v):
    return bpy.ops.allset.soft_mod('EXEC_DEFAULT', radius=float(v["radius"]))


def _match(kind):
    return ("allset.deformer", {"kind": kind})


def _bounds():
    return [F("low", "Low bound:", "float", -1.0, lo=-10.0, hi=0.0),
            F("high", "High bound:", "float", 1.0, lo=0.0, hi=10.0)]


_BOUNDS_NOTE = "Low / High bound beyond the object (Blender's limits stop at the object's ends)"

WINDOWS = [
    # Lattice Options (options_144.md, Lattice row): Divisions 2 5 2, Center around selection on
    Window("deform_lattice", "Lattice Options", "Create", _match('LATTICE'), [
        FDivisions("divisions", "Divisions:", (2, 5, 2)),
        F("center", "", "bool", True, text="Center around selection"),
        F("auto_parent", "", "bool", False, text="Auto parent to selection")], _create('LATTICE'),
        paths=("Deform/Lattice",),
        missing=("Use local mode / Local divisions 2 2 2 (Blender's lattice is B-spline over all points)",
                 "Group base and lattice (Blender has no ffd1Base: the lattice is its own rest)",
                 "Freeze geometry", "Bind original geometry",
                 "Outside lattice / Falloff distance (Blender deforms every point of the vertex group)") + ADVANCED),
    # Delta Mush Options: Smoothing iterations 10, Smoothing step 0.5, Pin border vertices on
    Window("deform_delta_mush", "Delta Mush Options", "Create", _match('DELTA_MUSH'), [
        F("iterations", "Smoothing iterations:", "int", 10, lo=0, hi=50),
        F("step", "Smoothing step:", "float", 0.5, lo=0.0, hi=1.0),
        F("pin_border", "", "bool", True, text="Pin border vertices")], _create('DELTA_MUSH'),
        paths=("Deform/Delta Mush",),
        missing=("Displacement 1.0", "Inward constraint / Outward constraint", "Distance weight", ENVELOPE)
        + ADVANCED),
    # Wrap Options (MEL box, no tabs): Render influence objects off
    Window("deform_wrap", "Wrap Options", "Create", _match('WRAP'), [
        F("render_influence", "", "bool", False, text="Render influence objects")], _create('WRAP'),
        paths=("Deform/Wrap",),
        missing=("Exclusive bind", "Auto weight threshold / Weight threshold", "Use max distance / Max distance",
                 "Falloff mode Volume (Blender's Surface Deform binds to the surface)",
                 "Moving the influence object (Surface Deform follows its shape, not its transform)")),
    # Proximity Wrap Options: Wrap mode Surface = Surface Deform; the rest has no Blender setting
    Window("deform_proximity_wrap", "Proximity Wrap Options", "Create", _match('PROXIMITY_WRAP'), [],
           _create('PROXIMITY_WRAP'), paths=("Deform/Proximity Wrap",),
           missing=("Wrap mode (always Surface: Blender's Surface Deform)", "Max drivers 5 (one driver)",
                    "Falloff scale", "Smooth influences / Smooth normals") + ADVANCED),
    # ShrinkWrap Options (MEL box): Projection Toward Inner Object ...
    Window("deform_shrink_wrap", "ShrinkWrap Options", "Create", _match('SHRINK_WRAP'), [
        F("projection", "Projection:", "enum", "Toward Inner Object",
          items=("Toward Inner Object", "Toward Center", "Parallel To Axes", "Vertex Normals", "Closest")),
        F("bidirectional", "", "bool", False, text="Bidirectional"),
        F("reverse", "", "bool", False, text="Reverse"),
        F("offset", "Offset:", "float", 0.0, lo=-10.0, hi=10.0),
        F("along_x", "", "bool", False, text="Along X"), F("along_y", "", "bool", False, text="Along Y"),
        F("along_z", "", "bool", False, text="Along Z")], _create('SHRINK_WRAP'), paths=("Deform/ShrinkWrap",),
        missing=("Closest If No Intersection", "Target Inflation", "Bounding Box Center", "Axis Reference",
                 "Single ShrinkWrap Node (one modifier per object)", "Toward Center (Blender: closest point)",
                 ENVELOPE)),
    # Cluster Options: Relative mode off, Envelope 1
    Window("deform_cluster", "Cluster Options", "Create", ("allset.cluster", {}), [
        F("envelope", "Envelope:", "float", 1.0, lo=0.0, hi=1.0)], _cluster, paths=("Deform/Cluster",),
        missing=("Relative mode (the Hook follows the handle's world position)",) + ADVANCED),
    # Soft Modification Options (button "Soft Modification"): Falloff radius 5
    Window("deform_soft_mod", "Soft Modification Options", "Soft Modification", ("allset.soft_mod", {}), [
        F("radius", "Falloff radius:", "float", 5.0, lo=0.0, hi=100.0)], _soft_mod,
        paths=("Deform/Soft Modification Tool",),
        missing=("Falloff curve (fixed: Maya's smooth curve)", "Falloff mode Surface (Blender: Volume)",
                 "Color Feedback", "Preserve history", "Mask unselected", "Falloff around selection",
                 "Falloff based on X / Y / Z")),
    # Nonlinear: Bend / Flare / Sine / Squash / Twist / Wave Options
    Window("deform_bend", "Bend Options", "Create", _match('BEND'), _bounds() + [
        F("curvature", "Curvature:", "float", 0.0, lo=-4.0, hi=4.0)], _create('BEND'),
        paths=("Deform/Nonlinear/Bend",), missing=(_BOUNDS_NOTE, ENVELOPE) + ADVANCED),
    Window("deform_flare", "Flare Options", "Create", _match('FLARE'), _bounds() + [
        F("end_flare", "End flare X:", "float", 1.0, lo=0.0, hi=10.0)], _create('FLARE'),
        paths=("Deform/Nonlinear/Flare",),
        missing=("Start flare X / Z (Blender tapers from 1 at the low end)",
                 "End flare Z (Blender tapers X and Z together: End flare X)", "Curve", _BOUNDS_NOTE, ENVELOPE)
        + ADVANCED),
    Window("deform_sine", "Sine Options", "Create", _match('SINE'), [
        F("amplitude", "Amplitude:", "float", 0.0, lo=-5.0, hi=5.0),
        F("wavelength", "Wavelength:", "float", 2.0, lo=0.1, hi=10.0)], _create('SINE'),
        paths=("Deform/Nonlinear/Sine",),
        missing=("Low bound / High bound (Blender's Wave has none)", "Dropoff", "Offset",
                 "A true sine shape (Blender's Wave modifier ripples)", ENVELOPE) + ADVANCED),
    Window("deform_squash", "Squash Options", "Create", _match('SQUASH'), _bounds() + [
        F("factor", "Factor:", "float", 0.0, lo=-10.0, hi=10.0)], _create('SQUASH'),
        paths=("Deform/Nonlinear/Squash",),
        missing=("Start smoothness / End smoothness", "Max expand position / Expand (Blender keeps the volume)",
                 _BOUNDS_NOTE, ENVELOPE) + ADVANCED),
    Window("deform_twist", "Twist Options", "Create", _match('TWIST'), _bounds() + [
        F("end_angle", "End angle:", "float", 0.0, lo=-360.0, hi=360.0)], _create('TWIST'),
        paths=("Deform/Nonlinear/Twist",),
        missing=("Start angle (Blender twists from 0 at the handle)", _BOUNDS_NOTE, ENVELOPE) + ADVANCED),
    Window("deform_wave", "Wave Options", "Create", _match('WAVE'), [
        F("max_radius", "Max radius:", "float", 1.0, lo=0.0, hi=10.0),
        F("amplitude", "Amplitude:", "float", 0.0, lo=-5.0, hi=5.0),
        F("wavelength", "Wavelength:", "float", 1.0, lo=0.1, hi=10.0)], _create('WAVE'),
        paths=("Deform/Nonlinear/Wave",),
        missing=("Min radius", "Dropoff", "Offset", ENVELOPE) + ADVANCED),
    # Texture Options (MEL box; Advanced tab empty)
    Window("deform_texture", "Texture Options", "Create", _match('TEXTURE'), [
        F("point_space", "Point Space:", "enum", "UV", items=("World", "Local", "UV")),
        F("direction", "Direction:", "enum", "Handle", items=("Normal", "Handle", "Vector")),
        F("vector_space", "Vector Space:", "enum", "Object", items=("Object", "World", "Tangent")),
        F("strength", "Strength:", "float", 1.0, lo=-10.0, hi=10.0),
        F("offset", "Offset:", "float", 0.0, lo=-10.0, hi=10.0)], _create('TEXTURE'), paths=("Deform/Texture",),
        missing=("Vector Strength / Vector Offset", "Vector Space Tangent", ENVELOPE,
                 "textureDeformerHandle1 (Direction Handle = the object's up axis)")),
]
