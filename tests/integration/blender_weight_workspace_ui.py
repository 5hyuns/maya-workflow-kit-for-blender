"""Render the Paint Skin Weights Tool Settings (Maya 2024+ sections, every section expanded) in an isolated Blender
GUI, then quit."""
import sys
import traceback
from pathlib import Path
import os

OUTPUT = Path(os.environ.get("ALLSET_INTEGRATION_OUTPUT",
                             str(Path(__file__).resolve().parents[2] / "tmp" / "integration_artifacts")))
OUTPUT.mkdir(parents=True, exist_ok=True)
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from allset.operators import weight_paint as w, skin
from allset import compat
from allset.ui import paint_weights as ui, dock_tabs, tool_dock
dock_tabs.register()
for c in (*w.classes, skin.ALLSET_OT_paint_skin_weights, skin.ALLSET_OT_weight_paint_exit,
          skin.ALLSET_OT_flood_weights):
    bpy.utils.register_class(c)
w.register_props(); ui.register()
bpy.context.preferences.view.show_splash = False
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.object.armature_add()
rig=bpy.context.object
bpy.ops.object.mode_set(mode='EDIT')
rig.data.edit_bones[0].name='shoulder_L'
for i,name in enumerate(['upperArm_L','forearm_L','wrist_L','hand_L']):
    bone=rig.data.edit_bones.new(name)
    bone.head=(0,0,i+1); bone.tail=(0,0,i+2)
    bone.parent=rig.data.edit_bones[i]
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16)
mesh=bpy.context.object; mesh.name='Character • Arm'
mod=mesh.modifiers.new('skinCluster','ARMATURE'); mod.object=rig
for i,bone in enumerate(rig.data.bones):
    vg=mesh.vertex_groups.new(name=bone.name)
    for v in mesh.data.vertices:
        vg.add([v.index], max(.01, 1-abs(v.co.z-(i*.4-1))/1.5), 'REPLACE')
mesh.vertex_groups.active_index=2
area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
region=next(r for r in area.regions if r.type=='WINDOW')
with bpy.context.temp_override(area=area,region=region):
    bpy.ops.allset.paint_skin_weights()
    bpy.ops.allset.weight_tool(kind='DRAW',blend='MIX')

draw_calls=[]
draw_errors=[]
class ALLSET_PT_weight_preview(bpy.types.Panel):
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='Tool'
    bl_label='Paint Skin Weights'
    bl_options={'HIDE_HEADER'}
    bl_order=-1000
    @classmethod
    def poll(cls,context): return ui.active(context)
    def draw(self,context):
        try:
            ui.draw(self.layout,context)
            draw_calls.append(tuple(name for name, _fn in ui.SECTIONS))
        except Exception:
            draw_errors.append(traceback.format_exc())
            raise
bpy.utils.register_class(ALLSET_PT_weight_preview)
prop=next(a for a in bpy.context.screen.areas if a.type=='PROPERTIES')
phase=0
pages=['COLLAPSED','EXPANDED']
FLAGS=[n for n in w.ALLSET_PG_weight_workspace.__annotations__ if n.startswith('show_')]

def tick():
    global phase
    try:
        if prop.spaces.active.context!='TOOL':
            prop.spaces.active.context='TOOL'
        if phase==0:
            tool_dock.configure(prop,bpy.context.window)
        prop.spaces.active.show_region_header=False
        prop.tag_redraw()
        if phase<len(pages)*2:
            page=pages[phase//2]
            if phase%2==0:
                s=w.state(bpy.context)
                if page=='EXPANDED':
                    for name in FLAGS:
                        setattr(s,name,True)
                    brush=bpy.context.tool_settings.weight_paint.brush
                    brush.stroke_method='CURVE'
                    brush.use_pressure_size=brush.use_pressure_strength=True
                    setattr(brush,compat.brush_falloff_props(brush)[0],'CUSTOM')   # 4.5 curve_preset, 5.x curve_distance_falloff_preset
                prop.tag_redraw()
            else:
                bpy.ops.screen.screenshot(filepath=str(OUTPUT / ('allset-weight-'+page.lower()+'.png')))
                with bpy.context.temp_override(area=prop,region=next(r for r in prop.regions if r.type=='WINDOW')):
                    bpy.ops.screen.screenshot_area(filepath=str(OUTPUT / ('allset-weight-panel-'+page.lower()+'.png')))
        else:
            assert draw_calls and draw_calls[-1][:7]==ui.MAYA_SECTIONS, draw_calls[-1:]
            assert ui.MAYA_SECTIONS==('Skin Clusters','Influences','Brush','Visualization','Stroke','Stylus Pressure','Display')
            assert not draw_errors, '\n'.join(draw_errors)
            (OUTPUT / 'allset-weight-ui-result.txt').write_text('PASS: Maya 2024+ sections (Skin Clusters, Influences, Brush, Visualization, Stroke, Stylus Pressure, Display) + extras, collapsed and expanded')
            bpy.ops.wm.quit_blender();return None
        phase+=1
        return .65
    except Exception:
        (OUTPUT / 'allset-weight-ui-result.txt').write_text(traceback.format_exc())
        bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(tick,first_interval=1)
