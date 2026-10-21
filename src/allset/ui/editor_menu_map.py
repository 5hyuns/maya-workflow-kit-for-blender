# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Graph Editor / Dope Sheet / UV Editor / UV Toolkit menu items -> Blender actions (docs/steps/step_104.md).

Keys are ``editor_menu_data`` paths ("Graph Editor/Keys/Insert Key Tool"); values use ``menu_map``'s forms plus
``("prop", "<context path>")`` = a Maya check item drawn as Blender's own check box (``{"value": v}`` = one choice
of a radio collection). ``menu_map`` merges ``MAP`` into its own, so the step 101 rules (every leaf mapped or greyed
with a notice) cover these menus too. Menu structure: research/maya/screens/editors104/_editors104.json (Maya 2022
GUI capture); Blender counterparts measured in 4.5 (docs/steps/step_104.md 「한 것」).
"""

import math

_MANUAL = "https://docs.blender.org/manual/en/4.5/"
_API = "https://docs.blender.org/api/4.5/"
_NOTES = "https://developer.blender.org/docs/release_notes/4.5/"
_PKG = __package__.rpartition(".")[0]


def _url(url):
    return ("wm.url_open", {"url": url})


def _prop(path, value=None):
    return ("prop", path, {} if value is None else {"value": value})


def _tangent(kind, side="BOTH"):
    return ("allset.set_tangent", {"kind": kind, "side": side})


def _infinity(side, mode):
    return ("allset.curve_infinity", {"side": side, "mode": mode})


def _key(action):
    return ("allset.key_edit", {"action": action})


def _uv_tool(idname):
    return ("wm.tool_set_by_id", {"name": idname, "space_type": 'IMAGE_EDITOR'})


# Maya tangent labels -> set_tangent kinds (operators/time_keys.TANGENTS). Maya 2022's Auto variants
# (Auto Span / Ease / Mix / Custom) are one Blender auto handle (Auto Clamped): notices in ui/notices.py.
TANGENT_KINDS = {"Spline": "SPLINE", "Linear": "LINEAR", "Clamped": "CLAMPED", "Stepped": "STEPPED",
                 "Stepped Next": "STEPPED_NEXT", "Flat": "FLAT", "Fixed": "FIXED", "Plateau": "PLATEAU"}
AUTO_KINDS = ("Auto Span (Legacy)", "Auto Ease", "Auto Mix", "Auto Custom")

# Default In / Out Tangent: Blender keeps the default for new keys in Preferences > Animation > F-Curves. The kit
# writes no preference (store review, #40 / #43): the items open that page and the user picks the value there.
_PREFS_ANIMATION = ("screen.userpref_show", {"section": 'ANIMATION'})
DEFAULT_TANGENT_LABELS = (*AUTO_KINDS, "Spline", "Clamped", "Plateau", "Linear", "Stepped")


def _tangents_menu(ed):
    m = {f"{ed}/Tangents/Auto/{label}": _tangent("AUTO") for label in AUTO_KINDS}
    m.update({f"{ed}/Tangents/{label}": _tangent(kind) for label, kind in TANGENT_KINDS.items()})
    for side, sub in (("IN", "In Tangent"), ("OUT", "Out Tangent")):
        m.update({f"{ed}/Tangents/{sub}/Auto/{label}": _tangent("AUTO", side) for label in AUTO_KINDS})
        m.update({f"{ed}/Tangents/{sub}/{label}": _tangent(kind, side) for label, kind in TANGENT_KINDS.items()})
    for sub in ("Default In Tangent", "Default Out Tangent"):
        m.update({f"{ed}/Tangents/{sub}/{label}": _PREFS_ANIMATION for label in DEFAULT_TANGENT_LABELS
                  if not (label == "Stepped" and sub == "Default In Tangent")})   # Maya has no stepped in-tangent
    m[f"{ed}/Tangents/Break Tangents"] = _tangent("BREAK")
    m[f"{ed}/Tangents/Unify Tangents"] = _tangent("UNIFY")
    return m


def _curves_menu(ed, graph):
    m = {}
    for side, sub in (("PRE", "Pre Infinity"), ("POST", "Post Infinity")):
        for label, mode in (("Cycle", "CYCLE"), ("Cycle with Offset", "CYCLE_OFFSET"), ("Oscillate", "OSCILLATE"),
                            ("Linear", "LINEAR"), ("Constant", "CONSTANT")):
            m[f"{ed}/Curves/{sub}/{label}"] = _infinity(side, mode)
    m.update({
        f"{ed}/Curves/Bake Channel": "graph.bake_keys" if graph else "action.bake_keys",
        f"{ed}/Curves/Mute Channel": ("anim.channels_setting_enable", {"type": 'MUTE'}),
        f"{ed}/Curves/Unmute Channel": ("anim.channels_setting_disable", {"type": 'MUTE'}),
        f"{ed}/Curves/Lock Channel": ("anim.channels_setting_enable", {"type": 'PROTECT'}),
        f"{ed}/Curves/Unlock Channel": ("anim.channels_setting_disable", {"type": 'PROTECT'}),
        f"{ed}/Curves/Simplify Curve": "graph.clean" if graph else "action.clean",
        f"{ed}/Curves/Key Reducer Filter": "graph.decimate" if graph else "action.clean",
    })
    if graph:
        m.update({
            f"{ed}/Curves/Isolate Curve": ("graph.hide", {"unselected": True}),
            f"{ed}/Curves/Smooth Filter (Butterworth)": "graph.butterworth_smooth",
            f"{ed}/Curves/Smooth Filter (Gaussian)": "graph.gaussian_smooth",
            f"{ed}/Curves/Euler Filter": "graph.euler_filter",
            f"{ed}/Curves/Resample Curve": "graph.bake_keys",
            f"{ed}/Curves/Buffer Curve/Snapshot": "graph.ghost_curves_create",
        })
    return m


def _edit_menu(ed, graph):
    move = "transform.translate" if graph else ("transform.transform", {"mode": 'TIME_TRANSLATE'})
    scale = "transform.resize" if graph else ("transform.transform", {"mode": 'TIME_SCALE'})
    return {
        f"{ed}/Edit/Undo": "ed.undo",
        f"{ed}/Edit/Redo": "ed.redo",
        f"{ed}/Edit/Cut": _key("CUT"),
        f"{ed}/Edit/Copy": _key("COPY"),
        f"{ed}/Edit/Paste": _key("PASTE"),
        f"{ed}/Edit/Delete": _key("DELETE"),
        f"{ed}/Edit/Scale": scale,
        f"{ed}/Edit/Transformation Tools/Move Keys Tool": move,
        f"{ed}/Edit/Transformation Tools/Scale Keys Tool": scale,
        f"{ed}/Edit/Snap": ("graph.snap" if graph else "action.snap", {"type": 'NEAREST_FRAME'}),
        f"{ed}/Edit/Change Curve Color": ("allset.curve_color", {"action": 'CHANGE'}),
        f"{ed}/Edit/Remove Curve Color": ("allset.curve_color", {"action": 'REMOVE'}),
        f"{ed}/Edit/Preferences": ("screen.userpref_show", {"section": 'ANIMATION'}),
    }


def _keys_menu(ed, graph):
    m = {
        f"{ed}/Keys/Convert to Key": _key("TO_KEY") if graph else ("action.keyframe_type", {"type": 'KEYFRAME'}),
        f"{ed}/Keys/Convert to Breakdown": _key("TO_BREAKDOWN") if graph else
        ("action.keyframe_type", {"type": 'BREAKDOWN'}),
        f"{ed}/Keys/Add Inbetween": _key("ADD_INBETWEEN"),
        f"{ed}/Keys/Remove Inbetween": _key("REMOVE_INBETWEEN"),
    }
    if graph:
        m[f"{ed}/Keys/Insert Key Tool"] = "allset.insert_key_tool"
    return m


# Maya Show > Objects / Attributes = Blender's dope sheet filters (the Graph Editor and Dope Sheet share them).
_DS = "space_data.dopesheet"
SHOW_OBJECTS = {"Geometry": "show_meshes", "Polygon Objects": "show_meshes", "NURBS Objects": "show_curves",
                "GPU Cache": "show_cache_files", "Cameras": "show_cameras", "Joints": "show_armatures"}
# Maya attribute groups -> the channel name filter (Blender names: Location / Rotation / Scale)
SHOW_ATTRIBUTES = {"Translate": "Location", "Rotate": "Rotation", "Scale": "Scale", "Scale Rotate Translate": "",
                   "Keyable": ""}


def _list_show_menus(ed):
    m = {
        f"{ed}/List/Auto Load Selected Objects": _prop(f"{_DS}.show_only_selected"),
        f"{ed}/Show/Invert Shown": _prop(f"{_DS}.use_filter_invert"),
        f"{ed}/Show/Show All": ("wm.context_set_string", {"data_path": f"{_DS}.filter_text", "value": ""}),
    }
    m.update({f"{ed}/Show/Objects/{label}": _prop(f"{_DS}.{attr}") for label, attr in SHOW_OBJECTS.items()})
    m.update({f"{ed}/Show/Attributes/{label}": _prop(f"{_DS}.filter_text", text)
              for label, text in SHOW_ATTRIBUTES.items()})
    return m


def _help_menu(ed, page):
    return {
        f"{ed}/Help/Search": _url(_MANUAL),
        f"{ed}/Help/Find Menu": "wm.search_menu",
        f"{ed}/Help/Maya Help": _url(_MANUAL),
        f"{ed}/Help/What's New/List of What's New": _url(_NOTES),
        f"{ed}/Help/Help on {ed}": _url(_MANUAL + page),
        f"{ed}/Help/MEL Command Reference": _url(_API),
        f"{ed}/Help/Python Command Reference": _url(_API),
        f"{ed}/Help/Node and Attribute Reference": _url(_API + "bpy.types.html"),
        f"{ed}/Help/Maya Home Page": _url("https://www.blender.org/"),
    }


GE, DS, UV = "Graph Editor", "Dope Sheet", "UV Editor"
_SP = "space_data"

MAP = {
    # --- Graph Editor (graphEditorPanel.mel menus, captured) ---
    **_edit_menu(GE, True),
    f"{GE}/View/Frame/Frame All": "graph.view_all",
    f"{GE}/View/Frame/Frame Selection": "graph.view_selected",
    f"{GE}/View/Frame/Frame Playback Range": "anim.scene_range_frame",
    f"{GE}/View/Center Current Time": "allset.graph_center_time",
    f"{GE}/View/Infinity": _prop(f"{_SP}.show_extrapolation"),
    # Blender's "Only Selected Curve Keyframes" is a preference (#43): open it, don't write it
    f"{GE}/View/Keys/Always": _PREFS_ANIMATION,
    f"{GE}/View/Keys/Active Only": _PREFS_ANIMATION,
    f"{GE}/View/Tangents/Always": _prop(f"{_SP}.use_only_selected_keyframe_handles", False),
    f"{GE}/View/Tangents/Never": _prop(f"{_SP}.show_handles", False),
    f"{GE}/View/Tangents/On Active Keys": _prop(f"{_SP}.use_only_selected_keyframe_handles", True),
    f"{GE}/View/Theme/Color Preferences": ("screen.userpref_show", {"section": 'THEMES'}),
    f"{GE}/View/Absolute View": _prop(f"{_SP}.use_normalization", False),
    f"{GE}/View/Stacked View": ("allset.graph_view_mode", {"mode": "STACKED"}),
    f"{GE}/View/Normalized View": _prop(f"{_SP}.use_normalization", True),
    f"{GE}/View/Renormalize": _prop(f"{_SP}.use_auto_normalization"),
    f"{GE}/Select/All": ("graph.select_all", {"action": 'SELECT'}),
    f"{GE}/Select/Snap time to selection": _prop("addon_prefs.snap_time_to_selection"),
    **_curves_menu(GE, True),
    **_keys_menu(GE, True),
    **_tangents_menu(GE),
    **_list_show_menus(GE),
    f"{GE}/List/Show Animated Shapes": _prop(f"{_DS}.show_shapekeys"),
    **_help_menu(GE, "editors/graph_editor/index.html"),

    # --- Dope Sheet (dopeSheetPanel.mel menus, captured) ---
    **_edit_menu(DS, False),
    f"{DS}/View/Frame All": "action.view_all",
    f"{DS}/View/Frame Selection": "action.view_selected",
    f"{DS}/View/Frame Playback Range": "anim.scene_range_frame",
    f"{DS}/View/Center Current Time": "action.view_frame",
    f"{DS}/View/Dope Sheet Summary": _prop(f"{_DS}.show_summary"),
    **_curves_menu(DS, False),
    **_keys_menu(DS, False),
    **_tangents_menu(DS),
    **_list_show_menus(DS),
    **_help_menu(DS, "editors/dope_sheet/index.html"),

    # --- UV Editor (textureWindow menus, captured); kit UV commands from step 66 ---
    f"{UV}/Edit/Copy": "uv.copy",
    f"{UV}/Edit/Paste": "uv.paste",
    f"{UV}/Edit/Pin Selection": "uv.pin",
    f"{UV}/Edit/Invert Pinning": ("uv.pin", {"invert": True}),
    f"{UV}/Edit/Unpin Selection": ("uv.pin", {"clear": True}),
    f"{UV}/Create/Assign Checker Shader": "allset.checker_shader",
    f"{UV}/Create/Automatic": "uv.smart_project",
    f"{UV}/Create/Camera-based": ("v3d", "uv.project_from_view", {}),
    f"{UV}/Create/Normal-based": "allset.uv_planar",
    f"{UV}/Create/Cylindrical": ("v3d", "uv.cylinder_project", {}),
    f"{UV}/Create/Planar": "allset.uv_planar",
    f"{UV}/Create/Spherical": ("v3d", "uv.sphere_project", {}),
    f"{UV}/Select/All": ("uv.select_all", {"action": 'SELECT'}),
    f"{UV}/Select/Clear": ("uv.select_all", {"action": 'DESELECT'}),
    f"{UV}/Select/Inverse": ("uv.select_all", {"action": 'INVERT'}),
    **{f"{UV}/Select/Components/{label}": ("allset.uv_component", {"mode": mode})
       for label, mode in (("Vertex", "VERTEX"), ("Edge", "EDGE"), ("Face", "FACE"), ("UV", "UV"),
                           ("UV Shell", "SHELL"))},
    f"{UV}/Select/Overlapping": "uv.select_overlap",
    f"{UV}/Select/Shortest Edge Path Tool": "uv.shortest_path_select",
    f"{UV}/Select/Grow": "uv.select_more",
    f"{UV}/Select/Shrink": "uv.select_less",
    **{f"{UV}/Select/Convert Selection/{label}": ("allset.uv_component", {"mode": mode})
       for label, mode in (("To Vertices", "VERTEX"), ("To Edges", "EDGE"), ("To Faces", "FACE"), ("To UVs", "UV"),
                           ("To UV Shell", "SHELL"))},
    f"{UV}/Cut/Sew/Cut": "allset.uv_cut",
    f"{UV}/Cut/Sew/Sew": "allset.uv_sew",
    f"{UV}/Cut/Sew/Merge": "uv.weld",
    f"{UV}/Cut/Sew/Move and Sew": "allset.uv_sew",
    f"{UV}/Cut/Sew/Stitch Together": "uv.stitch",
    f"{UV}/Modify/Align": ("uv.align", {"axis": 'ALIGN_AUTO'}),
    f"{UV}/Modify/Flip": ("transform.mirror", {"constraint_axis": (True, False, False)}),
    f"{UV}/Modify/Linear Align": ("uv.align", {"axis": 'ALIGN_S'}),
    f"{UV}/Modify/Match UVs": "uv.remove_doubles",
    f"{UV}/Modify/Rotate": ("transform.rotate", {"value": -math.pi / 2}),
    f"{UV}/Modify/Unitize": "uv.reset",
    f"{UV}/Modify/Gather Shells": "uv.pack_islands",
    f"{UV}/Modify/Layout": "allset.uv_layout",
    f"{UV}/Modify/Orient Shells": "uv.align_rotation",
    f"{UV}/Modify/Randomize Shells": "uv.randomize_uv_transform",
    f"{UV}/Modify/Optimize": "uv.minimize_stretch",
    f"{UV}/Modify/Straighten Shell": "uv.follow_active_quads",
    f"{UV}/Modify/Straighten UVs": ("uv.align", {"axis": 'ALIGN_S'}),
    f"{UV}/Modify/Unfold": "allset.uv_unfold",
    f"{UV}/Tools/Hide UV Toolkit": _prop(f"{_SP}.show_region_ui"),
    f"{UV}/Tools/Select": _uv_tool("builtin.select_box"),
    f"{UV}/Tools/Move": _uv_tool("builtin.move"),
    f"{UV}/Tools/Rotate": _uv_tool("builtin.rotate"),
    f"{UV}/Tools/Scale": _uv_tool("builtin.scale"),
    f"{UV}/Tools/Tweak": _uv_tool("builtin.select"),
    f"{UV}/Tools/Smooth": _uv_tool("sculpt.uv_sculpt_relax"),
    f"{UV}/Tools/Optimize": _uv_tool("sculpt.uv_sculpt_relax"),
    f"{UV}/Tools/Grab": _uv_tool("sculpt.uv_sculpt_grab"),
    f"{UV}/Tools/Pinch": _uv_tool("sculpt.uv_sculpt_pinch"),
    f"{UV}/View/Wireframe": _prop(f"{_SP}.uv_editor.uv_face_opacity", 0.0),
    f"{UV}/View/Shaded": _prop(f"{_SP}.uv_editor.uv_face_opacity", 1.0),
    f"{UV}/View/UV Distortion": _prop(f"{_SP}.uv_editor.show_stretch"),
    f"{UV}/View/Grid": _prop(f"{_SP}.overlay.show_grid_background"),
    f"{UV}/View/Toolbar": _prop(f"{_SP}.show_region_toolbar"),
    f"{UV}/View/Frame All": "image.view_all",
    f"{UV}/View/Frame Selection": "image.view_selected",
    f"{UV}/Image/RGB": _prop(f"{_SP}.display_channels", 'COLOR'),
    f"{UV}/Image/RGBA": _prop(f"{_SP}.display_channels", 'COLOR_ALPHA'),
    f"{UV}/Image/Alpha": _prop(f"{_SP}.display_channels", 'ALPHA'),
    f"{UV}/Image/Pixel Snap": _prop(f"{_SP}.uv_editor.pixel_round_mode", 'CORNER'),
    f"{UV}/Image/UV Snapshot...": "uv.export_layout",
    f"{UV}/Textures/Checker Map": "allset.checker_toggle",
    f"{UV}/UV Sets/UV Set Editor": ("allset.open_editor", {"ui_type": 'PROPERTIES', "tab": 'DATA'}),
    f"{UV}/UV Sets/Copy UVs to UV Set/Copy into New UV Set": "mesh.uv_texture_add",
    f"{UV}/UV Sets/Create Empty UV Set": "mesh.uv_texture_add",
    f"{UV}/UV Sets/Delete Current UV Set": "mesh.uv_texture_remove",
    **_help_menu(UV, "editors/uv/index.html"),
    "UV Toolkit/Help/Help on UV Toolkit": _url(_MANUAL + "modeling/meshes/uv/index.html"),
}

# --- step 105: Hypershade, Render Settings, Script Editor (research/maya/screens/editors105/_editors105.json) -----
HS, RS, SE = "Hypershade", "Render Settings", "Script Editor"
_HS_MATERIALS = {"Anisotropic": 'ANISOTROPIC', "Blinn": 'BLINN', "Lambert": 'LAMBERT', "Layered Shader": 'LAYERED',
                 "Phong": 'PHONG', "Phong E": 'PHONG_E', "Ramp Shader": 'RAMP', "Standard Surface": 'STANDARD_SURFACE',
                 "Surface Shader": 'SURFACE', "Use Background": 'USE_BACKGROUND'}
_HS_LIGHTS = {"Directional Light": 'DIRECTIONAL_LIGHT', "Point Light": 'POINT_LIGHT', "Spot Light": 'SPOT_LIGHT',
              "Area Light": 'AREA_LIGHT'}


def _hs_edit(action):
    return ("allset.hs_edit", {"action": action})


def _editor(ui_type):
    return ("allset.open_editor", {"ui_type": ui_type})


# Hypershade Create menu node types -> Blender shader nodes (added to the current material's graph)
HS_NODES = {
    "2D Textures/Checker": 'ShaderNodeTexChecker', "2D Textures/File": 'ShaderNodeTexImage',
    "2D Textures/Fractal": 'ShaderNodeTexNoise', "2D Textures/Noise": 'ShaderNodeTexNoise',
    "2D Textures/Simplex Noise": 'ShaderNodeTexNoise', "2D Textures/Ramp": 'ShaderNodeValToRGB',
    "2D Textures/Water": 'ShaderNodeTexWave', "2D Textures/Grid": 'ShaderNodeTexBrick',
    "2D Textures/Movie": 'ShaderNodeTexImage', "2D Textures/PSD File": 'ShaderNodeTexImage',
    "3D Textures/Brownian": 'ShaderNodeTexNoise', "3D Textures/Cloud": 'ShaderNodeTexNoise',
    "3D Textures/Solid Fractal": 'ShaderNodeTexNoise', "3D Textures/Volume Noise": 'ShaderNodeTexNoise',
    "3D Textures/Marble": 'ShaderNodeTexWave', "3D Textures/Wood": 'ShaderNodeTexWave',
    "3D Textures/Granite": 'ShaderNodeTexVoronoi', "3D Textures/Leather": 'ShaderNodeTexVoronoi',
    "3D Textures/Rock": 'ShaderNodeTexVoronoi',
    "Environment Textures/Env Sphere": 'ShaderNodeTexEnvironment',
    "Layered Texture": 'ShaderNodeMix',
    "General Utilities/Bump 2d": 'ShaderNodeBump', "General Utilities/Bump 3d": 'ShaderNodeBump',
    "General Utilities/Multiply Divide": 'ShaderNodeVectorMath',
    "General Utilities/Plus Minus Average": 'ShaderNodeVectorMath',
    "General Utilities/Reverse": 'ShaderNodeInvert', "General Utilities/Set Range": 'ShaderNodeMapRange',
    "General Utilities/2d Placement": 'ShaderNodeMapping', "General Utilities/3d Placement": 'ShaderNodeMapping',
    "General Utilities/Sampler Info": 'ShaderNodeNewGeometry', "General Utilities/Vector Product": 'ShaderNodeVectorMath',
    "General Utilities/Distance Between": 'ShaderNodeVectorMath', "General Utilities/Condition": 'ShaderNodeMath',
    "Scalar Utilities/Add Double Linear": 'ShaderNodeMath', "Scalar Utilities/Mult Double Linear": 'ShaderNodeMath',
    "Scalar Utilities/Float Constant": 'ShaderNodeValue', "Scalar Utilities/Float Math": 'ShaderNodeMath',
    "Scalar Utilities/Unit Conversion": 'ShaderNodeMath', "Scalar Utilities/Blend Two Attr": 'ShaderNodeMix',
    "Color Utilities/Blend Colors": 'ShaderNodeMix', "Color Utilities/Channels": 'ShaderNodeSeparateColor',
    "Color Utilities/Clamp": 'ShaderNodeClamp', "Color Utilities/Color Constant": 'ShaderNodeRGB',
    "Color Utilities/Color Math": 'ShaderNodeMix', "Color Utilities/Contrast": 'ShaderNodeBrightContrast',
    "Color Utilities/Gamma Correct": 'ShaderNodeGamma', "Color Utilities/Hsv To Rgb": 'ShaderNodeCombineColor',
    "Color Utilities/Rgb To Hsv": 'ShaderNodeSeparateColor', "Color Utilities/Luminance": 'ShaderNodeRGBToBW',
    "Color Utilities/Remap Value": 'ShaderNodeMapRange', "Color Utilities/Remap Color": 'ShaderNodeRGBCurve',
    "Color Utilities/Remap Hsv": 'ShaderNodeHueSaturation',
}


def _hs_nodes():
    return {f"{HS}/Create/{label}": ("allset.hs_node", {"node_type": node, "label": label.rsplit("/", 1)[-1]})
            for label, node in HS_NODES.items()}


MAP.update({
    f"{HS}/File/Import...": "allset.file_import",
    f"{HS}/Edit/Delete": _hs_edit("DELETE"),
    f"{HS}/Edit/Delete Unused Nodes": _hs_edit("DELETE_UNUSED"),
    f"{HS}/Edit/Delete All by Type/Shading Groups and Materials": _hs_edit("DELETE_MATERIALS"),
    f"{HS}/Edit/Delete All by Type/Lights": ("allset.delete_by_type", {"type": 'LIGHTS', "all": True}),
    f"{HS}/Edit/Delete All by Type/Cameras and Image Planes": ("allset.delete_by_type",
                                                               {"type": 'CAMERAS', "all": True}),
    f"{HS}/Edit/Select Objects with Materials": _hs_edit("SELECT_OBJECTS"),
    f"{HS}/Edit/Select Materials from Objects": _hs_edit("FROM_OBJECT"),
    f"{HS}/Edit/Duplicate/Shading Network": _hs_edit("DUPLICATE"),
    f"{HS}/Edit/Duplicate/Without Network": _hs_edit("DUPLICATE"),
    f"{HS}/View/Frame All": "node.view_all",
    f"{HS}/View/Frame Selected": "node.view_selected",
    **{f"{HS}/View/{label}": _prop("window_manager.allset_hs_swatch", key)
       for label, key in (("As Icons", 'ICONS'), ("As List", 'LIST'), ("As Small Swatches", 'SMALL'),
                          ("As Medium Swatches", 'MEDIUM'), ("As Large Swatches", 'LARGE'),
                          ("As Extra Large Swatches", 'XLARGE'))},
    **{f"{HS}/View/{label}": _prop("window_manager.allset_hs_sort", key)
       for label, key in (("By Name", 'NAME'), ("By Type", 'TYPE'), ("By Time", 'TIME'))},
    f"{HS}/View/Reverse Order": _prop("window_manager.allset_hs_reverse"),
    **{f"{HS}/Create/Materials/{label}": ("allset.hs_create", {"kind": kind}) for label, kind in _HS_MATERIALS.items()},
    **{f"{HS}/Create/Lights/{label}": ("allset.create", {"kind": kind}) for label, kind in _HS_LIGHTS.items()},
    f"{HS}/Create/Camera": ("allset.create", {"kind": 'CAMERA'}),
    f"{HS}/Create/Rendering/Render Layer": "scene.view_layer_add",
    f"{HS}/Create/Create Render Node...": ("wm.call_menu", {"name": "NODE_MT_add"}),
    f"{HS}/Graph/Graph Materials on Selected Objects": _hs_edit("FROM_OBJECT"),
    f"{HS}/Graph/Input and Output Connections": "node.view_all",
    **{f"{HS}/Window/{label}": "allset.hypershade"
       for label in ("Browser...", "Property Editor...", "Create...")},
    f"{HS}/Window/Render View...": "render.view_show",
    f"{HS}/Window/Outliner...": _editor('OUTLINER'),
    f"{HS}/Window/UV Editor...": _editor('UV'),
    f"{HS}/Window/Graph Editor...": _editor('FCURVES'),
    f"{HS}/Window/Attribute Spread Sheet...": _editor('SPREADSHEET'),
    **_help_menu(HS, "render/shader_nodes/index.html"),
    f"{HS}/Help/Help on Shader Library": _url(_MANUAL + "render/materials/index.html"),

    f"{RS}/Presets/Import Render Settings/Default Settings": "allset.rs_defaults",
    **_help_menu(RS, "render/output/properties/index.html"),

    f"{SE}/File/Open Script...": "text.open",
    f"{SE}/File/Save Script...": "text.save_as",
    f"{SE}/Edit/Undo": "ed.undo",
    f"{SE}/Edit/Redo": "ed.redo",
    f"{SE}/Edit/Cut": "text.cut",
    f"{SE}/Edit/Copy": "text.copy",
    f"{SE}/Edit/Paste": "text.paste",
    f"{SE}/Edit/Select All": "text.select_all",
    f"{SE}/Edit/Goto line...": "text.jump",
    f"{SE}/Edit/Search and Replace...": "text.start_find",
    f"{SE}/Edit/Indent Selection": "text.indent",
    f"{SE}/Edit/Unindent Selection": "text.unindent",
    f"{SE}/Edit/Clear History": ("allset.script_clear", {"what": "HISTORY"}),
    f"{SE}/Edit/Clear Input": ("allset.script_clear", {"what": "INPUT"}),
    f"{SE}/Edit/Clear All": ("allset.script_clear", {"what": "ALL"}),
    f"{SE}/Command/Show line numbers": _prop("space_data.show_line_numbers"),
    f"{SE}/Command/Use tabs for indent": _prop("space_data.text.indentation", 'TABS'),
    f"{SE}/Command/Command Completion": "text.autocomplete",
    f"{SE}/Command/Execute": "allset.script_run",
    f"{SE}/Tabs/New Tab...": ("allset.script_tab", {"new": True}),
    f"{SE}/Tabs/Delete Tab": "text.unlink",
    **_help_menu(SE, "editors/text_editor.html"),
    f"{SE}/Help/Help on MEL": _url(_API),
    f"{SE}/Help/Help on Python": _url(_API + "info_quickstart.html"),
})
MAP.update(_hs_nodes())
