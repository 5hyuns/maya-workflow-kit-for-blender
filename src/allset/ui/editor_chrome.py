# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya editor chrome for the Graph Editor, Dope Sheet and UV Editor (docs/steps/step_104.md 「계획」).

Maya 2022 measured in a GUI session (research/scripts/maya_editors104/, research/maya/screens/editors104/):

- menu bars: Graph Editor Edit / View / Select / Curves / Keys / Tangents / List / Show / Help, Dope Sheet the same
  without Select, UV Editor Edit / Create / Select / Cut/Sew / Modify / Tools / View / Image / Textures / UV Sets /
  Help (structure ``editor_menu_data``, actions ``editor_menu_map``, classes built by ``menu_sets``);
- icon rows under them (control names in the capture's ``widgets``; order kept, Maya icons not copied);
- the Graph Editor's outliner lists the object and its attributes "Translate X" (red) / "Translate Y" (green), no
  Action / group rows (graph_editor_win1.png).

Blender: ``GRAPH_HT_header.draw`` and ``DOPESHEET_HT_header.draw`` are swapped while the kit is on (restored on
unregister, ``tests/kit.py`` snapshots them); the UV Editor's header / tool header go through the ``ui/shelf.py``
``IMAGE_HT_header`` wrapper. Graph Editor and Dope Sheet areas have a single header row (no tool header region), so
the icon row follows the menus on it; the UV Editor's tool header is Maya's second row. Blender's own editor menus
stay in a 「Blender」 menu at the end of the bar.
"""

import blf
import bpy
import gpu
from bpy.props import BoolProperty, IntProperty, StringProperty
from gpu_extras.batch import batch_for_shader

from .. import live_refs
from . import editor_menu_data, menu_map, menu_sets

GE, DS, UV = "Graph Editor", "Dope Sheet", "UV Editor"


def enabled(context):
    """Maya editor chrome follows the Panel Menus preference (Maya menus in editor headers)."""
    from .. import preferences
    try:
        return preferences.get(context).maya_panel_menus
    except (KeyError, AttributeError):    # add-on prefs gone (disable in progress) / a context without preferences
        return False


def is_graph(space):
    return space is not None and space.type == 'GRAPH_EDITOR' and space.mode == 'FCURVES'


def is_dope(space):
    return space is not None and space.type == 'DOPESHEET_EDITOR' and space.mode in {'DOPESHEET', 'ACTION'}


def is_uv(space):
    return space is not None and space.type == 'IMAGE_EDITOR' and space.mode == 'UV'


# --- menu bars ---------------------------------------------------------------------------------------------------

BLENDER_MENUS = {GE: "GRAPH_MT_editor_menus", DS: "DOPESHEET_MT_editor_menus", UV: "IMAGE_MT_editor_menus",
                 # step 105 windows (the Render Settings window is a Properties editor: no Blender menus)
                 "Hypershade": "NODE_MT_editor_menus", "Script Editor": "INFO_MT_editor_menus"}


def _blender_menu_class(editor):
    def draw(self, context):
        layout = self.layout
        if editor == DS:
            layout.prop(context.space_data, "ui_mode", text="")
            layout.separator()
        getattr(bpy.types, BLENDER_MENUS[editor]).draw(self, context)
    idname = "ALLSET_MT_ed_blender_" + editor.replace(" ", "").lower()
    return type(idname, (bpy.types.Menu,), {"bl_idname": idname, "bl_label": "Blender", "draw": draw,
                                             "__doc__": f"Blender's own {editor} menus"})


def _bar_class(editor):
    def draw(self, context):
        draw_menu_bar(self.layout, context, editor)
    idname = "ALLSET_MT_ed_bar_" + editor.replace(" ", "").lower()
    return type(idname, (bpy.types.Menu,), {"bl_idname": idname, "bl_label": "Menus", "draw": draw,
                                             "__doc__": f"The Maya {editor} menus folded into one menu"})


_BLENDER = {ed: _blender_menu_class(ed) for ed in BLENDER_MENUS}
_BAR = {ed: _bar_class(ed) for ed in (*BLENDER_MENUS, "Render Settings")}


def draw_menu_bar(layout, context, editor):
    for i, (title, _items) in enumerate(editor_menu_data.EDITORS[editor]):
        layout.menu(menu_sets.editor_menu_idname(editor, i), text=title)
    if editor in _BLENDER:
        layout.menu(_BLENDER[editor].bl_idname, text="Blender")


def draw_menus(layout, context, editor):
    if context.area is None or context.area.show_menus:
        draw_menu_bar(layout.row(align=True), context, editor)
    else:
        layout.menu(_BAR[editor].bl_idname, text="", icon='COLLAPSEMENU')


# --- icon rows -----------------------------------------------------------------------------------------------------
# (Maya control name from the capture, Blender icon, action or None, Maya tooltip). An action is a menu_map value
# (incl. ("prop", ...)); "|" = separator, "STATS" = the selected key's time / value fields, "IMAGE" / "UVMAP" = the
# UV Editor's texture field / UV set. Unmapped buttons draw greyed with their notice (NOTICES below).

def _t(kind):
    return ("allset.set_tangent", {"kind": kind})


def _inf(side, mode):
    return ("allset.curve_infinity", {"side": side, "mode": mode})


_DSF = "space_data.dopesheet"
GRAPH_ICONS = (
    ("directKeyTool", 'RESTRICT_SELECT_OFF', None, "Move Nearest Picked Key Tool"),
    ("insertKeyTool", 'KEY_HLT', "allset.insert_key_tool", "Insert Keys Tool"),
    ("latticeDeformKeyTool", 'MOD_LATTICE', None, "Lattice Deform Keys"),
    ("regionSelectKeyTool", 'FULLSCREEN_ENTER', "transform.resize", "Region Tool: Scale or move keys"),
    ("retimeKeyTool", 'TIME', None, "Retime Tool: scale and ripple keys"),
    "|", "STATS", "|",
    ("frameAllButton", 'ZOOM_ALL', "graph.view_all", "Frame all"),
    ("frameRangeButton", 'PREVIEW_RANGE', "anim.scene_range_frame", "Frame playback range"),
    ("centerCurrentTimeButton", 'TIME', "allset.graph_center_time", "Center the view about the current time"),
    "|",
    ("autoTanButton", 'HANDLE_AUTOCLAMPED', _t("AUTO"), "Auto tangents"),
    ("autoeaseTanButton", 'HANDLE_AUTOCLAMPED', _t("AUTO"), "Auto Ease tangents"),
    ("automixTanButton", 'HANDLE_AUTOCLAMPED', _t("AUTO"), "Auto Mix tangents"),
    ("autocustomTanButton", 'HANDLE_AUTOCLAMPED', _t("AUTO"), "Auto Custom tangents"),
    ("splineTanButton", 'IPO_BEZIER', _t("SPLINE"), "Spline tangents"),
    ("clampedTanButton", 'HANDLE_AUTO', _t("CLAMPED"), "Clamped tangents"),
    ("linearTanButton", 'IPO_LINEAR', _t("LINEAR"), "Linear tangents"),
    ("flatTanButton", 'IPO_SINE', _t("FLAT"), "Flat tangents"),
    ("stepTanButton", 'IPO_CONSTANT', _t("STEPPED"), "Stepped tangents"),
    ("plateauTanButton", 'IPO_EASE_IN_OUT', _t("PLATEAU"), "Plateau tangents"),
    "|",
    ("graphEdDefaultTanInButton", 'TRIA_LEFT', ("submenu", "Tangents/Default In Tangent"), "Default in tangent"),
    ("graphEdDefaultTanOutButton", 'TRIA_RIGHT', ("submenu", "Tangents/Default Out Tangent"), "Default out tangent"),
    "|",
    ("bufferSnapButton", 'GHOST_ENABLED', "graph.ghost_curves_create", "Buffer curve snapshot"),
    ("bufferSwapButton", 'GHOST_DISABLED', None, "Swap buffer curves"),
    "|",
    ("breakTanButton", 'HANDLE_FREE', _t("BREAK"), "Break tangents"),
    ("unifyTanButton", 'HANDLE_ALIGNED', _t("UNIFY"), "Unify tangents"),
    ("freeTanButton", 'UNLOCKED', None, "Free tangent length"),
    ("lockTanButton", 'LOCKED', None, "Lock tangent length"),
    "|",
    ("OutlineEdloadToggleButton", 'RESTRICT_SELECT_OFF', ("prop", f"{_DSF}.show_only_selected", {}),
     "Auto load Graph Editor on selection"),
    ("OutlineEdreloadButton", 'FILE_REFRESH', None, "Load the selected objects"),
    "|",
    ("timeSnapButton", 'SNAP_ON', ("prop", "tool_settings.use_snap_anim", {}), "Time snap"),
    ("valueSnapButton", 'SNAP_INCREMENT', None, "Value snap"),
    "|",
    ("graphEditorAbsoluteViewIconButton", 'FCURVE', ("prop", "space_data.use_normalization", {"value": False}),
     "Absolute view"),
    ("graphEditorStackedViewIconButton", 'ALIGN_JUSTIFY', ("allset.graph_view_mode", {"mode": "STACKED"}),
     "Stacked view"),
    ("graphEditorNormalizedViewIconButton", 'NORMALIZE_FCURVES',
     ("prop", "space_data.use_normalization", {"value": True}), "Normalized view"),
    ("renormalizeCurvesButton", 'FILE_REFRESH', ("prop", "space_data.use_auto_normalization", {}),
     "Re-normalize curves"),
    "|",
    ("curvesPreInfinityCycleButton", 'LOOP_BACK', _inf("PRE", "CYCLE"), "Pre-infinity cycle"),
    ("curvesPreInfinityCycleOffsetButton", 'FRAME_PREV', _inf("PRE", "CYCLE_OFFSET"), "Pre-infinity cycle with offset"),
    ("curvesPostInfinityCycleButton", 'LOOP_FORWARDS', _inf("POST", "CYCLE"), "Post-infinity cycle"),
    ("curvesPostInfinityCycleOffsetButton", 'FRAME_NEXT', _inf("POST", "CYCLE_OFFSET"),
     "Post-infinity cycle with offset"),
    "|",
    ("getDopeSheetButton", 'ACTION', ("allset.open_editor", {"ui_type": 'DOPESHEET'}), "Open the Dope Sheet"),
    ("getTraxButton", 'NLA', ("allset.open_editor", {"ui_type": 'NLA_EDITOR'}), "Open the Time Editor"),
)

DOPE_ICONS = (
    ("selectKeyTool", 'RESTRICT_SELECT_OFF', None, "Select keys"),
    ("directKeyTool", 'ORIENTATION_CURSOR', None, "Move Nearest Picked Key Tool"),
    ("insertKeyTool", 'KEY_HLT', "action.keyframe_insert", "Insert Keys Tool"),
    "|", "STATS", "|",
    ("frameAllButton", 'ZOOM_ALL', "action.view_all", "Frame all"),
    ("frameRangeButton", 'PREVIEW_RANGE', "anim.scene_range_frame", "Frame playback range"),
    ("centerCurrentTimeButton", 'TIME', "action.view_frame", "Center the view about the current time"),
    "|",
    ("hierButton", 'OUTLINER', None, "Show the hierarchy below"),
    "|",
    ("OutlineEdloadToggleButton", 'RESTRICT_SELECT_OFF', ("prop", f"{_DSF}.show_only_selected", {}),
     "Auto load Dope Sheet on selection"),
    ("OutlineEdreloadButton", 'FILE_REFRESH', None, "Load the selected objects"),
    "|",
    ("getGraphEditorButton", 'GRAPH', ("allset.open_editor", {"ui_type": 'FCURVES'}), "Open the Graph Editor"),
    ("getTraxButton", 'NLA', ("allset.open_editor", {"ui_type": 'NLA_EDITOR'}), "Open the Time Editor"),
)

_UVE = "space_data.uv_editor"
UV_ICONS = (
    ("viewUVWireframeButton", 'SHADING_WIRE', ("prop", f"{_UVE}.show_faces", {"value": False}),
     "Display the UVs as wireframe"),
    ("viewShadeUVButton", 'SHADING_SOLID', ("prop", f"{_UVE}.show_faces", {"value": True}),
     "Shade the UV shells"),
    ("distortionButton", 'MOD_UVPROJECT', ("prop", f"{_UVE}.show_stretch", {}), "Display UV distortion"),
    "|",
    ("toggleTextureBorderButton", 'MOD_EDGESPLIT', ("prop", "window_manager.allset_uv_texture_borders", {}), "Display texture borders"),
    ("toggleShellBorderButton", 'MESH_DATA', ("prop", "window_manager.allset_uv_shell_borders", {}), "Display shell borders"),
    "|",
    ("gridDisplayButton", 'GRID', ("prop", "space_data.overlay.show_grid_background", {}), "Display the grid"),
    ("isolateViewSelectButton", 'HIDE_OFF', "allset.uv_isolate", "Isolate select"),
    "|",
    ("snapShotButton", 'IMAGE_DATA', "uv.export_layout", "UV snapshot"),
    "|",
    ("checkeredButton", 'TEXTURE', "allset.checker_toggle", "Checker tiling"),
    "IMAGE",
    ("imageChannelButton", 'IMAGE_RGB_ALPHA', ("channels", "space_data.display_channels", {}), "Image channels"),
    ("dimmerButton", 'LIGHT', None, "Dim the image"),
    "|", "UVMAP",
)

def _hsg(action):
    return ("allset.hs_graph", {"action": action})


# Maya Hypershade graph toolbar (step 131: control names + tooltips from research/maya/screens/hypershade131/
# _hypershade131.json); actions run in the Hypershade's graph (ui/hypershade.py)
HS_GRAPH_ICONS = (
    ("showUpstreamButton", 'BACK', _hsg("UPSTREAM"), "Input connections"),
    ("showUpAndDownstreamButton", 'ARROW_LEFTRIGHT', _hsg("BOTH"), "Input and output connections"),
    ("showDownstreamButton", 'FORWARD', _hsg("DOWNSTREAM"), "Output connections"),
    "|",
    ("clearGraphButton", 'X', None, "Clear graph"),
    ("addSelectedButton", 'ADD', None, "Add selected nodes to graph"),
    ("removeSelectedButton", 'REMOVE', None, "Remove selected nodes from graph"),
    ("rearrangeGraphButton", 'NODETREE', None, "Rearrange graph"),
    ("graphMaterialsButton", 'MATERIAL', ("allset.hs_edit", {"action": "FROM_OBJECT"}),
     "Graph materials on selected objects"),
    "|",
    ("LODSimpleModeButton", 'COLLAPSEMENU', _hsg("COLLAPSE"), "Hide attributes on selected nodes"),
    ("LODConnectedModeButton", 'LINKED', _hsg("CONNECTED"), "Show connected attributes on selected nodes"),
    ("LODShowAllButton", 'ALIGN_JUSTIFY', _hsg("SHOW_ALL"), "Show primary attributes on selected nodes"),
    ("LODShowCustomButton", 'PRESET', None, "Show attributes from custom attribute view"),
    ("attrFilterToggleButton", 'FILTER', None, "Toggle the display of the attribute filter field on selected nodes"),
    ("swatchSizeToggleButton", 'IMAGE_PLANE', _hsg("PREVIEW"), "Toggle the icon swatch size of selected nodes to "
     "small/large"),
    "|",
    ("tabsRLCTButton", 'LOOP_BACK', None, "Restore last closed tab"),
)
ICONS = {GE: GRAPH_ICONS, DS: DOPE_ICONS, UV: UV_ICONS, "Hypershade": HS_GRAPH_ICONS}

# Notices of the greyed icon buttons (same form as ui/notices.NOTICES)
NOTICES = {
    "directKeyTool": ("Drag a key", "Blender's Graph Editor / Dope Sheet always move the key under the mouse when you "
                      "drag it: no tool to pick."),
    "selectKeyTool": ("Click / box select", "Blender selects keys with a click or a box drag: no tool to pick."),
    "latticeDeformKeyTool": ("Scale (S)", "Blender has no lattice for keys: scale the selected keys with S."),
    "retimeKeyTool": ("Scale / Slide", "Blender has no retime tool: scale (S) or slide (T in the Dope Sheet) keys."),
    "bufferSwapButton": ("Ghost curves", "Blender's buffer (ghost) curves are a picture: they can't be swapped "
                         "with the curves."),
    "freeTanButton": ("Handle types", "Blender's handles keep their own length: lengths are never freed."),
    "lockTanButton": ("Handle types", "Blender's handles keep their own length: lengths are never locked."),
    "OutlineEdreloadButton": ("Only Show Selected", "Blender lists the selected objects' channels as you select "
                              "(the auto load button)."),
    "valueSnapButton": ("Snap", "Blender snaps keys to frames only (Edit > Snap, time snap button)."),
    "hierButton": ("Channel filters", "Blender lists child objects only when they are selected too."),
    "toggleTextureBorderButton": ("Seams", "Blender draws seams in the 3D View, not texture borders here."),
    "toggleShellBorderButton": ("Select Linked", "Blender doesn't draw shell borders in the UV Editor: select a "
                                "shell with Select > Select Linked."),
    "isolateViewSelectButton": ("Hide", "Blender isolates UVs by hiding the rest (H / Shift+H)."),
    "clearGraphButton": ("Pin", "Blender's graph always shows the whole material: pin another material to change "
                         "what it shows."),
    "addSelectedButton": ("Pin", "Blender's graph shows one material's whole network: nodes can't be added to it "
                          "from elsewhere."),
    "removeSelectedButton": ("Hide attributes", "Blender's graph shows the whole network: collapse nodes instead."),
    "rearrangeGraphButton": ("Move nodes", "Blender has no automatic node layout: move nodes with G."),
    "LODShowCustomButton": ("Not in Blender", "Blender has no custom attribute views on nodes."),
    "attrFilterToggleButton": ("Not in Blender", "Blender's nodes have no attribute filter field."),
    "tabsRLCTButton": ("Not in Blender", "Blender's graph has one tab (one material at a time)."),
    "dimmerButton": ("Image field", "Blender doesn't dim the image: pick no image in the header field to hide it."),
}


def _icon_spec(editor, key):
    return next((it for it in ICONS[editor] if isinstance(it, tuple) and it[0] == key), None)


def _submenu(editor, sub):
    return menu_sets.SUBMENU_IDS.get(f"{editor}/{sub}")


def draw_icons(layout, context, editor):
    row = layout.row(align=True)
    for it in ICONS[editor]:
        if it == "|":
            row.separator()
            row = layout.row(align=True)
        elif it == "STATS":
            scene = context.scene
            sub = layout.row(align=True)
            sub.label(text="Stats")
            col = sub.row(align=True)
            col.ui_units_x = 3.5
            col.prop(scene, "allset_key_time", text="")
            col = sub.row(align=True)
            col.ui_units_x = 3.5
            col.prop(scene, "allset_key_value", text="")
        elif it == "IMAGE":
            sima = context.space_data
            layout.template_ID(sima, "image", new="image.new", open="image.open")
        elif it == "UVMAP":
            ob = context.edit_object
            if ob is not None and ob.type == 'MESH' and ob.data.uv_layers.active is not None:
                sub = layout.row()
                sub.ui_units_x = 5
                sub.prop(ob.data.uv_layers.active, "name", text="", icon='GROUP_UVS')
        else:
            _draw_icon(row, context, editor, it)


def _draw_icon(row, context, editor, it):
    key, icon, action, _tip = it
    if action is None:
        row.operator(ALLSET_OT_editor_icon_unavailable.bl_idname, text="", icon=icon).key = f"{editor}|{key}"
        return
    if action[0] == "submenu":
        idname = _submenu(editor, action[1])
        if idname:
            row.menu(idname, text="", icon=icon)
        return
    if action[0] in ("prop", "channels"):
        owner, attr = menu_sets.prop_owner(context, action[1])
        if owner is None:
            row.operator(ALLSET_OT_editor_icon_unavailable.bl_idname, text="", icon=icon).key = f"{editor}|{key}"
            return
        if action[0] == "channels":
            row.prop(owner, attr, text="", icon_only=True)
            return
        props = action[2]
        if "value" not in props:
            row.prop(owner, attr, text="", icon=icon, toggle=True)
            return
        current = getattr(owner, attr)
        value = props["value"]
        on = abs(current - value) < 1e-6 if isinstance(value, float) else current == value
        op = row.operator(menu_sets.ALLSET_OT_menu_set_value.bl_idname, text="", icon=icon, depress=on)
        op.target, op.value = action[1], repr(value)
        return
    on = _toggle_state(context, key)
    row.operator(ALLSET_OT_editor_icon.bl_idname, text="", icon=icon, depress=bool(on)).key = f"{editor}|{key}"


def _toggle_state(context, key):
    """Pressed state of icon buttons that run a toggle operator (Maya iconTextCheckBox), None otherwise."""
    if key == "checkeredButton":
        from ..operators import menu_items
        return menu_items.checker_on(context)
    return None


class ALLSET_OT_editor_icon(bpy.types.Operator):
    """Maya editor icon-row button"""
    bl_idname = "allset.editor_icon"
    bl_label = "Editor Button"
    bl_options = {'INTERNAL'}

    key: StringProperty(options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, props):
        editor, _sep, key = props.key.partition("|")
        it = _icon_spec(editor, key) if editor in ICONS else None
        if it is None:
            return ""
        s = menu_map.normalize(it[2])
        target = f"\nBlender: {s[1]}" if s and s[0] in ("op", "v3d") else ""
        return f"Maya: {it[3]}{target}"

    def execute(self, context):
        editor, _sep, key = self.key.partition("|")
        it = _icon_spec(editor, key) if editor in ICONS else None
        if it is None or it[2] is None:
            return {'CANCELLED'}
        from ..marking.modal import run_action
        try:
            run_action(context, it[2])
        except RuntimeError as ex:
            self.report({'WARNING'}, str(ex).strip().splitlines()[-1])
            return {'CANCELLED'}
        return {'FINISHED'}


class ALLSET_OT_editor_icon_unavailable(bpy.types.Operator):
    """Maya editor button without a Blender counterpart (always greyed out)"""
    bl_idname = "allset.editor_icon_unavailable"
    bl_label = "Not Available"
    bl_options = {'INTERNAL'}

    key: StringProperty(options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return False

    @classmethod
    def description(cls, context, props):
        editor, _sep, key = props.key.partition("|")
        it = _icon_spec(editor, key) if editor in ICONS else None
        tip = it[3] if it else key
        sub, line = NOTICES.get(key, ("", "Not in this Blender editor."))
        return f"Maya: {tip} (greyed)  →  {sub}\n{line}" if sub else f"Maya: {tip} (greyed)\n{line}"

    def execute(self, context):
        return {'CANCELLED'}


# --- Stats fields: the selected key's time / value (Maya Graph Editor / Dope Sheet icon row) -----------------------

def _kind(fc):
    tail = fc.data_path.rsplit(".", 1)[-1]
    return "LENGTH" if tail in {"location", "delta_location"} else \
        "ROTATION" if tail in {"rotation_euler", "delta_rotation_euler"} else "NONE"


def selected_points(context):
    """[(fcurve, keyframe point)] selected in the editor the context belongs to (Graph Editor / Dope Sheet)."""
    out = []
    for fc in getattr(context, "editable_fcurves", None) or ():
        out += [(fc, kp) for kp in fc.keyframe_points if kp.select_control_point]
    return out


def _stats_get(field):
    def get(scene):
        from . import cb_entry
        pts = selected_points(bpy.context)
        if not pts:
            return ""
        values = {round(kp.co.x if field == "time" else kp.co.y, 6) for _fc, kp in pts}
        if len(values) > 1:
            return "-"          # Maya shows a blank field for several values; "-" = mixed
        fc, kp = pts[0]
        if field == "time":
            return cb_entry.fmt_number(kp.co.x)
        return cb_entry.format_value(kp.co.y, _kind(fc), scene)
    return get


def _stats_set(field):
    def set_(scene, text):
        from . import cb_entry
        for fc, kp in selected_points(bpy.context):
            old = kp.co.x if field == "time" else kp.co.y
            try:
                new = cb_entry.parse_entry(text, old, "NONE" if field == "time" else _kind(fc), scene)
            except (ValueError, TypeError):
                return
            d = new - old
            axis = 0 if field == "time" else 1
            for v in (kp.co, kp.handle_left, kp.handle_right):
                v[axis] += d
            fc.update()
    return set_


# --- Graph Editor channel list (Maya outliner pane: node rows, "Translate X" rows) --------------------------------
# Maya lists DAG nodes with their animated attributes under them (research/maya/screens/audit7/maya/
# e02_graph_editor_win1.png, research/maya/screens/graph/graph_00_frame_all_ge.png): objects, joints (= pose bones,
# CLAUDE.md step 55; their curves live on the armature object as ``pose.bones["joint1"].location``) and the
# blendShape node of a mesh (= its shape-key datablock, ``rig_tools`` names it blendShapeN; its curves are the Key
# ID's ``key_blocks["smile"].value``, one row per target, Maya's attribute = the target name). Step 150, #96.

MAYA_ATTR = {"location": "Translate", "rotation_euler": "Rotate", "scale": "Scale", "rotation_quaternion": "Rotate",
             "delta_location": "Delta Translate", "delta_rotation_euler": "Delta Rotate", "delta_scale": "Delta Scale"}
# One-value attributes: Maya visibility = hide_viewport (CLAUDE.md step 129); hide_render has no transform attribute
# in Maya, the closest is the shape's render stat Primary Visibility (step 150, delegated).
MAYA_SCALAR = {"hide_render": "Primary Visibility"}
AXES = "XYZ"
# Maya's default attribute name colours in the Graph Editor outliner (graph_editor_win1.png: Translate X red,
# Translate Y green; Z blue by the same rule as the manipulator / theme axis colours), other attributes light grey.
AXIS_COLOR = ((0.9, 0.25, 0.25, 1.0), (0.25, 0.85, 0.25, 1.0), (0.35, 0.55, 1.0, 1.0))
TEXT = (0.85, 0.85, 0.85, 1.0)
BACK = (0.267, 0.267, 0.267, 1.0)        # Maya outliner pane #444444 (colors.json ui_samples)
SELECT = (0.322, 0.522, 0.651, 1.0)      # Maya selection blue #5285a6 (kit-drawn pane: Maya's colours, any theme)
THUMB = (0.36, 0.36, 0.36, 1.0)          # Maya scroll bar thumb (e02_graph_editor_win1.png, right of the rows)
_expanded = {}                           # node key -> bool (Maya shows attributes expanded)
_scroll = {}                             # area pointer -> first row shown
# Rows the user picked in this outliner (Maya highlights only those, not every attribute of a selected node), valid
# while the scene selection is the one they were picked under.
_picked = {"ids": set(), "sig": None}
_BONES = 'pose.bones["'
_SHAPES = 'key_blocks["'


def _maya_names():
    """Attribute -> Maya name: the Channel Box's names first (one table), then MAYA_ATTR / MAYA_SCALAR."""
    from . import channel_box
    names, scalar = dict(MAYA_ATTR), dict(MAYA_SCALAR)
    for _key, label, path, idx, _kind in channel_box.MAIN:
        if idx < 0:
            scalar[path] = label
        else:
            names.setdefault(path, label.rsplit(" ", 1)[0])
    return names, scalar


def attr_label(fc):
    """Maya name of an F-curve's attribute: "Translate X", "Visibility", custom properties and blend shape targets
    by name."""
    path, idx = fc.data_path, fc.array_index
    if path.startswith(_SHAPES) and path.endswith('"].value'):
        return bpy.utils.unescape_identifier(path[len(_SHAPES):-len('"].value')])
    if path.endswith("]") and '["' in path:
        return path.rsplit('["', 1)[1].rstrip('"]')
    tail = path.rsplit(".", 1)[-1]
    names, scalar = _maya_names()
    if tail in scalar:
        return scalar[tail]
    if tail in names:
        name = names[tail]
        if tail == "rotation_quaternion":
            return f"{name} {'WXYZ'[idx]}"
        return f"{name} {AXES[idx]}" if idx < 3 else name
    return tail.replace("_", " ").title() + (f" {AXES[idx]}" if idx < 3 and fc.array_index else "")


def attr_color(fc):
    tail = fc.data_path.rsplit(".", 1)[-1]
    if tail in MAYA_ATTR and tail != "rotation_quaternion" and fc.array_index < 3:
        return AXIS_COLOR[fc.array_index]
    return TEXT


def object_curves(ob):
    """The object's own F-curves (its action's slot), Blender order."""
    from .. import compat
    return compat.id_fcurves(ob)


def shape_key(ob):
    """The object's shape-key datablock (Maya blendShape node) when it is animated, else None."""
    from .. import compat
    key = getattr(getattr(ob, "data", None), "shape_keys", None)
    return key if key is not None and compat.id_fcurves(key) else None


def _bone_name(path):
    """``pose.bones["joint1"].location`` -> "joint1" (None for other paths)."""
    if not path.startswith(_BONES):
        return None
    end = path.find('"]', len(_BONES))
    while end > 0 and path[end - 1] == "\\":      # an escaped quote inside the name
        end = path.find('"]', end + 1)
    return bpy.utils.unescape_identifier(path[len(_BONES):end]) if end > 0 else None


def split_object_curves(ob):
    """(the object's own curves, [(pose bone, its curves)] in the armature's bone order): joints are Maya nodes."""
    own, by_bone = [], {}
    bones = ob.pose.bones if ob.type == 'ARMATURE' and ob.pose is not None else None
    for fc in object_curves(ob):
        name = _bone_name(fc.data_path) if bones is not None else None
        pb = bones.get(name) if name is not None else None
        if pb is None:
            own.append(fc)
        else:
            by_bone.setdefault(pb.name, []).append(fc)
    return own, [(pb, by_bone[pb.name]) for pb in (bones or ()) if pb.name in by_bone]


def character_curves(scene, ks):
    """F-curves a character set's members (its own and its subcharacters' attributes) have (step 197, #104)."""
    from .. import compat
    from ..operators import character_sets
    out = []
    for p in character_sets.all_paths(scene, ks):
        if p.id is None:
            continue
        for fc in compat.id_fcurves(p.id):
            if fc.data_path == p.data_path and (p.use_entire_array or fc.array_index == p.array_index)                     and fc not in out:
                out.append(fc)
    return out


def node_name(node):
    return node.bl_label if isinstance(node, bpy.types.KeyingSet) else node.name


def node_curves(node):
    """F-curves of one outliner node: an object (without its joints'), a pose bone, a shape-key datablock or a
    character set."""
    from .. import compat
    if isinstance(node, bpy.types.KeyingSet):
        return character_curves(bpy.context.scene, node)
    if isinstance(node, bpy.types.PoseBone):
        return dict((pb.name, c) for pb, c in split_object_curves(node.id_data)[1]).get(node.name, [])
    if isinstance(node, bpy.types.Key):
        return compat.id_fcurves(node)
    return split_object_curves(node)[0]


def node_key(node):
    """Identity of a node row (``_expanded`` / picks): object name, ("JOINT", armature, bone), ("SHAPES", key)."""
    if isinstance(node, bpy.types.PoseBone):
        return ("JOINT", node.id_data.name, node.name)
    if isinstance(node, bpy.types.Key):
        return ("SHAPES", node.name)
    if isinstance(node, bpy.types.KeyingSet):
        return ("CHARACTER", node.bl_label)
    return node.name


def row_id(row):
    kind, node, fc = row
    return node_key(node) if kind != "ATTR" else (node_key(node), fc.data_path, fc.array_index)


def listed_objects(context, space):
    """Objects Blender's Graph Editor lists (animated, also by shape keys; only the selected with Only Show
    Selected), by name."""
    ds = space.dopesheet
    obs = [ob for ob in context.scene.objects
           if (ob.animation_data and ob.animation_data.action) or shape_key(ob) is not None]
    if ds.show_only_selected:
        obs = [ob for ob in obs if ob.select_get()]
    if not ds.show_hidden:
        obs = [ob for ob in obs if ob.visible_get()]
    return sorted(obs, key=lambda o: o.name)


# Maya lists a node's attributes in its attribute order (translate, rotate, scale, visibility, then the rest, e.g.
# custom attributes / blend shape targets), not in the order they were keyed (step 150, delegated).
ATTR_ORDER = ("location", "rotation_euler", "rotation_quaternion", "scale", "hide_viewport", "hide_render")


def maya_order(curves):
    def key(fc):
        tail = fc.data_path.rsplit(".", 1)[-1]
        return (ATTR_ORDER.index(tail) if tail in ATTR_ORDER else len(ATTR_ORDER), fc.array_index)
    return sorted(curves, key=key)      # stable: other attributes keep Blender's order


def listed_nodes(context, space):
    """[(kind, node, curves)]: per listed object its own row (when it has curves of its own), its joints (with Only
    Show Selected only the selected ones, in any mode: Blender's Graph Editor draws no curves of unselected bones
    then — measured in gui_step150_outliner), its blendShape node."""
    from . import channel_box
    ds = space.dopesheet
    out = []
    if getattr(context.window_manager, "allset_show_characters", False):
        # Show > Objects > Characters (step 197, #104): Maya lists the character nodes, their member attributes below
        from ..operators import character_sets
        for ks in character_sets.characters(context.scene):
            curves = character_curves(context.scene, ks)
            if curves:
                out.append(("CHARACTER", ks, curves))
    for ob in listed_objects(context, space):
        own, joints = split_object_curves(ob)
        if own:
            out.append(("OBJECT", ob, maya_order(own)))
        for pb, curves in joints:
            if ds.show_only_selected and not channel_box.bone_selected(pb):
                continue
            out.append(("JOINT", pb, maya_order(curves)))
        key = shape_key(ob)
        if key is not None:
            out.append(("SHAPES", key, object_curves(key)))
    return out


def rows(context, space):
    """[(kind, node, fcurve)] of the Maya list: a node row (OBJECT / JOINT / SHAPES), then its ATTR rows while
    expanded."""
    out = []
    flt = (space.dopesheet.filter_text or "").lower()
    for kind, node, curves in listed_nodes(context, space):
        out.append((kind, node, None))
        if _expanded.get(node_key(node), True):
            for fc in curves:
                if flt and flt not in fc.data_path.lower() and flt not in attr_label(fc).lower():
                    continue
                out.append(("ATTR", node, fc))
    return out


def listed_curves(context, space):
    return [fc for _kind, _node, curves in listed_nodes(context, space) for fc in curves]


def node_selected(context, kind, node):
    """Is the row's node selected in the scene (Maya loads the selection into the Graph Editor highlighted)?"""
    from . import channel_box
    if kind == "JOINT":
        arm = node.id_data
        return channel_box.bone_selected(node) if arm.mode == 'POSE' else arm.select_get()
    if kind == "CHARACTER":
        from ..operators import character_sets
        return node in character_sets.picked(context)
    if kind == "SHAPES":
        return any(o.select_get() for o in context.scene.objects
                   if getattr(getattr(o, "data", None), "shape_keys", None) == node)
    return node.select_get()


def selection_sig(context):
    """Scene selection (objects + pose-mode joints) the outliner picks belong to."""
    from . import channel_box
    sig = []
    for ob in context.scene.objects:
        if ob.select_get():
            sig.append(ob.name)
        if ob.type == 'ARMATURE' and ob.mode == 'POSE' and ob.pose is not None:
            sig += [(ob.name, pb.name) for pb in ob.pose.bones if channel_box.bone_selected(pb)]
    return tuple(sig)


def picked_ids(context, all_rows):
    """The user's picks that still name a listed row, or an empty set (none yet / the scene selection changed)."""
    if _picked["sig"] != selection_sig(context):
        return set()
    return _picked["ids"] & {row_id(r) for r in all_rows}


def highlighted(kind, rid, selected, picked):
    """Maya: once rows were picked in the outliner exactly those are highlighted; before that the selected nodes
    (never their attribute rows — Blender selects every F-curve of a selected object, so ``fc.select`` is not
    the highlight). Clicking an attribute un-highlights its node like Maya's outliner (step 150, delegated)."""
    if picked:
        return rid in picked
    return kind != "ATTR" and selected


def metrics(region):
    """(top of the first row, row height) in region pixels: Blender keeps its search field at the top."""
    s = bpy.context.preferences.system.ui_scale or 1.0     # 0 in background (step 68)
    return region.height - round(24 * s), round(20 * s)


def visible_rows(region):
    top, h = metrics(region)
    return max(1, int(top // h)) if h > 0 else 1


def clamp_scroll(offset, n_rows, n_visible):
    """First row shown: 0 .. the last full page (a list that fits doesn't scroll)."""
    return max(0, min(int(offset), n_rows - n_visible))


def _area_ptr(context):
    area = getattr(context, "area", None)
    return area.as_pointer() if area is not None else 0


def scroll_offset(context, region, n_rows):
    return clamp_scroll(_scroll.get(_area_ptr(context), 0), n_rows, visible_rows(region))


def row_at(context, region, y):
    top, h = metrics(region)
    if y > top:
        return None
    rs = rows(context, context.space_data)
    k = int((top - y) // h) + scroll_offset(context, region, len(rs))
    return rs[k] if 0 <= k < len(rs) else None


def _rect(x0, y0, x1, y1, color):
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": ((x0, y0), (x1, y0), (x1, y1), (x0, y0), (x1, y1), (x0, y1))})
    shader.uniform_float("color", color)
    batch.draw(shader)


def draw_channels():
    context = bpy.context
    space, region = context.space_data, context.region
    if not (is_graph(space) and enabled(context)) or region is None:
        return
    top, h = metrics(region)
    s = context.preferences.system.ui_scale
    gpu.state.blend_set('ALPHA')
    _rect(0, 0, region.width, top, BACK)
    font = 0
    blf.size(font, 12 * s)
    all_rows = rows(context, space)
    picked = picked_ids(context, all_rows)
    first = scroll_offset(context, region, len(all_rows))
    y = top
    for row in all_rows[first:]:
        if y < 0:
            break
        kind, node, fc = row
        sel = highlighted(kind, row_id(row), kind != "ATTR" and node_selected(context, kind, node), picked)
        if sel:
            _rect(0, y - h, region.width, y, SELECT)
        if kind != "ATTR":
            sign = "−" if _expanded.get(node_key(node), True) else "+"
            blf.color(font, *TEXT)
            blf.position(font, 6 * s, y - h + 6 * s, 0)
            blf.draw(font, sign)
            blf.position(font, 22 * s, y - h + 6 * s, 0)
            blf.draw(font, node_name(node))
        else:
            blf.color(font, *attr_color(fc))
            blf.position(font, 44 * s, y - h + 6 * s, 0)
            blf.draw(font, attr_label(fc))
        y -= h
    n_vis = visible_rows(region)
    if len(all_rows) > n_vis:       # Maya's scroll bar at the right edge: thumb = the shown part of the list
        span = top / len(all_rows)
        x1 = region.width - 2 * s
        _rect(x1 - 6 * s, top - (first + n_vis) * span, x1, top - first * span, THUMB)
    gpu.state.blend_set('NONE')


def show_rows(context, chosen):
    """Maya: the curves of the selected outliner rows are shown and selected, the others hidden."""
    for fc in listed_curves(context, context.space_data):
        on = fc in chosen
        fc.select = on
        fc.hide = not on


def pick_row(context, row, ctrl=False, shift=False):
    """A click on an outliner row: remember the picked rows (the highlight) and show / select their curves. Ctrl
    toggles, Shift adds, a plain click replaces."""
    space = context.space_data
    all_rows = rows(context, space)
    kind, node, fc = row
    rid = row_id(row)
    picked = set(node_curves(node) if kind != "ATTR" else [fc])
    current = {c for c in listed_curves(context, space) if c.select and not c.hide}
    ids = picked_ids(context, all_rows)
    if ctrl:
        chosen, ids = current ^ picked, ids ^ {rid}
    elif shift:
        chosen, ids = current | picked, ids | {rid}
    else:
        chosen, ids = picked, {rid}
    _picked["ids"], _picked["sig"] = ids, selection_sig(context)
    show_rows(context, chosen)
    return chosen


class ALLSET_OT_graph_channel_click(bpy.types.Operator):
    """Maya Graph Editor outliner: click a node (all its curves) or an attribute (that curve); Ctrl toggles,
    Shift adds; the +/- sign folds the attributes"""
    bl_idname = "allset.graph_channel_click"
    bl_label = "Graph Editor Outliner Click"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.region is not None and context.region.type == 'CHANNELS' and is_graph(context.space_data)

    def invoke(self, context, event):
        if not enabled(context):
            return {'PASS_THROUGH'}
        region = context.region
        if event.mouse_region_y > metrics(region)[0]:
            return {'PASS_THROUGH'}       # Blender's search field
        row = row_at(context, region, event.mouse_region_y)
        if row is None:
            return {'FINISHED'}
        kind, node, _fc = row
        s = context.preferences.system.ui_scale
        if kind != "ATTR" and event.mouse_region_x < 18 * s:
            key = node_key(node)
            _expanded[key] = not _expanded.get(key, True)
            region.tag_redraw()
            return {'FINISHED'}
        pick_row(context, row, ctrl=event.ctrl, shift=event.shift)
        for area in context.screen.areas:
            if area.type == 'GRAPH_EDITOR':
                area.tag_redraw()
        return {'FINISHED'}


def _channels_region(context):
    region = getattr(context, "region", None)
    if region is not None and region.type == 'CHANNELS':
        return region
    area = getattr(context, "area", None)
    return next((r for r in area.regions if r.type == 'CHANNELS'), None) if area is not None else None


class ALLSET_OT_graph_channel_scroll(bpy.types.Operator):
    """Scroll the Maya Graph Editor outliner by rows (positive = down the list)"""
    bl_idname = "allset.graph_channel_scroll"
    bl_label = "Graph Editor Outliner Scroll"

    delta: IntProperty(name="Rows", description="Rows to scroll, positive = down the list", default=3,
                       options={'SKIP_SAVE'})

    def execute(self, context):
        space = getattr(context, "space_data", None)
        region = _channels_region(context)
        if not (is_graph(space) and enabled(context)) or region is None:
            return {'PASS_THROUGH'}     # no Maya Graph Editor here: Blender's own channel scrolling
        n = len(rows(context, space))
        ptr = _area_ptr(context)
        old = scroll_offset(context, region, n)
        _scroll[ptr] = clamp_scroll(old + self.delta, n, visible_rows(region))
        region.tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        # a wheel item: only over the outliner pane itself (the curve area keeps Blender's zoom)
        region = getattr(context, "region", None)
        if region is None or region.type != 'CHANNELS':
            return {'PASS_THROUGH'}
        return self.execute(context)


# --- header draws ------------------------------------------------------------------------------------------------

_orig = {}


def _graph_header(self, context):
    if not (enabled(context) and is_graph(context.space_data)):
        return _orig["graph"](self, context)
    layout = self.layout
    layout.template_header()
    draw_menus(layout, context, GE)
    draw_icons(layout, context, GE)
    layout.separator_spacer()
    layout.popover(panel="GRAPH_PT_filters", text="", icon='FILTER')


def _dope_header(self, context):
    if not (enabled(context) and is_dope(context.space_data)):
        return _orig["dope"](self, context)
    layout = self.layout
    layout.template_header()
    draw_menus(layout, context, DS)
    draw_icons(layout, context, DS)
    layout.separator_spacer()
    layout.popover(panel="DOPESHEET_PT_filters", text="", icon='FILTER')


def draw_uv_header(self, context):
    """UV Editor header row (Maya menu bar); False = not a Maya UV Editor (draw Blender's)."""
    if not (enabled(context) and is_uv(context.space_data)):
        return False
    layout = self.layout
    layout.template_header()
    draw_menus(layout, context, UV)
    return True


def draw_uv_tool_header(self, context):
    """UV Editor tool header = Maya's icon row, then Blender's pivot / snapping / soft select."""
    if not (enabled(context) and is_uv(context.space_data)):
        return False
    layout = self.layout
    draw_icons(layout, context, UV)
    layout.separator_spacer()
    bpy.types.IMAGE_HT_header.draw_xform_template(layout, context)
    return True


HEADERS = (("graph", "GRAPH_HT_header", _graph_header), ("dope", "DOPESHEET_HT_header", _dope_header))


def own_draw(cls):
    """The class's own draw: the first of its draw functions once something appended to it (bpy_types
    _GenericUI), else ``draw``."""
    return getattr(cls.draw, "_draw_funcs", [cls.draw])[0]


def patch_headers():
    """Swap only the class's own draw (the first draw function), so UI appended to the header by others (e.g. the
    step 70 toolbar) keeps drawing after it."""
    for key, name, fn in HEADERS:
        funcs = getattr(bpy.types, name)._dyn_ui_initialize()
        if key not in _orig:
            _orig[key] = funcs[0]
        funcs[0] = fn


def unpatch_headers():
    for key, name, _fn in HEADERS:
        if key in _orig:
            getattr(bpy.types, name)._dyn_ui_initialize()[0] = _orig.pop(key)


# --- opening an editor the Maya way ----------------------------------------------------------------------------

def frame_playback_range(context, area):
    """Horizontal view = the playback range from frame 1 (Maya: no frame 0 / out-of-range area at the left)."""
    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
    if region is None or region.width < 2:
        return False
    with context.temp_override(window=context.window, area=area, region=region):
        if area.type == 'GRAPH_EDITOR':
            bpy.ops.graph.view_all()
        bpy.ops.anim.scene_range_frame()
        sc = context.scene
        start = sc.frame_preview_start if sc.use_preview_range else sc.frame_start
        lo, _ = region.view2d.region_to_view(0, 0)
        hi, _ = region.view2d.region_to_view(region.width, 0)
        per_px = (hi - lo) / region.width if hi > lo else 0
        if per_px > 0:
            dx = int(round(((start - 0.5) - lo) / per_px))
            if dx:
                bpy.ops.view2d.pan(deltax=dx, deltay=0)
    return True


def prepare_later(window, ui_type, tries=60):
    """After ``allset.open_editor``: frame the playback range (Graph Editor / Dope Sheet), fold the Dope Sheet to
    object rows (Maya Dopesheet Summary + objects), show the UV Editor's tool header and UV Toolkit. From a timer:
    a new window's regions have no size inside the operator (step 9)."""
    state = {"n": tries}
    ptr = window.as_pointer()

    def tick():
        window = live_refs.window(ptr)     # the pointer, looked up each tick: a closed window crashes (#36)
        if window is None:
            return None
        try:
            area = window.screen.areas[0]
            if area.ui_type != ui_type:
                return None
            space = area.spaces.active
            ctx = bpy.context
            with ctx.temp_override(window=window, area=area):
                if ui_type == 'UV':
                    space.show_region_tool_header = True
                    space.show_region_toolbar = False
                    from ..operators.menu_extras import sidebar_tab_later
                    from .uv_toolkit import CATEGORY
                    sidebar_tab_later(window, CATEGORY)
                    return None
                space.show_region_ui = False    # Maya's Graph Editor / Dope Sheet have no side panel
                if not frame_playback_range(ctx, area):
                    state["n"] -= 1
                    return 0.05 if state["n"] > 0 else None
                if ui_type == 'DOPESHEET':
                    chan = next((r for r in area.regions if r.type == 'CHANNELS'), None)
                    if chan is not None:
                        with ctx.temp_override(window=window, area=area, region=chan):
                            bpy.ops.anim.channels_collapse(all=True)
                    space.dopesheet.show_expanded_summary = True     # Dopesheet Summary open, objects folded
                area.tag_redraw()
        except (ReferenceError, AttributeError, IndexError, RuntimeError):
            return None
        return None

    bpy.app.timers.register(tick, first_interval=0.05)


# --- registration --------------------------------------------------------------------------------------------------

classes = (ALLSET_OT_editor_icon, ALLSET_OT_editor_icon_unavailable, ALLSET_OT_graph_channel_click,
           ALLSET_OT_graph_channel_scroll,
           *_BLENDER.values(), *_BAR.values())
_handle = []


def _redraw_graphs(context):
    for win in context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'GRAPH_EDITOR':
                area.tag_redraw()


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.allset_key_time = StringProperty(
        name="Key Time", description="Maya Stats: the selected keys' time (type a frame, +=5 to move them)",
        get=_stats_get("time"), set=_stats_set("time"))
    bpy.types.Scene.allset_key_value = StringProperty(
        name="Key Value", description="Maya Stats: the selected keys' value (display units, +=5 / *=2 work)",
        get=_stats_get("value"), set=_stats_set("value"))
    bpy.types.WindowManager.allset_show_characters = BoolProperty(
        name="Characters", description="List the character sets with their member attributes (Maya Show > Objects > "
        "Characters)", default=False, options={'SKIP_SAVE'}, update=lambda self, context: _redraw_graphs(context))
    patch_headers()
    _handle.append(bpy.types.SpaceGraphEditor.draw_handler_add(draw_channels, (), 'CHANNELS', 'POST_PIXEL'))


def unregister():
    while _handle:
        bpy.types.SpaceGraphEditor.draw_handler_remove(_handle.pop(), 'CHANNELS')
    unpatch_headers()
    del bpy.types.Scene.allset_key_time
    del bpy.types.Scene.allset_key_value
    del bpy.types.WindowManager.allset_show_characters
    _expanded.clear()
    _scroll.clear()
    _picked["ids"], _picked["sig"] = set(), None
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
