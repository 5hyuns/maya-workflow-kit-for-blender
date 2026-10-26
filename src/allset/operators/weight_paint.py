# SPDX-License-Identifier: GPL-3.0-or-later
"""Paint Skin Weights workspace: native brush tools and configurable weight operations."""
from contextlib import contextmanager

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty, StringProperty

from .. import compat
from . import skin

# Each native operation keeps its own settings, including all scalar operator options.
ACTIONS = {
    'SET': ('Set Weight', 'paint.weight_set'),
    'NORMALIZE_ALL': ('Normalize All', 'object.vertex_group_normalize_all'),
    'NORMALIZE': ('Normalize Influence', 'object.vertex_group_normalize'),
    'MIRROR': ('Mirror Weights', 'object.vertex_group_mirror'),
    'INVERT': ('Invert Weights', 'object.vertex_group_invert'),
    'CLEAN': ('Prune Small Weights', 'object.vertex_group_clean'),
    'QUANTIZE': ('Quantize Weights', 'object.vertex_group_quantize'),
    'LEVELS': ('Weight Levels', 'object.vertex_group_levels'),
    'SMOOTH': ('Smooth Weights', 'object.vertex_group_smooth'),
    'LIMIT': ('Limit Influences', 'object.vertex_group_limit_total'),
    'TRANSFER': ('Transfer Weights', 'object.data_transfer'),
    'AUTO': ('Automatic Weights', 'paint.weight_from_bones'),
    'ENVELOPE': ('Bone Envelope Weights', 'paint.weight_from_bones'),
}
SCOPE = [('ACTIVE', 'Active influence', 'Only the active vertex group'),
         ('BONE_SELECT', 'Selected joints', 'Groups belonging to selected pose bones'),
         ('BONE_DEFORM', 'Deform joints', 'All deforming bone groups'),
         ('ALL', 'All groups', 'All vertex groups, including non-joint groups')]
TRANSFER_FIELDS = {'vert_mapping', 'use_create', 'use_object_transform', 'use_auto_transform',
                   'use_max_distance', 'max_distance', 'ray_radius', 'layers_select_src',
                   'layers_select_dst', 'mix_mode', 'mix_factor'}


def native(name):
    module, op = name.split('.')
    return getattr(getattr(bpy.ops, module), op)


def _annotation(prop, action):
    kw = {'name': prop.name, 'description': prop.description}
    if prop.identifier == 'group_select_mode':
        return EnumProperty(**kw, items=SCOPE[1:] if action in {'NORMALIZE_ALL', 'LIMIT'} else SCOPE,
                            default='BONE_DEFORM' if action in {'NORMALIZE_ALL', 'LIMIT'} else 'ACTIVE')
    if prop.type == 'BOOLEAN':
        return BoolProperty(**kw, default=prop.default)
    if prop.type in {'INT', 'FLOAT'} and not prop.is_array:
        kw.update(default=prop.default, min=prop.hard_min, max=prop.hard_max)
        return (IntProperty if prop.type == 'INT' else FloatProperty)(**kw)
    if prop.type == 'ENUM':
        items = [(e.identifier, e.name, e.description) for e in prop.enum_items if e.identifier]
        if items and not prop.is_enum_flag:
            return EnumProperty(**kw, items=items, default=prop.default)
    return None


_SETTING_CLASSES = []
_FIELDS = {}
for _key, (_label, _op) in ACTIONS.items():
    _ann = {}
    for _p in native(_op).get_rna_type().properties:
        if _p.identifier == 'rna_type' or (_key == 'TRANSFER' and _p.identifier not in TRANSFER_FIELDS):
            continue
        _a = _annotation(_p, _key)
        if _a is not None:
            _ann[_p.identifier] = _a
    if _key == 'TRANSFER':
        _ann['source'] = PointerProperty(name='Source mesh', type=bpy.types.Object,
                                        poll=lambda self, ob: ob.type == 'MESH')
    _FIELDS[_key] = tuple(_ann)
    _SETTING_CLASSES.append(type('ALLSET_PG_weight_' + _key.lower(), (bpy.types.PropertyGroup,),
                                {'__annotations__': _ann, '__module__': __name__}))


def _normalize_get(self):
    return bpy.context.tool_settings.use_auto_normalize


def _normalize_set(self, value):
    bpy.context.tool_settings.use_auto_normalize = value
    mesh = bpy.context.active_object
    if mesh is not None and mesh.type == 'MESH':
        mesh[skin.NORMALIZE_PROP] = 'INTERACTIVE' if value else 'NONE'


class ALLSET_PG_weight_workspace(bpy.types.PropertyGroup):
    search: StringProperty(name='Find influence', options={'TEXTEDIT_UPDATE'})
    sort: EnumProperty(name='Sort', items=[('HIERARCHY', 'Hierarchy', 'Joint hierarchy order'),
                                         ('NAME', 'Name', 'Alphabetical order'),
                                         ('INDEX', 'Group order', 'Vertex group order')], default='HIERARCHY')
    show_all: BoolProperty(name='Include non-joint groups', default=False)
    locked_only: BoolProperty(name='Locked influences only', default=False)
    auto_normalize: BoolProperty(name='Auto normalize',
                                 description='Keep deform weights normalized while painting; remembered for this skin',
                                 get=_normalize_get, set=_normalize_set)
    # Tool Settings frames in Maya 2024+ order (Skin Clusters / Influences / Brush / Visualization / Stroke /
    # Stylus Pressure / Display), then the Blender-only extras (ui/paint_weights.SECTIONS)
    show_skin_clusters: BoolProperty(default=True)
    show_influences: BoolProperty(default=True)
    show_brush: BoolProperty(default=True)
    show_visualization: BoolProperty(default=False)
    show_stroke: BoolProperty(default=False)
    show_pressure: BoolProperty(default=False)
    show_display: BoolProperty(default=False)
    show_commands: BoolProperty(default=False)
    show_mask: BoolProperty(default=False)
    status: StringProperty(default='')
    __annotations__.update({key.lower(): PointerProperty(type=cls)
                            for key, cls in zip(ACTIONS, _SETTING_CLASSES)})


def state(context):
    return context.window_manager.allset_weight_workspace


def active(context):
    ob = context.active_object
    return context.mode == 'PAINT_WEIGHT' and ob is not None and ob.type == 'MESH'


@contextmanager
def viewport(context):
    from ..ui.status_line import main_view3d
    area, region = main_view3d(context.screen)
    if area is None or region is None:
        raise RuntimeError('Open a 3D View to paint skin weights')
    with context.temp_override(window=context.window, area=area, region=region):
        yield bpy.context


def brush_kind(brush):
    return getattr(brush, 'weight_brush_type', getattr(brush, 'weight_tool', 'DRAW')) if brush else ''


def brush_tool(context, kind):
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as tools
    ids = [t.idname for entry in tools.tools_from_context(context)
           for t in (entry if type(entry) is tuple else (entry,)) if t is not None]
    suffix = {'BLUR': 'blur', 'AVERAGE': 'average', 'SMEAR': 'smear'}.get(kind)
    return next((name for name in ids if suffix and name.lower() == 'builtin_brush.' + suffix), 'builtin.brush')


def activate_brush(context, kind='DRAW', blend=None):
    with viewport(context) as ctx:
        bpy.ops.wm.tool_set_by_id(name=brush_tool(ctx, kind))
        brush = ctx.tool_settings.weight_paint.brush
        if brush is None or brush_kind(brush) != kind:
            asset = {'DRAW': 'Paint', 'BLUR': 'Blur', 'AVERAGE': 'Average', 'SMEAR': 'Smear'}[kind]
            bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',
                relative_asset_identifier='brushes/essentials_brushes-mesh_weight.blend/Brush/' + asset)
            brush = ctx.tool_settings.weight_paint.brush
        if brush is None or brush_kind(brush) != kind:
            raise RuntimeError('Choose a compatible weight brush from Brush Assets')
        if blend is not None and not skin._brush_set(brush, 'blend', blend):
            raise RuntimeError('This brush is read-only; make an editable copy from Brush Assets')
        return brush


class ALLSET_OT_weight_tool(bpy.types.Operator):
    bl_idname = 'allset.weight_tool'
    bl_label = 'Weight Paint Tool'
    bl_options = {'REGISTER', 'UNDO'}
    kind: StringProperty(default='DRAW')
    blend: StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        return {'ASSETS': 'Browse Blender weight-paint brush assets',
                'DRAW': 'Paint weights with the chosen blend operation',
                'BLUR': 'Smooth weights across neighboring vertices',
                'AVERAGE': 'Paint the average weight under the brush',
                'SMEAR': 'Drag weights along the direction of your stroke',
                'LINEAR': 'Drag in the viewport to paint a linear weight gradient',
                'RADIAL': 'Drag in the viewport to paint a radial weight gradient',
                'SAMPLE': 'Click the mesh to sample its weight into Value',
                'SAMPLE_GROUP': 'Click the mesh to choose an influence under the cursor'}.get(properties.kind, 'Weight Paint Tool')

    @classmethod
    def poll(cls, context):
        return active(context)

    def execute(self, context):
        try:
            if self.kind == 'ASSETS':
                with viewport(context):
                    bpy.ops.wm.call_asset_shelf_popover('INVOKE_DEFAULT', name='VIEW3D_AST_brush_weight_paint')
            elif self.kind in {'DRAW', 'BLUR', 'AVERAGE', 'SMEAR'}:
                activate_brush(context, self.kind, self.blend or None)
            else:
                tool = {'LINEAR': 'builtin.gradient', 'RADIAL': 'builtin.gradient',
                        'SAMPLE': 'builtin.sample_weight', 'SAMPLE_GROUP': 'builtin.sample_vertex_group'}[self.kind]
                with viewport(context) as ctx:
                    bpy.ops.wm.tool_set_by_id(name=tool)
                    if self.kind in {'LINEAR', 'RADIAL'}:
                        current = ctx.workspace.tools.from_space_view3d_mode('PAINT_WEIGHT', create=False)
                        current.operator_properties('paint.weight_gradient').type = self.kind
            state(context).status = ''
            return {'FINISHED'}
        except (RuntimeError, TypeError, ValueError, KeyError) as ex:
            self.report({'WARNING'}, str(ex))
            return {'CANCELLED'}


class ALLSET_OT_weight_value(bpy.types.Operator):
    bl_idname = 'allset.weight_value'
    bl_label = 'Set Paint Value'
    bl_options = {'UNDO', 'INTERNAL'}
    value: FloatProperty(min=0, max=1)

    @classmethod
    def poll(cls, context):
        return active(context)

    def execute(self, context):
        ups = compat.unified_paint_settings(context.tool_settings)
        brush = context.tool_settings.weight_paint.brush
        owner = ups if ups.use_unified_weight or brush is None else brush
        owner.weight = self.value
        return {'FINISHED'}


class ALLSET_OT_weight_mask(bpy.types.Operator):
    bl_idname = 'allset.weight_mask'
    bl_label = 'Weight Paint Selection'
    bl_options = {'REGISTER', 'UNDO'}
    action: StringProperty(default='ALL')

    @classmethod
    def poll(cls, context):
        return active(context)

    def execute(self, context):
        mesh = context.active_object.data
        if not (mesh.use_paint_mask or mesh.use_paint_mask_vertex):
            mesh.use_paint_mask_vertex = True
        prefix = 'vert' if mesh.use_paint_mask_vertex else 'face'
        try:
            with viewport(context):
                if self.action in {'ALL', 'NONE', 'INVERT'}:
                    native('paint.' + prefix + '_select_all')(
                        action={'ALL': 'SELECT', 'NONE': 'DESELECT', 'INVERT': 'INVERT'}[self.action])
                elif self.action in {'BOX', 'CIRCLE', 'LASSO'}:
                    native('view3d.select_' + self.action.lower())('INVOKE_DEFAULT')
                elif self.action == 'REVEAL':
                    bpy.ops.paint.face_vert_reveal()
                elif self.action in {'HIDE', 'HIDE_OTHER'}:
                    native('paint.' + prefix + '_select_hide')(unselected=self.action == 'HIDE_OTHER')
                else:
                    suffix = {'GROW': 'more', 'SHRINK': 'less', 'LINKED': 'linked', 'UNGROUPED': 'ungrouped'}[self.action]
                    native('paint.' + prefix + '_select_' + suffix)()
            return {'FINISHED'}
        except (RuntimeError, KeyError) as ex:
            self.report({'WARNING'}, str(ex))
            return {'CANCELLED'}


class ALLSET_OT_weight_curve(bpy.types.Operator):
    bl_idname = 'allset.weight_curve'
    bl_label = 'Draw Paint Curve'

    def execute(self, context):
        with viewport(context):
            if not bpy.ops.paintcurve.draw.poll():
                self.report({'WARNING'}, 'Create a Paint Curve before drawing it')
                return {'CANCELLED'}
            bpy.ops.paintcurve.draw('INVOKE_DEFAULT')
        return {'FINISHED'}


class ALLSET_OT_weight_influence(bpy.types.Operator):
    bl_idname = 'allset.weight_influence'
    bl_label = 'Influence Locks'
    bl_options = {'UNDO'}
    action: EnumProperty(items=[('LOCK', 'Lock all', ''), ('UNLOCK', 'Unlock all', ''),
                               ('OTHERS', 'Lock unselected', ''), ('INVERT', 'Invert locks', ''),
                               ('LOCK_SELECTED', 'Lock selected joints', ''),
                               ('UNLOCK_SELECTED', 'Unlock selected joints', ''),
                               ('UNLOCK_OTHERS', 'Unlock other influences', ''),
                               ('JOINT', 'Select influence joint', '')])

    @classmethod
    def poll(cls, context):
        return active(context)

    def execute(self, context):
        mesh = context.active_object
        groups = list(mesh.vertex_groups) if state(context).show_all else skin.influences(mesh)
        vg = mesh.vertex_groups.active
        if self.action == 'JOINT':
            mod = skin.armature_modifier(mesh)
            pb = mod.object.pose.bones.get(vg.name) if mod and vg else None
            if pb is None:
                return {'CANCELLED'}
            from ..ui.channel_box import set_bone_selected
            for bone in mod.object.pose.bones:
                set_bone_selected(bone, bone == pb)
            mod.object.data.bones.active = pb.bone
        else:
            from ..ui.channel_box import bone_selected
            mod = skin.armature_modifier(mesh)
            selected = {b.name for b in mod.object.pose.bones if bone_selected(b)} if mod else set()
            if vg:
                selected.add(vg.name)
            for group in groups:
                if self.action in {'LOCK_SELECTED', 'UNLOCK_SELECTED'}:
                    if group.name in selected:
                        group.lock_weight = self.action == 'LOCK_SELECTED'
                elif self.action == 'UNLOCK_OTHERS':
                    if group.name not in selected:
                        group.lock_weight = False
                else:
                    group.lock_weight = (not group.lock_weight if self.action == 'INVERT' else
                                         group != vg if self.action == 'OTHERS' else self.action == 'LOCK')
        return {'FINISHED'}


class ALLSET_OT_weight_workspace(bpy.types.Operator):
    bl_idname = 'allset.weight_workspace'
    bl_label = 'Paint Skin Weights Workspace'

    def execute(self, context):
        if not active(context):
            result = bpy.ops.allset.paint_skin_weights('EXEC_DEFAULT')
            if 'FINISHED' not in result:
                return result
        from ..ui import tool_dock
        if tool_dock.show(context, width=400) is None:
            self.report({'WARNING'}, 'Open a modeling viewport to show Paint Skin Weights')
            return {'CANCELLED'}
        return {'FINISHED'}


def locked_snapshot(mesh):
    locked = {g.index: g.name for g in mesh.vertex_groups if g.lock_weight}
    result = {name: {} for name in locked.values()}
    if locked:
        for vertex in mesh.data.vertices:
            for entry in vertex.groups:
                name = locked.get(entry.group)
                if name is not None:
                    result[name][vertex.index] = entry.weight
    return result


def restore_locked(mesh, snapshot):
    indices = {g.index: g.name for g in mesh.vertex_groups if g.name in snapshot}
    current = {name: {} for name in indices.values()}
    if indices:
        for vertex in mesh.data.vertices:
            for entry in vertex.groups:
                name = indices.get(entry.group)
                if name is not None:
                    current[name][vertex.index] = entry.weight
    for name, before in snapshot.items():
        group = mesh.vertex_groups.get(name)
        if group is None:
            continue
        after = current[name]
        remove = list(after.keys() - before.keys())
        if remove:
            group.remove(remove)
        for index, weight in before.items():
            if after.get(index) != weight:
                group.add([index], weight, 'REPLACE')


@contextmanager
def vertex_targets(mesh, indices):
    """Give native flood/smooth/normalize the same precise mask, then restore it."""
    data = mesh.data
    selected = [v.select for v in data.vertices]
    vertex_mask, face_mask = data.use_paint_mask_vertex, data.use_paint_mask
    targets = set(indices)
    try:
        data.use_paint_mask = False
        data.use_paint_mask_vertex = True
        for vertex in data.vertices:
            vertex.select = vertex.index in targets
        data.update()
        yield
    finally:
        data.use_paint_mask_vertex = vertex_mask
        data.use_paint_mask = face_mask
        for vertex, value in zip(data.vertices, selected):
            vertex.select = value
        data.update()


def flood(context):
    """Maya Flood uses the active operation, opacity, influence locks and masks."""
    mesh = context.active_object
    group = mesh.vertex_groups.active
    if group is None or group.lock_weight:
        raise ValueError('Choose an unlocked influence before flooding')
    brush = context.tool_settings.weight_paint.brush
    kind = brush_kind(brush) or 'DRAW'
    if kind == 'SMEAR':
        raise ValueError('Smear needs a directional stroke; choose another operation to flood')
    ups = compat.unified_paint_settings(context.tool_settings)
    strength = (ups if ups.use_unified_strength or brush is None else brush).strength
    value = (ups if ups.use_unified_weight or brush is None else brush).weight
    data = mesh.data
    face_vertices = {i for f in data.polygons if f.select and not f.hide for i in f.vertices} if data.use_paint_mask else None
    vertices = [v for v in data.vertices if not v.hide
                and (not data.use_paint_mask_vertex or v.select)
                and (face_vertices is None or v.index in face_vertices)]
    if context.tool_settings.weight_paint.use_group_restrict:
        vertices = [v for v in vertices if any(e.group == group.index for e in v.groups)]
    before = {v.index: next((e.weight for e in v.groups if e.group == group.index), 0.0) for v in vertices}
    if not before or strength <= 0:
        return {'FINISHED'}
    protected = locked_snapshot(mesh)
    try:
        if kind == 'BLUR':
            with vertex_targets(mesh, before), viewport(context):
                bpy.ops.object.vertex_group_smooth(group_select_mode='ACTIVE', factor=strength, repeat=1)
        else:
            if kind == 'AVERAGE':
                value = sum(before.values()) / len(before) if before else 0.0
            blend = brush.blend if brush and kind == 'DRAW' else 'MIX'
            operations = {'MIX': lambda w: value, 'ADD': lambda w: w + value,
                          'SUB': lambda w: w - value, 'MUL': lambda w: w * value,
                          'LIGHTEN': lambda w: max(w, value), 'DARKEN': lambda w: min(w, value)}
            if blend not in operations:
                raise ValueError('Flood supports Replace, Add, Subtract, Scale, Lighten, Darken, Smooth and Average')
            for index, weight in before.items():
                result = weight + strength * (operations[blend](weight) - weight)
                group.add([index], min(1.0, max(0.0, result)), 'REPLACE')
        if context.tool_settings.use_auto_normalize:
            with vertex_targets(mesh, before), viewport(context):
                bpy.ops.object.vertex_group_normalize_all(
                    group_select_mode='BONE_DEFORM' if skin.armature_modifier(mesh) else 'ALL', lock_active=True)
        data.update()
        state(context).status = 'Flood complete'
        return {'FINISHED'}
    finally:
        restore_locked(mesh, protected)


class ALLSET_OT_weight_action(bpy.types.Operator):
    bl_idname = 'allset.weight_action'
    bl_label = 'Edit Skin Weights'
    bl_options = {'REGISTER', 'UNDO'}
    action: EnumProperty(items=[(key, label, label) for key, (label, op) in ACTIONS.items()])

    @classmethod
    def description(cls, context, properties):
        return ACTIONS.get(properties.action, ('Edit Skin Weights', ''))[0] + ': configure and apply; locked influences stay protected'

    @classmethod
    def poll(cls, context):
        return active(context) and len(context.active_object.vertex_groups) > 0

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=380, title=ACTIONS[self.action][0], confirm_text='Apply')

    def draw(self, context):
        layout = self.layout
        settings = getattr(state(context), self.action.lower())
        layout.use_property_split = True
        layout.use_property_decorate = False
        for name in _FIELDS[self.action]:
            if self.action in {'AUTO', 'ENVELOPE'} and name == 'type':
                continue
            layout.prop(settings, name)
        if not _FIELDS[self.action]:
            layout.label(text=('Assign the current Value to the masked or visible vertices.' if self.action == 'SET'
                               else 'Normalize the active influence to its maximum weight.'))
        note = layout.row()
        note.active = False
        note.label(text='Locked influences are preserved.', icon='LOCKED')
        if context.active_object.data.use_paint_mask_vertex or context.active_object.data.use_paint_mask:
            layout.label(text='Selection mask limits affected vertices.', icon='RESTRICT_SELECT_OFF')

    def execute(self, context):
        mesh = context.active_object
        settings = getattr(state(context), self.action.lower())
        values = {k: getattr(settings, k) for k in _FIELDS[self.action] if k != 'source'}
        if self.action in {'AUTO', 'ENVELOPE'}:
            values['type'] = 'AUTOMATIC' if self.action == 'AUTO' else 'ENVELOPES'
        if self.action == 'TRANSFER':
            source = settings.source
            if source is None or source == mesh or source.name not in context.view_layer.objects:
                self.report({'WARNING'}, 'Choose a different source mesh in this view layer')
                return {'CANCELLED'}
            values.update(data_type='VGROUP_WEIGHTS', use_reverse_transfer=True)
            # Blender's reverse-transfer flag also reverses the two layer enums.
            # Keep the workspace labels in source -> painted mesh order.
            values['layers_select_src'], values['layers_select_dst'] = (
                values['layers_select_dst'], values['layers_select_src'])
        snapshot = locked_snapshot(mesh)
        selected = list(context.selected_objects)
        try:
            with viewport(context):
                if self.action == 'TRANSFER':
                    for ob in context.selected_objects:
                        if ob != mesh:
                            ob.select_set(False)
                    settings.source.select_set(True)
                op = native(ACTIONS[self.action][1])
                if not op.poll():
                    raise RuntimeError('This operation needs a skinned mesh and a valid influence selection')
                result = op('EXEC_DEFAULT', **values)
                if 'FINISHED' not in result:
                    return result
            state(context).status = ACTIONS[self.action][0] + ' complete'
            return {'FINISHED'}
        except (RuntimeError, TypeError, ValueError) as ex:
            self.report({'WARNING'}, str(ex))
            return {'CANCELLED'}
        finally:
            restore_locked(mesh, snapshot)
            if self.action == 'TRANSFER':
                for ob in context.selected_objects:
                    if ob not in selected:
                        ob.select_set(False)
                for ob in selected:
                    ob.select_set(True)
                context.view_layer.objects.active = mesh


classes = (*_SETTING_CLASSES, ALLSET_PG_weight_workspace, ALLSET_OT_weight_tool,
           ALLSET_OT_weight_value, ALLSET_OT_weight_mask, ALLSET_OT_weight_influence, ALLSET_OT_weight_action,
           ALLSET_OT_weight_workspace, ALLSET_OT_weight_curve)


def register_props():
    bpy.types.WindowManager.allset_weight_workspace = PointerProperty(type=ALLSET_PG_weight_workspace)
    # Good skinning defaults without changing mesh/brush data.
    s = bpy.context.window_manager.allset_weight_workspace
    s.transfer.vert_mapping = 'POLYINTERP_NEAREST'
    s.transfer.layers_select_src = 'ALL'
    s.transfer.layers_select_dst = 'NAME'


def unregister_props():
    if hasattr(bpy.types.WindowManager, 'allset_weight_workspace'):
        del bpy.types.WindowManager.allset_weight_workspace
