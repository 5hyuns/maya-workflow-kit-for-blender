# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya UV Toolkit: a "UV Toolkit" tab in the UV Editor sidebar.

Order of Maya's toolkit: component icons (Vertex · Edge ·
Face | UV · UV Shell), "N object selected", Pick/Marquee · Drag · Tweak/Marquee, Symmetry, Selection / Transform
Constraint, All · Clear · Inverse, then the folded sections Pinning · Select By Type · Soft Selection · Transform · Create ·
Cut and Sew · Unfold · Align and Snap · Arrange and Layout · UV Sets. Buttons run the UV Editor menu items through
``allset.menu_item`` (same command, undo step and option box as the menu) or the kit's toolkit-only commands
(operators/uv_toolkit_ops.py); items Blender has no counterpart for are greyed with a notice. Stack Similar Shells
matches shells of the same shape onto each other. Transform holds Maya's Pivot / Move / Rotate / Scale areas and
Align and Snap its Snap grid (operators/uv_transform.py).
"""

import bpy

from .. import i18n
from . import notices, uv_toolkit_icons

CATEGORY = "UV Toolkit"
PICK = (("Pick/Marquee", "builtin.select_box"), ("Drag", "builtin.select_circle"), ("Tweak/Marquee", "builtin.select"))
COMPONENTS = (("VERTEX", 'VERTEXSEL', "Vertex"), ("EDGE", 'EDGESEL', "Edge"), ("FACE", 'FACESEL', "Face"))
UVE = "UV Editor"
# button label, UV Editor menu path (relative ones under UV Editor/)
CREATE = ((i18n.mark("Automatic"), "UV/Automatic"), (i18n.mark("Best Plane"), "UV/Best Plane"),
          (i18n.mark("Camera-based"), "UV/Camera-based"), (i18n.mark("Contour Stretch"), "UV/Contour Stretch"),
          (i18n.mark("Cylindrical"), "UV/Cylindrical"), (i18n.mark("Normal-based"), f"{UVE}/Create/Normal-based"),
          (i18n.mark("Planar"), "UV/Planar"), (i18n.mark("Spherical"), "UV/Spherical"))
SELECT_BY_TYPE = (i18n.mark("Back-Facing"), i18n.mark("Front-Facing"), i18n.mark("Overlapping"), i18n.mark("Non-Overlapping"),
                  i18n.mark("Texture Borders"), (i18n.mark("Unmapped"), "Unmapped Faces"))
CUT_SEW = ((i18n.mark("Auto Seams"), "Cut/Sew/Auto Seams"), (i18n.mark("Cut"), "Cut/Sew/Cut"),
           (i18n.mark("Split"), "Cut/Sew/Split"), (i18n.mark("Sew"), "Cut/Sew/Sew"),
           (i18n.mark("Create Shell"), "Cut/Sew/Create UV Shell"),
           (i18n.mark("Create Shell (Grid)"), "Cut/Sew/Create Shell (Grid)"),
           (i18n.mark("Move and Sew"), "Cut/Sew/Move and Sew"),
           (i18n.mark("Stitch Together"), "Cut/Sew/Stitch Together"), (i18n.mark("Merge"), "Cut/Sew/Merge"))
SNAP = ((i18n.mark("Linear Align"), "Modify/Linear Align"), (i18n.mark("Match Grid"), "Modify/Match Grid"),
        (i18n.mark("Match UVs"), "Modify/Match UVs"), (i18n.mark("Snap Together"), "Modify/Snap Together"),
        (i18n.mark("Snap and Stack"), "Modify/Snap and Stack"))
ARRANGE = ((i18n.mark("Distribute"), "Modify/Distribute Shells"),
           (i18n.mark("Gather Shells"), "Modify/Gather Shells"), (i18n.mark("Layout Along"), "Modify/Layout Along"),
           (i18n.mark("Normalize"), "Modify/Normalize"), (i18n.mark("Orient Shells"), "Modify/Orient Shells"),
           (i18n.mark("Orient to Edges"), "Modify/Orient Shells to Edges"),
           (i18n.mark("Randomize"), "Modify/Randomize Shells"), (i18n.mark("Stack"), "Modify/Stack Shells"),
           (i18n.mark("Stack and Orient"), "Modify/Stack and Orient Shells"),
           (i18n.mark("Stack Similar"), "Modify/Stack Similar Shells"),
           (i18n.mark("Unstack"), "Modify/Unstack Shells"), (i18n.mark("Unitize"), "Modify/Unitize"))
ALIGN = (('U', 'MIN', i18n.mark("Min U")), ('U', 'AVG', i18n.mark("Avg U")), ('U', 'MAX', i18n.mark("Max U")),
         ('V', 'MIN', i18n.mark("Min V")), ('V', 'AVG', i18n.mark("Avg V")), ('V', 'MAX', i18n.mark("Max V")))

GREY = {
    "UV Toolkit/Symmetry": (
        "Mirror UVs", "Blender has no UV symmetry selection: select one side, then UV > Mirror."),
    "UV Toolkit/Selection Constraint": (
        "Select menu", "Blender has no UV selection constraint: use Select > Select Linked / Select Split."),
    "UV Toolkit/Transform Constraint": (
        "Snapping", "Blender has no UV transform constraint: use snapping (UV Editor header magnet)."),
    "UV Toolkit/Scale Step Snap": (
        "UV grid step", "Blender's UV Scale tool steps by the UV grid step (the Move Step Snap value); it has no "
        "separate scale step."),
}


def _grey(layout, key, text):
    row = layout.row()
    row.enabled = False
    row.operator("allset.menu_unavailable", text=text, emboss=False).item = key


def _icon(key):
    """The kit picture beside toolkit button ``key`` (its English label), like Maya's toolkit (0 = none)."""
    return uv_toolkit_icons.icon(key)


def _op(layout, idname, text, key=None, **kw):
    """A toolkit button: its picture, then its text."""
    return layout.operator(idname, text=text, icon_value=_icon(key or text), **kw)


def _item(layout, path, text):
    """A UV Editor menu item: the same command, undo step and option box as the menu."""
    _op(layout, "allset.menu_item", text).item = path


def _grid(layout, rows, columns=2):
    """Buttons ``columns`` to a row, in reading order (left to right, then down)."""
    col = layout.column(align=True)
    for i in range(0, len(rows), columns):
        row = col.row(align=True)
        for text, path in rows[i:i + columns]:
            _item(row, path if path.startswith(("UV/", UVE)) else f"{UVE}/{path}", text)


# 3 x 3 button grids (Pivot, Move, Snap): the glyph points at the place / direction
GLYPHS = {'TOP_LEFT': "↖", 'TOP': "↑", 'TOP_RIGHT': "↗", 'LEFT': "←", 'CENTER': "•",
          'RIGHT': "→", 'BOTTOM_LEFT': "↙", 'BOTTOM': "↓", 'BOTTOM_RIGHT': "↘"}
GRID3 = (('TOP_LEFT', 'TOP', 'TOP_RIGHT'), ('LEFT', 'CENTER', 'RIGHT'), ('BOTTOM_LEFT', 'BOTTOM', 'BOTTOM_RIGHT'))
NUDGE = {'TOP_LEFT': 'UP_LEFT', 'TOP': 'UP', 'TOP_RIGHT': 'UP_RIGHT', 'LEFT': 'LEFT', 'RIGHT': 'RIGHT',
         'BOTTOM_LEFT': 'DOWN_LEFT', 'BOTTOM': 'DOWN', 'BOTTOM_RIGHT': 'DOWN_RIGHT'}


def _grid3(layout, op, prop, values=None):
    """Nine buttons of ``op`` (``prop`` = the place, or ``values[place]``; a place without a value stays empty)."""
    col = layout.column(align=True)
    for places in GRID3:
        row = col.row(align=True)
        row.scale_x = 1.2
        for place in places:
            value = place if values is None else values.get(place)
            if value is None:
                row.label(text="")
            else:
                setattr(row.operator(op, text=GLYPHS[place], translate=False), prop, value)
    return col


def _range_fields(layout, tk, prefix):
    for axis in ("u", "v"):
        row = layout.row(align=True)
        row.label(text=axis.upper())
        row.prop(tk, f"{prefix}_min_{axis}", text="")
        row.prop(tk, f"{prefix}_max_{axis}", text="")


def _step_snap(layout, context, kind, prop=None, grey_key=None):
    """Maya's Step Snap row of a Transform area: on / off (the UV Editor tool's step snapping) and its value."""
    from ..operators import snap_align
    on = snap_align.uv_step_snap_on(context.scene.tool_settings, kind)
    row = layout.row(align=True)
    row.label(text="Step Snap:")
    row.operator("allset.uv_step_snap", text="On" if on else "Off", depress=on).kind = kind
    if prop is not None:
        sub = row.row(align=True)
        sub.active = on
        sub.prop(context.scene.allset_uv_toolkit, prop, text="")
    elif grey_key is not None:
        sub = row.row(align=True)
        sub.enabled = False
        sub.operator("allset.menu_unavailable", text="1", emboss=True).item = grey_key


def _preset(layout, prop):
    layout.menu(f"ALLSET_MT_uvtk_preset_{prop}", text="", icon='DOWNARROW_HLT')


def _transform(layout, context):
    """Maya UV Toolkit Transform: Pivot, Move, Rotate, Scale (operators/uv_transform.py)."""
    tk = context.scene.allset_uv_toolkit
    box = layout.box().column()
    box.label(text="Pivot")
    split = box.split(factor=0.42)
    _grid3(split.column(), "allset.uv_pivot", "position")
    col = split.column(align=True)
    col.prop(tk, "pivot_area", expand=True)
    sub = col.column(align=True)
    sub.active = tk.pivot_area == 'UV_AREA'
    _range_fields(sub, tk, "pivot")
    row = box.row(align=True)
    row.operator("allset.uv_pivot_edit", text="Edit Pivot")
    row.operator("allset.uv_pivot_reset", text="Reset")
    box = layout.box().column()
    box.label(text="Move")
    split = box.split(factor=0.42)
    _grid3(split.column(), "allset.uv_nudge", "direction", NUDGE)
    col = split.column(align=True)
    row = col.row(align=True)
    row.prop(tk, "nudge", text="Step")
    _preset(row, "nudge")
    col.prop(tk, "position_u")
    col.prop(tk, "position_v")
    _step_snap(box, context, 'TRANSLATE', "move_snap_value")
    box.prop(tk, "retain_spacing")
    row = box.row(align=True)
    row.operator("allset.uv_distribute_toolkit", text="Distribute")
    row.prop(tk, "distribute_axis", expand=True)
    row.operator("allset.menu_option_box", text="", icon='OPTIONS').item = f"{UVE}/Modify/Distribute UVs"
    box = layout.box().column()
    box.label(text="Rotate")
    row = box.row(align=True)
    row.prop(tk, "rotate_angle", text="")
    _preset(row, "rotate_angle")
    row.operator("allset.uv_rotate_step", text="", icon='LOOP_BACK').clockwise = False
    row.operator("allset.uv_rotate_step", text="", icon='LOOP_FORWARDS').clockwise = True
    _step_snap(box, context, 'ROTATE', "rotate_snap_value")
    box = layout.box().column()
    box.label(text="Scale")
    row = box.row(align=True)
    row.prop(tk, "scale_factor", text="")
    _preset(row, "scale_factor")
    row.operator("allset.uv_scale_step", text="Scale").shrink = False
    row.operator("allset.uv_scale_step", text="Shrink").shrink = True
    box.row(align=True).prop(tk, "scale_axis", expand=True)
    _step_snap(box, context, 'RESIZE', grey_key="UV Toolkit/Scale Step Snap")


def _snap_grid(layout, context):
    """Maya UV Toolkit Snap: the shells of the selection onto a place of the Snap range."""
    tk = context.scene.allset_uv_toolkit
    layout.label(text="Snap")
    split = layout.split(factor=0.42)
    _grid3(split.column(), "allset.uv_snap_shells", "position")
    _range_fields(split.column(align=True), tk, "snap")


def _section(layout, idname, label, default_closed=True):
    header, body = layout.panel(idname, default_closed=default_closed)
    header.label(text=label)
    return body


def current_component(context):
    from ..operators import uv_shell_select
    if uv_shell_select.active(context):
        return 'SHELL'
    ts = context.scene.tool_settings
    if not ts.use_uv_select_sync:
        from .. import compat
        if compat.uv_island_mode(ts):
            return 'SHELL'
        return {'EDGE': 'UV_EDGE', 'FACE': 'UV_FACE'}.get(ts.uv_select_mode, 'UV')
    v, e, f = ts.mesh_select_mode
    return 'FACE' if f and not (v or e) else 'EDGE' if e and not v else 'VERTEX'


def _tool_id(context):
    try:
        tool = context.workspace.tools.from_space_image_mode('UV', create=False)
    except (AttributeError, TypeError):
        return ""
    return tool.idname if tool else ""


class ALLSET_PT_uv_toolkit(bpy.types.Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = CATEGORY
    bl_label = "UV Toolkit"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and space.mode == 'UV'

    def draw(self, context):
        layout = self.layout
        editing = context.mode == 'EDIT_MESH'
        comp = current_component(context) if editing else None
        from . import editor_menu_data, menu_sets
        bar = layout.row(align=True)    # the toolkit's own menu bar: Options / Help
        for i, (title, _items) in enumerate(editor_menu_data.EDITORS["UV Toolkit"]):
            bar.menu(menu_sets.editor_menu_idname("UV Toolkit", i), text=title)
        row = layout.row(align=True)
        row.scale_x = row.scale_y = 1.3
        for mode, icon, label in COMPONENTS:
            row.operator("allset.uv_component", text="", icon=icon, depress=comp == mode).mode = mode
        row.separator()
        for mode, icon in (('UV', 'UV_VERTEXSEL'), ('UV_EDGE', 'UV_EDGESEL'), ('UV_FACE', 'UV_FACESEL')):
            row.operator("allset.uv_component", text="", icon=icon, depress=comp == mode).mode = mode
        row.operator("allset.uv_component", text="", icon='UV_ISLANDSEL', depress=comp == 'SHELL').mode = 'SHELL'
        n = len([o for o in getattr(context, "objects_in_mode_unique_data", ()) if o.type == 'MESH'])
        layout.label(text=f"{n} object{'s' if n != 1 else ''} selected" if editing else "No mesh in edit mode")
        col = layout.column(align=True)
        tid = _tool_id(context)
        for label, tool in PICK:
            op = col.operator("wm.tool_set_by_id", text=label, text_ctxt=i18n.CTX_SELECT_STYLE, depress=tid == tool,
                              icon='RADIOBUT_ON' if tid == tool else 'RADIOBUT_OFF')
            op.name, op.space_type = tool, 'IMAGE_EDITOR'
        for name in ("Symmetry", "Selection Constraint", "Transform Constraint"):
            _grey(layout, f"UV Toolkit/{name}", f"{name}: Off")
        row = layout.row(align=True)
        for label, action in (("All", 'SELECT'), ("Clear", 'DESELECT'), ("Inverse", 'INVERT')):
            row.operator("uv.select_all", text=label).action = action
        if not editing:
            return
        self._sections(layout, context)

    def _sections(self, layout, context):
        s = context.scene.allset_uv
        ts = context.scene.tool_settings
        body = _section(layout, "ALLSET_uvtk_pin", "Pinning")
        if body:
            row = body.row(align=True)
            row.operator("uv.pin", text="Pin")
            row.operator("uv.pin", text="Unpin").clear = True
            row.operator("uv.pin", text="Invert").invert = True
        body = _section(layout, "ALLSET_uvtk_type", "Select By Type")
        if body:
            _grid(body, [(it, f"Select/{it}") if isinstance(it, str) else (it[0], f"Select/{it[1]}")
                         for it in SELECT_BY_TYPE])
        body = _section(layout, "ALLSET_uvtk_soft", "Soft Selection")
        if body:
            body.prop(ts, "use_proportional_edit", text="Soft Select")
            sub = body.column()
            sub.active = ts.use_proportional_edit
            sub.prop(ts, "proportional_size", text="Falloff radius (UV)")
            sub.prop(ts, "proportional_edit_falloff", text="Falloff curve")
        body = _section(layout, "ALLSET_uvtk_transform", "Transform")
        if body:
            _transform(body, context)
            box = body.column(align=True)
            box.label(text="Texel Density (px/unit)")
            box.prop(s, "map_size")
            row = box.row(align=True)
            row.prop(s, "texel_density", text="")
            row.operator("allset.uv_texel_get", text="Get")
            row.operator("allset.uv_texel_set", text="Set")
            row = body.row(align=True)
            op = row.operator("transform.mirror", text="Flip U")
            op.constraint_axis = (True, False, False)
            op = row.operator("transform.mirror", text="Flip V")
            op.constraint_axis = (False, True, False)
        body = _section(layout, "ALLSET_uvtk_create", "Create")
        if body:
            _grid(body, CREATE)
        body = _section(layout, "ALLSET_uvtk_cut", "Cut and Sew", default_closed=False)
        if body:
            _grid(body, CUT_SEW)
            _op(body, "allset.cut_sew_tool_set", text="3D Cut and Sew Tool")
        body = _section(layout, "ALLSET_uvtk_unfold", "Unfold", default_closed=False)
        if body:
            row = body.row(align=True)
            _item(row, f"{UVE}/Modify/Unfold", "Unfold")     # Shift+click: the Unfold options, like the menu
            _item(row, f"{UVE}/Modify/Optimize", "Optimize")
            row = body.row(align=True)
            _op(row, "allset.uv_unfold_along", text="Unfold Along U", key="Unfold Along").axis = 'U'
            _op(row, "allset.uv_unfold_along", text="Unfold Along V", key="Unfold Along").axis = 'V'
            tk = context.scene.allset_uv_toolkit
            from ..operators import uv_toolkit_ops
            split = body.split(factor=0.6, align=True)
            op = _op(split, "allset.uv_straighten_uvs", text="Straighten UVs")
            op.axis, op.tolerance = uv_toolkit_ops.straighten_axis(context), tk.straighten_tolerance
            row = split.row(align=True)
            row.prop(tk, "straighten_u", toggle=True)
            row.prop(tk, "straighten_v", toggle=True)
            body.prop(tk, "straighten_tolerance")
            row = body.row(align=True)
            _item(row, f"{UVE}/Modify/Straighten Shell", "Straighten Shell")
            _item(row, f"{UVE}/Modify/Straighten Border", "Straighten Border")
        body = _section(layout, "ALLSET_uvtk_align", "Align and Snap")
        if body:
            row = body.row(align=True)
            row.label(text="Align")
            for axis, where, label in ALIGN:      # Maya's row of six pictures; the label is the tooltip
                icon = _icon(f"Align {axis} {where}")
                op = row.operator("allset.uv_align_to", text="" if icon else label, icon_value=icon)
                op.axis, op.where = axis, where
            _snap_grid(body, context)
            _grid(body, SNAP)
        body = _section(layout, "ALLSET_uvtk_layout", "Arrange and Layout", default_closed=False)
        if body:
            _item(body, f"{UVE}/Modify/Layout", "Layout")    # the Layout options (padding, map size ...)
            _grid(body, ARRANGE)
        ob = context.edit_object
        body = _section(layout, "ALLSET_uvtk_sets", "UV Sets")
        if body and ob is not None and ob.type == 'MESH':
            me = ob.data
            body.template_list("MESH_UL_uvmaps", "", me, "uv_layers", me.uv_layers, "active_index", rows=2)


classes = (ALLSET_PT_uv_toolkit,)


def register():
    notices.PANEL_NOTICES.update(GREY)
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    uv_toolkit_icons.unregister()
    for key in GREY:
        notices.PANEL_NOTICES.pop(key, None)
