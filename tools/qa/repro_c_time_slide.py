"""Blender -b crash without the kit (step 271): blender -b --factory-startup --python repro_c_time_slide.py -- TIME_SLIDE"""
import bpy, sys
mode = sys.argv[-1]
ob = bpy.context.object
ob.keyframe_insert("location", frame=1); ob.keyframe_insert("location", frame=10)
if mode == "BONE_ROLL":
    bpy.ops.object.armature_add(); bpy.ops.object.mode_set(mode='EDIT')
print("CALL", mode, flush=True)
try:
    print(bpy.ops.transform.transform(mode=mode))
except Exception as e:
    print("EXC", e)
print("SURVIVED", mode, flush=True)
