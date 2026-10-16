# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya shelf button -> Blender action and Blender built-in icon.

Keys: the button's runTimeCommand (``shelf_data``), or "<shelf file>/<label>" for
buttons whose Maya command is a MEL expression. Values: (action, icon) with the
action in ``ui/menu_map.py`` form (run by ``marking.modal.run_action``). Icons are
Blender's own (no Maya artwork, ). Buttons not
listed have no Blender counterpart and are not drawn.
"""

from .menu_map import _con, _create, _mod


def _key(kind):
    return ("anim.keyframe_insert_by_name", {"type": kind})


def _shader(kind):
    return ("maya_kit.shelf_material", {"kind": kind})


_CONSTRAINTS = {
    "ParentConstraint": (_con('CHILD_OF'), 'CON_CHILDOF'),
    "PointConstraint": (_con('COPY_LOCATION'), 'CON_LOCLIKE'),
    "OrientConstraint": (_con('COPY_ROTATION'), 'CON_ROTLIKE'),
    "ScaleConstraint": (_con('COPY_SCALE'), 'CON_SIZELIKE'),
    "AimConstraint": (_con('TRACK_TO'), 'CON_TRACKTO'),
}

BY_COMMAND = {
    # --- Curves / Surfaces ---
    "CreateNURBSCircle": (_create('NURBS_CIRCLE'), 'CURVE_NCIRCLE'),
    "EPCurveTool": ("curve.primitive_nurbs_curve_add", 'CURVE_NCURVE'),
    "CreateBezierCurveTool": ("curve.primitive_bezier_curve_add", 'CURVE_BEZCURVE'),
    "InsertKnot": ("curve.subdivide", 'CURVE_PATH'),
    "CreateNURBSSphere": (_create('NURBS_SPHERE'), 'SURFACE_NSPHERE'),
    "CreateNURBSCylinder": (_create('NURBS_CYLINDER'), 'SURFACE_NCYLINDER'),
    "CreateNURBSPlane": (_create('NURBS_PLANE'), 'SURFACE_NSURFACE'),
    "CreateNURBSTorus": (_create('NURBS_TORUS'), 'SURFACE_NTORUS'),
    "Revolve": (_mod('SCREW'), 'MOD_SCREW'),
    "OpenCloseSurfaces": ("curve.cyclic_toggle", 'MOD_CURVE'),
    # --- Poly Modeling ---
    "CreatePolygonSphere": (_create('SPHERE'), 'MESH_UVSPHERE'),
    "CreatePolygonCube": (_create('CUBE'), 'MESH_CUBE'),
    "CreatePolygonCylinder": (_create('CYLINDER'), 'MESH_CYLINDER'),
    "CreatePolygonCone": (_create('CONE'), 'MESH_CONE'),
    "CreatePolygonTorus": (_create('TORUS'), 'MESH_TORUS'),
    "CreatePolygonPlane": (_create('PLANE'), 'MESH_GRID'),
    "CreatePolygonDisc": (_create('DISC'), 'MESH_CIRCLE'),
    "CreatePolygonPlatonic": (_create('PLATONIC'), 'MESH_ICOSPHERE'),
    "CreatePolygonType": ("object.text_add", 'OUTLINER_OB_FONT'),
    "CenterPivot": ("maya_kit.center_pivot", 'PIVOT_BOUNDBOX'),
    "DeleteHistory": ("maya_kit.delete_history", 'MODIFIER_OFF'),
    "FreezeTransformations": ("maya_kit.freeze_transform", 'FREEZE'),
    "CombinePolygons": ("object.join", 'AUTOMERGE_ON'),
    "ExtractFace": (("mesh.separate", {"type": 'SELECTED'}), 'MOD_EXPLODE'),
    "MirrorPolygonGeometry": (_mod('MIRROR'), 'MOD_MIRROR'),
    "SmoothPolygon": (_mod('SUBSURF'), 'MOD_SUBSURF'),
    "ReducePolygon": (_mod('DECIMATE'), 'MOD_DECIM'),
    "PolyRemesh": (_mod('REMESH'), 'MOD_REMESH'),
    "PolyExtrude": (("v3d", "view3d.edit_mesh_extrude_move_normal", {}), 'FACESEL'),
    "performBridgeOrFill": ("mesh.bridge_edge_loops", 'MOD_LATTICE'),
    "performBevelOrChamfer": (("v3d", "mesh.bevel", {}), 'MOD_BEVEL'),
    "PolyMerge": ("mesh.remove_doubles", 'AUTOMERGE_OFF'),
    "MergeToCenter": (("mesh.merge", {"type": 'CENTER'}), 'PIVOT_MEDIAN'),
    "FlipTriangleEdge": ("mesh.edge_rotate", 'MOD_TRIANGULATE'),
    "DuplicateFace": (("v3d", "mesh.duplicate_move", {}), 'DUPLICATE'),
    "PolygonCollapse": ("mesh.edge_collapse", 'FULLSCREEN_EXIT'),
    "dR_multiCutTool": (("tool", "builtin.knife", True), 'SCULPTMODE_HLT'),
    "dR_quadDrawTool": (("tool", "builtin.poly_build", True), 'MESH_DATA'),
    "TextureViewWindow": (("maya_kit.hb_pane", {"ui_type": 'UV'}), 'UV'),
    # --- Sculpting ---
    "SetMeshSculptTool": (("object.mode_set", {"mode": 'SCULPT'}), 'SCULPTMODE_HLT'),
    # --- Rigging ---
    "CreateLocator": (_create('LOCATOR'), 'EMPTY_AXIS'),
    "JointTool": ("object.armature_add", 'OUTLINER_OB_ARMATURE'),
    "IKHandleTool": ("pose.ik_add", 'CON_KINEMATIC'),
    "SmoothBindSkin": (("object.parent_set", {"type": 'ARMATURE_AUTO'}), 'MOD_ARMATURE'),
    "ArtPaintSkinWeightsTool": ("paint.weight_paint_toggle", 'WPAINT_HLT'),
    "CreateBlendShape": (("object.shape_key_add", {"from_mix": False}), 'SHAPEKEY_DATA'),
    "CreateLattice": (("object.add", {"type": 'LATTICE'}), 'OUTLINER_OB_LATTICE'),
    **_CONSTRAINTS,
    "SetKey": ("anim.keyframe_insert", 'KEY_HLT'),
    # --- Animation ---
    "PlayblastWindow": (("v3d", "render.opengl", {"animation": True}), 'RENDER_ANIMATION'),
    "CreateMotionTrail": ("object.paths_calculate", 'ANIM_DATA'),
    "BakeSimulation": ("nla.bake", 'ACTION'),
    "SetKeyAnimated": (_key("Available"), 'KEYINGSET'),
    "SetKeyTranslate": (_key("Location"), 'CON_LOCLIKE'),
    "SetKeyRotate": (_key("Rotation"), 'CON_ROTLIKE'),
    "SetKeyScale": (_key("Scaling"), 'CON_SIZELIKE'),
    # --- Rendering ---
    "CreateDirectionalLight": (_create('DIRECTIONAL_LIGHT'), 'LIGHT_SUN'),
    "CreatePointLight": (_create('POINT_LIGHT'), 'LIGHT_POINT'),
    "CreateSpotLight": (_create('SPOT_LIGHT'), 'LIGHT_SPOT'),
    "CreateAreaLight": (_create('AREA_LIGHT'), 'LIGHT_AREA'),
    "CreateCameraOnly": (_create('CAMERA'), 'OUTLINER_OB_CAMERA'),
    "BatchRender": (("render.render", {"animation": True}), 'RENDER_ANIMATION'),
    "RenderSequence": (("render.render", {"animation": True}), 'RENDER_RESULT'),
    "Art3dPaintTool": ("paint.texture_paint_toggle", 'TPAINT_HLT'),
    # --- FX ---
    "NCreateEmitter": ("object.particle_system_add", 'PARTICLES'),
    "makeCollideNCloth": (_mod('COLLISION'), 'MOD_PHYSICS'),
    "CreateHairOptions": ("object.curves_empty_hair_add", 'CURVES_DATA'),
    "InteractivePlayback": ("screen.animation_play", 'PLAY'),
    # --- FX Caching (Blender point caches) ---
    "CreateFluidCache": (("ptcache.bake_all", {"bake": True}), 'FILE_CACHE'),
    "fluidDeleteCache": ("ptcache.free_bake_all", 'TRASH'),
    "deleteNclothCache": ("ptcache.free_bake_all", 'TRASH'),
}

BY_LABEL = {
    "Polygons/Planar Mapping": (("v3d", "uv.project_from_view", {}), 'UV_FACESEL'),
    "Polygons/Cylindrical Mapping": (("v3d", "uv.cylinder_project", {}), 'MESH_CYLINDER'),
    "Polygons/Spherical Mapping": (("v3d", "uv.sphere_project", {}), 'MESH_UVSPHERE'),
    "Polygons/Automatic Mapping": ("uv.smart_project", 'UV_DATA'),
    "Rendering/Standard Surface Material": (_shader('STANDARD_SURFACE'), 'MATERIAL'),
    "Rendering/Lambert Material": (_shader('LAMBERT'), 'SHADING_SOLID'),
    "Rendering/Blinn Material": (_shader('BLINN'), 'SHADING_RENDERED'),
    "Rendering/Phong Material": (_shader('PHONG'), 'SHADING_TEXTURE'),
    "Rendering/Surface Material": (_shader('SURFACE'), 'LIGHT'),
    "FX/Create nCloth": (_mod('CLOTH'), 'MOD_CLOTH'),
    "FXCaching/Create New Cache": (("ptcache.bake_all", {"bake": True}), 'FILE_CACHE'),
}


def lookup(shelf, label, command):
    """(action, icon) for a factory button, or None."""
    if command and command in BY_COMMAND:
        return BY_COMMAND[command]
    return BY_LABEL.get(f"{shelf}/{label}")
