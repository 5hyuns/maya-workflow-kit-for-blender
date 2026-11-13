"""Graph Editor keys and tangent handles with a keyed rig: one read of the curves per draw serves the bigger keys and
the kit's handles, with the same numbers as reading every curve key by key; rings are drawn from their corner points;
a view drag (pan / zoom) keeps the keys it read and moves its drawing while the scale stays."""

import math
from importlib import import_module
from types import SimpleNamespace

import bpy
import numpy as np

import kit

gk = import_module(kit.MODULE + ".ui.graph_keys_draw")
gh = import_module(kit.MODULE + ".ui.graph_handles")
layers = import_module(kit.MODULE + ".ui.graph_layers")
weights = import_module(kit.MODULE + ".operators.graph_weights")


class View2D:
    def __init__(self, px_frame=20.0, px_value=10.0, x0=100.0, y0=200.0):
        self.f, self.v, self.x0, self.y0 = px_frame, px_value, x0, y0

    def region_to_view(self, x, y):
        return (x - self.x0) / self.f, (y - self.y0) / self.v


def _region():
    return SimpleNamespace(type='WINDOW', width=800, height=600, x=0, y=0, view2d=View2D())


def _gspace(**kw):
    base = dict(type='GRAPH_EDITOR', mode='FCURVES', use_normalization=False, show_handles=True,
                use_only_selected_keyframe_handles=False)
    base.update(kw)
    return SimpleNamespace(**base)


def _ctx(fcurves, space):
    return SimpleNamespace(visible_fcurves=list(fcurves), scene=bpy.context.scene, space_data=space,
                           preferences=bpy.context.preferences)


def _keyed(curves=6, keys=7):
    """Curves with mixed interpolation, selections, weighted and not, rotation curves (degrees), a hidden one."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    ob = bpy.data.objects.new("pCube1", bpy.data.meshes.new("pCubeShape1"))
    bpy.context.scene.collection.objects.link(ob)
    for f in range(keys):
        ob.location = (math.sin(f), math.cos(f) * 3, f * 0.5)
        ob.rotation_euler = (0.1 * f, 0.2 * f, -0.3 * f)
        ob.scale = (1.0, 1.0 + 0.1 * f, 1.0)
        ob.keyframe_insert("location", frame=1 + 4 * f)
        ob.keyframe_insert("rotation_euler", frame=1 + 4 * f)
        ob.keyframe_insert("scale", frame=1 + 4 * f)
    fcs = list(kit.fcurves(ob))[:curves + 3]
    rng = np.random.default_rng(7)
    ipos = ('BEZIER', 'LINEAR', 'CONSTANT', 'BEZIER', 'BEZIER')
    for i, fc in enumerate(fcs):
        weights.set_weighted(fc, i % 2 == 0)
        weights.third_arms(fc)
        for j, kp in enumerate(fc.keyframe_points):
            kp.select_control_point = bool(rng.integers(0, 3) == 0)
            kp.select_left_handle = bool(rng.integers(0, 2))
            kp.select_right_handle = bool(rng.integers(0, 2))
            kp.interpolation = ipos[(i + j) % len(ipos)]
    fcs[-1].hide = True
    return fcs


def _old_sides(ipo):
    bez = ipo == 'BEZIER'
    left = np.empty_like(bez)
    if len(bez):
        left[0] = bez[0]
        left[1:] = bez[:-1]
    return left, bez


def _old_handles(context, space, region):
    """Reference: the handles read curve by curve, key by key."""
    out = {k: [] for k in ("curves", "keys", "sides", "key_px", "end_px", "selected", "weighted")}
    fcurves = []
    if not gh.shows_handles(space):
        return out, fcurves
    scene = context.scene
    near = bool(space.use_only_selected_keyframe_handles)
    for fc in context.visible_fcurves:
        if not gk.draws_keys(fc, False):
            continue
        kps = fc.keyframe_points
        n = len(kps)
        flags = {}
        for name in ("select_control_point", "select_left_handle", "select_right_handle"):
            flags[name] = np.array([getattr(kp, name) for kp in kps], dtype=bool)
        left_on, right_on = _old_sides(np.array([kp.interpolation for kp in kps]))
        key_sel = flags["select_control_point"]
        if near:
            any_sel = key_sel | flags["select_left_handle"] | flags["select_right_handle"]
            left_on, right_on = left_on & any_sel, right_on & any_sel
        if not (left_on.any() or right_on.any()):
            continue
        off, k = layers.normalization(fc) if space.use_normalization else (0.0, layers.value_factor(scene, fc))

        def view(prop):
            co = np.array([tuple(getattr(kp, prop)) for kp in kps], dtype=np.float64).reshape(n, 2)
            co[:, 1] = (co[:, 1] + off) * k
            return co
        key_px = gk.to_region(region, view("co"))
        weighted = weights.is_weighted(fc)
        ci = len(fcurves)
        fcurves.append(fc)
        for side, prop, shown, picked in ((0, "handle_left", left_on, flags["select_left_handle"]),
                                          (1, "handle_right", right_on, flags["select_right_handle"])):
            idx = np.nonzero(shown)[0]
            if not len(idx):
                continue
            ends = gk.to_region(region, view(prop))[idx]
            if not weighted:
                ends = gh.fixed_ends(key_px[idx], ends, np.full(len(idx), side), gh.fixed_px(context))
            out["curves"] += [ci] * len(idx)
            out["keys"] += list(idx)
            out["sides"] += [side] * len(idx)
            out["key_px"] += list(key_px[idx])
            out["end_px"] += list(ends)
            out["selected"] += list(picked[idx] & ~key_sel[idx])
            out["weighted"] += [weighted] * len(idx)
    return out, fcurves


def test_handles_match_reading_every_key():
    fcs = _keyed()
    region = _region()
    for space in (_gspace(), _gspace(use_only_selected_keyframe_handles=True), _gspace(use_normalization=True)):
        ctx = _ctx(fcs, space)
        h = gh.Handles(ctx, space, region)
        want, curves = _old_handles(ctx, space, region)
        assert h.fcurves == curves
        assert len(h) == len(want["keys"]) > 0, (len(h), len(want["keys"]))
        for name in ("curves", "keys", "sides", "selected", "weighted"):
            assert np.array_equal(getattr(h, name), np.array(want[name])), name
        assert np.array_equal(h.key_px, np.array(want["key_px"]))           # the same numbers, bit for bit
        assert np.array_equal(h.end_px, np.array(want["end_px"]))
        assert h.selected.dtype == bool and h.weighted.dtype == bool
    empty = gh.Handles(_ctx(fcs, _gspace(show_handles=False)), _gspace(show_handles=False), region)
    assert not len(empty) and empty.key_px.shape == (0, 2)


def test_key_and_handle_points_match_reading_every_key():
    fcs = _keyed()
    space = _gspace()
    ctx = _ctx(fcs, space)
    unsel, sel = gk.key_points(ctx, space)
    want_u, want_s = [], []
    h_u, h_s = [], []
    for fc in fcs:
        if not gk.draws_keys(fc, False):
            continue
        k = layers.value_factor(bpy.context.scene, fc)
        bez = np.array([kp.interpolation == 'BEZIER' for kp in fc.keyframe_points])
        left = np.concatenate([bez[:1], bez[:-1]])
        for kp in fc.keyframe_points:
            (want_s if kp.select_control_point else want_u).append((kp.co[0], kp.co[1] * k))
        for side, prop, shown in ((0, "handle_left", left), (1, "handle_right", bez)):
            for kp, on in zip(fc.keyframe_points, shown):
                if on:
                    picked = kp.select_left_handle if side == 0 else kp.select_right_handle
                    (h_s if picked else h_u).append((getattr(kp, prop)[0], getattr(kp, prop)[1] * k))
    assert np.array_equal(unsel, np.array(want_u)) and np.array_equal(sel, np.array(want_s))
    got_u, got_s = gk.handle_points(ctx, space)
    assert np.array_equal(got_u, np.array(h_u)) and np.array_equal(got_s, np.array(h_s))


def test_one_read_serves_keys_and_handles():
    fcs = _keyed()
    space, region = _gspace(), _region()
    ctx = _ctx(fcs, space)
    keys = gk.Keys(ctx, space, handles=True)
    assert all(np.array_equal(a, b) for a, b in zip(gk.key_points(ctx, space, keys), gk.key_points(ctx, space)))
    assert all(np.array_equal(a, b) for a, b in zip(gk.handle_points(ctx, space, keys),
                                                    gk.handle_points(ctx, space)))
    shared, own = gh.Handles(ctx, space, region, keys=keys), gh.Handles(ctx, space, region)
    assert np.array_equal(shared.end_px, own.end_px) and np.array_equal(shared.selected, own.selected)


def test_handles_map_the_view_once():
    """The view -> region map is read twice per draw, not three times per curve."""
    fcs = _keyed(curves=9)
    space, region = _gspace(), _region()
    real, calls = gk.to_region, [0]

    def counted(r, pts):
        calls[0] += 1
        return real(r, pts)
    gk.to_region = counted
    try:
        h = gh.Handles(_ctx(fcs, space), space, region)
    finally:
        gk.to_region = real
    assert len(h.fcurves) >= 6 and calls[0] <= 2, (len(h.fcurves), calls[0])


def test_rim_mesh_draws_the_rims_triangles():
    centres = np.array([[50.0, 50.0], [-100.0, 50.0], [60.0, 2000.0], [123.25, 77.5], [0.1, 1e-7]])
    for kw in ({}, {"width": 200, "height": 100}):
        verts, tris = gk.rim_mesh(centres, 3.0, 7.0, **kw)
        flat = gk.rims(centres, 3.0, 7.0, **kw)
        assert verts.dtype == np.float32 and tris.dtype == np.int32
        assert verts[tris].reshape(-1, 2).tobytes() == flat.tobytes(), kw    # same triangles, order, bits
    verts, tris = gk.rim_mesh(np.zeros((0, 2)), 3.0, 7.0)
    assert verts.shape == (0, 2) and tris.shape == (0, 3)


def test_a_view_drag_keeps_the_keys_it_read():
    fcs = _keyed()
    space, region = _gspace(), SimpleNamespace(as_pointer=lambda: 42, **vars(_region()))
    space.as_pointer = lambda: 7

    def ctx(*ops):
        window = SimpleNamespace(modal_operators=[SimpleNamespace(bl_idname=i, as_pointer=lambda p=p: p)
                                                  for p, i in ops])
        return SimpleNamespace(window=window, **vars(_ctx(fcs, space)))
    drag = ctx((1, "ALLSET_OT_cb_wheel"), (2, "ALLSET_OT_nav_2d"))
    first = gk.drawn_keys(drag, space, region, True)
    assert gk.drawn_keys(drag, space, region, True) is first             # the same drag: kept
    assert gk.drawn_keys(drag, space, region, False) is not first        # another read asked
    first = gk.drawn_keys(drag, space, region, True)
    gk._on_depsgraph()                                                   # a script / timer edited something
    second = gk.drawn_keys(drag, space, region, True)
    assert second is not first
    plain = ctx((1, "ALLSET_OT_cb_wheel"))
    assert gk.drawn_keys(plain, space, region, True) is not gk.drawn_keys(plain, space, region, True)
    # after a draw without a drag, the next drag reads again (even if its operator reuses the address)
    assert gk.drawn_keys(drag, space, region, True) is not second
    # what is drawn during the drag is the same as a fresh read
    kept = gk.drawn_keys(drag, space, region, True)
    fresh = gk.Keys(_ctx(fcs, space), space, handles=True)
    assert np.array_equal(kept.co, fresh.co) and np.array_equal(kept.right, fresh.right)


def test_pan_shift_and_zoom():
    old = (10.0, -2.0, 20.0, 10.0)
    assert gk.panned(old, (12.5, -1.0, 20.0, 10.0)) == (-50.0, -10.0)       # 2.5 frames left = 50 px
    assert gk.panned(old, (12.5, -1.0, 20.0 * (1 + 1e-9), 10.0)) is not None   # float rounding of the view
    assert gk.panned(old, (12.5, -1.0, 22.0, 10.0)) is None                    # a zoom: drawn anew


def test_handlers_follow_enable():
    assert gk._on_depsgraph in bpy.app.handlers.depsgraph_update_post
    kit.disable()
    try:
        assert gk._on_depsgraph not in bpy.app.handlers.depsgraph_update_post
        assert gk._on_load not in bpy.app.handlers.load_post
    finally:
        kit.enable()
    assert gk._on_depsgraph in bpy.app.handlers.depsgraph_update_post
