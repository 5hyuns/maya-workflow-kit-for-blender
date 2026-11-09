"""Issue #340: Preserve UVs and Transform Constraint Edge keep the UV layout in place.

Blender's UV correction (Preserve UVs, and the edge / vertex slide of Transform Constraint Edge) projects each moved
point through the stored face normals. The Scale tool and Universal Manipulator drags put the points back before
each preview and before the final step, so they refresh those normals too: a released drag with Preserve UVs on
corrects the UVs exactly like one plain resize / rotate, and a cancelled drag leaves nothing stale for the next Move.
Points typed in the Input Line or the Component Editor refresh them the same way. The Edge slide corrects UVs only
with Preserve UVs on, like Maya. While a transform runs, the pre-selection caches keep the edit mesh's BMesh wrapper
alive (releasing it moves the loop data the slide's UV correction points into). GUI (the slides, with the UV Editor
open): tests/gui/gui_issue340_preserve_uvs.py."""

from importlib import import_module

import bmesh
import bpy

import kit

ms = import_module(kit.MODULE + ".operators.manip_scale")
um = import_module(kit.MODULE + ".operators.universal_manip")
xc = import_module(kit.MODULE + ".operators.xform_constraint")
il = import_module(kit.MODULE + ".ui.input_line")
ce = import_module(kit.MODULE + ".ui.component_editor")

TOL = 1e-4


def _override():
    """Operators run on the window alone: a background 3D View area has no region types (a registered operator's
    redo panel would crash Blender there)."""
    return bpy.context.temp_override(window=bpy.context.window_manager.windows[0])


def _sphere():
    """A Maya sphere in edit mode with a patch of side faces selected."""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    with _override():
        bpy.ops.allset.create(kind='SPHERE')
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(ob.data)
    r = max(v.co.length for v in bm.verts)
    for f in bm.faces:
        c = f.calc_center_median()
        if c.x > 0.6 * r and abs(c.z) < 0.35 * r and abs(c.y) < 0.5 * r:
            f.select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    assert any(f.select for f in bm.faces)
    ts = bpy.context.scene.tool_settings
    ts.use_proportional_edit = False
    ts.use_transform_correct_face_attributes = True
    return ob


def _state(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    return [v.co.copy() for v in bm.verts], [l[uv].uv.copy() for f in bm.faces for l in f.loops]


def _put(ob, state):
    """Back to ``state`` with fresh normals (what the mesh looks like before a drag)."""
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    for v, co in zip(bm.verts, state[0]):
        v.co = co
    for l, u in zip((l for f in bm.faces for l in f.loops), state[1]):
        l[uv].uv = u
    bm.normal_update()
    bmesh.update_edit_mesh(ob.data)


def _uv_gap(a, b):
    return max((p - q).length for p, q in zip(a[1], b[1]))


def _stale(ob):
    """How far the stored face / vertex normals are from the mesh's real ones (0 = fresh)."""
    bm = bmesh.from_edit_mesh(ob.data)
    fresh = bm.copy()
    fresh.normal_update()
    gap = max(max((a.normal - b.normal).length for a, b in zip(bm.faces, fresh.faces)),
              max((a.normal - b.normal).length for a, b in zip(bm.verts, fresh.verts)))
    fresh.free()
    return gap


def _scale_drag(ob, preview, final):
    """The Scale tool drag: previews from the saved state, then the final resize (None = cancelled)."""
    with _override():
        st = ms.save_state(bpy.context)
        for f in preview:
            ms.restore(st)
            ms.apply(bpy.context, f)
        ms.restore(st)
        if final is not None:
            ms.apply(bpy.context, final, final=True)


def test_scale_drag_preserves_uvs_like_one_resize():
    ob = _sphere()
    orig = _state(ob)
    with _override():
        ms.apply(bpy.context, 1.6, final=True)
    want = _state(ob)
    assert _uv_gap(orig, want) > 1e-3, "Preserve UVs moves the scaled faces' UVs"
    _put(ob, orig)
    _scale_drag(ob, (1.2, 2.4, 0.5), 1.6)
    got = _state(ob)
    assert max((p - q).length for p, q in zip(got[0], want[0])) < 1e-5, "same geometry as one resize"
    gap = _uv_gap(got, want)
    assert gap < TOL, f"the UVs after the drag differ from one resize by {gap:.4f}"
    assert _stale(ob) < 1e-4


def test_cancelled_scale_drag_leaves_fresh_normals():
    ob = _sphere()
    orig = _state(ob)
    _scale_drag(ob, (1.8, 0.4), None)
    assert max((p - q).length for p, q in zip(_state(ob)[0], orig[0])) < 1e-6, "the cancel puts the points back"
    assert _stale(ob) < 1e-4, f"stale normals after a cancelled Scale drag ({_stale(ob):.3f})"


def _move(ob, value):
    with _override():
        bpy.ops.transform.translate(value=value, orient_type='GLOBAL')


def test_move_after_cancelled_scale_drag_preserves_uvs():
    """A Move with Preserve UVs right after a cancelled Scale drag: the same UVs as on the untouched mesh."""
    ob = _sphere()
    orig = _state(ob)
    r = max(c.length for c in orig[0])
    _move(ob, (0, 0.3 * r, 0.2 * r))
    want = _state(ob)
    _put(ob, orig)
    _scale_drag(ob, (2.0, 0.3), None)
    _move(ob, (0, 0.3 * r, 0.2 * r))
    gap = _uv_gap(_state(ob), want)
    assert gap < TOL, f"Move with Preserve UVs after a cancelled Scale drag: UVs off by {gap:.4f}"


def _um_drag(ob, final):
    """The Universal Manipulator scale drag on the component box."""
    with _override():
        frame, lo, hi = um.box_of(bpy.context, 'WORLD')
        fixed = frame @ um.centre(lo, hi)
        st = um.save_state(bpy.context)
        for f in ((1.5, 1.5, 1.5), (0.6, 0.6, 0.6)):
            um.restore(st)
            um.apply_scale(f, frame, fixed)
        um.restore(st)
        if final:
            um.apply_scale((1.4, 1.4, 1.4), frame, fixed, final=True)
    return frame, fixed


def test_universal_manipulator_drag_preserves_uvs():
    ob = _sphere()
    orig = _state(ob)
    with _override():
        frame, lo, hi = um.box_of(bpy.context, 'WORLD')
        um.apply_scale((1.4, 1.4, 1.4), frame, frame @ um.centre(lo, hi), final=True)
    want = _state(ob)
    _put(ob, orig)
    _um_drag(ob, True)
    gap = _uv_gap(_state(ob), want)
    assert gap < TOL, f"Universal Manipulator drag with Preserve UVs: UVs off by {gap:.4f}"
    _put(ob, orig)
    _um_drag(ob, False)
    assert _stale(ob) < 1e-4, "a cancelled Universal Manipulator drag leaves fresh normals"


def test_input_line_and_component_editor_leave_fresh_normals():
    ob = _sphere()
    with _override():
        il._transform_components(bpy.context, 'SCALE', [(0, 1.7), (1, 1.7), (2, 1.7)], True)
    assert _stale(ob) < 1e-4, "Input Line component scale leaves fresh normals"
    bm = bmesh.from_edit_mesh(ob.data)
    vi = next(v.index for v in bm.verts if v.select)
    ce.set_position(ob, vi, 'x', 3.0, bpy.context.scene)
    assert _stale(ob) < 1e-4, "Component Editor position edit leaves fresh normals"


def test_edge_slide_corrects_uvs_only_with_preserve_uvs():
    ts = bpy.context.scene.tool_settings
    for on in (False, True):
        ts.use_transform_correct_face_attributes = on
        assert xc.slide_options(bpy.context) == {"correct_uv": on}, xc.slide_options(bpy.context)
    for on in (False, True):
        ob = _sphere()
        ts.use_transform_correct_face_attributes = on
        orig = _state(ob)
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(ob.data)
        bm.verts.ensure_lookup_table()
        v = max(bm.verts, key=lambda v: v.co.x)
        v.select_set(True)
        bm.select_flush_mode()
        bmesh.update_edit_mesh(ob.data)
        # Blender reads a slide's Correct UVs only in a 3D View (no undo step here: no redo panel in background)
        w = bpy.context.window_manager.windows[0]
        area = next(a for a in w.screen.areas if a.type == 'VIEW_3D')
        region = next(r for r in area.regions if r.type == 'WINDOW')
        with bpy.context.temp_override(window=w, area=area, region=region):
            bpy.ops.transform.vert_slide(value=0.6, **xc.slide_options(bpy.context))
        got = _state(ob)
        assert max((p - q).length for p, q in zip(got[0], orig[0])) > 1e-4, "the vertex slid"
        gap = _uv_gap(got, orig)
        if on:
            assert gap > 1e-4, "Preserve UVs on: the slid vertex's UVs follow"
        else:
            assert gap < 1e-7, f"Preserve UVs off: the UVs stay ({gap:.5f})"
    ts.use_transform_correct_face_attributes = False


def test_preselect_keeps_the_edit_bmesh_while_a_transform_runs():
    """The pre-selection caches hold the edit mesh's BMesh wrapper. A depsgraph update during a transform drops the
    caches but keeps that wrapper until the transform ends (its release would move the loop data a running UV
    correction points into); afterwards it is released."""
    ps = import_module(kit.MODULE + ".operators.preselect")
    ob = _sphere()
    ps._cache.clear()
    c = ps._cache[ob.as_pointer()] = ps.MeshCache(ob)
    running = [True]
    real = ps._edit_modal_running
    ps._edit_modal_running = lambda: running[0]
    try:
        ps.invalidate()
        assert not ps._cache, "the caches are dropped"
        assert ps._held.get(ob.as_pointer()) is c.bm, "... but their edit BMesh stays referenced during the transform"
        running[0] = False
        ps.invalidate()
        assert not ps._held, "released once no transform runs"
    finally:
        ps._edit_modal_running = real
        ps._held.clear()
    assert real() is False, "no transform runs in background"
