"""QA 240 C: Blender 4.5 -b crashes (EXCEPTION_ACCESS_VIOLATION after ed.undo + ed.redo) when data changed after the last
undo push (keyframe_insert + frame_set) — WITHOUT the kit (AUTO_ENABLE = False). Not a kit bug; the harness pushes an undo
step after every data change to avoid it. The same steps with the kit enabled did not crash."""
import bpy
import bmesh
AUTO_ENABLE = False


def test_variant():
    bpy.ops.ed.undo_push(message="start")
    me = bpy.data.meshes.new("m")
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0); bm.to_mesh(me); bm.free()
    cube = bpy.data.objects.new("pCube1", me)
    bpy.context.scene.collection.objects.link(cube)
    bpy.ops.ed.undo_push(message="cube")
    bpy.context.scene.tool_settings.use_snap = True
    bpy.ops.ed.undo_push(message="qa x")
    cube.keyframe_insert("location", index=2, frame=1)
    bpy.context.scene.frame_set(4)
    cube.location.z += 0.25
    bpy.context.view_layer.update()
    cube.location.z = 0.0
    bpy.context.scene.frame_set(1)
    print("STEP undo", flush=True)
    bpy.ops.ed.undo()
    print("STEP redo", flush=True)
    bpy.ops.ed.redo()
    bpy.context.view_layer.update()
    print("STEP done", flush=True)
