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
    return ("maya_kit.set_tangent", {"kind": kind, "side": side})


def _infinity(side, mode):
    return ("maya_kit.curve_infinity", {"side": side, "mode": mode})


def _key(action):
    return ("maya_kit.key_edit", {"action": action})


def _uv_tool(idname):
    return ("wm.tool_set_by_id", {"name": idname, "space_type": 'IMAGE_EDITOR'})


# Maya tangent labels -> set_tangent kinds (operators/time_keys.TANGENTS). Maya 2022's Auto variants
# (Auto Span / Ease / Mix / Custom) are one Blender auto handle (Auto Clamped): notices in ui/notices.py.
TANGENT_KINDS = {"Spline": "SPLINE", "Linear": "LINEAR", "Clamped": "CLAMPED", "Stepped": "STEPPED",
                 "Stepped Next": "STEPPED_NEXT", "Flat": "FLAT", "Fixed": "FIXED", "Plateau": "PLATEAU"}
AUTO_KINDS = ("Auto Span (Legacy)", "Auto Ease", "Auto Mix", "Auto Custom")

# Default In / Out Tangent -> Blender's one default for new keys (Preferences > Animation > F-Curves).
_EDIT = "preferences.edit"
DEFAULT_TANGENT = {
    **{label: (f"{_EDIT}.keyframe_new_handle_type", 'AUTO_CLAMPED') for label in AUTO_KINDS},
    "Spline": (f"{_EDIT}.keyframe_new_handle_type", 'AUTO'),
    "Clamped": (f"{_EDIT}.keyframe_new_handle_type", 'AUTO_CLAMPED'),
    "Plateau": (f"{_EDIT}.keyframe_new_handle_type", 'AUTO_CLAMPED'),
    "Linear": (f"{_EDIT}.keyframe_new_interpolation_type", 'LINEAR'),
    "Stepped": (f"{_EDIT}.keyframe_new_interpolation_type", 'CONSTANT'),
}


def _tangents_menu(ed):
    m = {f"{ed}/Tangents/Auto/{label}": _tangent("AUTO") for label in AUTO_KINDS}
    m.update({f"{ed}/Tangents/{label}": _tangent(kind) for label, kind in TANGENT_KINDS.items()})
    for side, sub in (("IN", "In Tangent"), ("OUT", "Out Tangent")):
        m.update({f"{ed}/Tangents/{sub}/Auto/{label}": _tangent("AUTO", side) for label in AUTO_KINDS})
        m.update({f"{ed}/Tangents/{sub}/{label}": _tangent(kind, side) for label, kind in TANGENT_KINDS.items()})
    for sub in ("Default In Tangent", "Default Out Tangent"):
        m.update({f"{ed}/Tangents/{sub}/{label}": _prop(*target) for label, target in DEFAULT_TANGENT.items()
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
        f"{ed}/Edit/Change Curve Color": ("maya_kit.curve_color", {"action": 'CHANGE'}),
        f"{ed}/Edit/Remove Curve Color": ("maya_kit.curve_color", {"action": 'REMOVE'}),
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
        m[f"{ed}/Keys/Insert Key Tool"] = "maya_kit.insert_key_tool"
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
    f"{GE}/View/Center Current Time": "maya_kit.graph_center_time",
    f"{GE}/View/Infinity": _prop(f"{_SP}.show_extrapolation"),
    f"{GE}/View/Keys/Always": _prop(f"{_EDIT}.show_only_selected_curve_keyframes", False),
    f"{GE}/View/Keys/Active Only": _prop(f"{_EDIT}.show_only_selected_curve_keyframes", True),
    f"{GE}/View/Tangents/Always": _prop(f"{_SP}.use_only_selected_keyframe_handles", False),
    f"{GE}/View/Tangents/Never": _prop(f"{_SP}.show_handles", False),
    f"{GE}/View/Tangents/On Active Keys": _prop(f"{_SP}.use_only_selected_keyframe_handles", True),
    f"{GE}/View/Theme/Color Preferences": ("screen.userpref_show", {"section": 'THEMES'}),
    f"{GE}/View/Absolute View": _prop(f"{_SP}.use_normalization", False),
    f"{GE}/View/Stacked View": ("maya_kit.graph_view_mode", {"mode": "STACKED"}),
    f"{GE}/View/Normalized View": _prop(f"{_SP}.use_normalization", True),
    f"{GE}/View/Renormalize": _prop(f"{_SP}.use_auto_normalization"),
    f"{GE}/Select/All": ("graph.select_all", {"action": 'SELECT'}),
    f"{GE}/Select/Snap time to selection": _prop(f"addon_prefs.snap_time_to_selection"),
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
    f"{UV}/Create/Assign Checker Shader": "maya_kit.checker_shader",
    f"{UV}/Create/Automatic": "uv.smart_project",
    f"{UV}/Create/Camera-based": ("v3d", "uv.project_from_view", {}),
    f"{UV}/Create/Normal-based": "maya_kit.uv_planar",
    f"{UV}/Create/Cylindrical": ("v3d", "uv.cylinder_project", {}),
    f"{UV}/Create/Planar": "maya_kit.uv_planar",
    f"{UV}/Create/Spherical": ("v3d", "uv.sphere_project", {}),
    f"{UV}/Select/All": ("uv.select_all", {"action": 'SELECT'}),
    f"{UV}/Select/Clear": ("uv.select_all", {"action": 'DESELECT'}),
    f"{UV}/Select/Inverse": ("uv.select_all", {"action": 'INVERT'}),
    **{f"{UV}/Select/Components/{label}": ("maya_kit.uv_component", {"mode": mode})
       for label, mode in (("Vertex", "VERTEX"), ("Edge", "EDGE"), ("Face", "FACE"), ("UV", "UV"),
                           ("UV Shell", "SHELL"))},
    f"{UV}/Select/Overlapping": "uv.select_overlap",
    f"{UV}/Select/Shortest Edge Path Tool": "uv.shortest_path_select",
    f"{UV}/Select/Grow": "uv.select_more",
    f"{UV}/Select/Shrink": "uv.select_less",
    **{f"{UV}/Select/Convert Selection/{label}": ("maya_kit.uv_component", {"mode": mode})
       for label, mode in (("To Vertices", "VERTEX"), ("To Edges", "EDGE"), ("To Faces", "FACE"), ("To UVs", "UV"),
                           ("To UV Shell", "SHELL"))},
    f"{UV}/Cut/Sew/Cut": "maya_kit.uv_cut",
    f"{UV}/Cut/Sew/Sew": "maya_kit.uv_sew",
    f"{UV}/Cut/Sew/Merge": "uv.weld",
    f"{UV}/Cut/Sew/Move and Sew": "maya_kit.uv_sew",
    f"{UV}/Cut/Sew/Stitch Together": "uv.stitch",
    f"{UV}/Modify/Align": ("uv.align", {"axis": 'ALIGN_AUTO'}),
    f"{UV}/Modify/Flip": ("transform.mirror", {"constraint_axis": (True, False, False)}),
    f"{UV}/Modify/Linear Align": ("uv.align", {"axis": 'ALIGN_S'}),
    f"{UV}/Modify/Match UVs": "uv.remove_doubles",
    f"{UV}/Modify/Rotate": ("transform.rotate", {"value": -math.pi / 2}),
    f"{UV}/Modify/Unitize": "uv.reset",
    f"{UV}/Modify/Gather Shells": "uv.pack_islands",
    f"{UV}/Modify/Layout": "maya_kit.uv_layout",
    f"{UV}/Modify/Orient Shells": "uv.align_rotation",
    f"{UV}/Modify/Randomize Shells": "uv.randomize_uv_transform",
    f"{UV}/Modify/Optimize": "uv.minimize_stretch",
    f"{UV}/Modify/Straighten Shell": "uv.follow_active_quads",
    f"{UV}/Modify/Straighten UVs": ("uv.align", {"axis": 'ALIGN_S'}),
    f"{UV}/Modify/Unfold": "maya_kit.uv_unfold",
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
    f"{UV}/Textures/Checker Map": "maya_kit.checker_shader",
    f"{UV}/UV Sets/UV Set Editor": ("maya_kit.open_editor", {"ui_type": 'PROPERTIES', "tab": 'DATA'}),
    f"{UV}/UV Sets/Copy UVs to UV Set/Copy into New UV Set": "mesh.uv_texture_add",
    f"{UV}/UV Sets/Create Empty UV Set": "mesh.uv_texture_add",
    f"{UV}/UV Sets/Delete Current UV Set": "mesh.uv_texture_remove",
    **_help_menu(UV, "editors/uv/index.html"),
    "UV Toolkit/Help/Help on UV Toolkit": _url(_MANUAL + "modeling/meshes/uv/index.html"),
}
