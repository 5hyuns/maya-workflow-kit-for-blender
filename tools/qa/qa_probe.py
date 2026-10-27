"""QA 240 probe: which toggle effects can be measured headless (snap / proportional / mirror / auto key / undo)."""
import bpy
import bmesh
from importlib import import_module

import kit


def _cube():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    return bpy.context.active_object


def test_probe():
    ts = bpy.context.scene.tool_settings
    print("PROBE screen", bpy.context.screen, "window", bpy.context.window, "area", bpy.context.area)
    ob = _cube()
    # grid snap on object translate
    ts.use_snap = True
    ts.snap_elements = {'GRID'}
    ts.use_snap_translate = True
    for kw in ({}, {"snap": True}):
        ob.location = (0, 0, 0)
        try:
            bpy.ops.transform.translate(value=(0.37, 0, 0), **kw)
            print("PROBE grid", kw, tuple(ob.location))
        except Exception as ex:
            print("PROBE grid err", kw, ex)
    ts.snap_elements = {'INCREMENT'}
    ob.location = (0, 0, 0)
    bpy.ops.transform.translate(value=(0.37, 0, 0), snap=True)
    print("PROBE incr", tuple(ob.location))
    ts.use_snap = False
    # proportional + mirror in edit mode
    ob.location = (0, 0, 0)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.select = v.co.x > 0 and v.co.y > 0 and v.co.z > 0
    bm.select_flush(True)
    bmesh.update_edit_mesh(ob.data)
    ts.use_proportional_edit = True
    ts.proportional_size = 10
    try:
        bpy.ops.transform.translate(value=(0, 0, 1))
    except Exception as ex:
        print("PROBE prop err", ex)
    bm = bmesh.from_edit_mesh(ob.data)
    print("PROBE prop zs", sorted(round(v.co.z, 3) for v in bm.verts))
    ts.use_proportional_edit = False
    ob.data.use_mirror_x = True
    before = sorted(round(v.co.z, 3) for v in bm.verts)
    bpy.ops.transform.translate(value=(0, 0, 1), mirror=True)
    bm = bmesh.from_edit_mesh(ob.data)
    print("PROBE mirror zs", before, sorted(round(v.co.z, 3) for v in bm.verts))
    bpy.ops.object.mode_set(mode='OBJECT')
    # undo
    name = ob.name
    bpy.ops.ed.undo_push(message="a")
    ob.location.x = 5
    bpy.ops.ed.undo_push(message="b")
    bpy.ops.ed.undo()
    ob = bpy.context.scene.objects[name]
    print("PROBE undo x", ob.location.x)
    bpy.ops.ed.redo()
    ob = bpy.context.scene.objects[name]
    print("PROBE redo x", ob.location.x)
    # auto key
    ak = import_module(kit.MODULE + ".operators.auto_key")
    bpy.context.scene.allset_auto_key = True
    ob.keyframe_insert("location", frame=1)
    bpy.context.scene.frame_set(5)
    ob.location.x = 3
    bpy.context.view_layer.update()
    print("PROBE pending", dict(ak._pending))
    ak._flush()
    fc = kit.fcurves(ob).find("location", index=0)
    print("PROBE keys", [tuple(k.co) for k in fc.keyframe_points])
    sw = import_module(kit.MODULE + ".switch")
    print("PROBE switch off", sw.set_mode(False, layout=False), hasattr(bpy.types.Scene, "allset_symmetry"))
    print("PROBE switch on", sw.set_mode(True, layout=False), hasattr(bpy.types.Scene, "allset_symmetry"))
