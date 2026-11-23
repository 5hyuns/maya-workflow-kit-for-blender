"""#494: the UV Toolkit's Transform section works like Maya's: Pivot (nine places of the selection or of the UV Area,
Reset), Move (eight step buttons, U / V position fields), Rotate (angle, counterclockwise / clockwise about the
pivot), Scale (factor in UV / U / V about the pivot, Shrink), and the Align and Snap section's Snap grid.
GUI: tests/gui/gui_issue494_uv_toolkit_transform.py."""

import math
from importlib import import_module

import bmesh
import bpy

import kit

uvx = import_module(kit.MODULE + ".operators.uv_transform")
uv_hud = import_module(kit.MODULE + ".ui.uv_hud")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _two_quads():
    """Two separate quads in edit mode: shell A at UV (0.1-0.3, 0.1-0.2), shell B at (0.6-0.7, 0.6-0.7); every UV
    selected (UV Sync Selection on, vertex mode)."""
    _clear()
    verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (3, 0, 0), (4, 0, 0), (4, 1, 0), (3, 1, 0)]
    me = bpy.data.meshes.new("q")
    me.from_pydata(verts, [], [(0, 1, 2, 3), (4, 5, 6, 7)])
    me.uv_layers.new(name="UVMap")
    ob = bpy.data.objects.new("q", me)
    bpy.context.collection.objects.link(ob)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (True, False, False)
    bm = bmesh.from_edit_mesh(me)
    uv = bm.loops.layers.uv.active
    boxes = {0: ((0.1, 0.1), (0.3, 0.2)), 1: ((0.6, 0.6), (0.7, 0.7))}
    for f in bm.faces:
        (u0, v0), (u1, v1) = boxes[f.index]
        for lp in f.loops:
            x, y = lp.vert.co.x % 3, lp.vert.co.y
            lp[uv].uv = (u0 + (u1 - u0) * x, v0 + (v1 - v0) * y)
    for v in bm.verts:
        v.select = True
    bm.select_flush(True)
    bmesh.update_edit_mesh(me)
    return ob


def _select_face(ob, index):
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.select = False
    for e in bm.edges:
        e.select = False
    for f in bm.faces:
        f.select = False
    bm.faces.ensure_lookup_table()
    bm.faces[index].select_set(True)
    bm.select_flush(True)
    bmesh.update_edit_mesh(ob.data)


def _uv_area():
    scr = bpy.context.window.screen
    a = next(a for a in scr.areas if a.type in ('VIEW_3D', 'IMAGE_EDITOR'))
    a.ui_type = 'UV'
    return a, next(r for r in a.regions if r.type == 'WINDOW')


def _run(op, **props):
    a, r = _uv_area()
    with bpy.context.temp_override(area=a, region=r):
        res = getattr(bpy.ops.allset, op)(**props)
    assert res == {'FINISHED'}, (op, props, res)
    return a.spaces.active


def _uvs(ob, face):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    return sorted((round(lp[uv].uv.x, 5), round(lp[uv].uv.y, 5)) for lp in bm.faces[face].loops)


def _box(pts):
    return (round(min(p[0] for p in pts), 5), round(min(p[1] for p in pts), 5),
            round(max(p[0] for p in pts), 5), round(max(p[1] for p in pts), 5))


def _tk():
    return bpy.context.scene.allset_uv_toolkit


def test_transform_defaults():
    tk = _tk()
    assert math.isclose(tk.nudge, 0.1, abs_tol=1e-6) and math.isclose(tk.rotate_angle, 90.0)
    assert math.isclose(tk.scale_factor, 2.0) and tk.scale_axis == 'UV' and tk.pivot_area == 'SELECTION'
    assert (tk.pivot_min_u, tk.pivot_max_u, tk.pivot_min_v, tk.pivot_max_v) == (0, 1, 0, 1)
    assert (tk.snap_min_u, tk.snap_max_u, tk.snap_min_v, tk.snap_max_v) == (0, 1, 0, 1)


def test_move_buttons_and_position_fields():
    ob = _two_quads()
    _select_face(ob, 0)
    _run("uv_nudge", direction='UP_RIGHT')
    assert _box(_uvs(ob, 0)) == (0.2, 0.2, 0.4, 0.3), _uvs(ob, 0)
    assert _box(_uvs(ob, 1)) == (0.6, 0.6, 0.7, 0.7), "the other shell stays"
    _tk().nudge = 0.05
    _run("uv_nudge", direction='LEFT')
    assert _box(_uvs(ob, 0)) == (0.15, 0.2, 0.35, 0.3)
    _tk().nudge = 0.1
    # the U / V fields read the centre of the selection and move it there, spacing kept
    a, r = _uv_area()
    with bpy.context.temp_override(area=a, region=r):
        uv_hud._invalidate()
        assert math.isclose(_tk().position_u, 0.25, abs_tol=1e-5), _tk().position_u
        assert math.isclose(_tk().position_v, 0.25, abs_tol=1e-5), _tk().position_v
        _tk().position_u = 0.5
        _tk().position_v = 0.75
    assert _box(_uvs(ob, 0)) == (0.4, 0.7, 0.6, 0.8), _uvs(ob, 0)


def test_rotate_about_the_selection_centre_and_the_pivot():
    ob = _two_quads()
    _select_face(ob, 0)
    space = _run("uv_pivot_reset")
    assert space.pivot_point == 'BOUNDING_BOX_CENTER'
    _run("uv_rotate_step", clockwise=False)         # 90 counterclockwise about (0.2, 0.15)
    assert _box(_uvs(ob, 0)) == (0.15, 0.05, 0.25, 0.25), _uvs(ob, 0)
    _run("uv_rotate_step", clockwise=True)
    assert _box(_uvs(ob, 0)) == (0.1, 0.1, 0.3, 0.2)
    # pivot on the bottom left corner: a quarter turn counterclockwise puts the shell left of it
    space = _run("uv_pivot", position='BOTTOM_LEFT')
    assert space.pivot_point == 'CURSOR'
    u, v = uvx.cursor_uv(space)
    assert math.isclose(u, 0.1, abs_tol=1e-5) and math.isclose(v, 0.1, abs_tol=1e-5), (u, v)
    _run("uv_rotate_step", clockwise=False)
    assert _box(_uvs(ob, 0)) == (0.0, 0.1, 0.1, 0.3), _uvs(ob, 0)
    _run("uv_pivot_reset")


def test_scale_factor_axis_and_shrink():
    ob = _two_quads()
    _select_face(ob, 0)
    _run("uv_pivot_reset")
    _run("uv_scale_step")                            # x2 about (0.2, 0.15)
    assert _box(_uvs(ob, 0)) == (0.0, 0.05, 0.4, 0.25), _uvs(ob, 0)
    _run("uv_scale_step", shrink=True)
    assert _box(_uvs(ob, 0)) == (0.1, 0.1, 0.3, 0.2), _uvs(ob, 0)
    _tk().scale_axis = 'V'
    try:
        _run("uv_scale_step")
        assert _box(_uvs(ob, 0)) == (0.1, 0.05, 0.3, 0.25), "V only"
    finally:
        _tk().scale_axis = 'UV'


def test_pivot_places_on_the_selection_and_the_uv_area():
    ob = _two_quads()
    _select_face(ob, 1)
    for place, want in (('TOP_LEFT', (0.6, 0.7)), ('TOP', (0.65, 0.7)), ('RIGHT', (0.7, 0.65)),
                        ('CENTER', (0.65, 0.65)), ('BOTTOM_RIGHT', (0.7, 0.6))):
        space = _run("uv_pivot", position=place)
        got = uvx.cursor_uv(space)
        assert all(math.isclose(g, w, abs_tol=1e-5) for g, w in zip(got, want)), (place, got)
    _tk().pivot_area = 'UV_AREA'
    try:
        space = _run("uv_pivot", position='TOP_RIGHT')
        assert all(math.isclose(g, 1.0, abs_tol=1e-5) for g in uvx.cursor_uv(space))
        _tk().pivot_max_u = 2
        space = _run("uv_pivot", position='TOP')
        got = uvx.cursor_uv(space)
        assert math.isclose(got[0], 1.0, abs_tol=1e-5) and math.isclose(got[1], 1.0, abs_tol=1e-5), got
    finally:
        _tk().pivot_area = 'SELECTION'
        _tk().pivot_max_u = 1
    _run("uv_pivot_reset")


def test_snap_moves_the_selected_shells_as_one_block():
    ob = _two_quads()
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:          # one UV of shell A and one of shell B: both whole shells move
        v.select = v.index in (0, 4)
    bm.select_flush(True)
    bmesh.update_edit_mesh(ob.data)
    _run("uv_snap_shells", position='BOTTOM_LEFT')
    a, b = _box(_uvs(ob, 0)), _box(_uvs(ob, 1))
    assert a == (0.0, 0.0, 0.2, 0.1) and b == (0.5, 0.5, 0.6, 0.6), (a, b)
    _run("uv_snap_shells", position='CENTER')        # block 0.6 x 0.6 centred in 0-1
    a, b = _box(_uvs(ob, 0)), _box(_uvs(ob, 1))
    assert a == (0.2, 0.2, 0.4, 0.3) and b == (0.7, 0.7, 0.8, 0.8), (a, b)
    _run("uv_snap_shells", position='TOP_RIGHT')
    assert _box(_uvs(ob, 1))[2:] == (1.0, 1.0)


def test_nothing_selected_warns():
    ob = _two_quads()
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.select = False
    bm.select_flush(False)
    bmesh.update_edit_mesh(ob.data)
    a, r = _uv_area()
    with bpy.context.temp_override(area=a, region=r):
        for op, props in (("uv_nudge", {}), ("uv_rotate_step", {}), ("uv_scale_step", {}),
                          ("uv_snap_shells", {}), ("uv_pivot", {})):
            assert getattr(bpy.ops.allset, op)(**props) == {'CANCELLED'}, op
