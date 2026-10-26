"""Viewport integration: run Blender --factory-startup --python this_file.py.
Creates a temporary scene in that process and quits it after checking viewport picking.
"""
import importlib
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
addon = importlib.import_module(ROOT.name)
from allset.operators import joints, joint_selection, select_priority, tool_keys
from allset.ui.channel_box import bone_selected

bpy.utils.register_class(tool_keys.ALLSET_OT_toggle_sel_mode)
select_priority._enabled = lambda context: True
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
rig = joints.new_skeleton(bpy.context)
a = joints.add_joint(rig, (-2, 0, 0))
b = joints.add_joint(rig, (-2, 2, 0), a)
joints.finish(bpy.context, rig, [a, b])
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.mesh.primitive_cube_add(location=(2, 0, 0))
cube = bpy.context.object
area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
region = next(r for r in area.regions if r.type == 'WINDOW')
rv3d = area.spaces.active.region_3d
rv3d.view_rotation = Quaternion((1, 0, 0, 0))
rv3d.view_perspective = 'ORTHO'
rv3d.view_location = Vector((0, 0, 0))
rv3d.view_distance = 12
class Probe:
    _finish_pick = select_priority.ALLSET_OT_select_priority._finish_pick

probe = Probe()
step = 0

def click(point, shift=False, ctrl=False):
    xy = location_3d_to_region_2d(region, rv3d, Vector(point))
    event = SimpleNamespace(mouse_region_x=int(xy.x), mouse_region_y=int(xy.y),
                            value='CLICK', shift=shift, ctrl=ctrl)
    result = select_priority.ALLSET_OT_select_priority.invoke(probe, bpy.context, event)
    assert result == {'FINISHED'}, result

def run():
    global step
    try:
        with bpy.context.temp_override(area=area, region=region):
            if step == 0:
                click((-2, 0, 0))
                assert bpy.context.mode == 'POSE' and bone_selected(rig.pose.bones[a])
            elif step == 1:
                click((2, 0, 0))
                assert bpy.context.mode == 'OBJECT' and bpy.context.active_object == cube
                assert not any(bone_selected(pb) for pb in rig.pose.bones)
            elif step == 2:
                click((-2, 2, 0))
                assert bpy.context.mode == 'POSE' and rig.data.bones.active.name == b
            elif step == 3:
                click((0, -3, 0))
                assert bpy.context.mode == 'OBJECT' and not bpy.context.selected_objects
                assert bpy.context.active_object is None
            elif step == 4:
                click((-2, 0, 0))
                bpy.ops.allset.toggle_sel_mode()
                assert bpy.context.mode == 'EDIT_ARMATURE'
            elif step == 5:
                click((2, 0, 0))
                assert bpy.context.mode == 'OBJECT' and bpy.context.active_object == cube
            elif step == 6:
                select_priority._enabled = lambda context: False
                click((-2, 0, 0))
                assert bpy.context.mode == 'POSE' and bone_selected(rig.pose.bones[a])
            elif step == 7:
                click((2, 0, 0))
                assert bpy.context.mode == 'OBJECT' and bpy.context.active_object == cube
            else:
                Path('/tmp/allset-viewport-result.txt').write_text('PASS: joint -> mesh -> joint -> empty -> edit -> mesh')
                bpy.ops.wm.quit_blender()
                return None
            area.tag_redraw()
        step += 1
        return 0.3
    except Exception:
        Path('/tmp/allset-viewport-result.txt').write_text(traceback.format_exc())
        bpy.ops.wm.quit_blender()
        return None

bpy.app.timers.register(run, first_interval=2.0)
