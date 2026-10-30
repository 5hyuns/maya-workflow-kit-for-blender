"""Skin layer maths (operators/skin_layers_math.py, no bpy): compositing a layer stack, the edit rule, Set Weights,
smoothing, mirroring columns, Assign from Closest Joint."""

from importlib import import_module

import numpy as np

import kit

m = import_module(kit.MODULE + ".operators.skin_layers_math")


def _layer(weights, mask=None, opacity=1.0, enabled=True):
    return {"weights": weights, "mask": mask, "opacity": opacity, "enabled": enabled}


def test_base_layer_alone_is_the_result():
    base = _layer({"a": [1.0, 0.25, 0.0], "b": [0.0, 0.75, 1.0]})
    out = m.composite([base], 3, ["a", "b"])
    assert np.allclose(out, [[1, 0], [0.25, 0.75], [0, 1]])


def test_full_layer_replaces_by_mask_times_opacity():
    base = _layer({"a": [1.0, 1.0, 1.0]})
    top = _layer({"b": [1.0, 1.0, 1.0]}, mask=[1.0, 0.5, 0.0], opacity=0.5)
    out = m.composite([top, base], 3, ["a", "b"])
    # coverage 0.5 / 0.25 / 0
    assert np.allclose(out, [[0.5, 0.5], [0.75, 0.25], [1.0, 0.0]])


def test_partial_layer_lets_the_lower_result_show_through():
    base = _layer({"a": [1.0], "b": [0.0]})
    top = _layer({"b": [0.4]})
    out = m.composite([top, base], 1, ["a", "b"])
    assert np.allclose(out, [[0.6, 0.4]])


def test_empty_or_disabled_layer_changes_nothing():
    base = _layer({"a": [0.3, 1.0], "b": [0.7, 0.0]})
    empty = _layer({})
    off = _layer({"b": [1.0, 1.0]}, enabled=False)
    out = m.composite([off, empty, base], 2, ["a", "b"])
    assert np.allclose(out, [[0.3, 0.7], [1.0, 0.0]])


def test_layer_over_one_is_clamped_and_result_normalised():
    base = _layer({"a": [0.5]})                        # a base that weighs 0.5 still ends at 1
    assert np.allclose(m.composite([base], 1, ["a", "b"]), [[1.0, 0.0]])
    big = _layer({"a": [2.0], "b": [2.0]})
    assert np.allclose(m.composite([big], 1, ["a", "b"]), [[0.5, 0.5]])


def test_unknown_influence_is_ignored_and_no_weight_stays_zero():
    out = m.composite([_layer({"zz": [1.0]})], 1, ["a"])
    assert np.allclose(out, [[0.0]])


def test_settle_rows_makes_room_but_never_inflates():
    old = np.array([[0.8, 0.2, 0.0], [0.0, 0.0, 0.0], [0.5, 0.5, 0.0]])
    new = old.copy()
    new[0, 2] = 0.5          # others 1.0 -> 0.5 room: scaled 0.4 / 0.1
    new[1, 0] = 0.5          # empty row: stays 0.5 (lower layers fill the rest)
    out = m.settle_rows(old, new)
    assert np.allclose(out[0], [0.4, 0.1, 0.5])
    assert np.allclose(out[1], [0.5, 0.0, 0.0])
    assert np.allclose(out[2], [0.5, 0.5, 0.0])        # unchanged row kept
    lower = np.array([[0.2, 0.2, 0.0]])
    up = lower.copy()
    up[0, 0] = 0.6           # others 0.2 fit in 0.4: kept
    assert np.allclose(m.settle_rows(lower, up), [[0.6, 0.2, 0.0]])


def test_set_value_modes():
    w = np.array([[0.6, 0.4], [1.0, 0.0], [0.0, 0.0]])
    rows = [0, 1, 2]
    r = m.set_value(w, rows, 1, "REPLACE", 1.0)
    assert np.allclose(r, [[0, 1], [0, 1], [0, 1]])
    a = m.set_value(w, rows, 1, "ADD", 0.25)
    assert np.allclose(a, [[0.35, 0.65], [0.75, 0.25], [0.0, 0.25]])
    s = m.set_value(w, [0], 0, "SCALE", 0.5)
    assert np.allclose(s, [[0.3, 0.4], [1.0, 0.0], [0.0, 0.0]])


def test_smooth_moves_rows_toward_neighbours():
    nb = [[1], [0, 2], [1]]
    v = m.smooth([0.0, 1.0, 0.0], nb, [1], 1.0)
    assert np.allclose(v, [0.0, 0.0, 0.0])
    v = m.smooth([0.0, 1.0, 0.0], nb, [0, 1, 2], 0.5)
    assert np.allclose(v, [0.5, 0.5, 0.5])        # every row moves halfway to its old neighbours


def test_mirror_columns_and_closest_joint():
    w = np.array([[1.0, 0.0], [0.0, 0.0]])
    out = m.mirror_columns(w, [0], {0: 1, 1: 0}, [1])
    assert np.allclose(out, [[1, 0], [0, 1]])
    assert np.allclose(m.closest_joint([[2.0, 1.0], [0.5, 3.0]]), [[0, 1], [1, 0]])
