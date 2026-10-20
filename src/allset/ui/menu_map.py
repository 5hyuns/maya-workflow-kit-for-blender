# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya menu item -> Blender action.

Key = label path in ``menu_data.MENUS`` ("Create/Polygon Primitives/Cube"),
starting with the menu *label*, so the Deform and Constrain menus that
Modeling, Rigging and Animation share map once. Value:

- ``"op.id"`` or ``("op.id", {props})``: drawn as that operator (its poll
  greys the item out where Blender can't run it, e.g. edit-mode commands in
  object mode);
- ``("v3d", "op.id", {props})``: needs a 3D View region; run through
  ``allset.menu_run`` in the largest 3D View;
- ``("tool", "builtin.id", edit)``: switch the active tool, entering mesh edit
  mode first when ``edit``;
- ``("menu", "MENU_ID")``: a Blender menu as the submenu.
- ``("prop", "context.path", {"value": v})``: a Maya check / radio item drawn as that Blender property (step 104;
  without ``value`` a check box, with it one choice of a radio collection).

Items not listed are drawn greyed out. ``EXTRA`` adds items Maya builds at run
time (not in the static menu data), e.g. Modify's Pivot section.
"""

def _create(kind):
    # Maya default size at the origin, Maya names (operators/create.py, ).
    return ("allset.create", {"kind": kind})


_PRIMS = {label: _create(kind) for label, kind in (
    ("Sphere", 'SPHERE'), ("Cube", 'CUBE'), ("Cylinder", 'CYLINDER'), ("Cone", 'CONE'),
    ("Torus", 'TORUS'), ("Plane", 'PLANE'), ("Disc", 'DISC'), ("Platonic Solid", 'PLATONIC'),
    ("Pyramid", 'PYRAMID'), ("Prism", 'PRISM'))}


def _del(kind, all_=False):
    return ("allset.delete_by_type", {"type": kind, "all": all_})


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
    return ("allset.constrain", {"type": kind})


def _editor(ui_type):
    # A Blender editor in a new window, like a Maya editor window (operators/menu_extras.py).
    return ("allset.open_editor", {"ui_type": ui_type})


def _dock(dock):
    return ("v3d", "allset.dock_show", {"dock": dock})


def _hud(data_path):
    return ("v3d", "wm.context_toggle", {"data_path": data_path})


def _kit_pref(prop):
    """Toggle one of this add-on's preferences (Maya HUD options are global)."""
    pkg = __package__.rpartition(".")[0]
    return ("wm.context_toggle", {"data_path": f'preferences.addons["{pkg}"].preferences.{prop}'})


# Windows > ... Editors: Maya fills these submenus at run time (startup/Maya
# Maya / Maya / Maya / buildRenderingEdMenu /
# Maya; labels from ). Items listed in
# CHILDREN without an action here draw greyed. 
_WINDOW_EDITORS = {
    "General Editors/Attribute Editor": _dock('ATTRIBUTE_EDITOR'),
    "General Editors/Channel Box / Layer Editor": _dock('CHANNEL_BOX'),
    "General Editors/Channel Box": _dock('CHANNEL_BOX'),
    "General Editors/Layer Editor": _dock('CHANNEL_BOX'),
    "General Editors/Tool Settings": ("allset.editor_toggle", {"editor": 'TOOL_SETTINGS'}),
    "General Editors/Attribute Spread Sheet": _editor('SPREADSHEET'),
    "General Editors/Display Layer Editor": _dock('CHANNEL_BOX'),
    "General Editors/Script Editor": "allset.script_editor",
    "Modeling Editors/UV Editor": _editor('UV'),
    "Modeling Editors/Modeling Toolkit": _dock('MODELING_TOOLKIT'),          # step 63
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
    "Rendering Editors/Hypershade": "allset.hypershade",                 # step 67: browser + graph + AE
    "Rendering Editors/Light Editor": "allset.light_editor",             # step 67: kit light list
    "Rendering Editors/Render View": "render.view_show",
    "Rendering Editors/Render Settings": "allset.render_settings",
    "Rendering Editors/Shading Group Attributes": ("v3d", "allset.material_attributes", {}),
    "Relationship Editors/Display Layers": _dock('CHANNEL_BOX'),
}

MAP = {
    # --- File ( "File") ---
    "File/New Scene": "wm.read_homefile",
    # step 69: file dialogs start in the project's scenes folder (operators/project.py)
    "File/Open Scene...": "allset.open_scene",
    "File/Save Scene": "allset.save_scene",
    "File/Save Scene As...": "allset.save_scene_as",
    "File/Increment and Save": "allset.increment_save",          # step 34
    "File/Save Preferences": "wm.save_userpref",
    "File/Optimize Scene Size": "outliner.orphans_purge",
    # step 102: one Maya file dialog (Files of type + Options, cm / Y-up presets; operators/file_io.py)
    "File/Import...": "allset.file_import",
    "File/Export All...": "allset.file_export_all",
    "File/Export Selection...": "allset.file_export_selection",
    "File/Create Reference...": "allset.create_reference",           # step 69 (link + override + ns:)
    "File/Reference Editor": ("allset.open_editor", {"ui_type": 'OUTLINER', "display_mode": 'LIBRARIES'}),
    "File/Project Window": "allset.project_window",
    "File/Set Project...": "allset.set_project",
    "File/Recent Projects": ("menu", "ALLSET_MT_recent_projects"),
    "File/Recent Files": ("menu", "TOPBAR_MT_file_open_recent"),
    "File/Exit": "wm.quit_blender",
    # --- Edit ---
    "Edit/Undo": "ed.undo",
    "Edit/Redo": "ed.redo",
    "Edit/Repeat": "screen.repeat_last",
    "Edit/Recent Commands List": "screen.repeat_history",
    "Edit/Cut": "allset.cut",                              # copy + delete (step 90)
    "Edit/Copy": ("v3d", "view3d.copybuffer", {}),
    "Edit/Paste": ("v3d", "allset.paste", {}),
    # Maya Delete Keys = every key of the selection (step 56; Time Slider RMB Delete = this frame / range)
    "Edit/Keys/Delete Keys": ("v3d", "anim.keyframe_clear_v3d", {"confirm": False}),
    "Edit/Keys/Cut Keys": ("allset.time_keys", {"action": "CUT"}),
    "Edit/Keys/Copy Keys": ("allset.time_keys", {"action": "COPY"}),
    "Edit/Keys/Paste Keys": ("allset.time_keys", {"action": "PASTE"}),
    "Edit/Keys/Bake Simulation": "nla.bake",
    "Edit/Delete": "object.delete",
    "Edit/Ungroup": "allset.ungroup",                            # step 34
    "Edit/Delete by Type/History": "allset.delete_history",
    "Edit/Delete by Type/Non-Deformer History": ("allset.delete_history", {"non_deformer": True}),
    **{f"Edit/Delete by Type/{k}": _del(v) for k, v in _DELETE_BY_TYPE.items()
       if v not in ('HISTORY', 'NON_DEFORMER_HISTORY')},
    **{f"Edit/Delete All by Type/{k}": _del(v, True)
       for k, v in {**_DELETE_BY_TYPE, **_DELETE_ALL_ONLY}.items()},
    "Edit/Duplicate": "allset.duplicate",                     # step 19: Maya names, in place
    "Edit/Duplicate Special": "allset.duplicate_special",
    "Edit/Duplicate with Transform": "allset.duplicate_with_transform",
    "Edit/Group": "allset.group",
    "Edit/Parent": "allset.parent",
    "Edit/Unparent": "allset.unparent",
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
    "Create/Sets/Set": "allset.create_set",                       # step 96: kit sets (operators/sets.py)
    "Create/Sets/Quick Select Set...": "allset.create_quick_select_set",
    # --- Select ---
    "Select/All": ("object.select_all", {"action": 'SELECT'}),
    "Select/Quick Select Sets": ("menu", "ALLSET_MT_quick_select_sets"),   # step 96
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
    "Select/Object/Component": "allset.toggle_sel_mode",
    "Select/Components/Multi-Component": ("allset.component_mode", {"type": 'MULTI'}),
    "Select/Components/Vertex": ("allset.component_mode", {"type": 'VERT'}),
    "Select/Components/Edge": ("allset.component_mode", {"type": 'EDGE'}),
    "Select/Components/Face": ("allset.component_mode", {"type": 'FACE'}),
    "Select/Contiguous Edges": ("allset.select_loops", {"ring": False}),
    "Select/Convert Selection/To Vertices": ("mesh.select_mode", {"type": 'VERT'}),
    "Select/Convert Selection/To Edges": ("mesh.select_mode", {"type": 'EDGE', "use_expand": True}),
    "Select/Convert Selection/To Edge Loop": ("allset.select_loops", {"ring": False}),
    "Select/Convert Selection/To Edge Ring": ("allset.select_loops", {"ring": True}),
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
    "Modify/Reset Transformations": "allset.reset_transform",
    "Modify/Freeze Transformations": "allset.freeze_transform",
    "Modify/Center Pivot": "allset.center_pivot",
    # step 59: pivot / align ( P7, P8, S8-S13)
    "Modify/Bake Pivot": "allset.bake_pivot",
    "Modify/Match Transformations/Match All Transforms": ("allset.match_transform", {"kind": 'ALL'}),
    "Modify/Match Transformations/Match Translation": ("allset.match_transform", {"kind": 'TRANSLATE'}),
    "Modify/Match Transformations/Match Rotation": ("allset.match_transform", {"kind": 'ROTATE'}),
    "Modify/Match Transformations/Match Scaling": ("allset.match_transform", {"kind": 'SCALE'}),
    "Modify/Match Transformations/Match Pivots": "allset.match_pivots",
    "Modify/Snap Align Objects/Point to Point": ("allset.snap_points", {"count": 1}),
    "Modify/Snap Align Objects/2 Points to 2 Points": ("allset.snap_points", {"count": 2}),
    "Modify/Snap Align Objects/3 Points to 3 Points": ("allset.snap_points", {"count": 3}),
    "Modify/Snap Align Objects/Align Objects": "allset.align_objects",
    "Modify/Snap Together Tool": "allset.snap_together",
    "Modify/Make Live": "allset.make_live",
    "Modify/Add Attribute...": "allset.add_attribute",     # Attributes section (EXTRA), step 62
    "Modify/Edit Attribute...": "allset.edit_attribute",
    "Modify/Delete Attribute...": "allset.delete_attribute",
    "Windows/Switch to Blender": ("allset.switch_mode", {"mode": 'BLENDER'}),
    "Modify/Convert/NURBS to Polygons": ("object.convert", {"target": 'MESH'}),
    "Modify/Convert/Smooth Mesh Preview to Polygons": ("object.convert", {"target": 'MESH'}),
    "Modify/Convert/Polygon Edges to Curve": ("object.convert", {"target": 'CURVE'}),
    "Modify/Convert/Type to Curves": ("object.convert", {"target": 'CURVE'}),
    "Modify/Convert/Instance to Object": "object.duplicates_make_real",
    # --- Display ---
    "Display/Grid": ("v3d", "allset.toggle_grid", {}),     # Maya grid (ui/maya_grid.py, step 45)
    "Display/Hide": ("object.hide_view_set", {"unselected": False}),
    "Display/Show": "object.hide_view_clear",
    "Display/Transform Display/Local Rotation Axes": ("wm.context_toggle", {"data_path": "object.show_axis"}),
    "Display/Frame All in All Views": ("allset.frame_all_views", {"selected": False}),
    "Display/Frame Selection in All Views": ("allset.frame_all_views", {"selected": True}),
    "Display/Frame Selection with Children in All Views": ("allset.frame_all_views",
                                                           {"selected": True, "children": True}),
    # --- Windows ---
    "Windows/Workspaces": ("menu", "TOPBAR_MT_workspace_menu"),
    # Maya raises a docked Outliner, else opens a floating one (ui/maya_dock.py, step 116)
    "Windows/Outliner": ("allset.panel_show", {"panel": 'OUTLINER'}),
    "Windows/Node Editor": _editor('ShaderNodeTree'),
    **{f"Windows/{path}": action for path, action in _WINDOW_EDITORS.items()},
    "Windows/UI Elements": ("menu", "ALLSET_MT_ui_elements"),
    # Settings/Preferences submenu ($M/scripts/startup/Maya Maya; step 120)
    "Windows/Settings/Preferences/Preferences": "screen.userpref_show",
    "Windows/Settings/Preferences/Hotkey Editor": ("screen.userpref_show", {"section": 'KEYMAP'}),
    "Windows/Settings/Preferences/Color Settings": "allset.color_settings",   # viewport background
    "Windows/Settings/Preferences/Plug-in Manager": ("screen.userpref_show", {"section": 'ADDONS'}),
    "Windows/Playblast": ("v3d", "allset.playblast", {}),              # step 70: temp movie + player
    "Windows/Output Window": "wm.console_toggle",
    # --- Mesh (Modeling) ---
    "Mesh/Combine": "allset.combine",                     # Maya: new pCube2, centre pivot (step 63)
    "Mesh/Separate": "allset.separate",                   # object mode: polySurfaceN under a group
    "Mesh/Booleans/Union": ("allset.boolean", {"operation": 'UNION'}),
    "Mesh/Booleans/Difference": ("allset.boolean", {"operation": 'DIFFERENCE'}),
    "Mesh/Booleans/Intersection": ("allset.boolean", {"operation": 'INTERSECT'}),
    "Mesh/Fill Hole": "mesh.fill_holes",
    "Mesh/Reduce": _mod('DECIMATE'),
    "Mesh/Remesh": _mod('REMESH'),
    "Mesh/Smooth": _mod('SUBSURF'),
    "Mesh/Triangulate": _mod('TRIANGULATE'),
    "Mesh/Quadrangulate": "mesh.tris_convert_to_quads",
    "Mesh/Mirror": "allset.mirror",                       # applied, world plane; □ = Mirror Options
    "Mesh/Transfer Attributes": _mod('DATA_TRANSFER'),
    "Mesh/Smooth Proxy/Subdiv Proxy": _mod('SUBSURF'),
    # --- Edit Mesh ---
    "Edit Mesh/Add Divisions": "mesh.subdivide",
    "Edit Mesh/Bevel": ("v3d", "mesh.bevel", {}),
    "Edit Mesh/Bridge": "mesh.bridge_edge_loops",
    "Edit Mesh/Collapse": "mesh.edge_collapse",
    "Edit Mesh/Connect": "mesh.vert_connect_path",
    "Edit Mesh/Extrude": ("v3d", "allset.extrude", {}),       # polyExtrudeFace (step 65)
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
    "Mesh Tools/Show/Hide Modeling Toolkit": ("allset.editor_toggle", {"editor": 'MODELING_TOOLKIT'}),
    "Mesh Tools/Create Polygon": ("tool", "builtin.poly_build", True),
    "Mesh Tools/Insert Edge Loop": ("tool", "builtin.loop_cut", True),
    "Mesh Tools/Multi-Cut": ("tool", "builtin.knife", True),
    "Mesh Tools/Offset Edge Loop": ("v3d", "mesh.offset_edge_loops_slide", {}),
    "Mesh Tools/Quad Draw": ("tool", "builtin.poly_build", True),
    "Mesh Tools/Slide Edge": ("tool", "builtin.edge_slide", True),
    "Mesh Tools/Target Weld": ("tool", "allset.target_weld_tool", True),     # step 64
    "Mesh Tools/Crease Tool": ("tool", "allset.crease_tool", True),
    # --- Mesh Display ---
    "Mesh Display/Average": "mesh.average_normals",
    "Mesh Display/Conform": "mesh.normals_make_consistent",
    "Mesh Display/Reverse": "mesh.flip_normals",
    "Mesh Display/Set to Face": "mesh.set_normals_from_faces",
    # Maya polySoftEdge: edges selected = those, object = every edge (step 101, Maya)
    "Mesh Display/Harden Edge": ("allset.soften_harden", {"angle": 0.0}),
    "Mesh Display/Soften Edge": ("allset.soften_harden", {"angle": 180.0}),
    "Mesh Display/Paint Vertex Color Tool": "paint.vertex_paint_toggle",
    # --- Curves ---
    "Curves/Open/Close": "curve.cyclic_toggle",
    "Curves/Insert Knot": "curve.subdivide",
    "Curves/Smooth": "curve.smooth",
    "Curves/Reverse Direction": "curve.switch_direction",
    # --- Deform (Modeling, Rigging, Animation share it) ---
    "Deform/Blend Shape": "allset.blend_shape",          # targets, then the base (join_shapes, step 62)
    "Deform/Blend Shape#2/Add": "allset.blend_shape",
    "Deform/Delta Mush": _mod('CORRECTIVE_SMOOTH'),
    "Deform/Solidify": _mod('SOLIDIFY'),
    "Deform/Lattice": _mod('LATTICE'),
    "Deform/Wrap": _mod('SURFACE_DEFORM'),
    "Deform/ShrinkWrap": _mod('SHRINKWRAP'),
    "Deform/Nonlinear/Wave": _mod('WAVE'),
    "Deform/Texture": _mod('DISPLACE'),
    "Deform/Paint Weights/Set Membership": "paint.weight_paint_toggle",
    # --- UV ---
    "UV/UV Editor": _editor('UV'),
    "UV/Planar": "allset.uv_planar",
    "UV/Normal-Based": "allset.uv_planar",
    "UV/Automatic": "uv.smart_project",
    "UV/Camera-based": ("v3d", "uv.project_from_view", {}),
    "UV/Cylindrical": ("v3d", "uv.cylinder_project", {}),
    "UV/Spherical": ("v3d", "uv.sphere_project", {}),
    "UV/Cut UV Edges": "allset.uv_cut",          # seam + shells apart in place (step 66)
    "UV/Sew UV Edges": "allset.uv_sew",
    "UV/3D Cut and Sew UV Tool": "allset.cut_sew_tool_set",   # step 79          # seam cleared + the smaller shell moved onto the edge
    "UV/Merge UVs": "uv.weld",
    # --- Skeleton (Rigging) ---
    "Control/Create Character Set": "anim.keying_set_add",   # step 54: Keying Set + notice (ui/notices.py)
    # step 57: Joint Tool (click, click, Enter), option-box dialogs
    "Skeleton/Create Joints": "allset.joint_tool",
    "Skeleton/Quick Rig": "allset.quick_rig",              # Rigify (notice in ui/notices.py), step 62
    "Windows/Animation Editors/Quick Rig": "allset.quick_rig",
    "Skeleton/Mirror Joints": "allset.mirror_joints",
    "Skeleton/Orient Joint": "allset.orient_joint",
    "Skeleton/Remove Joints": "armature.delete",
    "Skeleton/Disconnect Joint": ("armature.parent_clear", {"type": 'DISCONNECT'}),
    "Skeleton/Create IK Handle": "allset.ik_handle",       # step 58: click start + end joint
    # --- Skin ---
    # step 58: any selection order, no parenting, Max Influences
    "Skin/Bind Skin": "allset.bind_skin",
    "Skin/Unbind Skin": "allset.unbind_skin",
    "Skin/Go to Bind Pose": "pose.transforms_clear",
    "Skin/Paint Skin Weights": "allset.paint_skin_weights",
    "Skin/Mirror Skin Weights": "allset.mirror_skin_weights",
    "Skin/Copy Skin Weights": "allset.copy_skin_weights",
    "Skin/Copy Vertex Weights": "allset.copy_vertex_weights",
    "Skin/Paste Vertex Weights": "allset.paste_vertex_weights",
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
    "Constrain/Pole Vector": "allset.pole_vector",
    "Constrain/Motion Paths/Attach to Motion Path": _con('FOLLOW_PATH'),
    "Constrain/Geometry": _con('SHRINKWRAP'),
    # --- Key (Animation) ---
    # step 56: S = every keyable channel
    "Key/Set Key": "allset.set_key",
    "Key/Set Key on Animated": ("anim.keyframe_insert_by_name", {"type": "Available"}),
    "Key/Set Breakdown Key": ("allset.set_key", {"breakdown": True}),
    "Key/Set Driven Key/Set...": "allset.sdk_window",      # step 62
    "Key/Set Driven Key/Go to Previous": ("allset.sdk_go", {"direction": 'PREVIOUS'}),
    "Key/Set Driven Key/Go to Next": ("allset.sdk_go", {"direction": 'NEXT'}),
    "Key/Insert Key": ("anim.keyframe_insert_by_name", {"type": "Available"}),
    "Key/Cut Keys": ("allset.time_keys", {"action": "CUT"}),
    "Key/Copy Keys": ("allset.time_keys", {"action": "COPY"}),
    "Key/Paste Keys": ("allset.time_keys", {"action": "PASTE"}),
    "Key/Snap Keys": ("allset.time_keys", {"action": "SNAP"}),
    "Key/Hold Current Keys": ("anim.keyframe_insert_by_name", {"type": "Available"}),
    "Key/Set Key on Translate": ("anim.keyframe_insert_by_name", {"type": "Location"}),
    "Key/Set Key on Rotate": ("anim.keyframe_insert_by_name", {"type": "Rotation"}),
    "Key/Set Key on Scale": ("anim.keyframe_insert_by_name", {"type": "Scaling"}),
    "Key/Delete Keys": ("v3d", "anim.keyframe_clear_v3d", {"confirm": False}),
    "Key/Bake Simulation": "nla.bake",
    # --- Playback ---
    "Playback/Playblast": ("v3d", "allset.playblast", {}),
    "Playback/Play": "screen.animation_play",
    "Playback/Backward": ("screen.animation_play", {"reverse": True}),
    "Playback/Stop": ("screen.animation_cancel", {"restore_frame": False}),
    "Playback/Next Key": ("screen.keyframe_jump", {"next": True}),
    "Playback/Prev Key": ("screen.keyframe_jump", {"next": False}),
    "Playback/Next Frame": ("screen.frame_offset", {"delta": 1}),
    "Playback/Prev Frame": ("screen.frame_offset", {"delta": -1}),
    "Playback/Play Range Start": ("screen.frame_jump", {"end": False}),
    "Playback/Play Range End": ("screen.frame_jump", {"end": True}),
    "Playback/Set Range to/Start/End": ("allset.time_set_range", {"mode": "START_END"}),
    "Playback/Set Range to/Min/Max": ("allset.time_set_range", {"mode": "MIN_MAX"}),
    "Playback/Set Range to/Selected": ("allset.time_set_range", {"mode": "SELECTED"}),
    "Playback/Playback Speed/Real-time": ("wm.context_set_enum", {"data_path": "scene.sync_mode",
                                                                   "value": "FRAME_DROP"}),
    "Playback/Render Current Frame": "render.render",
    "Playback/Render Settings": "allset.render_settings",
    # --- Visualize ---
    "Visualize/Create Editable Motion Trail": "object.paths_calculate",
    # --- FX ---
    # step 68 (operators/fx.py, ): Maya units + nucleus, every selected mesh
    "nParticles/Create Emitter": "allset.fx_emitter",
    "nParticles/Create Emitter#2": "allset.fx_emitter",               # Legacy Particles section
    "nParticles/Emit from Object": "allset.fx_emit_from_object",
    "nParticles/Emit from Object#2": "allset.fx_emit_from_object",
    "nCloth/Create nCloth": "allset.fx_ncloth",
    "nCloth/Create Passive Collider": "allset.fx_passive",
    "nCloth/Remove nCloth": "allset.fx_remove_ncloth",
    "nCache/Create New Cache/nObject": ("allset.ncache", {"action": 'CREATE', "kind": 'NOBJECT'}),
    "nCache/Create New Cache/Maya Fluid": ("allset.ncache", {"action": 'CREATE', "kind": 'FLUID'}),
    "nCache/Delete Cache": ("allset.ncache", {"action": 'DELETE', "kind": 'ALL'}),
    "Fields/Solvers/Interactive Playback": "screen.animation_play",
    "nHair/Create Hair": "object.curves_empty_hair_add",
    "Fluids/3D Container": "allset.quick_smoke",
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
    "Fields/Solvers/Create Active Rigid Body": ("allset.fx_rigid", {"type": 'ACTIVE'}),
    "Fields/Solvers/Create Passive Rigid Body": ("allset.fx_rigid", {"type": 'PASSIVE'}),
    "Fields/Solvers/Create Pin Constraint": ("rigidbody.connect", {"con_type": 'POINT'}),
    "Fields/Solvers/Create Hinge Constraint": ("rigidbody.connect", {"con_type": 'HINGE'}),
    "Fields/Solvers/Create Spring Constraint": ("rigidbody.connect", {"con_type": 'GENERIC_SPRING'}),
    "Effects/Fire": ("allset.quick_smoke", {"style": 'FIRE'}),
    "Effects/Smoke": "allset.quick_smoke",
    # --- Rendering ---
    # Materials (; operators/material.py, ).
    "Lighting/Shading/Material Attributes": ("v3d", "allset.material_attributes", {}),
    "Lighting/Shading/Assign New Material...": "allset.assign_new_material",
    "Lighting/Shading/Assign Favorite Material": ("menu", "ALLSET_MT_assign_favorite_material"),
    "Lighting/Shading/Assign Existing Material": ("menu", "ALLSET_MT_assign_existing_material"),
    "Texturing/3D Paint Tool": "paint.texture_paint_toggle",
    "Render/Render Settings...": "allset.render_settings",
    # Render menu (, restored by tools/gen_menu_data.py PLACEHOLDERS; step 67).
    # Maya renders into the Render View window: render.render INVOKE opens Blender's (Render Result).
    "Render/Render Using": ("menu", "ALLSET_MT_render_using"),
    "Render/Render Current Frame": "render.render",
    "Render/Redo Previous Render": "render.render",
    "Render/IPR Render Current Frame": "allset.ipr_toggle",
    "Render/Redo Previous IPR Render": "allset.ipr_toggle",
    "Render/Render Sequence": ("render.render", {"animation": True}),
}

# Items Maya adds at run time, inserted after a data path: {after path: [item]} with
# items like menu_data's ((label,) or ("-", section label)). Modify's Pivot / Naming / Attributes
# sections now come from tools/gen_menu_data.py RUNTIME_LABELS (step 101).
EXTRA = {
    # The kit's own switch back to plain Blender (switch.py, step 60): found by the menu search too.
    "Windows/Settings/Preferences": [("Switch to Blender",)],
}

# Submenus Maya builds at run time, so  has them as leaves (or with a
# placeholder child): {label path: [items like menu_data's]}. Their actions are in MAP.
CHILDREN = {
    # Windows > Settings/Preferences ($M/scripts/startup/Maya Maya; Performance
    # Settings only with the legacy viewport, off by default; step 120)
    "Windows/Settings/Preferences": [
        ("Preferences",), ("-", ""), ("Hotkey Editor",), ("Color Settings",), ("Marking Menu Editor",),
        ("Shelf Editor",), ("Panel Editor",), ("-", ""), ("Plug-in Manager",)],
    # Modify > Match Transformations / Snap Align Objects ($M\startup\Maya-480, step 59)
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
    # Hypershade / Render View / Render Settings head Maya's list (added by the renderer menus) .
    "Windows/Rendering Editors": [
        ("Hypershade",), ("Render View",), ("Render Settings",), ("-", ""), ("Render Layer Editor",),
        ("Light Editor",), ("Rendering Flags",), ("Shading Group Attributes",),
        ("Hardware Render Buffer",)],
    "Windows/Relationship Editors": [
        ("Animation Layers",), ("Camera Sets",), ("Character Sets",), ("Deformer Sets",),
        ("Display Layers",), ("Dynamic Relationships",), ("Light Linking",), ("Partitions",),
        ("Render Layers",), ("Render Pass Sets",), ("Sets",), ("UV Linking",)],
    # Display > Heads Up Display: Maya lists every HUD item at run time ; the ones Blender's
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


def _props(tab):
    # A Properties window on one tab (Maya editors whose Blender counterpart is a Properties panel).
    return ("allset.open_editor", {"ui_type": 'PROPERTIES', "tab": tab})


def _url(url):
    return ("wm.url_open", {"url": url})


def _sculpt(brush):
    return ("allset.sculpt_tool", {"brush": brush})


_PROPORTIONAL = ("wm.context_toggle", {"data_path": "tool_settings.use_proportional_edit"})
_MANUAL = "https://docs.blender.org/manual/en/4.5/"
_API = "https://docs.blender.org/api/4.5/"
_NOTES = "https://developer.blender.org/docs/release_notes/4.5/"
_TUTORIALS = "https://www.blender.org/support/tutorials/"

# step 101: what Blender does cheaply. Items whose meaning differs carry a
# notice (ui/notices.py NOTICES);  has the Maya behaviour checked .
MAP.update({
    # File
    "File/Archive Scene": "file.pack_all",
    "File/View Image...": _editor('IMAGE_EDITOR'),
    "File/View Sequence...": "render.play_rendered_anim",
    "File/Recent Increments": ("menu", "TOPBAR_MT_file_open_recent"),
    "File/Game Exporter": "export_scene.fbx",
    "File/Send To Unity": "export_scene.fbx",
    "File/Send To Unreal": "export_scene.fbx",
    # Edit
    "Edit/Keys/Snap Keys": ("allset.time_keys", {"action": "SNAP"}),
    "Edit/Delete All by Type/Shading Groups and Materials": "outliner.orphans_purge",
    # Create
    "Create/SVG": "import_curve.svg",
    "Create/Universal Scene Description (USD)": "wm.usd_import",
    # Select
    "Select/Shortest Edge Path Tool": "mesh.shortest_path_select",
    "Select/Convert Selection/To Contained Edges": ("mesh.select_mode", {"type": 'EDGE'}),
    "Select/Convert Selection/To Contained Faces": ("mesh.select_mode", {"type": 'FACE'}),
    "Select/Convert Selection/To UV Shell": ("mesh.select_linked", {"delimit": {'UV'}}),
    "Select/All CVs": ("curve.select_all", {"action": 'SELECT'}),
    "Select/First CV": "curve.de_select_first",
    "Select/Last CV": "curve.de_select_last",
    "Select/All by Type/Image Planes": ("object.select_by_type", {"type": 'EMPTY'}),
    # Modify
    "Modify/Transformation Tools/Proportional Modification Tool": _PROPORTIONAL,
    "Modify/Transformation Tools/Soft Modification Tool": _PROPORTIONAL,
    "Modify/Transformation Tools/Move Normal Tool": ("v3d", "transform.shrink_fatten", {}),
    "Modify/Prefix Hierarchy Names...": "allset.prefix_hierarchy",
    "Modify/Search and Replace Names...": "allset.search_replace_names",
    "Modify/Replace Objects": ("object.make_links_data", {"type": 'OBDATA'}),
    "Modify/Convert/NURBS Curve to Bezier": ("curve.spline_type_set", {"type": 'BEZIER'}),
    "Modify/Convert/Bezier Curve to NURBS": ("curve.spline_type_set", {"type": 'NURBS'}),
    "Modify/Evaluate Nodes/Evaluate All": ("allset.menu_note", {"item": "Modify/Evaluate Nodes/Evaluate All"}),
    # Display
    "Display/Heads Up Display/Frame Rate": ("wm.context_toggle",
                                            {"data_path": "preferences.view.show_playback_fps"}),
    "Display/Heads Up Display/Object Details": _hud("space_data.overlay.show_stats"),
    "Display/Heads Up Display/Selection Details": _hud("space_data.overlay.show_stats"),
    "Display/Toggle Show/Hide": ("allset.visibility", {"action": 'TOGGLE'}),
    "Display/Object Display/Template": ("allset.object_display", {"kind": 'TEMPLATE'}),
    "Display/Object Display/Untemplate": ("allset.object_display", {"kind": 'UNTEMPLATE'}),
    "Display/Object Display/Bounding Box": ("allset.object_display", {"kind": 'BBOX'}),
    "Display/Object Display/No Bounding Box": ("allset.object_display", {"kind": 'NO_BBOX'}),
    "Display/Polygons": ("v3d", "wm.call_panel", {"name": "VIEW3D_PT_overlay_edit_mesh", "keep_open": True}),
    "Display/Animation": ("v3d", "wm.call_panel", {"name": "VIEW3D_PT_overlay_bones", "keep_open": True}),
    "Display/Rendering": ("v3d", "wm.call_panel", {"name": "VIEW3D_PT_shading", "keep_open": True}),
    "Display/Wireframe Color...": _props('OBJECT'),
    # Windows
    "Windows/General Editors/Component Editor": _editor('SPREADSHEET'),
    "Windows/General Editors/Connection Editor": _editor('DRIVERS'),
    "Windows/General Editors/File Path Editor": ("allset.open_editor", {"ui_type": 'OUTLINER',
                                                                          "display_mode": 'LIBRARIES'}),
    "Windows/General Editors/Command Shell": _editor('CONSOLE'),
    "Windows/Animation Editors/Shape Editor": _props('DATA'),
    "Windows/Rendering Editors/Render Layer Editor": _props('VIEW_LAYER'),
    "Windows/Relationship Editors/Render Layers": _props('VIEW_LAYER'),
    "Windows/Relationship Editors/Light Linking": _props('OBJECT'),
    "Windows/Relationship Editors/Sets": _editor('OUTLINER'),
    "Windows/Content Browser": _editor('ASSETS'),
    # Mesh
    "Mesh/Conform": _mod('SHRINKWRAP'),
    "Mesh/Retopologize": "object.quadriflow_remesh",
    "Mesh/Transfer Shading Sets": ("object.make_links_data", {"type": 'MATERIAL'}),
    "Mesh/Cleanup...": ("menu", "VIEW3D_MT_edit_mesh_clean"),
    "Mesh/Smooth Proxy/Crease Tool": ("tool", "allset.crease_tool", True),
    "Mesh/Smooth Proxy/Toggle Proxy Display": ("allset.smooth_proxy", {"action": 'TOGGLE'}),
    "Mesh/Smooth Proxy/Both Proxy and Subdiv Display": ("allset.smooth_proxy", {"action": 'BOTH'}),
    # Edit Mesh
    "Edit Mesh/Detach": "allset.detach",
    "Edit Mesh/Transform": ("tool", "builtin.transform", True),
    "Edit Mesh/Flip": ("v3d", "transform.mirror", {"orient_type": 'LOCAL', "constraint_axis": (True, False, False)}),
    "Edit Mesh/Edit Edge Flow": "allset.edge_flow",
    "Edit Mesh/Wedge": "allset.wedge",
    "Edit Mesh/Split Mesh with Projected Curve": ("v3d", "mesh.knife_project", {}),
    # Mesh Tools (Sculpting Tools -> the essentials brushes, )
    "Mesh Tools/Append to Polygon": ("tool", "builtin.poly_build", True),
    **{f"Mesh Tools/Sculpting Tools/{maya} Tool": _sculpt(brush) for maya, brush in (
        ("Sculpt", "Draw"), ("Smooth", "Smooth"), ("Relax", "Relax Slide"), ("Grab", "Grab"),
        ("Pinch", "Pinch/Magnify"), ("Flatten", "Flatten/Contrast"), ("Foamy", "Clay"), ("Wax", "Clay Strips"),
        ("Scrape", "Scrape/Fill"), ("Fill", "Fill/Deepen"), ("Knife", "Crease Sharp"), ("Smear", "Smear"),
        ("Bulge", "Inflate/Deflate"), ("Amplify", "Sharpen"), ("Freeze", "Mask"))},
    # Mesh Display
    "Mesh Display/Soften/Harden Edges": "allset.soften_harden",
    "Mesh Display/Lock Normals": "mesh.customdata_custom_splitnormals_add",
    "Mesh Display/Unlock Normals": "mesh.customdata_custom_splitnormals_clear",
    "Mesh Display/Vertex Normal Edit Tool": ("v3d", "transform.rotate_normal", {}),
    "Mesh Display/Create Empty Set": "geometry.color_attribute_add",
    "Mesh Display/Delete Current Set": "geometry.color_attribute_remove",
    "Mesh Display/Color Set Editor": _props('DATA'),
    "Mesh Display/Toggle Display Colors Attribute": ("v3d", "wm.context_set_enum",
                                                     {"data_path": "space_data.shading.color_type",
                                                      "value": 'VERTEX'}),
    # Curves
    "Curves/Attach": "curve.make_segment",
    "Curves/Detach": "curve.split",
    "Curves/Extend/Extend Curve": ("v3d", "curve.extrude_move", {}),
    "Curves/Smooth#2": "curve.smooth",
    "Curves/Bezier Curves/Anchor Presets/Bezier": ("curve.handle_type_set", {"type": 'ALIGNED'}),
    "Curves/Bezier Curves/Anchor Presets/Bezier Corner": ("curve.handle_type_set", {"type": 'FREE_ALIGN'}),
    "Curves/Bezier Curves/Anchor Presets/Corner": ("curve.handle_type_set", {"type": 'VECTOR'}),
    "Curves/Bezier Curves/Tangent Options/Smooth Anchor Tangents": ("curve.handle_type_set", {"type": 'ALIGNED'}),
    "Curves/Bezier Curves/Tangent Options/Break Anchor Tangents": ("curve.handle_type_set", {"type": 'FREE_ALIGN'}),
    "Curves/Bezier Curves/Tangent Options/Even Anchor Tangents": ("curve.handle_type_set", {"type": 'AUTOMATIC'}),
    # Surfaces
    "Surfaces/Revolve": _mod('SCREW'),
    "Surfaces/Open/Close": "curve.cyclic_toggle",
    "Surfaces/Reverse Direction": "curve.switch_direction",
    "Surfaces/Insert Isoparms": "curve.subdivide",
    # Deform
    "Deform/Curve Warp": _mod('CURVE'),
    "Deform/Proximity Wrap": _mod('SURFACE_DEFORM'),
    "Deform/Nonlinear/Bend": ("allset.nonlinear", {"method": 'BEND'}),
    "Deform/Nonlinear/Flare": ("allset.nonlinear", {"method": 'TAPER'}),
    "Deform/Nonlinear/Squash": ("allset.nonlinear", {"method": 'STRETCH'}),
    "Deform/Nonlinear/Sine": _mod('WAVE'),
    "Deform/Blend Shape#2/Remove": "object.shape_key_remove",
    **{f"Deform/Paint Weights/{kind}": "paint.weight_paint_toggle" for kind in (
        "Blend Shape", "Cluster", "Delta Mush", "Tension", "Proximity Wrap", "Lattice", "ShrinkWrap", "Wire",
        "Nonlinear", "Jiggle", "Texture Deformer")},
    "Deform/Mirror Deformer Weights": "object.vertex_group_mirror",
    # UV
    "UV/UV Set Editor": _props('DATA'),
    "UV/Assign Checker Shader": "allset.checker_shader",
    "UV/Best Plane": "allset.uv_planar",
    "UV/Contour Stretch": "uv.follow_active_quads",
    "UV/Split UVs": "allset.uv_cut",
    # Generate (XGen -> hair curves)
    "Generate/Create Description...": "object.curves_empty_hair_add",
    "Generate/Create Interactive Groom Splines": "object.curves_empty_hair_add",
    # Skeleton / Skin / Constrain
    "Skeleton/Insert Joints": "armature.subdivide",
    "Skeleton/Connect Joint": ("armature.parent_set", {"type": 'CONNECTED'}),
    "Skin/Normalize Weights/Enable Weight Normalization":
        ("wm.context_set_boolean", {"data_path": "tool_settings.use_auto_normalize", "value": True}),
    "Skin/Normalize Weights/Disable Weight Normalization":
        ("wm.context_set_boolean", {"data_path": "tool_settings.use_auto_normalize", "value": False}),
    "Constrain/Rivet": "object.vertex_parent_set",
    "Constrain/Closest Point": _con('SHRINKWRAP'),
    "Constrain/Point On Poly": _con('SHRINKWRAP'),
    # Key / Playback / Visualize
    "Key/Insert Key on Translate": ("anim.keyframe_insert_by_name", {"type": "Location"}),
    "Key/Insert Key on Rotate": ("anim.keyframe_insert_by_name", {"type": "Rotation"}),
    "Key/Insert Key on Scale": ("anim.keyframe_insert_by_name", {"type": "Scaling"}),
    "Playback/Select Next Key": ("screen.keyframe_jump", {"next": True}),
    "Playback/Select Previous Key": ("screen.keyframe_jump", {"next": False}),
    "Playback/Playback Looping/Continuous": ("allset.menu_note", {"item": "Playback/Playback Looping/Continuous"}),
    "Visualize/Time Slider Bookmarks": "marker.add",
    # Audio (): sounds are Video Sequencer sound strips
    "Audio/Import Audio...": "allset.import_audio",
    "Audio/Import Audio Clip to Time Editor...": "allset.import_audio",
    "Audio/Mute": ("wm.context_toggle", {"data_path": "scene.use_audio"}),
    "Audio/Adjust Volume": _props('SCENE'),
    "Audio/Delete Sounds": "allset.delete_sounds",
    # FX
    "nParticles/Soft Body": _mod('SOFT_BODY'),
    "nParticles/Soft Body#2": _mod('SOFT_BODY'),
    "nParticles/Make Collide": "allset.fx_passive",
    # Rendering
    "Lighting/Shading/Light Linking Editor": _props('OBJECT'),
    "Toon/Assign Outline": ("v3d", "object.grease_pencil_add", {"type": 'LINEART_OBJECT'}),
    "Stereo/Create/Stereo Camera": "allset.stereo_camera",
    # Cache (Alembic / GPU cache = Alembic files; Geometry Cache = Alembic too, with a notice)
    "Cache/Alembic Cache/Open Alembic...": "wm.alembic_import",
    "Cache/Alembic Cache/Reference Alembic...": "wm.alembic_import",
    "Cache/Alembic Cache/Import Alembic...": "wm.alembic_import",
    "Cache/Alembic Cache/Export All to Alembic...": ("wm.alembic_export", {"selected": False}),
    "Cache/Alembic Cache/Export Selection to Alembic...": ("wm.alembic_export", {"selected": True}),
    "Cache/Geometry Cache/Create New Cache": ("wm.alembic_export", {"selected": True}),
    "Cache/Geometry Cache/Import Cache...": "wm.alembic_import",
    "Cache/Geometry Cache/Export Cache": ("wm.alembic_export", {"selected": True}),
    "Cache/GPU Cache/Import...": "wm.alembic_import",
    "Cache/GPU Cache/Export All...": ("wm.alembic_export", {"selected": False}),
    "Cache/GPU Cache/Export Selection...": ("wm.alembic_export", {"selected": True}),
    # Help -> Blender's documentation and community
    "Help/Search": _url(_MANUAL),
    "Help/Find Menu": "wm.search_menu",
    "Help/Maya Help": _url(_MANUAL),
    "Help/What's New/List of What's New": _url(_NOTES),
    "Help/Quick Tour": _url(_MANUAL + "getting_started/index.html"),
    "Help/Interactive Tutorials/Basic Skills": _url(_TUTORIALS),
    "Help/Interactive Tutorials/View All Interactive Tutorials...": _url(_TUTORIALS),
    "Help/YouTube Learning Channel": _url("https://www.youtube.com/@BlenderOfficial"),
    "Help/Scripting Reference/MEL Command Reference": _url(_API),
    "Help/Scripting Reference/Python Command Reference": _url(_API),
    "Help/Scripting Reference/Node and Attribute Reference": _url(_API + "bpy.types.html"),
    "Help/MEL Command Reference": _url(_API),
    "Help/Python Command Reference": _url(_API),
    "Help/Node and Attribute Reference": _url(_API + "bpy.types.html"),
    "Help/Services and Support/Patch Release Notes": _url(_NOTES),
    "Help/Services and Support/Release Notes Updates": _url(_NOTES),
    "Help/Services and Support/Support Center": _url("https://www.blender.org/support/"),
    "Help/Feedback/Report a Problem...": _url("https://projects.blender.org/blender/blender/issues"),
    "Help/Blender Extensions": _url("https://extensions.blender.org/"),
    "Help/About Maya": "wm.splash_about",
})

# Mapped items whose Blender operator needs component (edit) mode run the Maya way from object mode
# (step 101 「계획」 4, , checked):
# ('ALL', select mode) = Maya acts on every component of the selected meshes; a string = Maya's warning.
OBJECT_MODE = {
    "Edit Mesh/Add Divisions": ('ALL', 'FACE'),
    "Edit Mesh/Collapse": ('ALL', 'FACE'),
    "Edit Mesh/Merge": ('ALL', 'VERT'),
    "Edit Mesh/Merge to Center": "polyMergeVert1 (Poly Merge Vert): No vertices were merged. Tolerance too large - "
                                 "no geometry left after merge",
    "Edit Mesh/Average Vertices": ('ALL', 'VERT'),
    "Edit Mesh/Poke": ('ALL', 'FACE'),
    "Edit Mesh/Circularize": ('ALL', 'VERT'),
    "Edit Mesh/Edit Edge Flow": ('ALL', 'EDGE'),
    "Edit Mesh/Bevel": ('ALL', 'EDGE'),
    "Edit Mesh/Chamfer Vertices": ('ALL', 'VERT'),
    "Edit Mesh/Bridge": "Invalid selection : polyBridgeEdge requires equal number of border edges to be selected "
                        "for source and target selection.",
    "Edit Mesh/Delete Edge/Vertex": "No Vertices / Edges have been selected for Delete!",
    "Edit Mesh/Extract": "polyChipOff works only on polygonal faces.",
    "Edit Mesh/Duplicate": "polyChipOff works only on polygonal faces.",
    "Edit Mesh/Detach": "No vertices or edges selected to detach.",
    "Edit Mesh/Wedge": "No faces selected to wedge. Select faces and one or more edges from the selected faces "
                       "to wedge about.",
    "Edit Mesh/Connect": "Can't perform polyConnectComponents1 on selection",
    "Edit Mesh/Flip Triangle Edge": "Select edges to flip.",
    "Edit Mesh/Spin Edge Backward": "Select edges to spin.",
    "Edit Mesh/Spin Edge Forward": "Select edges to spin.",
}

# Step 109: Curves / Surfaces and FX commands built for the shelf, same in the
# menus. operators/curve_tools.py, operators/fx.py; Maya results checked  ().
MAP.update({
    "Create/NURBS Primitives/Square": _create('NURBS_SQUARE'),
    "Create/NURBS Primitives/Cube": _create('NURBS_CUBE'),
    "Create/NURBS Primitives/Cone": _create('NURBS_CONE'),
    "Create/Curve Tools/Pencil Curve Tool": "allset.pencil_curve",
    "Create/Sweep Mesh": "allset.sweep_mesh",
    "Curves/Add Points Tool": ("v3d", "allset.add_points", {}),
    "Curves/Offset/Offset Curve": "allset.offset_curve",
    "Surfaces/Loft": "allset.loft",
    "Surfaces/Planar": "allset.surface_planar",
    "Surfaces/Extrude": "allset.surface_extrude",
    "Surfaces/Bevel Plus": "allset.bevel_plus",
    # Sculpting stamps Blender lacks: the keymap's step-107 substitutes (sculpt Ctrl+8 / Ctrl+9)
    "Mesh Tools/Sculpting Tools/Spray Tool": _sculpt("Draw Sharp"),
    "Mesh Tools/Sculpting Tools/Repeat Tool": _sculpt("Layer"),
    "Fluids/Add/Edit Contents/Emit from Object": "allset.quick_smoke",
    "Fluids/Make Collide": "allset.fluid_collide",
    "nCloth/Display Input Mesh": ("allset.ncloth_display", {"mesh": 'INPUT'}),
    "nCloth/Display Current Mesh": ("allset.ncloth_display", {"mesh": 'CURRENT'}),
    "nHair/Paint Hair Follicles": ("object.mode_set", {"mode": 'SCULPT_CURVES'}),
})

# Step 110: modeling / rigging commands with checked results
# (); operators/poly_maya.py, operators/rig_maya.py, menu_items.nonlinear.
MAP.update({
    "Edit Mesh/Circularize": "allset.circularize",
    "Mesh Tools/Connect": "allset.connect",
    "Mesh Tools/Make Hole": "allset.make_hole",
    "Skeleton/Reroot Skeleton": "allset.reroot_skeleton",
    "Skeleton/Set Preferred Angle": "allset.set_preferred_angle",
    "Skeleton/Assume Preferred Angle": "allset.assume_preferred_angle",
    "Skeleton/Create IK Spline Handle": "allset.ik_spline_handle",
    "Skin/Hammer Skin Weights": "allset.hammer_weights",
    "Skin/Edit Influences/Add Influence": "allset.add_influence",
    "Skin/Edit Influences/Remove Influence": "allset.remove_influence",
    "Skin/Edit Influences/Remove Unused Influences": "allset.remove_unused_influences",
    "Deform/Cluster": "allset.cluster",
    "Deform/Nonlinear/Twist": ("allset.nonlinear", {"method": 'TWIST'}),
    "Deform/Soft Modification Tool": "allset.soft_mod",
})

# Blender's own menu kept at the end of the Maya menu with the same role.
BLENDER_MENU = {
    "File": ("TOPBAR_MT_file", "Blender File"),
    "Edit": ("TOPBAR_MT_edit", "Blender Edit"),
    "Windows": ("TOPBAR_MT_window", "Blender Window"),
    "Render": ("TOPBAR_MT_render", "Blender Render"),
    "Help": ("TOPBAR_MT_help", "Blender Help"),
}


# Graph Editor / Dope Sheet / UV Editor / UV Toolkit menu bars (step 104): their own module, same forms.
from .editor_menu_map import MAP as _EDITOR_MAP  # noqa: E402

MAP.update(_EDITOR_MAP)


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
    if value[0] == "prop":   # a Maya check / radio item = a Blender property (step 104)
        return ("prop", value[1], dict(value[2]))
    return ("op", value[0], dict(value[1]))
