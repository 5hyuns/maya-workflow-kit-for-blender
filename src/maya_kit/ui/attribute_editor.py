# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Attribute Editor in the 3D View sidebar, sharing the Channel Box dock.

; design:  「계획」 1, 3.
- Dock mode (``WindowManager.maya_kit_dock``): the sidebar tabs "Channel Box / Layer
  Editor", "Attribute Editor", "Modeling Toolkit" = the tabs of Maya's right dock
  (, step 99); Ctrl+A toggles
  (``ShowAttributeEditorOrChannelBox``).
- Node tabs (attribute_editor.md:42-61): transform = object, shape = object
  data, one tab per modifier (construction history inputs) and per material.
- Sections and their rows: ``ae_layout`` (Maya template sections, collapse flags
  from ), drawn as ``layout.panel`` sections.
- Joints (step 55): in pose mode the node is the lead pose bone (``channel_box.lead``): a
  ``joint`` tab (ae_layout.JOINT) plus one tab per constraint node, like Maya's
  ``pCube1_parentConstraint1``.
"""

import math

import bpy
from bpy.props import EnumProperty, StringProperty

from ..operators import display
from . import ae_layout
from . import cb_entry, channel_box
from .channel_box import CATEGORY

DOCK_ITEMS = (('CHANNEL_BOX', "Channel Box / Layer Editor", "Maya Channel Box and Layer Editor"),
              ('ATTRIBUTE_EDITOR', "Attribute Editor", "Maya Attribute Editor"),
              ('MODELING_TOOLKIT', "Modeling Toolkit", "Maya Modeling Toolkit (ui/modeling_toolkit.py, step 63)"))


def dock_mode(context):
    return getattr(context.window_manager, "maya_kit_dock", 'CHANNEL_BOX')


# --- tabs ---------------------------------------------------------------------------------

def principled(material):
    if material is None or not material.use_nodes or material.node_tree is None:
        return None
    return next((n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)


def material_type(material):
    """Maya node type of a material: the type a kit-made material recorded (lambert, blinn,
    phong, standardSurface, surfaceShader; operators/material.py), else standardSurface for a
    Principled material, else "material"."""
    if material is None:
        return "material"
    from ..operators.material import TYPE_PROP
    recorded = material.get(TYPE_PROP)
    if isinstance(recorded, str) and recorded in ae_layout.BY_KIND and principled(material):
        return recorded
    return "standardSurface" if principled(material) else "material"


def node_type(ob):
    if ob.type == 'LIGHT':
        return ae_layout.LIGHT_TYPE.get(ob.data.type, "light")
    return ae_layout.NODE_TYPE.get(ob.type, ob.type.lower())


def _constraint_tabs(node):
    return [(f"C:{con.name}", channel_box.constraint_node_name(node, con),
             channel_box.MAYA_CONSTRAINT.get(con.type, con.type.lower()))
            for con in channel_box.constraints(node)]


def tabs(ob):
    """[(key, label, Maya node type)] in Maya's order: transform, shape, history, materials,
    constraints; a joint (pose bone): joint, constraints."""
    if channel_box.is_bone(ob):
        return [("J", ob.name, "joint")] + _constraint_tabs(ob)
    out = [("T", ob.name, "transform")]
    if ob.data is not None:
        out.append(("S", ob.data.name, node_type(ob)))
    for md in ob.modifiers:
        if display.is_preview(md):   # shape display attribute, drawn in "Smooth Mesh" (step 15)
            continue
        out.append((f"M:{md.name}", md.name, md.type.lower()))
    for i, slot in enumerate(ob.material_slots):
        if slot.material is not None:
            out.append((f"MAT:{i}", slot.material.name, material_type(slot.material)))
    if has_nucleus(ob):
        out.append(("NUC", "nucleus1", "nucleus"))     # Maya's shared solver node (operators/fx.py, step 68)
    return out + _constraint_tabs(ob)


def has_nucleus(ob):
    """The kit nucleus exists and ``ob`` is simulated by it (cloth, particles, collider, rigid body)."""
    scene = bpy.context.scene
    nuc = getattr(scene, "maya_kit_nucleus", None)
    if nuc is None or not nuc.exists:
        return False
    return (ob.rigid_body is not None or any(md.type in {'CLOTH', 'COLLISION', 'PARTICLE_SYSTEM', 'SOFT_BODY'}
                                             for md in ob.modifiers))


def _kind(key):
    return key.split(":", 1)[0]


def current_tab(context, ob):
    """The selected tab key: the stored one, else the first of the stored kind, else
    the shape (Maya's preferred node, attribute_editor.md:43-53), else the transform."""
    wm = context.window_manager
    keys = [t[0] for t in tabs(ob)]
    if wm.maya_kit_ae_tab in keys:
        return wm.maya_kit_ae_tab
    for k in keys:
        if _kind(k) == wm.maya_kit_ae_kind:
            return k
    if "J" in keys:
        return "J"
    return "S" if "S" in keys else "T"


def tab_target(ob, key):
    """The datablock or modifier a tab shows."""
    kind = _kind(key)
    if kind in ("T", "J"):
        return ob
    if kind == "C":
        return ob.constraints.get(key[2:])
    if kind == "S":
        return ob.data
    if kind == "M":
        return ob.modifiers.get(key[2:])
    if kind == "MAT":
        i = int(key[4:])
        return ob.material_slots[i].material if i < len(ob.material_slots) else None
    if kind == "NUC":
        return bpy.context.scene.maya_kit_nucleus
    return None


def sections_for(ob, key):
    """(sections, layout id) for a tab; empty for history tabs (drawn generically)."""
    kind = _kind(key)
    if kind == "T":
        return ae_layout.BY_KIND["transform"][0], "transform"
    if kind == "J":
        return ae_layout.BY_KIND["joint"][0], "joint"
    if kind == "S":
        sub = ob.data.type if ob.type == 'LIGHT' else ob.type
        return ae_layout.BY_KIND.get(sub, ([], None))[0], sub.lower()
    if kind == "MAT":
        mat = tab_target(ob, key)
        name = material_type(mat)
        return ae_layout.BY_KIND[name][0], name
    if kind == "NUC":
        return ae_layout.BY_KIND["nucleus"][0], "nucleus"
    return [], None


# --- drawing --------------------------------------------------------------------------------

def resolve(owner, path):
    """(object, attribute) for a dotted path such as ``overlay.show_face_normals``."""
    *head, attr = path.split(".")
    for part in head:
        owner = getattr(owner, part, None)
        if owner is None:
            return None, attr
    return owner, attr


def _owner(context, ob, target, name):
    if name == "ob":
        return ob
    if name == "data":
        return target
    if name == "view":
        space = context.space_data
        return space if space is not None and space.type == 'VIEW_3D' else None
    if channel_box.is_bone(ob):
        return {"bone": ob.bone, "arm": ob.id_data.data, "armob": ob.id_data}.get(name)
    return None


def _length(context, value):
    us = context.scene.unit_settings
    return bpy.utils.units.to_string(us.system, 'LENGTH', value * us.scale_length, precision=3)


def _vector_row(layout, owner, attr, label):
    """Maya AE float3 row: label, then the three fields side by side."""
    split = layout.split(factor=0.3, align=True)
    split.label(text=label)
    split.row(align=True).prop(owner, attr, text="")


def draw_transform_channels(layout, context, ob):
    col = layout.column(align=True)
    _vector_row(col, ob, "location", "Translate")
    if ob.rotation_mode == 'QUATERNION':
        _vector_row(col, ob, "rotation_quaternion", "Rotate")
    elif ob.rotation_mode == 'AXIS_ANGLE':
        _vector_row(col, ob, "rotation_axis_angle", "Rotate")
    else:
        _vector_row(col, ob, "rotation_euler", "Rotate")
    _vector_row(col, ob, "scale", "Scale")


def draw_world_pivot(layout, context, ob):
    col = layout.column(align=True)
    for axis, value in zip("XYZ", ob.matrix_world.translation):
        col.label(text=f"World Rotate Pivot {axis}: {_length(context, value)}")


LIMIT_PROPS = {
    'LIMIT_LOCATION': ("use_min_{a}", "min_{a}", "use_max_{a}", "max_{a}"),
    'LIMIT_SCALE': ("use_min_{a}", "min_{a}", "use_max_{a}", "max_{a}"),
    'LIMIT_ROTATION': ("use_limit_{a}", "min_{a}", "max_{a}"),
}


def draw_limit(layout, context, ob, kind):
    con = next((c for c in ob.constraints if c.type == kind), None)
    if con is None:
        layout.operator("maya_kit.ae_add_limit", text=f"Add {kind.replace('_', ' ').title()}").type = kind
        return
    for a in "xyz":
        row = layout.row(align=True)
        for pattern in LIMIT_PROPS[kind]:
            row.prop(con, pattern.format(a=a))


def draw_visibility(layout, context, ob):
    if channel_box.is_bone(ob):
        layout.prop(ob.bone, "hide", text="Visibility", invert_checkbox=True)
    else:
        layout.prop(ob, "hide_viewport", text="Visibility", invert_checkbox=True)


JOINT_AXIS_NOTE = "Bone Y points to the child joint (Maya Primary Axis X)"


def joint_orient(pb):
    """Maya jointOrient ~ the bone's rest rotation relative to its parent's rest (Euler XYZ)."""
    bone = pb.bone
    rest = bone.matrix_local if bone.parent is None else bone.parent.matrix_local.inverted() @ bone.matrix_local
    return rest.to_euler('XYZ')


def draw_joint_orient(layout, context, pb):
    split = layout.split(factor=0.3, align=True)
    split.label(text="Joint Orient")
    row = split.row(align=True)
    for v in joint_orient(pb):
        row.label(text=cb_entry.fmt_number(math.degrees(v)))   # Maya numbers: no "-0"
    note = layout.row()
    note.active = False
    note.label(text=JOINT_AXIS_NOTE)


def draw_joint_stiffness(layout, context, pb):
    split = layout.split(factor=0.3, align=True)
    split.label(text="Stiffness")
    row = split.row(align=True)
    for a in "xyz":
        row.prop(pb, f"ik_stiffness_{a}", text="")


def draw_shading(layout, context, ob):
    row = layout.row(align=True)
    row.operator("object.shade_smooth", text="Soften (Smooth)")
    row.operator("object.shade_flat", text="Harden (Flat)")
    layout.operator("object.shade_auto_smooth", text="Soften by Angle")


def draw_smooth_mesh(layout, context, ob):
    row = layout.row(align=True)
    for level, label in ((1, "1 Off"), (2, "2 Cage"), (3, "3 Smooth")):
        row.operator("maya_kit.smooth_preview", text=label).level = level
    sub = display.preview_modifier(ob, create=False)
    if sub is not None:
        layout.prop(sub, "levels", text="Division Levels")
        layout.prop(sub, "render_levels", text="Render Levels")


DRAWERS = {"transform_channels": draw_transform_channels, "world_pivot": draw_world_pivot,
           "visibility": draw_visibility, "shading": draw_shading, "smooth_mesh": draw_smooth_mesh,
           "joint_orient": draw_joint_orient, "joint_stiffness": draw_joint_stiffness}


def draw_row(layout, context, ob, target, row):
    kind = row[0]
    if kind == "prop":
        _k, owner_name, path, label = row
        owner, attr = resolve(_owner(context, ob, target, owner_name), path)
        if owner is not None and hasattr(owner, attr):
            layout.prop(owner, attr, text=label)
    elif kind == "draw":
        name = row[1]
        if name.startswith("limit:"):
            draw_limit(layout, context, ob, name[6:])
        else:
            DRAWERS[name](layout, context, ob)
    elif kind == "socket":
        _k, socket, label = row
        node = principled(target)
        inp = node.inputs.get(socket) if node is not None else None
        if inp is None:
            return
        row = layout.row(align=True)
        if inp.is_linked:
            source = inp.links[0].from_node
            row.label(text=f"{label}: connected ({source.name})")
        elif hasattr(inp, "default_value"):
            row.prop(inp, "default_value", text=label)
        else:
            row.label(text=label)
        # Maya's map (checker) button: Create Render Node / Break Connection (operators/shading_maps.py, step 67)
        op = row.operator("maya_kit.ae_map", text="", icon='TEXTURE')
        op.material, op.socket = target.name, socket
        if inp.is_linked and source.type == 'TEX_IMAGE':
            # Maya file node's Image Name with its folder button
            layout.template_ID(source, "image", new="image.new", open="image.open")
    elif kind == "missing":
        _k, label, note = row
        sub = layout.row()
        sub.enabled = False
        sub.label(text=f"{label}: {note}")


def draw_sections(layout, context, ob, target, sections, layout_id, prefix=""):
    for sec in sections:
        header, body = layout.panel(f"maya_kit_ae_{layout_id}_{prefix}{sec.name}",
                                    default_closed=not sec.open)
        header.label(text=sec.name)
        if body is None:
            continue
        col = body.column()
        for row in sec.rows:
            draw_row(col, context, ob, target, row)
        if sec.subs:
            draw_sections(col, context, ob, target, sec.subs, layout_id, f"{prefix}{sec.name}/")


# RNA properties of every modifier that are not the node's own attributes.
_MOD_SKIP = {"rna_type", "name", "type", "show_viewport", "show_render", "show_in_editmode",
             "show_on_cage", "show_expanded", "is_active", "is_override_data_editable",
             "use_apply_on_spline", "use_pin_to_last", "persistent_uid", "execution_time"}


def modifier_props(md):
    out = []
    for p in md.bl_rna.properties:
        ident = p.identifier
        if ident in _MOD_SKIP or p.is_readonly or p.type == 'COLLECTION' or ident.startswith("open_"):
            continue
        out.append(ident)
    return out


def draw_history(layout, context, ob, md):
    header, body = layout.panel(f"maya_kit_ae_history_{md.type}", default_closed=False)
    header.label(text=f"{md.type.replace('_', ' ').title()} History")
    if body is not None:
        col = body.column()
        col.prop(md, "show_viewport", text="Enabled (Node State)")
        for ident in modifier_props(md):
            col.prop(md, ident)
    row = layout.row(align=True)
    op = row.operator("maya_kit.ae_modifier", text="Delete History")
    op.modifier, op.action = md.name, 'APPLY'
    op = row.operator("maya_kit.ae_modifier", text="Delete", icon='X')
    op.modifier, op.action = md.name, 'REMOVE'


# Constraint properties that are not the Maya constraint node's own attributes.
_CON_SKIP = {"rna_type", "name", "type", "show_expanded", "is_valid", "active", "is_override_data_editable",
             "is_override_data_local", "mute", "enabled", "influence", "error_location", "error_rotation"}


def constraint_props(con):
    return [p.identifier for p in con.bl_rna.properties
            if p.identifier not in _CON_SKIP and not p.is_readonly and p.type != 'COLLECTION']


def draw_constraint(layout, context, node, con):
    """A Maya constraint node tab: target weight (= influence), then the constraint's settings."""
    header, body = layout.panel(f"maya_kit_ae_constraint_{con.type}", default_closed=False)
    header.label(text=f"{channel_box.MAYA_CONSTRAINT.get(con.type, con.type.title())} Attributes")
    if body is not None:
        col = body.column()
        if hasattr(con, "enabled"):
            col.prop(con, "enabled", text="Enabled (Node State)")
        col.prop(con, "influence", text=channel_box.weight_name(con))
        for ident in constraint_props(con):
            col.prop(con, ident)


def draw_extra(layout, owner, layout_id):
    keys = [k for k in owner.keys() if not k.startswith(("_", "maya_kit_", "cycles"))]
    header, body = layout.panel(f"maya_kit_ae_{layout_id}_extra", default_closed=True)
    header.label(text="Extra Attributes")
    if body is None:
        return
    if not keys:
        body.label(text="(none)")
    for k in sorted(keys):
        body.prop(owner, f'["{k}"]', text=k)


def draw_tab_strip(layout, context, ob, current):
    row = layout.row(align=True)
    for key, label, _type in tabs(ob):
        op = row.operator("maya_kit.ae_tab", text=label, depress=(key == current))
        op.key = key


def draw(layout, context, ob):
    """The whole Attribute Editor for ``ob`` (also used by tests with a fake layout)."""
    key = current_tab(context, ob)
    draw_tab_strip(layout, context, ob, key)
    target = tab_target(ob, key)
    if target is None:
        return
    label = next(t[2] for t in tabs(ob) if t[0] == key)
    head = layout.row(align=True)
    head.label(text=f"{label}:")
    if _kind(key) == "NUC":
        head.label(text="nucleus1")
        from . import chrome
        chrome.paragraph(layout, context, ae_layout.NUCLEUS_NOTE)
        draw_sections(layout, context, ob, target, ae_layout.NUCLEUS, "nucleus")
        return
    head.prop(target, "name", text="")
    if _kind(key) == "C":
        draw_constraint(layout, context, ob, target)
        return
    if _kind(key) == "M":
        sub = head.row(align=True)
        sub.operator("maya_kit.ae_step", text="", icon='TRIA_LEFT').forward = False
        sub.operator("maya_kit.ae_step", text="", icon='TRIA_RIGHT').forward = True
        draw_history(layout, context, ob, target)
        return
    sections, layout_id = sections_for(ob, key)
    draw_sections(layout, context, ob, target, sections, layout_id or "data")
    if isinstance(target, (bpy.types.ID, bpy.types.PoseBone)):
        draw_extra(layout, target, layout_id or "data")
    if _kind(key) == "T":
        layout.operator("maya_kit.ae_select", text="Select")


# --- operators -----------------------------------------------------------------------------

def set_tab(context, key):
    wm = context.window_manager
    wm.maya_kit_ae_tab = key
    wm.maya_kit_ae_kind = _kind(key)


class MAYAKIT_OT_ae_tab(bpy.types.Operator):
    """Show this node in the Attribute Editor"""
    bl_idname = "maya_kit.ae_tab"
    bl_label = "Attribute Editor Tab"
    bl_options = {'INTERNAL'}

    key: StringProperty()

    def execute(self, context):
        set_tab(context, self.key)
        _redraw(context)
        return {'FINISHED'}


class MAYAKIT_OT_ae_step(bpy.types.Operator):
    """Go to the next input (left) or output (right) node in the history (Maya in/out arrows)"""
    bl_idname = "maya_kit.ae_step"
    bl_label = "Input / Output Node"
    bl_options = {'INTERNAL'}

    forward: bpy.props.BoolProperty()

    def execute(self, context):
        ob = context.active_object
        if ob is None:
            return {'CANCELLED'}
        keys = [t[0] for t in tabs(ob) if _kind(t[0]) == "M"]
        cur = current_tab(context, ob)
        if cur not in keys:
            return {'CANCELLED'}
        i = keys.index(cur) + (1 if self.forward else -1)
        if 0 <= i < len(keys):
            set_tab(context, keys[i])
        _redraw(context)
        return {'FINISHED'}


class MAYAKIT_OT_ae_modifier(bpy.types.Operator):
    """Delete History: apply this modifier (keep its effect, drop the node); Delete: remove it"""
    bl_idname = "maya_kit.ae_modifier"
    bl_label = "History Node"
    bl_options = {'REGISTER', 'UNDO'}

    modifier: StringProperty()
    action: EnumProperty(items=(('APPLY', "Apply", ""), ('REMOVE', "Remove", "")))

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object is not None

    def execute(self, context):
        ob = context.active_object
        md = ob.modifiers.get(self.modifier)
        if md is None:
            return {'CANCELLED'}
        if self.action == 'REMOVE':
            ob.modifiers.remove(md)
            return {'FINISHED'}
        with context.temp_override(object=ob, active_object=ob):
            return bpy.ops.object.modifier_apply(modifier=self.modifier)


class MAYAKIT_OT_ae_add_limit(bpy.types.Operator):
    """Add a limit constraint (Maya Limit Information)"""
    bl_idname = "maya_kit.ae_add_limit"
    bl_label = "Add Limit"
    bl_options = {'REGISTER', 'UNDO'}

    type: EnumProperty(items=[(k, k.replace('_', ' ').title(), "") for k in LIMIT_PROPS])

    @classmethod
    def poll(cls, context):
        return channel_box.lead(context) is not None

    def execute(self, context):
        con = channel_box.lead(context).constraints.new(self.type)   # a joint: the pose bone
        con.owner_space = 'LOCAL'   # Maya limits act on the channel values
        return {'FINISHED'}


class MAYAKIT_OT_ae_select(bpy.types.Operator):
    """Select only the node shown in the Attribute Editor"""
    bl_idname = "maya_kit.ae_select"
    bl_label = "Select"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object is not None

    def execute(self, context):
        ob = context.active_object
        for o in context.selected_objects:
            o.select_set(False)
        ob.select_set(True)
        return {'FINISHED'}


def _show_sidebar_later(space):
    # Setting a region flag inside an operator doesn't stick (step 9): use a timer.
    def later():
        try:
            space.show_region_ui = True
        except ReferenceError:
            pass
        return None
    bpy.app.timers.register(later, first_interval=0.0)


class MAYAKIT_OT_ae_toggle(bpy.types.Operator):
    """Switch the dock between Channel Box / Layer Editor and Attribute Editor
    (Maya Ctrl+A)"""
    bl_idname = "maya_kit.ae_toggle"
    bl_label = "Attribute Editor / Channel Box"

    def execute(self, context):
        wm = context.window_manager
        wm.maya_kit_dock = 'CHANNEL_BOX' if wm.maya_kit_dock == 'ATTRIBUTE_EDITOR' else 'ATTRIBUTE_EDITOR'
        space = context.space_data
        if space is not None and space.type == 'VIEW_3D' and not space.show_region_ui:
            _show_sidebar_later(space)
        _redraw(context)
        return {'FINISHED'}


class MAYAKIT_OT_dock_show(bpy.types.Operator):
    """Show the Attribute Editor or the Channel Box / Layer Editor in the sidebar dock
    (Maya Windows > General Editors)"""
    bl_idname = "maya_kit.dock_show"
    bl_label = "Show Dock Editor"

    dock: EnumProperty(items=DOCK_ITEMS, name="Editor")

    def execute(self, context):
        context.window_manager.maya_kit_dock = self.dock
        space = context.space_data
        if space is not None and space.type == 'VIEW_3D' and not space.show_region_ui:
            _show_sidebar_later(space)
        _redraw(context)
        return {'FINISHED'}


class MAYAKIT_OT_object_attributes(bpy.types.Operator):
    """Show this object in the Attribute Editor (Maya RMB menu "<object>...", showEditor:
    Maya)"""
    bl_idname = "maya_kit.object_attributes"
    bl_label = "Object Attributes"

    rmb: bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'},
                                description="The object the RMB menu was opened on")

    @staticmethod
    def _object(context, rmb):
        if rmb:
            ob = bpy.data.objects.get(getattr(context.window_manager, "maya_kit_mm_target", ""))
            if ob is not None:
                return ob
        return context.active_object

    @classmethod
    def poll(cls, context):
        return cls._object(context, True) is not None

    def execute(self, context):
        ob = self._object(context, self.rmb)
        if ob is None:
            return {'CANCELLED'}
        if context.active_object is not ob:
            try:   # Maya shows the node without changing the selection; the AE here shows the active object
                ob.select_get(view_layer=context.view_layer)
                context.view_layer.objects.active = ob
            except RuntimeError:
                return {'CANCELLED'}
        return bpy.ops.maya_kit.dock_show(dock='ATTRIBUTE_EDITOR')


def _redraw(context):
    screen = context.screen
    for area in (screen.areas if screen else ()):
        if area.type == 'VIEW_3D':
            area.tag_redraw()


# --- panels ----------------------------------------------------------------------------------

# --- dock tabs (step 99) ----------------------------------------------------------------------
# Maya's dock tabs are the sidebar's own vertical category tabs (Blender draws them on the region's outer edge,
# like Maya's tab stack, ). WindowManager.maya_kit_dock stays the dock state
# the rest of the kit reads and sets (Ctrl+A, Windows menu, RMB "<object>..."): setting it switches the tabs
# (update), and a timer makes it follow a tab the user clicked.

DOCK_CATEGORIES = {'CHANNEL_BOX': channel_box.CATEGORY, 'ATTRIBUTE_EDITOR': channel_box.AE_CATEGORY,
                   'MODELING_TOOLKIT': channel_box.MTK_CATEGORY}
_CATEGORY_DOCK = {v: k for k, v in DOCK_CATEGORIES.items()}
_seen = {}          # UI region pointer -> category at the last sync tick
SYNC_TICK = 0.2


def _dock_regions(context):
    """Sidebars that show the dock (or nothing / Item yet): not the Light Editor's or other kit tabs."""
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != 'VIEW_3D' or not area.spaces.active.show_region_ui:
                continue
            for region in area.regions:
                if region.type == 'UI' and region.width > 1:
                    cat = region.active_panel_category
                    if cat in _CATEGORY_DOCK or cat in ("", "Item"):
                        yield area, region


def show_dock_category(context, dock):
    category = DOCK_CATEGORIES.get(dock, channel_box.CATEGORY)
    for area, region in _dock_regions(context):
        try:
            region.active_panel_category = category
        except (TypeError, AttributeError):   # "read-only" until the region has drawn its tabs: the timer retries
            pass
        _seen[region.as_pointer()] = region.active_panel_category
        area.tag_redraw()


def _dock_update(self, context):
    show_dock_category(context, self.maya_kit_dock)


def _sync_tick():
    """A tab the user clicked becomes maya_kit_dock; a sidebar that missed a switch (no tabs yet) gets it."""
    try:
        context = bpy.context
        wm = context.window_manager
        want = DOCK_CATEGORIES.get(wm.maya_kit_dock, channel_box.CATEGORY)
        for area, region in list(_dock_regions(context)):
            key = region.as_pointer()
            cat = region.active_panel_category
            if cat == want:
                _seen[key] = cat
                continue
            prev = _seen.get(key)
            if prev is not None and cat != prev:   # changed since the last tick: the user clicked a tab
                _seen[key] = cat
                if cat in _CATEGORY_DOCK:
                    wm.maya_kit_dock = _CATEGORY_DOCK[cat]
                    return SYNC_TICK
                continue   # Blender's Item tab (a C panel the kit can't hide): leave it open
            if cat == "Item" and prev == "Item":
                continue
            try:
                region.active_panel_category = want
                area.tag_redraw()
            except (TypeError, AttributeError):
                pass
            _seen[key] = region.active_panel_category
    except Exception:   # a timer that raises is dropped: keep it running
        pass
    return SYNC_TICK


def draw_panel(layout, context):
    """The Attribute Editor body of the dock (``channel_box.MAYAKIT_PT_dock_attribute_editor``)."""
    if channel_box.placing_joints(context):
        from . import chrome
        chrome.wrapped(layout, channel_box.PLACING_TEXT)
        return
    ob = channel_box.lead(context)
    if ob is None:
        layout.label(text="make a selection")
        return
    draw(layout, context, ob)


classes = (MAYAKIT_OT_ae_tab, MAYAKIT_OT_ae_step, MAYAKIT_OT_ae_modifier, MAYAKIT_OT_ae_add_limit,
           MAYAKIT_OT_ae_select, MAYAKIT_OT_ae_toggle, MAYAKIT_OT_dock_show, MAYAKIT_OT_object_attributes)


def register():
    wm = bpy.types.WindowManager
    wm.maya_kit_dock = EnumProperty(name="Dock", items=DOCK_ITEMS, options={'SKIP_SAVE'}, update=_dock_update)
    wm.maya_kit_ae_tab = StringProperty(options={'SKIP_SAVE'})
    wm.maya_kit_ae_kind = StringProperty(default="S", options={'SKIP_SAVE'})
    for cls in classes:
        bpy.utils.register_class(cls)
    if not bpy.app.background and not bpy.app.timers.is_registered(_sync_tick):
        bpy.app.timers.register(_sync_tick, first_interval=SYNC_TICK, persistent=True)


def unregister():
    if bpy.app.timers.is_registered(_sync_tick):
        bpy.app.timers.unregister(_sync_tick)
    _seen.clear()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    wm = bpy.types.WindowManager
    del wm.maya_kit_ae_kind
    del wm.maya_kit_ae_tab
    del wm.maya_kit_dock
