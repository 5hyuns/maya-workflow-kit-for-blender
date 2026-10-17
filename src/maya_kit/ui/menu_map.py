# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya menu item -> Blender action (docs/steps/step_7.md 「계획」 2).

Key = label path in ``menu_data.MENUS`` ("Create/Polygon Primitives/Cube"),
starting with the menu *label*, so the Deform and Constrain menus that
Modeling, Rigging and Animation share map once. Value:

- ``"op.id"`` or ``("op.id", {props})``: drawn as that operator (its poll
  greys the item out where Blender can't run it, e.g. edit-mode commands in
  object mode);
- ``("v3d", "op.id", {props})``: needs a 3D View region; run through
  ``maya_kit.menu_run`` in the largest 3D View;
- ``("tool", "builtin.id", edit)``: switch the active tool, entering mesh edit
  mode first when ``edit``;
- ``("menu", "MENU_ID")``: a Blender menu as the submenu.

Items not listed are drawn greyed out. ``EXTRA`` adds items Maya builds at run
time (not in the static menu data), e.g. Modify's Pivot section.
"""

def _create(kind):
    # Maya default size at the origin, Maya names (operators/create.py, docs/steps/step_10.md).
    return ("maya_kit.create", {"kind": kind})


_PRIMS = {label: _create(kind) for label, kind in (
    ("Sphere", 'SPHERE'), ("Cube", 'CUBE'), ("Cylinder", 'CYLINDER'), ("Cone", 'CONE'),
    ("Torus", 'TORUS'), ("Plane", 'PLANE'), ("Disc", 'DISC'), ("Platonic Solid", 'PLATONIC'),
    ("Pyramid", 'PYRAMID'), ("Prism", 'PRISM'))}


def _del(kind, all_=False):
    return ("maya_kit.delete_by_type", {"type": kind, "all": all_})


_DELETE_BY_TYPE = {"History": 'HISTORY', "Non-Deformer History": 'NON_DEFORMER_HISTORY',
                   "Channels": 'CHANNELS', "Static Channels": 'STATIC_CHANNELS',
                   "Constraints": 'CONSTRAINTS', "Motion Paths": 'MOTION_PATHS',
                   "Rigid Bodies": 'RIGID_BODIES'}
_DELETE_ALL_ONLY = {"Joints": 'JOINTS', "Lattices": 'LATTICES', "Cameras": 'CAMERAS',
                    "Lights": 'LIGHTS', "Image Planes": 'IMAGE_PLANES', "Clusters": 'CLUSTERS',
                    "Nonlinears": 'NONLINEARS', "Particles": 'PARTICLES'}


def _mod(kind):
    return ("object.modifier_add", {"type": kind})


def _con(kind):
    # Maya order (targets, then the constrained node); on the active joint in pose mode (step 62)
    return ("maya_kit.constrain", {"type": kind})


def _editor(ui_type):
    # A Blender editor in a new window, like a Maya editor window (operators/menu_extras.py).
    return ("maya_kit.open_editor", {"ui_type": ui_type})


def _dock(dock):
    return ("v3d", "maya_kit.dock_show", {"dock": dock})


def _hud(data_path):
    return ("v3d", "wm.context_toggle", {"data_path": data_path})


def _kit_pref(prop):
    """Toggle one of this add-on's preferences (Maya HUD options are global)."""
    pkg = __package__.rpartition(".")[0]
    return ("wm.context_toggle", {"data_path": f'preferences.addons["{pkg}"].preferences.{prop}'})


# Windows > ... Editors: Maya fills these submenus at run time (startup/WindowMenu.mel
# buildObjectEdMenu / buildModelingEdMenu / buildAnimationEdMenu / buildRenderingEdMenu /
# buildRelationshipEdMenu; labels from research/maya/runtime_commands.json). Items listed in
# CHILDREN without an action here draw greyed. docs/steps/step_34.md.
_WINDOW_EDITORS = {
    "General Editors/Attribute Editor": _dock('ATTRIBUTE_EDITOR'),
    "General Editors/Channel Box / Layer Editor": _dock('CHANNEL_BOX'),
    "General Editors/Channel Box": _dock('CHANNEL_BOX'),
    "General Editors/Layer Editor": _dock('CHANNEL_BOX'),
    "General Editors/Tool Settings": ("maya_kit.editor_toggle", {"editor": 'TOOL_SETTINGS'}),
    "General Editors/Attribute Spread Sheet": _editor('SPREADSHEET'),
    "General Editors/Display Layer Editor": _dock('CHANNEL_BOX'),
    "General Editors/Script Editor": "maya_kit.script_editor",
    "Modeling Editors/UV Editor": _editor('UV'),
    "Animation Editors/Graph Editor": _editor('FCURVES'),
    "Animation Editors/Time Editor": _editor('NLA_EDITOR'),
    "Animation Editors/Trax Editor": _editor('NLA_EDITOR'),
    "Animation Editors/Camera Sequencer": _editor('SEQUENCE_EDITOR'),
    "Animation Editors/Dope Sheet": _editor('DOPESHEET'),
    "Animation Editors/Expression Editor": _editor('DRIVERS'),
    # step 54: near substitutes with a notice (ui/notices.py, PLAN W3)
    "Relationship Editors/Animation Layers": _editor('NLA_EDITOR'),
    "General Editors/Hypergraph: Hierarchy": _editor('OUTLINER'),
    "General Editors/Hypergraph: Connections": _editor('DRIVERS'),
    "Rendering Editors/Hypershade": _editor('ShaderNodeTree'),
    "Rendering Editors/Render View": "render.view_show",
    "Rendering Editors/Render Settings": "maya_kit.render_settings",
    "Rendering Editors/Shading Group Attributes": ("v3d", "maya_kit.material_attributes", {}),
    "Relationship Editors/Display Layers": _dock('CHANNEL_BOX'),
}

MAP = {
    # --- File (research/maya/menus.md "File") ---
    "File/New Scene": "wm.read_homefile",
    "File/Open Scene...": "wm.open_mainfile",
    "File/Save Scene": "wm.save_mainfile",
    "File/Save Scene As...": "wm.save_as_mainfile",
    "File/Increment and Save": "maya_kit.increment_save",          # step 34
    "File/Save Preferences": "wm.save_userpref",
    "File/Optimize Scene Size": "outliner.orphans_purge",
    "File/Import...": ("menu", "TOPBAR_MT_file_import"),
    "File/Export All...": ("menu", "TOPBAR_MT_file_export"),
    "File/Export Selection...": ("menu", "MAYAKIT_MT_export_selection"),   # step 34
    "File/Create Reference...": "wm.link",
    "File/Recent Files": ("menu", "TOPBAR_MT_file_open_recent"),
    "File/Exit": "wm.quit_blender",
    # --- Edit ---
    "Edit/Undo": "ed.undo",
    "Edit/Redo": "ed.redo",
    "Edit/Repeat": "screen.repeat_last",
    "Edit/Recent Commands List": "screen.repeat_history",
    "Edit/Copy": ("v3d", "view3d.copybuffer", {}),
    "Edit/Paste": ("v3d", "view3d.pastebuffer", {}),
    # Maya Delete Keys = every key of the selection (step 56; Time Slider RMB Delete = this frame / range)
    "Edit/Keys/Delete Keys": ("v3d", "anim.keyframe_clear_v3d", {"confirm": False}),
    "Edit/Keys/Cut Keys": ("maya_kit.time_keys", {"action": "CUT"}),
    "Edit/Keys/Copy Keys": ("maya_kit.time_keys", {"action": "COPY"}),
    "Edit/Keys/Paste Keys": ("maya_kit.time_keys", {"action": "PASTE"}),
    "Edit/Keys/Bake Simulation": "nla.bake",
    "Edit/Delete": "object.delete",
    "Edit/Ungroup": "maya_kit.ungroup",                            # step 34
    "Edit/Delete by Type/History": "maya_kit.delete_history",
    "Edit/Delete by Type/Non-Deformer History": ("maya_kit.delete_history", {"non_deformer": True}),
    **{f"Edit/Delete by Type/{k}": _del(v) for k, v in _DELETE_BY_TYPE.items()
       if v not in ('HISTORY', 'NON_DEFORMER_HISTORY')},
    **{f"Edit/Delete All by Type/{k}": _del(v, True)
       for k, v in {**_DELETE_BY_TYPE, **_DELETE_ALL_ONLY}.items()},
    "Edit/Duplicate": "maya_kit.duplicate",                     # step 19: Maya names, in place
    "Edit/Duplicate Special": "maya_kit.duplicate_special",
    "Edit/Duplicate with Transform": "maya_kit.duplicate_with_transform",
    "Edit/Group": "maya_kit.group",
    "Edit/Parent": "maya_kit.parent",
    "Edit/Unparent": "maya_kit.unparent",
    # --- Create ---
    **{f"Create/Polygon Primitives/{k}": v for k, v in _PRIMS.items()},
    "Create/NURBS Primitives/Sphere": _create('NURBS_SPHERE'),
    "Create/NURBS Primitives/Cylinder": _create('NURBS_CYLINDER'),
    "Create/NURBS Primitives/Plane": _create('NURBS_PLANE'),
    "Create/NURBS Primitives/Torus": _create('NURBS_TORUS'),
    "Create/NURBS Primitives/Circle": _create('NURBS_CIRCLE'),
    "Create/Lights/Directional Light": _create('DIRECTIONAL_LIGHT'),
    "Create/Lights/Point Light": _create('POINT_LIGHT'),
    "Create/Lights/Spot Light": _create('SPOT_LIGHT'),
    "Create/Lights/Area Light": _create('AREA_LIGHT'),
    "Create/Cameras": _create('CAMERA'),
    "Create/Curve Tools/CV Curve Tool": _create('CV_CURVE'),
    "Create/Curve Tools/Bezier Curve Tool": _create('BEZIER_CURVE'),
    "Create/Type": _create('TEXT'),                 # step 54: Maya units (W5)
    "Create/Free Image Plane": _create('IMAGE_PLANE'),
    "Create/Locator": _create('LOCATOR'),
    "Create/Annotation...": ("tool", "builtin.annotate", False),
    "Create/Measure Tools/Distance Tool": ("tool", "builtin.measure", False),
    "Create/Empty Group": _create('EMPTY_GROUP'),
    "Create/Sets/Set": "collection.create",
    # --- Select ---
    "Select/All": ("object.select_all", {"action": 'SELECT'}),
    "Select/All by Type/Joints": ("object.select_by_type", {"type": 'ARMATURE'}),
    "Select/All by Type/Lattices": ("object.select_by_type", {"type": 'LATTICE'}),
    "Select/All by Type/Transforms": ("object.select_by_type", {"type": 'EMPTY'}),
    "Select/All by Type/Geometry": ("object.select_by_type", {"type": 'MESH'}),
    "Select/All by Type/NURBS Curves": ("object.select_by_type", {"type": 'CURVE'}),
    "Select/All by Type/NURBS Surfaces": ("object.select_by_type", {"type": 'SURFACE'}),
    "Select/All by Type/Polygon Geometry": ("object.select_by_type", {"type": 'MESH'}),
    "Select/All by Type/Cameras": ("object.select_by_type", {"type": 'CAMERA'}),
    "Select/All by Type/Lights": ("object.select_by_type", {"type": 'LIGHT'}),
    "Select/Deselect All": ("object.select_all", {"action": 'DESELECT'}),
    "Select/Hierarchy": ("object.select_grouped", {"type": 'CHILDREN_RECURSIVE', "extend": True}),
    "Select/Inverse": ("object.select_all", {"action": 'INVERT'}),
    "Select/Similar": ("object.select_grouped", {"type": 'TYPE'}),
    "Select/Grow": "mesh.select_more",
    "Select/Shrink": "mesh.select_less",
    "Select/Object/Component": "object.editmode_toggle",
    "Select/Components/Multi-Component": ("maya_kit.component_mode", {"type": 'MULTI'}),
    "Select/Components/Vertex": ("maya_kit.component_mode", {"type": 'VERT'}),
    "Select/Components/Edge": ("maya_kit.component_mode", {"type": 'EDGE'}),
    "Select/Components/Face": ("maya_kit.component_mode", {"type": 'FACE'}),
    "Select/Contiguous Edges": ("maya_kit.select_loops", {"ring": False}),
    "Select/Convert Selection/To Vertices": ("mesh.select_mode", {"type": 'VERT'}),
    "Select/Convert Selection/To Edges": ("mesh.select_mode", {"type": 'EDGE', "use_expand": True}),
    "Select/Convert Selection/To Edge Loop": ("maya_kit.select_loops", {"ring": False}),
    "Select/Convert Selection/To Edge Ring": ("maya_kit.select_loops", {"ring": True}),
    "Select/Convert Selection/To Edge Perimeter": "mesh.region_to_loop",
    "Select/Convert Selection/To Faces": ("mesh.select_mode", {"type": 'FACE', "use_expand": True}),
    "Select/Convert Selection/To Face Perimeter": "mesh.region_to_loop",
    "Select/Convert Selection/To Shell": "mesh.select_linked",
    # --- Modify ---
    "Modify/Transformation Tools/Move Tool": ("tool", "builtin.move", False),
    "Modify/Transformation Tools/Rotate Tool": ("tool", "builtin.rotate", False),
    "Modify/Transformation Tools/Scale Tool": ("tool", "builtin.scale", False),
    "Modify/Transformation Tools/Universal Manipulator": ("tool", "builtin.transform", False),
    "Modify/Transformation Tools/Move/Rotate/Scale Tool": ("tool", "builtin.transform", False),
    "Modify/Reset Transformations": "maya_kit.reset_transform",
    "Modify/Freeze Transformations": "maya_kit.freeze_transform",
    "Modify/Center Pivot": "maya_kit.center_pivot",
    # step 59: pivot / align (research/maya/workflows/pivot_snap.md P7, P8, S8-S13)
    "Modify/Bake Pivot": "maya_kit.bake_pivot",
    "Modify/Match Transformations/Match All Transforms": ("maya_kit.match_transform", {"kind": 'ALL'}),
    "Modify/Match Transformations/Match Translation": ("maya_kit.match_transform", {"kind": 'TRANSLATE'}),
    "Modify/Match Transformations/Match Rotation": ("maya_kit.match_transform", {"kind": 'ROTATE'}),
    "Modify/Match Transformations/Match Scaling": ("maya_kit.match_transform", {"kind": 'SCALE'}),
    "Modify/Match Transformations/Match Pivots": "maya_kit.match_pivots",
    "Modify/Snap Align Objects/Point to Point": ("maya_kit.snap_points", {"count": 1}),
    "Modify/Snap Align Objects/2 Points to 2 Points": ("maya_kit.snap_points", {"count": 2}),
    "Modify/Snap Align Objects/3 Points to 3 Points": ("maya_kit.snap_points", {"count": 3}),
    "Modify/Snap Align Objects/Align Objects": "maya_kit.align_objects",
    "Modify/Snap Together Tool": "maya_kit.snap_together",
    "Modify/Make Live": "maya_kit.make_live",
    "Modify/Add Attribute...": "maya_kit.add_attribute",     # Attributes section (EXTRA), step 62
    "Modify/Edit Attribute...": "maya_kit.edit_attribute",
    "Modify/Delete Attribute...": "maya_kit.delete_attribute",
    "Windows/Switch to Blender": ("maya_kit.switch_mode", {"mode": 'BLENDER'}),
    "Modify/Convert/NURBS to Polygons": ("object.convert", {"target": 'MESH'}),
    "Modify/Convert/Smooth Mesh Preview to Polygons": ("object.convert", {"target": 'MESH'}),
    "Modify/Convert/Polygon Edges to Curve": ("object.convert", {"target": 'CURVE'}),
    "Modify/Convert/Type to Curves": ("object.convert", {"target": 'CURVE'}),
    "Modify/Convert/Instance to Object": "object.duplicates_make_real",
    # --- Display ---
    "Display/Grid": ("v3d", "maya_kit.toggle_grid", {}),     # Maya grid (ui/maya_grid.py, step 45)
    "Display/Hide": ("object.hide_view_set", {"unselected": False}),
    "Display/Show": "object.hide_view_clear",
    "Display/Transform Display/Local Rotation Axes": ("wm.context_toggle", {"data_path": "object.show_axis"}),
    "Display/Frame All in All Views": ("maya_kit.frame_all_views", {"selected": False}),
    "Display/Frame Selection in All Views": ("maya_kit.frame_all_views", {"selected": True}),
    "Display/Frame Selection with Children in All Views": ("maya_kit.frame_all_views",
                                                           {"selected": True, "children": True}),
    # --- Windows ---
    "Windows/Workspaces": ("menu", "TOPBAR_MT_workspace_menu"),
    "Windows/Outliner": _editor('OUTLINER'),
    "Windows/Node Editor": _editor('ShaderNodeTree'),
    **{f"Windows/{path}": action for path, action in _WINDOW_EDITORS.items()},
    "Windows/UI Elements": ("menu", "MAYAKIT_MT_ui_elements"),
    "Windows/Settings/Preferences": "screen.userpref_show",
    "Windows/Playblast": ("v3d", "render.opengl", {"animation": True}),
    "Windows/Output Window": "wm.console_toggle",
    # --- Mesh (Modeling) ---
    "Mesh/Combine": "object.join",
    "Mesh/Separate": ("mesh.separate", {"type": 'LOOSE'}),
    "Mesh/Fill Hole": "mesh.fill_holes",
    "Mesh/Reduce": _mod('DECIMATE'),
    "Mesh/Remesh": _mod('REMESH'),
    "Mesh/Smooth": _mod('SUBSURF'),
    "Mesh/Triangulate": _mod('TRIANGULATE'),
    "Mesh/Quadrangulate": "mesh.tris_convert_to_quads",
    "Mesh/Mirror": _mod('MIRROR'),
    "Mesh/Transfer Attributes": _mod('DATA_TRANSFER'),
    "Mesh/Smooth Proxy/Subdiv Proxy": _mod('SUBSURF'),
    # --- Edit Mesh ---
    "Edit Mesh/Add Divisions": "mesh.subdivide",
    "Edit Mesh/Bevel": ("v3d", "mesh.bevel", {}),
    "Edit Mesh/Bridge": "mesh.bridge_edge_loops",
    "Edit Mesh/Collapse": "mesh.edge_collapse",
    "Edit Mesh/Connect": "mesh.vert_connect_path",
    "Edit Mesh/Extrude": ("v3d", "view3d.edit_mesh_extrude_move_normal", {}),
    "Edit Mesh/Merge": "mesh.remove_doubles",
    "Edit Mesh/Merge to Center": ("mesh.merge", {"type": 'CENTER'}),
    "Edit Mesh/Symmetrize": "mesh.symmetrize",
    "Edit Mesh/Average Vertices": "mesh.vertices_smooth",
    "Edit Mesh/Chamfer Vertices": ("v3d", "mesh.bevel", {"affect": 'VERTICES'}),
    "Edit Mesh/Delete Edge/Vertex": "mesh.dissolve_mode",
    "Edit Mesh/Flip Triangle Edge": "mesh.edge_rotate",
    "Edit Mesh/Spin Edge Backward": ("mesh.edge_rotate", {"use_ccw": True}),
    "Edit Mesh/Spin Edge Forward": ("mesh.edge_rotate", {"use_ccw": False}),
    "Edit Mesh/Duplicate": ("v3d", "mesh.duplicate_move", {}),
    "Edit Mesh/Extract": ("mesh.separate", {"type": 'SELECTED'}),
    "Edit Mesh/Poke": "mesh.poke",
    # --- Mesh Tools ---
    "Mesh Tools/Create Polygon": ("tool", "builtin.poly_build", True),
    "Mesh Tools/Insert Edge Loop": ("tool", "builtin.loop_cut", True),
    "Mesh Tools/Multi-Cut": ("tool", "builtin.knife", True),
    "Mesh Tools/Offset Edge Loop": ("v3d", "mesh.offset_edge_loops_slide", {}),
    "Mesh Tools/Quad Draw": ("tool", "builtin.poly_build", True),
    "Mesh Tools/Slide Edge": ("tool", "builtin.edge_slide", True),
    # --- Mesh Display ---
    "Mesh Display/Average": "mesh.average_normals",
    "Mesh Display/Conform": "mesh.normals_make_consistent",
    "Mesh Display/Reverse": "mesh.flip_normals",
    "Mesh Display/Set to Face": "mesh.set_normals_from_faces",
    "Mesh Display/Harden Edge": "mesh.mark_sharp",
    "Mesh Display/Soften Edge": ("mesh.mark_sharp", {"clear": True}),
    "Mesh Display/Paint Vertex Color Tool": "paint.vertex_paint_toggle",
    # --- Curves ---
    "Curves/Open/Close": "curve.cyclic_toggle",
    "Curves/Insert Knot": "curve.subdivide",
    "Curves/Smooth": "curve.smooth",
    "Curves/Reverse Direction": "curve.switch_direction",
    # --- Deform (Modeling, Rigging, Animation share it) ---
    "Deform/Blend Shape": "maya_kit.blend_shape",          # targets, then the base (join_shapes, step 62)
    "Deform/Blend Shape#2/Add": "maya_kit.blend_shape",
    "Deform/Delta Mush": _mod('CORRECTIVE_SMOOTH'),
    "Deform/Solidify": _mod('SOLIDIFY'),
    "Deform/Lattice": _mod('LATTICE'),
    "Deform/Wrap": _mod('SURFACE_DEFORM'),
    "Deform/ShrinkWrap": _mod('SHRINKWRAP'),
    "Deform/Nonlinear/Twist": _mod('SIMPLE_DEFORM'),
    "Deform/Nonlinear/Wave": _mod('WAVE'),
    "Deform/Texture": _mod('DISPLACE'),
    "Deform/Paint Weights/Set Membership": "paint.weight_paint_toggle",
    # --- UV ---
    "UV/UV Editor": _editor('UV'),
    "UV/Planar": "maya_kit.uv_planar",
    "UV/Normal-Based": "maya_kit.uv_planar",
    "UV/Automatic": "uv.smart_project",
    "UV/Camera-based": ("v3d", "uv.project_from_view", {}),
    "UV/Cylindrical": ("v3d", "uv.cylinder_project", {}),
    "UV/Spherical": ("v3d", "uv.sphere_project", {}),
    "UV/Cut UV Edges": "mesh.mark_seam",
    "UV/Sew UV Edges": ("mesh.mark_seam", {"clear": True}),
    # --- Skeleton (Rigging) ---
    "Control/Create Character Set": "anim.keying_set_add",   # step 54: Keying Set + notice (ui/notices.py)
    # step 57: Joint Tool (click, click, Enter), option-box dialogs (docs/steps/step_57.md)
    "Skeleton/Create Joints": "maya_kit.joint_tool",
    "Skeleton/Quick Rig": "maya_kit.quick_rig",              # Rigify (notice in ui/notices.py), step 62
    "Windows/Animation Editors/Quick Rig": "maya_kit.quick_rig",
    "Skeleton/Mirror Joints": "maya_kit.mirror_joints",
    "Skeleton/Orient Joint": "maya_kit.orient_joint",
    "Skeleton/Remove Joints": "armature.delete",
    "Skeleton/Disconnect Joint": ("armature.parent_clear", {"type": 'DISCONNECT'}),
    "Skeleton/Create IK Handle": "maya_kit.ik_handle",       # step 58: click start + end joint
    # --- Skin ---
    # step 58 (docs/steps/step_58.md): any selection order, no parenting, Max Influences
    "Skin/Bind Skin": "maya_kit.bind_skin",
    "Skin/Unbind Skin": "maya_kit.unbind_skin",
    "Skin/Go to Bind Pose": "pose.transforms_clear",
    "Skin/Paint Skin Weights": "maya_kit.paint_skin_weights",
    "Skin/Mirror Skin Weights": "maya_kit.mirror_skin_weights",
    "Skin/Copy Skin Weights": "maya_kit.copy_skin_weights",
    "Skin/Copy Vertex Weights": "maya_kit.copy_vertex_weights",
    "Skin/Paste Vertex Weights": "maya_kit.paste_vertex_weights",
    "Skin/Edit Influences/Set Max Influences...": "object.vertex_group_limit_total",
    "Skin/Smooth Skin Weights": "object.vertex_group_smooth",
    "Skin/Prune Small Weights": "object.vertex_group_clean",
    "Skin/Normalize Weights/Normalize Weights": "object.vertex_group_normalize_all",
    # --- Constrain (Rigging, Animation): Maya selects targets first, the
    # constrained object last = Blender's active object.
    "Constrain/Parent": _con('CHILD_OF'),
    "Constrain/Point": _con('COPY_LOCATION'),
    "Constrain/Orient": _con('COPY_ROTATION'),
    "Constrain/Scale": _con('COPY_SCALE'),
    "Constrain/Aim": _con('TRACK_TO'),
    "Constrain/Pole Vector": "maya_kit.pole_vector",
    "Constrain/Motion Paths/Attach to Motion Path": _con('FOLLOW_PATH'),
    "Constrain/Geometry": _con('SHRINKWRAP'),
    # --- Key (Animation) ---
    # step 56: S = every keyable channel (docs/steps/step_56.md 「계획」 4)
    "Key/Set Key": "maya_kit.set_key",
    "Key/Set Key on Animated": ("anim.keyframe_insert_by_name", {"type": "Available"}),
    "Key/Set Breakdown Key": ("maya_kit.set_key", {"breakdown": True}),
    "Key/Set Driven Key/Set...": "maya_kit.sdk_window",      # step 62
    "Key/Set Driven Key/Go to Previous": ("maya_kit.sdk_go", {"direction": 'PREVIOUS'}),
    "Key/Set Driven Key/Go to Next": ("maya_kit.sdk_go", {"direction": 'NEXT'}),
    "Key/Insert Key": ("anim.keyframe_insert_by_name", {"type": "Available"}),
    "Key/Cut Keys": ("maya_kit.time_keys", {"action": "CUT"}),
    "Key/Copy Keys": ("maya_kit.time_keys", {"action": "COPY"}),
    "Key/Paste Keys": ("maya_kit.time_keys", {"action": "PASTE"}),
    "Key/Snap Keys": ("maya_kit.time_keys", {"action": "SNAP"}),
    "Key/Hold Current Keys": ("anim.keyframe_insert_by_name", {"type": "Available"}),
    "Key/Set Key on Translate": ("anim.keyframe_insert_by_name", {"type": "Location"}),
    "Key/Set Key on Rotate": ("anim.keyframe_insert_by_name", {"type": "Rotation"}),
    "Key/Set Key on Scale": ("anim.keyframe_insert_by_name", {"type": "Scaling"}),
    "Key/Delete Keys": ("v3d", "anim.keyframe_clear_v3d", {"confirm": False}),
    "Key/Bake Simulation": "nla.bake",
    # --- Playback ---
    "Playback/Playblast": ("v3d", "render.opengl", {"animation": True}),
    "Playback/Play": "screen.animation_play",
    "Playback/Backward": ("screen.animation_play", {"reverse": True}),
    "Playback/Stop": ("screen.animation_cancel", {"restore_frame": False}),
    "Playback/Next Key": ("screen.keyframe_jump", {"next": True}),
    "Playback/Prev Key": ("screen.keyframe_jump", {"next": False}),
    "Playback/Next Frame": ("screen.frame_offset", {"delta": 1}),
    "Playback/Prev Frame": ("screen.frame_offset", {"delta": -1}),
    "Playback/Play Range Start": ("screen.frame_jump", {"end": False}),
    "Playback/Play Range End": ("screen.frame_jump", {"end": True}),
    "Playback/Set Range to/Start/End": ("maya_kit.time_set_range", {"mode": "START_END"}),
    "Playback/Set Range to/Min/Max": ("maya_kit.time_set_range", {"mode": "MIN_MAX"}),
    "Playback/Set Range to/Selected": ("maya_kit.time_set_range", {"mode": "SELECTED"}),
    "Playback/Playback Speed/Real-time": ("wm.context_set_enum", {"data_path": "scene.sync_mode",
                                                                   "value": "FRAME_DROP"}),
    "Playback/Render Current Frame": "render.render",
    "Playback/Render Settings": "maya_kit.render_settings",
    # --- Visualize ---
    "Visualize/Create Editable Motion Trail": "object.paths_calculate",
    # --- FX ---
    "nCloth/Create nCloth": _mod('CLOTH'),
    "nCloth/Create Passive Collider": _mod('COLLISION'),
    "nHair/Create Hair": "object.curves_empty_hair_add",
    "Fluids/3D Container": "maya_kit.quick_smoke",
    "Fluids/Ocean": _mod('OCEAN'),
    # step 54: fields in Maya units at the origin (operators/create.py FIELD_*)
    "Fields/Solvers/Air": _create('FIELD_AIR'),
    "Fields/Solvers/Drag": _create('FIELD_DRAG'),
    "Fields/Solvers/Gravity": _create('FIELD_GRAVITY'),
    "Fields/Solvers/Newton": _create('FIELD_NEWTON'),
    "Fields/Solvers/Radial": _create('FIELD_RADIAL'),
    "Fields/Solvers/Turbulence": _create('FIELD_TURBULENCE'),
    "Fields/Solvers/Uniform": _create('FIELD_UNIFORM'),
    "Fields/Solvers/Vortex": _create('FIELD_VORTEX'),
    "Fields/Solvers/Create Active Rigid Body": ("rigidbody.object_add", {"type": 'ACTIVE'}),
    "Fields/Solvers/Create Passive Rigid Body": ("rigidbody.object_add", {"type": 'PASSIVE'}),
    "Fields/Solvers/Create Pin Constraint": ("rigidbody.connect", {"con_type": 'POINT'}),
    "Fields/Solvers/Create Hinge Constraint": ("rigidbody.connect", {"con_type": 'HINGE'}),
    "Fields/Solvers/Create Spring Constraint": ("rigidbody.connect", {"con_type": 'GENERIC_SPRING'}),
    "Effects/Fire": ("maya_kit.quick_smoke", {"style": 'FIRE'}),
    "Effects/Smoke": "maya_kit.quick_smoke",
    # --- Rendering ---
    # Materials (research/maya/menus.md:1652-1657; operators/material.py, docs/steps/step_29.md).
    "Lighting/Shading/Material Attributes": ("v3d", "maya_kit.material_attributes", {}),
    "Lighting/Shading/Assign New Material...": "maya_kit.assign_new_material",
    "Lighting/Shading/Assign Favorite Material": ("menu", "MAYAKIT_MT_assign_favorite_material"),
    "Lighting/Shading/Assign Existing Material": ("menu", "MAYAKIT_MT_assign_existing_material"),
    "Texturing/3D Paint Tool": "paint.texture_paint_toggle",
    "Render/Render Settings...": "maya_kit.render_settings",
}

# Items Maya adds at run time, inserted after a data path: {after path: [item]} with
# items like menu_data's ((label,) or ("-", section label)). Modify's Pivot section
# (Center Pivot, Bake Pivot) is built by ModObjectsMenu.mel at run time and missing from
# research/maya/menus.json (docs/steps/step_10.md 「계획」 9); it sits after Match
# Transformations, before the Align section ($M\startup\ModObjectsMenu.mel:356-376, step 59).
EXTRA = {
    "Modify/Match Transformations": [("-", "Pivot"), ("Center Pivot",), ("Bake Pivot",)],
    # Attributes section, built at run time from the AddAttribute / RenameAttribute / DeleteAttribute run time
    # commands (research/maya/runtime_commands.json:4659-4685); Maya puts Naming between them (not mapped yet).
    "Modify/Evaluate Nodes": [("-", "Attributes"), ("Add Attribute...",), ("Edit Attribute...",),
                              ("Delete Attribute...",)],
    # Maya Kit's own switch back to plain Blender (switch.py, step 60): found by the menu search too.
    "Windows/Settings/Preferences": [("Switch to Blender",)],
}

# Submenus Maya builds at run time, so research/maya/menus.json has them as leaves (or with a
# placeholder child): {label path: [items like menu_data's]}. Their actions are in MAP.
CHILDREN = {
    # Modify > Match Transformations / Snap Align Objects ($M\startup\ModObjectsMenu.mel:290-480, step 59)
    "Modify/Match Transformations": [
        ("Match All Transforms",), ("Match Translation",), ("Match Rotation",), ("Match Scaling",),
        ("-", ""), ("Match Pivots",)],
    "Modify/Snap Align Objects": [
        ("Point to Point",), ("2 Points to 2 Points",), ("3 Points to 3 Points",), ("Align Objects",),
        ("Position Along Curve",)],
    "Windows/General Editors": [
        ("Attribute Editor",), ("Channel Box / Layer Editor",), ("Channel Box",), ("Layer Editor",),
        ("Tool Settings",), ("-", ""), ("Hypergraph: Hierarchy",), ("Hypergraph: Connections",),
        ("Asset Editor",), ("Attribute Spread Sheet",), ("Component Editor",), ("Connection Editor",),
        ("Channel Control",), ("Display Layer Editor",), ("File Path Editor",), ("Namespace Editor",),
        ("-", ""), ("Script Editor",), ("Command Shell",), ("Profiler",), ("Evaluation Toolkit",)],
    "Windows/Modeling Editors": [
        ("Modeling Toolkit",), ("Paint Effects",), ("UV Editor",), ("XGen Editor",), ("Crease Sets",)],
    "Windows/Animation Editors": [
        ("Graph Editor",), ("Time Editor",), ("Trax Editor",), ("Camera Sequencer",), ("Dope Sheet",),
        ("Quick Rig",), ("HumanIK",), ("Shape Editor",), ("Pose Editor",), ("Expression Editor",),
        ("Motion Library",)],
    # Hypershade / Render View / Render Settings head Maya's list (added by the renderer menus) [K].
    "Windows/Rendering Editors": [
        ("Hypershade",), ("Render View",), ("Render Settings",), ("-", ""), ("Render Layer Editor",),
        ("Light Editor",), ("Rendering Flags",), ("Shading Group Attributes",),
        ("Hardware Render Buffer",)],
    "Windows/Relationship Editors": [
        ("Animation Layers",), ("Camera Sets",), ("Character Sets",), ("Deformer Sets",),
        ("Display Layers",), ("Dynamic Relationships",), ("Light Linking",), ("Partitions",),
        ("Render Layers",), ("Render Pass Sets",), ("Sets",), ("UV Linking",)],
    # Display > Heads Up Display: Maya lists every HUD item at run time [K]; the ones Blender's
    # viewport overlay can show are mapped (Poly Count = scene statistics).
    "Display/Heads Up Display": [
        ("Animation Details",), ("Bounding Box",), ("Camera Names",), ("Frame Rate",),
        ("Object Details",), ("Poly Count",), ("Selection Details",), ("View Axis",), ("View Cube",)],
}
MAP.update({
    "Display/Heads Up Display/Poly Count": _hud("space_data.overlay.show_stats"),
    # Maya furniture (ui/view_furniture.py, step 46): global like Maya's HUD.
    "Display/Heads Up Display/Camera Names": _kit_pref("maya_camera_names"),
    "Display/Heads Up Display/View Axis": _kit_pref("maya_view_axis"),
    "Display/Heads Up Display/View Cube": _kit_pref("maya_viewcube"),
})

# Blender's own menu kept at the end of the Maya menu with the same role.
BLENDER_MENU = {
    "File": ("TOPBAR_MT_file", "Blender File"),
    "Edit": ("TOPBAR_MT_edit", "Blender Edit"),
    "Windows": ("TOPBAR_MT_window", "Blender Window"),
    "Render": ("TOPBAR_MT_render", "Blender Render"),
    "Help": ("TOPBAR_MT_help", "Blender Help"),
}


def spec(path):
    """Normalised (kind, target, props) for a label path, or None if unmapped."""
    return normalize(MAP.get(path))


def normalize(value):
    """(kind, target, props) for a mapping value (also used by marking menus,
    which add ``("pie", MENU_ID)``); None stays None (greyed out)."""
    if value is None:
        return None
    if isinstance(value, str):
        return ("op", value, {})
    if value[0] == "v3d":
        return ("v3d", value[1], dict(value[2]))
    if value[0] == "tool":
        return ("tool", value[1], {"edit": value[2]})
    if value[0] in ("menu", "pie"):
        return (value[0], value[1], {})
    return ("op", value[0], dict(value[1]))
