# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Create menu: primitives at the origin with Maya's default size and names.

 interactive creation is off by default, so a
primitive appears at the origin at its default size (polyCube 1x1x1, polySphere
r=1, polyPlane 1x1 with 10x10); names ``pCube1`` / ``pCubeShape1``
(concepts.md:150-154). Other default values are Maya behaviour knowledge 
and two are unverified .

Size rule: 1 Maya unit = 1 BU, so a
cube fills one grid cell; with the "Maya Units" preference 1 BU = 1 cm and the
numbers read like Maya's too.
"""

import math

import bpy
from bpy.props import EnumProperty

from . import naming

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
    'DIRECTIONAL_LIGHT': ("Directional Light", "directionalLight", "object.light_add",
                          {"type": 'SUN'}, LEVEL),
    'POINT_LIGHT': ("Point Light", "pointLight", "object.light_add", {"type": 'POINT'}, None),
    'SPOT_LIGHT': ("Spot Light", "spotLight", "object.light_add", {"type": 'SPOT'}, LEVEL),
    'AREA_LIGHT': ("Area Light", "areaLight", "object.light_add", {"type": 'AREA'}, LEVEL),
    'CAMERA': ("Camera", "camera", "object.camera_add", {}, LEVEL),
    'LOCATOR': ("Locator", "locator", "object.empty_add", {"type": 'PLAIN_AXES'}, None),
    'EMPTY_GROUP': ("Empty Group", "null", "object.empty_add", {"type": 'PLAIN_AXES'}, None),
}


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
    kw = dict(props, location=(0.0, 0.0, 0.0), rotation=rot or (0.0, 0.0, 0.0), align='WORLD')
    getattr(getattr(bpy.ops, mod), name)(**kw)
    ob = context.view_layer.objects.active
    if maya_naming:
        naming.apply_maya_name(ob, base)
    return ob


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
        self.report({'INFO'}, f"Created {ob.name}")
        return {'FINISHED'}


classes = (MAYAKIT_OT_create,)
