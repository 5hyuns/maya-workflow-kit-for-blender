"""Blender --background --factory-startup --python tests/blender_weight_paint_exit.py"""
import importlib
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2] / 'src' / 'allset'
sys.path.insert(0, str(ROOT.parent))
addon = importlib.import_module(ROOT.name)
from allset.operators import skin
from allset.ui import toolbox
from bl_ui import space_toolsystem_common as stc

for cls in (skin.ALLSET_OT_paint_skin_weights, skin.ALLSET_OT_weight_paint_exit):
    bpy.utils.register_class(cls)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.object.armature_add()
arm = bpy.context.object
joint = arm.data.bones[0].name
bpy.ops.mesh.primitive_cube_add()
mesh = bpy.context.object
mod = mesh.modifiers.new('Skin', 'ARMATURE')
mod.object = arm
vg = mesh.vertex_groups.new(name=joint)
vg.add(list(range(len(mesh.data.vertices))), 0.63, 'REPLACE')

area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
region = next(r for r in area.regions if r.type == 'WINDOW')

def weights():
    return tuple(tuple((g.group, g.weight) for g in v.groups) for v in mesh.data.vertices)

baseline = weights()

def enter():
    bpy.context.view_layer.objects.active = mesh
    mesh.select_set(True)
    assert bpy.ops.allset.paint_skin_weights() == {'FINISHED'}
    assert bpy.context.mode == 'PAINT_WEIGHT'

def check(tool):
    assert bpy.context.mode == 'OBJECT', bpy.context.mode
    assert bpy.context.active_object == mesh
    assert mesh.select_get() and not arm.select_get()
    assert arm.mode == 'OBJECT', arm.mode
    assert weights() == baseline, 'Leaving the tool changed painted weights'
    active = bpy.context.workspace.tools.from_space_view3d_mode('OBJECT', create=False)
    assert active is not None and active.idname == tool, (tool, active.idname if active else None)

with bpy.context.temp_override(area=area, region=region):
    for tool in ('builtin.select_box', 'builtin.move', 'builtin.rotate', 'builtin.scale'):
        enter()
        assert bpy.ops.allset.weight_paint_exit(tool=tool) == {'FINISHED'}
        check(tool)
    # Repeating the Skin menu command uses the same safe exit path.
    enter()
    assert bpy.ops.allset.paint_skin_weights() == {'FINISHED'}
    check('builtin.select_box')
    # Real toolbar activation leaves paint before resolving Object-only tools.
    activate = toolbox._make_activate_by_id(stc.activate_by_id)
    for tool in toolbox.MAYA_TOOLS:
        enter()
        assert activate(bpy.context, 'VIEW_3D', tool)
        check(tool)
    # Object tools are visible while the paint tool is active.
    enter()
    cls = toolbox.TOOLBAR
    toolbox._saved['tools_from_context'] = cls.__dict__['tools_from_context']
    toolbox._drawing[0] = True
    try:
        shown = list(toolbox._tools_from_context(cls, bpy.context))
        names = {t.idname for t in toolbox._flat(shown)}
        assert set(toolbox.MAYA_TOOLS) <= names, names
    finally:
        toolbox._drawing[0] = False
    # A previously stuck paint-mode transform cannot strand re-entry without a brush.
    bpy.ops.wm.tool_set_by_id(name='builtin.move')
    assert bpy.context.mode == 'PAINT_WEIGHT'
    skin.leave_weight_paint(bpy.context)
    enter()
    brush_tool = bpy.context.workspace.tools.from_space_view3d_mode('PAINT_WEIGHT', create=False)
    assert brush_tool.idname == 'builtin.brush', brush_tool.idname
    skin.leave_weight_paint(bpy.context)

# Every plain Q/W/E/R paint binding exits, with no native paint-mode tool switch left.
data = addon.keymap.generate_data()
km = next(k for k in data if k[0] == 'Weight Paint')
for key in ('Q', 'W', 'E', 'R'):
    bindings = [it for it in km[2]['items'] if it[1]['type'] == key
                and not any(it[1].get(m) for m in ('ctrl','shift','alt','oskey'))]
    assert len(bindings) == 1 and bindings[0][0] == 'allset.weight_paint_exit', (key, bindings)
print('PASS: Q/W/E/R, toolbar tools, menu toggle, re-entry, mesh selection, rig release, and weight preservation')
