"""#486: UV Layout keeps every shell's orientation and first scales the shells to their 3D size ratio (one texel
density), then packs them into 0-1."""

import math
from importlib import import_module

import bmesh
import bpy

import kit

uvt = import_module(kit.MODULE + ".operators.uv_tools")


def _cube_six_shells():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add(size=2)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_all(action='SELECT')
    assert bpy.ops.allset.uv_automatic() == {'FINISHED'}
    bpy.ops.mesh.select_all(action='SELECT')
    return ob


def _bm(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    return bm, bm.loops.layers.uv.active


def _angles(bm, uv):
    """Per face: the angle of its first UV edge."""
    out = {}
    for f in bm.faces:
        d = f.loops[1][uv].uv - f.loops[0][uv].uv
        out[f.index] = math.atan2(d.y, d.x)
    return out


def test_layout_keeps_orientation_and_evens_the_texel_density():
    ob = _cube_six_shells()
    bm, uv = _bm(ob)
    assert len(uvt.islands(bm, uv)) == 6
    big = bm.faces[0]
    uvt.scale_island([big], uv, 2.0)           # one shell scaled up in the UV Editor
    bmesh.update_edit_mesh(ob.data)
    bm, uv = _bm(ob)
    before = _angles(bm, uv)
    assert bpy.ops.allset.uv_layout() == {'FINISHED'}
    bm, uv = _bm(ob)
    after = _angles(bm, uv)
    for i, a in before.items():
        turn = (after[i] - a + math.pi) % (2 * math.pi) - math.pi
        assert abs(turn) < 1e-4, f"face {i} turned by {math.degrees(turn):.1f} degrees"
    areas = [uvt._uv_area(f, uv) for f in bm.faces]
    assert max(areas) / min(areas) < 1.01, f"one texel density: {areas}"
    for f in bm.faces:
        for lp in f.loops:
            assert -1e-6 <= lp[uv].uv.x <= 1 + 1e-6 and -1e-6 <= lp[uv].uv.y <= 1 + 1e-6, "inside 0-1"
