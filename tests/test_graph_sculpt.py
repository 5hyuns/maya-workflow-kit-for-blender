"""Graph Editor Sculpting Tools like Maya: the brush falloff, the Smooth and Key Reducer rules and the menu items."""

from importlib import import_module

import bpy

import kit

gs = import_module(kit.MODULE + ".operators.graph_sculpt")
menu_map = import_module(kit.MODULE + ".ui.editor_menu_map")
notices = import_module(kit.MODULE + ".ui.notices")


def test_falloff_shape():
    f = gs.falloff
    assert f(0) == 1.0 and f(1) == 0.0 and f(1.5) == 0.0
    assert abs(f(0.25) - 0.9) < 1e-9 and abs(f(0.75) - 0.1) < 1e-9
    vals = [f(i / 50) for i in range(51)]
    assert all(a >= b for a, b in zip(vals, vals[1:])), "falls off steadily"
    # one, two and three frames across from the middle with the default size (Maya: .83 / .37 / .03), at any zoom
    for d, want in ((1, 0.83), (2, 0.37), (3, 0.03)):
        u = gs.brush_distance(d, 0, gs.RADIUS_PX)
        assert abs(f(u) - want) < 0.07, (d, f(u))
    # one, two, three value steps of 14.6 px up (Maya: .74 / .36 / .06), four (58 px): outside
    for d, want in ((14.6, 0.74), (29.2, 0.36), (43.8, 0.06)):
        u = gs.brush_distance(0, d, gs.RADIUS_PX)
        assert abs(f(u) - want) < 0.2, (d, f(u))
    assert f(gs.brush_distance(0, 58.4, gs.RADIUS_PX)) == 0.0


def test_smooth_and_reduce_rules():
    assert gs.smooth_target(0.0, 8.0, 0.0) == 0.0
    assert gs.smooth_target(None, 8.0, 0.0) == 8.0, "a curve end stays"
    assert gs.reducible((0, 0), (10, 10.5), (20, 20), 1.0)
    assert not gs.reducible((0, 0), (10, 14), (20, 20), 1.0)


def test_menu_items():
    m = menu_map.MAP
    base = "Graph Editor/Edit/Transformation Tools/Sculpting Tools/"
    for item, mode in (("Grab Tool", "GRAB"), ("Smooth Tool", "SMOOTH"), ("Smear Tool", "SMEAR"),
                       ("Key Reducer Tool", "REDUCE")):
        assert m[base + item] == ("allset.graph_sculpt", {"mode": mode})
    assert "Graph Editor/Edit/Transformation Tools/Sculpting Tools" not in notices.NOTICES
    assert bpy.context.window_manager.allset_sculpt_keys_radius == 0.0
