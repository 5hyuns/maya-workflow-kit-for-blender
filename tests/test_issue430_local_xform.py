"""#430: Ctrl+middle-drag with the Rotate / Scale tool in mesh edit mode turns each selected component group about its
own normal / scales it across its normal, around the group's centre. GUI: tests/gui/gui_issue430_ctrl_mmb_local.py."""

import math
from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit

local = import_module(kit.MODULE + ".operators.component_local")


def test_keymap_items():
    kc = kit.maya_kc()
    for km, mode in (("3D View Tool: Rotate", 'ROTATE'), ("3D View Tool: Scale", 'SCALE')):
        items = [k for k in kc.keymaps[km].keymap_items if k.active and k.type == 'MIDDLEMOUSE'
                 and k.value == 'PRESS' and k.ctrl and not k.shift and not k.alt]
        assert items and items[0].idname == "allset.component_local", (km, [k.idname for k in items])
        assert items[0].properties.mode == mode
    # the Move tool keeps Ctrl+MMB along normals (#394)
    move = [k for k in kc.keymaps["3D View Tool: Move"].keymap_items if k.active and k.type == 'MIDDLEMOUSE'
            and k.ctrl and not k.shift]
    assert move and move[0].idname == "allset.component_slide"


def _cube_edit(select, kind):
    """A new 2 x 2 x 2 cube in edit mode, select mode ``kind``, ``select(bm)`` picks the components."""
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_cube_add(size=2)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.tool_settings.mesh_select_mode = kind
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(ob.data)
    bm.normal_update()
    select(bm)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    return ob


def _done():
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.delete()


def test_face_groups_and_axes():
    def sel(bm):
        for f in bm.faces:
            if abs(f.normal.z) > 0.9 or f.normal.x > 0.9:
                f.select_set(True)
    _cube_edit(sel, (False, False, True))
    try:
        data = local.collect(bpy.context)
        groups = data[0][1]
        # top + side share an edge: one group; bottom touches the side too (shared edge): all three are one group
        assert len(groups) == 1, len(groups)
        centre, normal, pts = groups[0]
        assert len(pts) == 8
        assert (normal - Vector((1, 0, 0))).length < 1e-6, normal
    finally:
        _done()

    def sel2(bm):
        for f in bm.faces:
            if abs(f.normal.z) > 0.9:
                f.select_set(True)
    _cube_edit(sel2, (False, False, True))
    try:
        groups = local.collect(bpy.context)[0][1]
        assert len(groups) == 2
        for centre, normal, pts in groups:
            assert abs(abs(centre.z) - 1) < 1e-6 and abs(centre.x) < 1e-6 and abs(centre.y) < 1e-6
            assert (normal - Vector((0, 0, math.copysign(1, centre.z)))).length < 1e-6
    finally:
        _done()


def test_edge_and_vertex_axes():
    def sel(bm):
        for e in bm.edges:
            if all(abs(v.co.x - 1) < 1e-4 and abs(v.co.z - 1) < 1e-4 for v in e.verts):
                e.select_set(True)
    _cube_edit(sel, (False, True, False))
    try:
        centre, normal, pts = local.collect(bpy.context)[0][1][0]
        assert (normal - Vector((1, 0, 1)).normalized()).length < 1e-6, normal
        assert (centre - Vector((1, 0, 1))).length < 1e-6
    finally:
        _done()

    def selv(bm):
        for v in bm.verts:
            if v.co.z > 0.9:
                v.select_set(True)
        for e in bm.edges:
            if all(v.select for v in e.verts):
                e.select_set(True)
    _cube_edit(selv, (True, False, False))
    try:
        groups = local.collect(bpy.context)[0][1]
        assert len(groups) == 1
        centre, normal, pts = groups[0]
        assert (normal - Vector((0, 0, 1))).length < 1e-6 and (centre - Vector((0, 0, 1))).length < 1e-6
    finally:
        _done()


def test_transform_math():
    c, n = Vector((0, 0, 1)), Vector((0, 0, 1))
    p = local.transform('ROTATE', local.amount_from_drag('ROTATE', 250), c, n, Vector((1, 0, 1)))
    # 250 px = 90 degrees, to the right = clockwise seen from the normal's tip
    assert (p - Vector((0, -1, 1))).length < 1e-6, p
    p = local.transform('SCALE', local.amount_from_drag('SCALE', local.PX_PER_SCALE), c, n, Vector((1, 1, 1)))
    assert (p - Vector((2, 2, 1))).length < 1e-6, p
    # the normal part stays: a point off the plane keeps its height
    p = local.transform('SCALE', 3.0, c, n, Vector((1, 0, 2)))
    assert (p - Vector((3, 0, 2))).length < 1e-6, p
    assert local.amount_from_drag('SCALE', 0) == 1.0 and local.amount_from_drag('ROTATE', 0) == 0.0
