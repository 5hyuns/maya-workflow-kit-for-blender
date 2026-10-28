"""Blender -b crash without the kit (step 271): blender -b --factory-startup --python repro_c_bone_roll.py"""
import bpy
bpy.ops.object.armature_add()
bpy.ops.object.select_all(action='SELECT')
print("CALL", flush=True)
try:
    print(bpy.ops.transform.transform(mode='BONE_ROLL', release_confirm=True))
except Exception as e:
    print("EXC", e)
print("SURVIVED", flush=True)
