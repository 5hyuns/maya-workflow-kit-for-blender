"""Step 239 (Issue #124): fixes from the first-hour audit on Maya 2026 (C:/Repos/bmk-strategy/FIRST_HOUR_239.md).

F-4: Edit Mesh > Bevel on the border of an extruded cylinder cap gave 0.078 wide bevels (Maya 0.49995): the cap ring's
neighbouring edges were counted as slide edges although no face holds two of them. Maya truth: tests/maya239_cylinder_data.py
(mayapy, audit230/maya/first_hour239.py)."""

from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit
from maya239_cylinder_data import BEVELED, COUNTS

ex = import_module(kit.MODULE + ".operators.extrude")
bev = import_module(kit.MODULE + ".operators.bevel_maya")
create = import_module(kit.MODULE + ".operators.create")
units = import_module(kit.MODULE + ".operators.units")


def b(p, k=1.0):
    return Vector((p[0], -p[2], p[1])) * k            # Maya (x, y, z) -> Blender (x, -z, y)


def test_bevel_on_an_extruded_cylinder_cap_like_maya():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    ob = create.create(bpy.context, 'CYLINDER')
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    k = units.maya_unit(bpy.context.scene)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    assert (len(bm.verts), len(bm.edges), len(bm.faces)) == (42, 100, 60)
    cap = [f for f in bm.faces if f.calc_center_median().z > 0.99 * k]          # Maya's +Y cap (20 triangles)
    assert len(cap) == 20
    ex.extrude(bm, cap, local_translate_z=1.0 * k)
    top = {f for f in bm.faces if f.calc_center_median().z > 1.99 * k}
    border = [e for e in bm.edges if sum(1 for f in e.link_faces if f in top) == 1]
    assert len(border) == 20
    import math
    want = math.sin(math.radians(81.0)) * k                  # fan edges at 81 degrees to the ring, length 1
    assert abs(bev.slide_limit(border) - want) < 1e-5 * k, bev.slide_limit(border)
    bev.bevel_edges(bm, border, unit=k)
    got = (len(bm.verts), len(bm.edges), len(bm.faces))
    assert got == (COUNTS["v"], COUNTS["e"], COUNTS["f"]), got
    pts = [v.co.copy() for v in bm.verts]
    worst = max(min((p - b(q, k)).length for p in pts) for q in BEVELED) / k
    assert worst < 2e-4, f"{worst:.5f} Maya units off"
    bm.free()


def test_cube_top_loop_still_quarter():
    # the cube's top loop: neighbours share the top face -> slides used from both ends (0.5), width 0.24997 (§3)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    top = [e for e in bm.edges if all(v.co.z > 0.49 for v in e.verts)]
    assert abs(bev.slide_limit(top) - 0.5) < 1e-6
    bm.free()


def test_delete_history_drops_the_bevel_node():
    # F-5: after Edit > Delete by Type > History the Channel Box INPUTS still listed polyBevel1 (Maya: nothing)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    ob = create.create(bpy.context, 'CYLINDER')
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.view_layer.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bm = bmesh.from_edit_mesh(ob.data)
    k = units.maya_unit(bpy.context.scene)
    for f in bm.faces:
        f.select_set(f.calc_center_median().z > 0.99 * k)
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.extrude() == {'FINISHED'}
    assert ob.name in ex.RECORDS
    bpy.ops.object.mode_set(mode='OBJECT')
    assert bpy.ops.allset.delete_history() == {'FINISHED'}
    assert ob.name not in ex.RECORDS, "the polyExtrudeFace record went with the history"
