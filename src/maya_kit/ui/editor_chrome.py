# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya editor chrome for the Graph Editor, Dope Sheet and UV Editor.

Maya 2022 checked in a GUI session (, ):

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
stay in a menu at the end of the bar.
"""

import blf
import bpy
import gpu
from bpy.props import StringProperty
from gpu_extras.batch import batch_for_shader

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

BLENDER_MENUS = {GE: "GRAPH_MT_editor_menus", DS: "DOPESHEET_MT_editor_menus", UV: "IMAGE_MT_editor_menus"}


def _blender_menu_class(editor):
    def draw(self, context):
        layout = self.layout
        if editor == DS:
            layout.prop(context.space_data, "ui_mode", text="")
            layout.separator()
        getattr(bpy.types, BLENDER_MENUS[editor]).draw(self, context)
    idname = "MAYAKIT_MT_ed_blender_" + editor.replace(" ", "").lower()
    return type(idname, (bpy.types.Menu,), {"bl_idname": idname, "bl_label": "Blender", "draw": draw,
                                             "__doc__": f"Blender's own {editor} menus"})


def _bar_class(editor):
    def draw(self, context):
        draw_menu_bar(self.layout, context, editor)
    idname = "MAYAKIT_MT_ed_bar_" + editor.replace(" ", "").lower()
    return type(idname, (bpy.types.Menu,), {"bl_idname": idname, "bl_label": "Menus", "draw": draw,
                                             "__doc__": f"The Maya {editor} menus folded into one menu"})


_BLENDER = {ed: _blender_menu_class(ed) for ed in (GE, DS, UV)}
_BAR = {ed: _bar_class(ed) for ed in (GE, DS, UV)}


def draw_menu_bar(layout, context, editor):
    for i, (title, _items) in enumerate(editor_menu_data.EDITORS[editor]):
        layout.menu(menu_sets.editor_menu_idname(editor, i), text=title)
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
    return ("maya_kit.set_tangent", {"kind": kind})


def _inf(side, mode):
    return ("maya_kit.curve_infinity", {"side": side, "mode": mode})


_DSF = "space_data.dopesheet"
GRAPH_ICONS = (
    ("directKeyTool", 'RESTRICT_SELECT_OFF', None, "Move Nearest Picked Key Tool"),
    ("insertKeyTool", 'KEY_HLT', "maya_kit.insert_key_tool", "Insert Keys Tool"),
    ("latticeDeformKeyTool", 'MOD_LATTICE', None, "Lattice Deform Keys"),
    ("regionSelectKeyTool", 'FULLSCREEN_ENTER', "transform.resize", "Region Tool: Scale or move keys"),
    ("retimeKeyTool", 'TIME', None, "Retime Tool: scale and ripple keys"),
    "|", "STATS", "|",
    ("frameAllButton", 'ZOOM_ALL', "graph.view_all", "Frame all"),
    ("frameRangeButton", 'PREVIEW_RANGE', "anim.scene_range_frame", "Frame playback range"),
    ("centerCurrentTimeButton", 'TIME', "maya_kit.graph_center_time", "Center the view about the current time"),
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
    ("graphEditorStackedViewIconButton", 'ALIGN_JUSTIFY', ("maya_kit.graph_view_mode", {"mode": "STACKED"}),
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
    ("getDopeSheetButton", 'ACTION', ("maya_kit.open_editor", {"ui_type": 'DOPESHEET'}), "Open the Dope Sheet"),
    ("getTraxButton", 'NLA', ("maya_kit.open_editor", {"ui_type": 'NLA_EDITOR'}), "Open the Time Editor"),
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
    ("getGraphEditorButton", 'GRAPH', ("maya_kit.open_editor", {"ui_type": 'FCURVES'}), "Open the Graph Editor"),
    ("getTraxButton", 'NLA', ("maya_kit.open_editor", {"ui_type": 'NLA_EDITOR'}), "Open the Time Editor"),
)

_UVE = "space_data.uv_editor"
UV_ICONS = (
    ("viewUVWireframeButton", 'SHADING_WIRE', ("prop", f"{_UVE}.uv_face_opacity", {"value": 0.0}),
     "Display the UVs as wireframe"),
    ("viewShadeUVButton", 'SHADING_SOLID', ("prop", f"{_UVE}.uv_face_opacity", {"value": 1.0}),
     "Shade the UV shells"),
    ("distortionButton", 'MOD_UVPROJECT', ("prop", f"{_UVE}.show_stretch", {}), "Display UV distortion"),
    "|",
    ("toggleTextureBorderButton", 'MOD_EDGESPLIT', None, "Display texture borders"),
    ("toggleShellBorderButton", 'MESH_DATA', None, "Display shell borders"),
    "|",
    ("gridDisplayButton", 'GRID', ("prop", "space_data.overlay.show_grid_background", {}), "Display the grid"),
    ("isolateViewSelectButton", 'HIDE_OFF', None, "Isolate select"),
    "|",
    ("snapShotButton", 'IMAGE_DATA', "uv.export_layout", "UV snapshot"),
    "|",
    ("checkeredButton", 'TEXTURE', "maya_kit.checker_shader", "Checker tiling"),
    "IMAGE",
    ("imageChannelButton", 'IMAGE_RGB_ALPHA', ("channels", "space_data.display_channels", {}), "Image channels"),
    ("dimmerButton", 'LIGHT', None, "Dim the image"),
    "|", "UVMAP",
)

ICONS = {GE: GRAPH_ICONS, DS: DOPE_ICONS, UV: UV_ICONS}

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
            col.prop(scene, "maya_kit_key_time", text="")
            col = sub.row(align=True)
            col.ui_units_x = 3.5
            col.prop(scene, "maya_kit_key_value", text="")
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
        row.operator(MAYAKIT_OT_editor_icon_unavailable.bl_idname, text="", icon=icon).key = f"{editor}|{key}"
        return
    if action[0] == "submenu":
        idname = _submenu(editor, action[1])
        if idname:
            row.menu(idname, text="", icon=icon)
        return
    if action[0] in ("prop", "channels"):
        owner, attr = menu_sets.prop_owner(context, action[1])
        if owner is None:
            row.operator(MAYAKIT_OT_editor_icon_unavailable.bl_idname, text="", icon=icon).key = f"{editor}|{key}"
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
        op = row.operator(menu_sets.MAYAKIT_OT_menu_set_value.bl_idname, text="", icon=icon, depress=on)
        op.target, op.value = action[1], repr(value)
        return
    row.operator(MAYAKIT_OT_editor_icon.bl_idname, text="", icon=icon).key = f"{editor}|{key}"


class MAYAKIT_OT_editor_icon(bpy.types.Operator):
    """Maya editor icon-row button"""
    bl_idname = "maya_kit.editor_icon"
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


class MAYAKIT_OT_editor_icon_unavailable(bpy.types.Operator):
    """Maya editor button without a Blender counterpart (always greyed out)"""
    bl_idname = "maya_kit.editor_icon_unavailable"
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


# --- Graph Editor channel list (Maya outliner pane: object rows, "Translate X" rows) ------------------------------

MAYA_ATTR = {"location": "Translate", "rotation_euler": "Rotate", "scale": "Scale", "rotation_quaternion": "Rotate",
             "delta_location": "Delta Translate", "delta_rotation_euler": "Delta Rotate", "delta_scale": "Delta Scale"}
AXES = "XYZ"
# Maya's default attribute name colours in the Graph Editor outliner (graph_editor_win1.png: Translate X red,
# Translate Y green; Z blue by the same rule as the manipulator / theme axis colours), other attributes light grey.
AXIS_COLOR = ((0.9, 0.25, 0.25, 1.0), (0.25, 0.85, 0.25, 1.0), (0.35, 0.55, 1.0, 1.0))
TEXT = (0.85, 0.85, 0.85, 1.0)
BACK = (0.267, 0.267, 0.267, 1.0)        # Maya outliner pane #444444 (colors.json ui_samples)
SELECT = (0.322, 0.522, 0.651, 1.0)      # Maya selection blue #5285a6 (theme SELECT)
_expanded = {}                           # object name -> bool (Maya shows attributes expanded)


def attr_label(fc):
    """Maya name of an F-curve's attribute: "Translate X", custom properties by name."""
    path, idx = fc.data_path, fc.array_index
    if path.endswith("]") and '["' in path:
        return path.rsplit('["', 1)[1].rstrip('"]')
    tail = path.rsplit(".", 1)[-1]
    if tail in MAYA_ATTR:
        name = MAYA_ATTR[tail]
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
    ad = ob.animation_data
    if ad is None or ad.action is None:
        return []
    act = ad.action
    try:
        from bpy_extras import anim_utils
        bag = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
        if bag is not None:
            return list(bag.fcurves)
    except (ImportError, AttributeError):
        pass
    return list(getattr(act, "fcurves", ()))


def listed_objects(context, space):
    """Objects Blender's Graph Editor lists (animated; only the selected with Only Show Selected), by name."""
    ds = space.dopesheet
    obs = [ob for ob in context.scene.objects if ob.animation_data and ob.animation_data.action]
    if ds.show_only_selected:
        obs = [ob for ob in obs if ob.select_get()]
    if not ds.show_hidden:
        obs = [ob for ob in obs if ob.visible_get()]
    return sorted(obs, key=lambda o: o.name)


def rows(context, space):
    """[(kind, object, fcurve)] of the Maya list: an OBJECT row, then its ATTR rows while expanded."""
    out = []
    flt = (space.dopesheet.filter_text or "").lower()
    for ob in listed_objects(context, space):
        out.append(("OBJECT", ob, None))
        if _expanded.get(ob.name, True):
            for fc in object_curves(ob):
                if flt and flt not in fc.data_path.lower() and flt not in attr_label(fc).lower():
                    continue
                out.append(("ATTR", ob, fc))
    return out


def metrics(region):
    """(top of the first row, row height) in region pixels: Blender keeps its search field at the top."""
    s = bpy.context.preferences.system.ui_scale
    return region.height - round(24 * s), round(20 * s)


def row_at(context, region, y):
    top, h = metrics(region)
    if y > top:
        return None
    k = int((top - y) // h)
    rs = rows(context, context.space_data)
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
    y = top
    for kind, ob, fc in rows(context, space):
        if y < 0:
            break
        sel = (fc.select if fc is not None else ob.select_get())
        if sel:
            _rect(0, y - h, region.width, y, SELECT)
        if kind == "OBJECT":
            sign = "−" if _expanded.get(ob.name, True) else "+"
            blf.color(font, *TEXT)
            blf.position(font, 6 * s, y - h + 6 * s, 0)
            blf.draw(font, sign)
            blf.position(font, 22 * s, y - h + 6 * s, 0)
            blf.draw(font, ob.name)
        else:
            blf.color(font, *attr_color(fc))
            blf.position(font, 44 * s, y - h + 6 * s, 0)
            blf.draw(font, attr_label(fc))
        y -= h
    gpu.state.blend_set('NONE')


def show_rows(context, chosen):
    """Maya: the curves of the selected outliner rows are shown and selected, the others hidden."""
    space = context.space_data
    for ob in listed_objects(context, space):
        for fc in object_curves(ob):
            on = fc in chosen
            fc.select = on
            fc.hide = not on


class MAYAKIT_OT_graph_channel_click(bpy.types.Operator):
    """Maya Graph Editor outliner: click an object (all its curves) or an attribute (that curve); Ctrl toggles,
    Shift adds; the +/- sign folds the attributes"""
    bl_idname = "maya_kit.graph_channel_click"
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
        kind, ob, fc = row
        s = context.preferences.system.ui_scale
        if kind == "OBJECT" and event.mouse_region_x < 18 * s:
            _expanded[ob.name] = not _expanded.get(ob.name, True)
            region.tag_redraw()
            return {'FINISHED'}
        picked = set(object_curves(ob)) if kind == "OBJECT" else {fc}
        current = {c for o in listed_objects(context, context.space_data) for c in object_curves(o)
                   if c.select and not c.hide}
        if event.ctrl:
            chosen = current ^ picked
        elif event.shift:
            chosen = current | picked
        else:
            chosen = picked
        show_rows(context, chosen)
        for area in context.screen.areas:
            if area.type == 'GRAPH_EDITOR':
                area.tag_redraw()
        return {'FINISHED'}


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
    """After ``maya_kit.open_editor``: frame the playback range (Graph Editor / Dope Sheet), fold the Dope Sheet to
    object rows (Maya Dopesheet Summary + objects), show the UV Editor's tool header and UV Toolkit. From a timer:
    a new window's regions have no size inside the operator (step 9)."""
    state = {"n": tries}

    def tick():
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

classes = (MAYAKIT_OT_editor_icon, MAYAKIT_OT_editor_icon_unavailable, MAYAKIT_OT_graph_channel_click,
           *_BLENDER.values(), *_BAR.values())
_handle = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.maya_kit_key_time = StringProperty(
        name="Key Time", description="Maya Stats: the selected keys' time (type a frame, +=5 to move them)",
        get=_stats_get("time"), set=_stats_set("time"))
    bpy.types.Scene.maya_kit_key_value = StringProperty(
        name="Key Value", description="Maya Stats: the selected keys' value (display units, +=5 / *=2 work)",
        get=_stats_get("value"), set=_stats_set("value"))
    patch_headers()
    _handle.append(bpy.types.SpaceGraphEditor.draw_handler_add(draw_channels, (), 'CHANNELS', 'POST_PIXEL'))


def unregister():
    while _handle:
        bpy.types.SpaceGraphEditor.draw_handler_remove(_handle.pop(), 'CHANNELS')
    unpatch_headers()
    del bpy.types.Scene.maya_kit_key_time
    del bpy.types.Scene.maya_kit_key_value
    _expanded.clear()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
