# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Create menu: primitives at the origin with Maya's default size and names.

research/maya/concepts.md:156-159: interactive creation is off by default, so a
primitive appears at the origin at its default size (polyCube 1x1x1, polySphere
r=1, polyPlane 1x1 with 10x10); names ``pCube1`` / ``pCubeShape1``
(concepts.md:150-154). Other default values are Maya behaviour knowledge [K]
and two are unverified [U] (docs/steps/step_10.md 「계획」 6).

Size rule (decision 8, docs/steps/step_21.md 「계획」, delegated): a Maya length of 1
is one scene display unit (``units.maya_unit``), like ``cmds.polyCube()`` and a
Maya FBX import: pCube1 shows 1 cm in the MayaKit template (0.01 BU) and with
the "Maya Units" preference (1 BU). Lengths below are in Maya units.
"""

import math

import bpy
from bpy.props import EnumProperty

from . import naming, units

HALF_PI = math.pi / 2
# Maya's Y-up "front" (looking down -Z) is Blender's front (+Y): directional lights,
# spots, area lights and cameras start level, not pointing at the floor (delegated).
LEVEL = (HALF_PI, 0.0, 0.0)

# kind: (label, Maya base name, operator, props, rotation)
KINDS = {
    'CUBE': ("Cube", "pCube", "mesh.primitive_cube_add", {"size": 1.0}, None),
    'SPHERE': ("Sphere", "pSphere", "mesh.primitive_uv_sphere_add",
               {"segments": 20, "ring_count": 20, "radius": 1.0}, None),
    'CYLINDER': ("Cylinder", "pCylinder", "mesh.primitive_cylinder_add",
                 {"vertices": 20, "radius": 1.0, "depth": 2.0}, None),
    'CONE': ("Cone", "pCone", "mesh.primitive_cone_add",
             {"vertices": 20, "radius1": 1.0, "radius2": 0.0, "depth": 2.0}, None),
    'TORUS': ("Torus", "pTorus", "mesh.primitive_torus_add",
              {"major_segments": 20, "minor_segments": 20, "major_radius": 1.0,
               "minor_radius": 0.5}, None),
    'PLANE': ("Plane", "pPlane", "mesh.primitive_grid_add",
              {"x_subdivisions": 10, "y_subdivisions": 10, "size": 1.0}, None),
    'DISC': ("Disc", "pDisc", "mesh.primitive_circle_add",
             {"vertices": 20, "radius": 1.0, "fill_type": 'NGON'}, None),
    'PLATONIC': ("Platonic Solid", "pPlatonic", "mesh.primitive_ico_sphere_add",
                 {"subdivisions": 1, "radius": 1.0}, None),
    # Side length 1: square base radius 1/sqrt(2), equilateral faces -> height 1/sqrt(2).
    'PYRAMID': ("Pyramid", "pPyramid", "mesh.primitive_cone_add",
                {"vertices": 4, "radius1": math.sqrt(0.5), "radius2": 0.0,
                 "depth": math.sqrt(0.5)}, None),
    # Side length 1: triangle radius 1/sqrt(3); length 2.
    'PRISM': ("Prism", "pPrism", "mesh.primitive_cylinder_add",
              {"vertices": 3, "radius": 1 / math.sqrt(3), "depth": 2.0}, None),
    'NURBS_SPHERE': ("NURBS Sphere", "nurbsSphere", "surface.primitive_nurbs_surface_sphere_add",
                     {"radius": 1.0}, None),
    'NURBS_CYLINDER': ("NURBS Cylinder", "nurbsCylinder",
                       "surface.primitive_nurbs_surface_cylinder_add", {"radius": 1.0}, None),
    'NURBS_PLANE': ("NURBS Plane", "nurbsPlane", "surface.primitive_nurbs_surface_surface_add",
                    {"radius": 0.5}, None),
    'NURBS_TORUS': ("NURBS Torus", "nurbsTorus", "surface.primitive_nurbs_surface_torus_add",
                    {"radius": 1.0}, None),
    'NURBS_CIRCLE': ("NURBS Circle", "nurbsCircle", "curve.primitive_nurbs_circle_add",
                     {"radius": 1.0}, None),
    # Maya's curve tools draw a curve; Blender adds one to edit (names "curve1" / "bezier1" [K]).
    'CV_CURVE': ("CV Curve", "curve", "curve.primitive_nurbs_curve_add", {"radius": 1.0}, None),
    'BEZIER_CURVE': ("Bezier Curve", "bezier", "curve.primitive_bezier_curve_add",
                     {"radius": 1.0}, None),
    'DIRECTIONAL_LIGHT': ("Directional Light", "directionalLight", "object.light_add",
                          {"type": 'SUN'}, LEVEL),
    'POINT_LIGHT': ("Point Light", "pointLight", "object.light_add", {"type": 'POINT'}, None),
    'SPOT_LIGHT': ("Spot Light", "spotLight", "object.light_add", {"type": 'SPOT'}, LEVEL),
    'AREA_LIGHT': ("Area Light", "areaLight", "object.light_add", {"type": 'AREA'}, LEVEL),
    'CAMERA': ("Camera", "camera", "object.camera_add", {}, LEVEL),
    'LOCATOR': ("Locator", "locator", "object.empty_add",
                {"type": 'PLAIN_AXES', "radius": 1.0}, None),
    'EMPTY_GROUP': ("Empty Group", "null", "object.empty_add",
                    {"type": 'PLAIN_AXES', "radius": 1.0}, None),
    # Step 54 (docs/steps/step_54.md 「계획」 (a), PLAN W5): create paths that used Blender's operators with
    # metre defaults. A joint = a bone in one armature (W1, research/maya/workflows/rigging.md:134): bone length 1.
    'JOINT': ("Joint", "skeleton", "object.armature_add", {"radius": 1.0}, None),
    'TEXT': ("Type", "typeMesh", "object.text_add", {"radius": 1.0}, None),
    # Maya's Free Image Plane faces the front camera with no image yet: an image empty, no file browser.
    'IMAGE_PLANE': ("Free Image Plane", "imagePlane", "object.empty_add", {"type": 'IMAGE', "radius": 1.0}, LEVEL),
    # Fields (research/maya/workflows/fx.md:61-62,105): Blender force fields are empties, display size 1 Maya unit.
    # Blender has no gravity field: a wind blowing down (Maya -Y = Blender -Z); Uniform blows along Maya's +X.
    'FIELD_AIR': ("Air Field", "airField", "object.effector_add", {"type": 'WIND', "radius": 1.0}, None),
    'FIELD_DRAG': ("Drag Field", "dragField", "object.effector_add", {"type": 'DRAG', "radius": 1.0}, None),
    'FIELD_GRAVITY': ("Gravity Field", "gravityField", "object.effector_add", {"type": 'WIND', "radius": 1.0},
                      (math.pi, 0.0, 0.0)),
    'FIELD_NEWTON': ("Newton Field", "newtonField", "object.effector_add", {"type": 'FORCE', "radius": 1.0}, None),
    'FIELD_RADIAL': ("Radial Field", "radialField", "object.effector_add", {"type": 'FORCE', "radius": 1.0}, None),
    'FIELD_TURBULENCE': ("Turbulence Field", "turbulenceField", "object.effector_add",
                         {"type": 'TURBULENCE', "radius": 1.0}, None),
    'FIELD_UNIFORM': ("Uniform Field", "uniformField", "object.effector_add", {"type": 'WIND', "radius": 1.0},
                      (0.0, HALF_PI, 0.0)),
    'FIELD_VORTEX': ("Vortex Field", "vortexField", "object.effector_add", {"type": 'VORTEX', "radius": 1.0}, None),
}
# Kinds whose data keeps Blender's name (Maya has no "...Shape" node for them).
NO_SHAPE_NAME = {'JOINT', 'TEXT'}
# Blender's light_add power (10 W for point / spot / area, measured: research/maya/workflows/render.md:84) falls
# off with the square of the distance in metres; scaled by maya_unit()^2 a light at the same Maya-unit distance
# lights like in a metre scene. The sun has no falloff (render.md:185-187, PLAN W5).
FALLOFF_LIGHTS = {'POINT', 'SPOT', 'AREA'}
LIGHT_NOTICE = ("Blender lights always get darker with the square of the distance (Maya Decay Rate: Quadratic); "
                "there is no No Decay. Power is scaled to the Maya unit.")

MAYA_CAMERA_LENS, MAYA_FILM_MM = 35.0, 36.0

# Operator properties that are lengths (scaled by units.maya_unit).
LENGTHS = {"size", "radius", "depth", "radius1", "radius2", "major_radius", "minor_radius"}


def _scale_data(ob, k):
    """Lengths the add operators don't take: camera (Maya clip 0.1 / 10000,
    defaults.json:45-46), Blender's light sizes, kept in proportion to the Maya unit."""
    data = ob.data
    if ob.type == 'CAMERA':
        # Maya camera: focal length 35 on a 1.417 in (36 mm) film back (research/maya/concepts.md:163;
        # Blender's camera_add gives 50 mm). Camera from View (Ctrl+Shift+C) overrides the lens with the view's.
        data.lens, data.sensor_width = MAYA_CAMERA_LENS, MAYA_FILM_MM
        data.display_size *= k
        data.clip_start, data.clip_end = units.CLIP["clip_start"] * k, units.CLIP["clip_end"] * k
    elif ob.type == 'LIGHT':
        data.shadow_soft_size *= k
        if data.type == 'AREA':
            data.size *= k
            data.size_y *= k
        if data.type in FALLOFF_LIGHTS:
            data.energy *= k * k


def _maya_naming(context):
    from .. import preferences
    try:
        return preferences.get(context).maya_naming
    except KeyError:
        return True


def create(context, kind, maya_naming=True):
    """Create ``kind`` at the world origin; returns the new object."""
    _label, base, op, props, rot = KINDS[kind]
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    mod, name = op.split(".")
    k = units.maya_unit(context.scene)
    kw = {key: v * k if key in LENGTHS else v for key, v in props.items()}
    kw.update(location=(0.0, 0.0, 0.0), rotation=rot or (0.0, 0.0, 0.0), align='WORLD')
    getattr(getattr(bpy.ops, mod), name)(**kw)
    ob = context.view_layer.objects.active
    _scale_data(ob, k)
    if maya_naming:
        naming.apply_maya_name(ob, base, rename_data=kind not in NO_SHAPE_NAME)
    if kind == 'JOINT':
        _first_joint(ob, maya_naming)
    if maya_naming:
        from . import material
        material.give_default(ob)   # Maya: a new shape joins initialShadingGroup = lambert1 (step 100)
    return ob


def _first_joint(ob, maya_naming):
    """The armature's one bone = Maya's joint1, rotate order XYZ (W1)."""
    bone = ob.data.bones[0]
    if maya_naming:
        bone.name = "joint1"
    pose_bone = ob.pose.bones.get(bone.name)
    if pose_bone is not None:
        pose_bone.rotation_mode = 'XYZ'


class MAYAKIT_OT_create(bpy.types.Operator):
    """Create a primitive, light, camera or locator at the origin with Maya's default
    size and name (Maya Create menu)"""
    bl_idname = "maya_kit.create"
    bl_label = "Create"
    bl_options = {'REGISTER', 'UNDO'}

    kind: EnumProperty(name="Kind", items=[(k, v[0], "") for k, v in KINDS.items()])

    @classmethod
    def description(cls, context, props):
        return f"Create a {KINDS[props.kind][0]} at the origin, Maya default size and name"

    def execute(self, context):
        ob = create(context, self.kind, _maya_naming(context))
        note = LIGHT_NOTICE if ob.type == 'LIGHT' and ob.data.type in FALLOFF_LIGHTS else ""
        self.report({'INFO'}, f"Created {ob.name}" + (f". {note}" if note else ""))
        return {'FINISHED'}


# Blender's quick smoke (Fluids > 3D Container, Effects > Fire / Smoke) puts a domain around the selection with a
# margin of (1, 1, 2) BU and 1 BU up ($S\startupl_operators\object_quick_effects.py:482-483): 200 x 200 x 400
# Maya units in a cm scene (research/maya/workflows/fx.md:76). The margin is redone in Maya units here.
SMOKE_MARGIN = (1.0, 1.0, 2.0)
SMOKE_LIFT = 1.0


def _selection_bounds(objects):
    from mathutils import Vector
    pts = [ob.matrix_world @ Vector(c) for ob in objects for c in ob.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


class MAYAKIT_OT_quick_smoke(bpy.types.Operator):
    """Smoke or fire from the selected meshes in a Mantaflow domain sized in Maya units
    (Maya Fluids > 3D Container, Effects > Fire / Smoke)"""
    bl_idname = "maya_kit.quick_smoke"
    bl_label = "Quick Smoke"
    bl_options = {'REGISTER', 'UNDO'}

    style: EnumProperty(name="Style", items=(('SMOKE', "Smoke", ""), ('FIRE', "Fire", ""), ('BOTH', "Both", "")))

    @classmethod
    def poll(cls, context):
        return any(ob.type == 'MESH' for ob in context.selected_objects)

    def execute(self, context):
        from mathutils import Vector
        meshes = [ob for ob in context.selected_objects if ob.type == 'MESH']
        lo, hi = _selection_bounds(meshes)
        before = set(bpy.data.objects)
        res = bpy.ops.object.quick_smoke(style=self.style)
        if res != {'FINISHED'}:
            return res
        domain = next((ob for ob in bpy.data.objects if ob not in before), None)
        if domain is None:
            return res
        k = units.maya_unit(context.scene)
        domain.location = (lo + hi) / 2 + Vector((0.0, 0.0, SMOKE_LIFT * k))
        domain.scale = (hi - lo) / 2 + Vector(SMOKE_MARGIN) * k
        return res


classes = (MAYAKIT_OT_create, MAYAKIT_OT_quick_smoke)
