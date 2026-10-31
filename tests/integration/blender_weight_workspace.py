"""Blender --background --factory-startup --python tests/blender_weight_workspace.py"""
import importlib
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2] / 'src' / 'allset'
sys.path.insert(0, str(ROOT.parent))
addon = importlib.import_module(ROOT.name)
from allset.operators import weight_paint as w, skin
from allset.ui import paint_weights as ui
from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active
VIEW3D_PT_tools_active.register_ensure()

for c in (*w.classes, skin.ALLSET_OT_paint_skin_weights, skin.ALLSET_OT_flood_weights,
          skin.ALLSET_OT_weight_paint_exit):
    bpy.utils.register_class(c)
w.register_props()
ui.register()
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.object.armature_add()
rig = bpy.context.object
bpy.ops.object.mode_set(mode='EDIT')
rig.data.edit_bones[0].name = 'Shoulder'
bone = rig.data.edit_bones.new('Elbow')
bone.head, bone.tail = (0, 0, 1), (0, 0, 2)
bone.parent = rig.data.edit_bones['Shoulder']
bone = rig.data.edit_bones.new('Wrist')
bone.head, bone.tail = (0, 0, 2), (0, 0, 3)
bone.parent = rig.data.edit_bones['Elbow']
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.mesh.primitive_cube_add()
mesh = bpy.context.object
mod = mesh.modifiers.new('Skin', 'ARMATURE'); mod.object = rig
for name, value in [('Wrist', .2), ('Shoulder', .5), ('Elbow', .3), ('Utility', .1)]:
    group = mesh.vertex_groups.new(name=name)
    group.add(list(range(len(mesh.data.vertices))), value, 'REPLACE')
mesh.vertex_groups.active_index = 1
area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
region = next(r for r in area.regions if r.type == 'WINDOW')

def values(name):
    g = mesh.vertex_groups[name]
    return [next((e.weight for e in v.groups if e.group == g.index), 0) for v in mesh.data.vertices]

def near(seq, target):
    assert all(abs(x-target) < 1e-5 for x in seq), (seq,target)

with bpy.context.temp_override(area=area, region=region):
    bpy.ops.allset.paint_skin_weights()
    assert bpy.context.mode == 'PAINT_WEIGHT'
    # The modern brush selector really activates each Blender brush family.
    for kind in ('DRAW','BLUR','AVERAGE','SMEAR','DRAW'):
        assert bpy.ops.allset.weight_tool(kind=kind, blend='MIX' if kind=='DRAW' else '') == {'FINISHED'}
        assert w.brush_kind(bpy.context.tool_settings.weight_paint.brush) == kind
    for tool in ('LINEAR','RADIAL','SAMPLE','SAMPLE_GROUP'):
        assert bpy.ops.allset.weight_tool(kind=tool) == {'FINISHED'}
        assert bpy.context.mode == 'PAINT_WEIGHT'
    bpy.ops.allset.weight_tool(kind='DRAW', blend='MIX')
    ups = addon.compat.unified_paint_settings(bpy.context.tool_settings)
    ups.use_unified_weight = ups.use_unified_strength = True
    ups.strength = .5
    bpy.context.tool_settings.use_auto_normalize = False
    bpy.ops.allset.weight_value(value=.8)
    assert abs(ups.weight-.8)<1e-5
    # Flood uses opacity and the paint operation instead of blindly setting weights.
    assert bpy.ops.allset.flood_weights() == {'FINISHED'}
    near(values('Shoulder'), .65)
    bpy.ops.allset.weight_tool(kind='DRAW', blend='ADD')
    bpy.ops.allset.weight_value(value=.2)
    bpy.ops.allset.flood_weights()
    near(values('Shoulder'), .75)
    bpy.ops.allset.weight_tool(kind='DRAW', blend='SUB')
    bpy.ops.allset.flood_weights()
    near(values('Shoulder'), .65)
    bpy.ops.allset.weight_tool(kind='DRAW', blend='MUL')
    bpy.ops.allset.weight_value(value=.5)
    bpy.ops.allset.flood_weights()
    near(values('Shoulder'), .4875)
    # Masking only paints the chosen vertices.
    bpy.ops.allset.weight_tool(kind='DRAW', blend='MIX')
    mesh.data.use_paint_mask_vertex=True
    for v in mesh.data.vertices: v.select=v.index==0
    ups.strength=1
    bpy.ops.allset.weight_value(value=1)
    bpy.ops.allset.flood_weights()
    near(values('Shoulder')[:1],1)
    near(values('Shoulder')[1:],.4875)
    mesh.data.use_paint_mask_vertex=False
    # Lock tools affect the influences, not utility groups.
    bpy.ops.allset.weight_influence(action='OTHERS')
    assert not mesh.vertex_groups['Shoulder'].lock_weight
    assert mesh.vertex_groups['Wrist'].lock_weight and mesh.vertex_groups['Elbow'].lock_weight
    assert not mesh.vertex_groups['Utility'].lock_weight
    protected = w.locked_snapshot(mesh)
    for key in ('NORMALIZE','NORMALIZE_ALL','CLEAN','SMOOTH','QUANTIZE','LEVELS','INVERT','LIMIT','MIRROR','SET'):
        assert bpy.ops.allset.weight_action(action=key) == {'FINISHED'}, key
        assert w.locked_snapshot(mesh)==protected, key
        assert bpy.context.mode=='PAINT_WEIGHT'
    bpy.ops.allset.weight_influence(action='UNLOCK')
    assert not any(g.lock_weight for g in skin.influences(mesh))
    w.state(bpy.context).normalize_all.group_select_mode='BONE_DEFORM'
    w.state(bpy.context).normalize_all.lock_active=False
    bpy.ops.allset.weight_action(action='NORMALIZE_ALL')
    for vertex in mesh.data.vertices:
        total=sum(e.weight for e in vertex.groups if e.group in {0,1,2})
        assert abs(total-1)<1e-5, total
    # Transfer has an explicit source and leaves object selection and locked groups intact.
    source=bpy.data.objects.new('Weight Source',mesh.data.copy())
    bpy.context.collection.objects.link(source)
    source.vertex_groups.clear()
    source.vertex_groups.new(name='Shoulder').add(list(range(len(source.data.vertices))),.9,'REPLACE')
    w.state(bpy.context).transfer.source=source
    old_selection={o.name for o in bpy.context.selected_objects}
    mesh.vertex_groups['Wrist'].lock_weight=True
    locked=w.locked_snapshot(mesh)
    assert bpy.ops.allset.weight_action(action='TRANSFER')=={'FINISHED'}
    near(values('Shoulder'),.9)
    assert w.locked_snapshot(mesh)==locked
    assert {o.name for o in bpy.context.selected_objects}==old_selection
    mesh.vertex_groups['Wrist'].lock_weight=False
    # Auto-normalization choice survives leaving and returning to the skin tool.
    w.state(bpy.context).auto_normalize=False
    assert skin.normalize_mode(mesh)=='NONE'
    bpy.ops.allset.weight_paint_exit()
    bpy.ops.allset.paint_skin_weights()
    assert not bpy.context.tool_settings.use_auto_normalize
    # Filter, hierarchy order, and non-joint visibility.
    flags, order=ui.influence_filter(mesh,1,sort='HIERARCHY')
    assert flags==[1,1,1,0] and order[:3]==[2,0,1], (flags,order)
    flags,_=ui.influence_filter(mesh,1,search='elB')
    assert flags==[0,0,1,0],flags
    assert ui.influence_filter(mesh,1,show_all=True)[0]==[1,1,1,1]
    # Mask selection stays in the paint context.
    bpy.ops.allset.weight_mask(action='NONE')
    assert mesh.data.use_paint_mask_vertex
    assert not any(v.select for v in mesh.data.vertices)
    bpy.ops.allset.weight_mask(action='ALL')
    assert all(v.select for v in mesh.data.vertices)
    mesh.data.use_paint_mask_vertex=False
    # Selecting an influence joint does not leave paint mode.
    assert bpy.ops.allset.weight_influence(action='JOINT')=={'FINISHED'}
    assert rig.data.bones.active.name==mesh.vertex_groups.active.name
    assert bpy.context.mode=='PAINT_WEIGHT'
    # Bone-derived assignments are available from the workspace too.
    for key in ('AUTO','ENVELOPE'):
        assert bpy.ops.allset.weight_action(action=key)=={'FINISHED'}, key
        assert bpy.context.mode=='PAINT_WEIGHT'
    # Legacy option scripts share the same modern brush activation and falloff API.
    options=dict(operation='SMOOTH',profile='SOFT',normalize=None,opacity=.5,value=.8,
                 radius=1,screen_projection=True,show_wireframe=False,xray_joints=False)
    assert skin.apply_paint_settings(bpy.context,mesh,rig,options)==[]
    assert w.brush_kind(bpy.context.tool_settings.weight_paint.brush)=='BLUR'
    options['operation']='REPLACE'
    assert skin.apply_paint_settings(bpy.context,mesh,rig,options)==[]
    assert w.brush_kind(bpy.context.tool_settings.weight_paint.brush)=='DRAW'
    bpy.ops.allset.weight_paint_exit()
    assert bpy.context.mode=='OBJECT'

ui.unregister()
w.unregister_props()
for c in reversed(w.classes): bpy.utils.unregister_class(c)
print('PASS: workspace brush families, tools, flood arithmetic, masks, locks, weight actions, filters, normalization and cleanup')
