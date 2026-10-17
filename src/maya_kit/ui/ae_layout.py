# SPDX-License-Identifier: GPL-3.0-or-later
"""Attribute Editor sections: Maya template sections -> Blender properties (data only).

Section names and open/closed state follow 
(``collapse`` flag of each ``editorTemplate -beginLayout``; Maya frameLayouts
without a flag start collapsed ); rows are the Blender properties that play
the part of the Maya attributes. Maya
attributes with no Blender counterpart (shear, rotateAxis, tessellation, depth
map shadows, Node Behavior, UUID, ...) are left out.

Row forms:
  ("prop", owner, attr, label)   owner: "ob" | "data" | "view" (3D View space); joints (pose bones):
                                 "ob" = the pose bone, "bone" = its Bone, "arm" = the Armature data,
                                 "armob" = the armature object
  ("draw", name)                 custom drawer in ui/attribute_editor.py
  ("socket", input name, label)  Principled BSDF input (material tabs), with the Maya map button
  ("missing", label, note)       Maya attribute Blender doesn't have: a greyed row with the note (step 67)

``TEMPLATE`` names the research template a section list is checked against
(tests/test_step11_outliner_ae.py); ``None`` = no Maya template in the research.
"""


class Section:
    __slots__ = ("name", "open", "rows", "subs")

    def __init__(self, name, open_, rows=(), subs=()):
        self.name = name
        self.open = open_
        self.rows = list(rows)
        self.subs = list(subs)


def S(name, open_, *rows, subs=()):
    return Section(name, open_, rows, subs)


# --- transform (Maya, Maya-800) ---------------------
TRANSFORM = [
    S("Transform Attributes", True,                                          # collapse=0
      ("draw", "transform_channels"),
      ("prop", "ob", "rotation_mode", "Rotate Order")),
    S("Pivots", False, subs=[
        S("Local Space", False, ("prop", "ob", "delta_location", "Pivot Offset")),
        S("World Space", True, ("draw", "world_pivot")),                    # collapse=0
    ]),
    S("Limit Information", False, subs=[
        S("Translate", False, ("draw", "limit:LIMIT_LOCATION")),
        S("Rotate", True, ("draw", "limit:LIMIT_ROTATION")),                # collapse=0
        S("Scale", False, ("draw", "limit:LIMIT_SCALE")),
    ]),
    S("Display", False,
      ("draw", "visibility"),
      ("prop", "ob", "show_axis", "Display Local Axis"),
      ("prop", "ob", "hide_select", "Template (unselectable)"),
      ("prop", "ob", "show_in_front", "Always Draw On Top"),
      ("prop", "ob", "show_name", "Display Name"),
      subs=[
          S("Bounding Box Information", False,
            ("prop", "ob", "show_bounds", "Display Bounding Box"),
            ("prop", "ob", "display_bounds_type", "Bounds Type")),
          S("Drawing Overrides", False,                                     # collapse=1
            ("prop", "ob", "display_type", "Display Type"),
            ("prop", "ob", "color", "Color")),
      ]),
]

# --- mesh shape (Maya-1119, :874; Maya) ------
MESH = [
    S("Mesh Component Display", False,
      ("prop", "ob", "show_wire", "Wireframe on Shaded"),
      ("prop", "ob", "show_all_edges", "Display All Edges"),
      ("prop", "view", "overlay.show_face_normals", "Display Normals (Face)"),
      ("prop", "view", "overlay.show_vertex_normals", "Display Normals (Vertex)"),
      ("prop", "view", "overlay.normals_length", "Normal Size")),
    S("Mesh Controls", False, ("draw", "shading")),
    S("Smooth Mesh", False, ("draw", "smooth_mesh")),
    S("Render Stats", False,
      ("prop", "ob", "visible_camera", "Primary Visibility"),
      ("prop", "ob", "visible_shadow", "Casts Shadows"),
      ("prop", "ob", "visible_diffuse", "Visible in Diffuse"),
      ("prop", "ob", "visible_glossy", "Visible in Reflections"),
      ("prop", "ob", "visible_transmission", "Visible in Refractions"),
      ("prop", "ob", "visible_volume_scatter", "Visible in Volume"),
      ("prop", "ob", "hide_render", "Hide in Render")),
    S("Object Display", False,
      ("prop", "ob", "display_type", "Display Type")),
]

# --- camera (Maya-756) ---------------------------------------------
CAMERA = [
    S("Camera Attributes", True,
      ("prop", "data", "lens", "Focal Length"),
      ("prop", "data", "clip_start", "Near Clip Plane"),
      ("prop", "data", "clip_end", "Far Clip Plane")),
    S("Film Back", True,
      ("prop", "data", "sensor_width", "Horizontal Film Aperture"),
      ("prop", "data", "sensor_height", "Vertical Film Aperture"),
      ("prop", "data", "sensor_fit", "Fit Resolution Gate"),
      ("prop", "data", "shift_x", "Film Offset X"),
      ("prop", "data", "shift_y", "Film Offset Y")),
    S("Depth of Field", False,
      ("prop", "data", "dof.use_dof", "Depth of Field"),
      ("prop", "data", "dof.focus_distance", "Focus Distance"),
      ("prop", "data", "dof.aperture_fstop", "F Stop")),
    S("Display Options", False,
      ("prop", "data", "show_limits", "Display Near/Far Clip"),
      ("prop", "data", "show_passepartout", "Display Film Gate Mask"),
      ("prop", "data", "passepartout_alpha", "Gate Mask Opacity"),
      ("prop", "data", "display_size", "Locator Scale")),
    S("Orthographic Views", False,
      ("prop", "data", "type", "Projection"),
      ("prop", "data", "ortho_scale", "Orthographic Width")),
]

# --- lights (Maya-124, Maya-43) -----------
_LIGHT_MAIN = (("prop", "data", "type", "Type"),
               ("prop", "data", "color", "Color"),
               ("prop", "data", "energy", "Intensity"),
               ("prop", "data", "diffuse_factor", "Emit Diffuse"),
               ("prop", "data", "specular_factor", "Emit Specular"))
POINT_LIGHT = [
    S("Point Light Attributes", True, *_LIGHT_MAIN),
    S("Shadows", False, ("prop", "data", "use_shadow", "Use Shadows"), subs=[
        S("Raytrace Shadow Attributes", True, ("prop", "data", "shadow_soft_size", "Light Radius")),
    ]),
]
DIRECTIONAL_LIGHT = [
    S("Directional Light Attributes", True, *_LIGHT_MAIN),
    S("Shadows", False, ("prop", "data", "use_shadow", "Use Shadows"), subs=[
        S("Raytrace Shadow Attributes", True, ("prop", "data", "angle", "Light Angle")),
    ]),
]
# Spot and area lights: no template in the research; Maya's layout is the point light's .
SPOT_LIGHT = [
    S("Spot Light Attributes", True, *_LIGHT_MAIN,
      ("prop", "data", "spot_size", "Cone Angle"),
      ("prop", "data", "spot_blend", "Penumbra")),
    S("Shadows", False, ("prop", "data", "use_shadow", "Use Shadows"),
      ("prop", "data", "shadow_soft_size", "Light Radius")),
]
AREA_LIGHT = [
    S("Area Light Attributes", True, *_LIGHT_MAIN,
      ("prop", "data", "shape", "Shape"),
      ("prop", "data", "size", "Size")),
    S("Shadows", False, ("prop", "data", "use_shadow", "Use Shadows")),
]

# --- material: standardSurface (Maya-512) on Principled BSDF ----
STANDARD_SURFACE = [
    S("Base", True, ("socket", "Weight", "Weight"), ("socket", "Base Color", "Color"),
      ("socket", "Diffuse Roughness", "Diffuse Roughness"), ("socket", "Metallic", "Metalness")),
    S("Specular", True, ("socket", "Specular IOR Level", "Weight"),
      ("socket", "Specular Tint", "Color"), ("socket", "Roughness", "Roughness"),
      ("socket", "IOR", "IOR"), ("socket", "Anisotropic", "Anisotropy"),
      ("socket", "Anisotropic Rotation", "Rotation")),
    S("Transmission", False, ("socket", "Transmission Weight", "Weight")),
    S("Subsurface", False, ("socket", "Subsurface Weight", "Weight"),
      ("socket", "Subsurface Radius", "Radius"), ("socket", "Subsurface Scale", "Scale"),
      ("socket", "Subsurface Anisotropy", "Anisotropy")),
    S("Coat", False, ("socket", "Coat Weight", "Weight"), ("socket", "Coat Tint", "Color"),
      ("socket", "Coat Roughness", "Roughness"), ("socket", "Coat IOR", "IOR")),
    S("Sheen", False, ("socket", "Sheen Weight", "Weight"), ("socket", "Sheen Tint", "Color"),
      ("socket", "Sheen Roughness", "Roughness")),
    S("Emission", False, ("socket", "Emission Strength", "Weight"),
      ("socket", "Emission Color", "Color")),
    S("Thin Film", False, ("socket", "Thin Film Thickness", "Thickness"),
      ("socket", "Thin Film IOR", "IOR")),
    S("Geometry", False, ("socket", "Alpha", "Opacity"), ("socket", "Normal", "Normal"),
      ("missing", "Thin Walled", "Blender's Principled BSDF has no thin-walled mode")),
]

# standardSurface / aiStandardSurface attribute -> Principled BSDF 4.5 input (
#, names from the public Autodesk Standard Surface spec ; Arnold's aiStandardSurface uses the same names).
# None = no Principled input. Map button tooltips name the Maya attribute (attribute_editor, step 67).
STANDARD_SURFACE_ATTRS = (
    ("base", "Weight"), ("baseColor", "Base Color"), ("diffuseRoughness", "Diffuse Roughness"),
    ("metalness", "Metallic"), ("specular", "Specular IOR Level"), ("specularColor", "Specular Tint"),
    ("specularRoughness", "Roughness"), ("specularIOR", "IOR"), ("specularAnisotropy", "Anisotropic"),
    ("specularRotation", "Anisotropic Rotation"), ("transmission", "Transmission Weight"),
    ("transmissionColor", None), ("transmissionDepth", None),
    ("subsurface", "Subsurface Weight"), ("subsurfaceColor", None), ("subsurfaceRadius", "Subsurface Radius"),
    ("subsurfaceScale", "Subsurface Scale"), ("subsurfaceAnisotropy", "Subsurface Anisotropy"),
    ("coat", "Coat Weight"), ("coatColor", "Coat Tint"), ("coatRoughness", "Coat Roughness"),
    ("coatIOR", "Coat IOR"), ("coatNormal", "Coat Normal"),
    ("sheen", "Sheen Weight"), ("sheenColor", "Sheen Tint"), ("sheenRoughness", "Sheen Roughness"),
    ("emission", "Emission Strength"), ("emissionColor", "Emission Color"),
    ("thinFilmThickness", "Thin Film Thickness"), ("thinFilmIOR", "Thin Film IOR"),
    ("opacity", "Alpha"), ("normalCamera", "Normal"), ("thinWalled", None),
)
MAYA_ATTR = {socket: attr for attr, socket in STANDARD_SURFACE_ATTRS if socket}
# --- lambert (Maya -> Maya; attribute_editor.md:137-140) ---
# Principled stand-ins: transparency -> Alpha (opacity), incandescence -> Emission, bump ->
# Normal, diffuse -> Weight, translucence -> Subsurface; refractions -> Transmission.
_LAMBERT_COMMON = S("Common Material Attributes", True,
                    ("socket", "Base Color", "Color"), ("socket", "Alpha", "Opacity"),
                    ("socket", "Emission Color", "Incandescence"), ("socket", "Normal", "Bump Mapping"),
                    ("socket", "Weight", "Diffuse"), ("socket", "Subsurface Weight", "Translucence"))
_RAYTRACE = S("Raytrace Options", False, ("socket", "Transmission Weight", "Refractions"),
              ("socket", "IOR", "Refractive Index"))
LAMBERT = [_LAMBERT_COMMON, _RAYTRACE]
# blinn / phong = lambert common + Specular Shading, open (Maya 2022 Maya-39,
# Maya-33; not in the research templates).
BLINN = [_LAMBERT_COMMON,
         S("Specular Shading", True, ("socket", "Roughness", "Eccentricity"),
           ("socket", "Specular IOR Level", "Specular Roll Off"),
           ("socket", "Specular Tint", "Specular Color")),
         _RAYTRACE]
PHONG = [_LAMBERT_COMMON,
         S("Specular Shading", True, ("socket", "Roughness", "Roughness (Cosine Power)"),
           ("socket", "Specular Tint", "Specular Color")),
         _RAYTRACE]
# surfaceShader (Maya-34): out color = emission.
SURFACE_SHADER = [
    S("Surface Shader Attributes", True, ("socket", "Emission Color", "Out Color"),
      ("socket", "Alpha", "Out Opacity")),
]
# Material without nodes: Blender viewport values (no Maya template).
# --- joint = pose bone (Maya-54, ) ----
# Joint Labelling (side / type) and Preferred Angle have no Blender counterpart.
JOINT = [
    S("Transform Attributes", True,                                          # collapse=0
      ("draw", "transform_channels"),
      ("prop", "ob", "rotation_mode", "Rotate Order")),
    S("Joint", True,                                                         # collapse=0
      ("prop", "arm", "display_type", "Draw Style"),
      ("draw", "joint_stiffness"),
      ("draw", "joint_orient"),
      ("prop", "bone", "inherit_scale", "Segment Scale Compensate")),
    S("Limit Information", False, subs=[
        S("Translate", False, ("draw", "limit:LIMIT_LOCATION")),
        S("Rotate", True, ("draw", "limit:LIMIT_ROTATION")),                # collapse=0
        S("Scale", False, ("draw", "limit:LIMIT_SCALE")),
    ]),
    S("Display", False,
      ("draw", "visibility"),
      ("prop", "arm", "show_axes", "Display Local Axis"),
      ("prop", "armob", "show_in_front", "Always Draw On Top"),
      ("prop", "ob", "custom_shape", "Display as Control Shape")),
]

PLAIN_MATERIAL = [
    S("Common Material Attributes", True,
      ("prop", "data", "diffuse_color", "Color"),
      ("prop", "data", "metallic", "Metalness"),
      ("prop", "data", "roughness", "Roughness")),
]

# (sections, research template name or None)
BY_KIND = {
    "transform": (TRANSFORM, "transform"),
    "joint": (JOINT, "joint"),
    "MESH": (MESH, "mesh"),
    "CAMERA": (CAMERA, "camera"),
    "POINT": (POINT_LIGHT, "pointLight"),
    "SUN": (DIRECTIONAL_LIGHT, "directionalLight"),
    "SPOT": (SPOT_LIGHT, None),
    "AREA": (AREA_LIGHT, None),
    "standardSurface": (STANDARD_SURFACE, "standardSurface"),
    "aiStandardSurface": (STANDARD_SURFACE, None),      # Arnold's, same attribute names (step 67)
    "lambert": (LAMBERT, "lambert"),
    "blinn": (BLINN, None),
    "phong": (PHONG, None),
    "surfaceShader": (SURFACE_SHADER, None),
    "material": (PLAIN_MATERIAL, None),
}

# Maya node type shown in the tab header ("transform: [pCube1]").
NODE_TYPE = {"MESH": "mesh", "CURVE": "nurbsCurve", "SURFACE": "nurbsSurface", "CAMERA": "camera",
             "LIGHT": "light", "LATTICE": "lattice", "ARMATURE": "joint", "FONT": "type",
             "META": "metaball", "EMPTY": "locator"}
LIGHT_TYPE = {"POINT": "pointLight", "SUN": "directionalLight", "SPOT": "spotLight",
              "AREA": "areaLight"}


def walk(sections, depth=0):
    """Yield (depth, section) depth first."""
    for sec in sections:
        yield depth, sec
        yield from walk(sec.subs, depth + 1)
