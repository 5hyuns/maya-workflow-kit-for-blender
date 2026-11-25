"""#548: soft selection applies to the Scale manipulator's drag like it does to Move and Rotate.

The Scale tool's drag (``manip_scale``) previews and finishes with Blender's resize; with soft select on, the
points around the selection follow with the falloff, exactly as Blender's own proportional resize does, and a
cancelled drag puts them back."""

from importlib import import_module

import bmesh
import bpy

import kit

ms = import_module(kit.MODULE + ".operators.manip_scale")


def _grid():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=10, y_subdivisions=10, size=10.0)
    ob = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.select_set(abs(v.co.x) < 1.2 and abs(v.co.y) < 1.2)
    bm.select_flush(True)
    bmesh.update_edit_mesh(ob.data)
    ts = bpy.context.scene.tool_settings
    ts.transform_pivot_point = 'MEDIAN_POINT'
    ts.use_proportional_edit = True
    ts.proportional_size = 4.0
    ts.proportional_edit_falloff = 'SMOOTH'
    ts.use_proportional_connected = False
    ts.use_proportional_projected = False
    return ob


def _coords(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return [v.co.copy() for v in bm.verts]


def _set(ob, coords):
    bm = bmesh.from_edit_mesh(ob.data)
    for v, co in zip(bm.verts, coords):
        v.co = co
    bmesh.update_edit_mesh(ob.data)


def _same(a, b, tol=1e-5):
    return all((p - q).length <= tol for p, q in zip(a, b))


def _finish():
    ts = bpy.context.scene.tool_settings
    ts.use_proportional_edit = False
    bpy.ops.object.mode_set(mode='OBJECT')


def test_soft_select_follows_the_scale_drag():
    ob = _grid()
    try:
        before = _coords(ob)
        sel = [v.select for v in bmesh.from_edit_mesh(ob.data).verts]
        ts = bpy.context.scene.tool_settings
        # Blender's own proportional resize: the result the drag must give
        bpy.ops.transform.resize(value=(0.5, 0.5, 0.5), use_proportional_edit=True,
                                 proportional_edit_falloff=ts.proportional_edit_falloff,
                                 proportional_size=ts.proportional_size, use_proportional_connected=False,
                                 use_proportional_projected=False, snap=False)
        expected = _coords(ob)
        _set(ob, before)
        state = ms.save_state(bpy.context)
        assert ms.apply(bpy.context, 0.8) == {'FINISHED'}
        ms.restore(state)
        assert _same(_coords(ob), before), "restore did not put the soft points back"
        assert ms.apply(bpy.context, 0.5, final=True) == {'FINISHED'}
        after = _coords(ob)
        moved_soft = [i for i, (a, b) in enumerate(zip(before, after)) if not sel[i] and (a - b).length > 1e-4]
        assert moved_soft, "no unselected point followed the scale with soft select on"
        assert _same(after, expected), "scale drag differs from Blender's proportional resize"
        far = [i for i, co in enumerate(before) if co.length > 1.2 * 1.5 + ts.proportional_size]
        assert far and all((before[i] - after[i]).length < 1e-6 for i in far), "points beyond the radius moved"
    finally:
        _finish()


def test_soft_select_follows_an_axis_scale():
    ob = _grid()
    try:
        before = _coords(ob)
        sel = [v.select for v in bmesh.from_edit_mesh(ob.data).verts]
        assert ms.apply(bpy.context, 2.0, ms.channels('AXIS', 'X'), 'GLOBAL', final=True) == {'FINISHED'}
        after = _coords(ob)
        soft = [i for i, (a, b) in enumerate(zip(before, after)) if not sel[i] and (a - b).length > 1e-4]
        assert soft, "no unselected point followed the X scale"
        assert all(abs(before[i].y - after[i].y) < 1e-6 for i in range(len(before))), "Y changed on an X scale"
    finally:
        _finish()


def test_soft_select_off_moves_only_the_selection():
    ob = _grid()
    try:
        bpy.context.scene.tool_settings.use_proportional_edit = False
        before = _coords(ob)
        sel = [v.select for v in bmesh.from_edit_mesh(ob.data).verts]
        assert ms.apply(bpy.context, 0.5, final=True) == {'FINISHED'}
        after = _coords(ob)
        assert all((before[i] - after[i]).length < 1e-6 for i in range(len(before)) if not sel[i])
    finally:
        _finish()
