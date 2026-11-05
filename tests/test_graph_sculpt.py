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
    # one, two and three frames from the middle at 19.5 px per frame with the default radius (Maya: .82 / .37 / .03)
    for d, want in ((19.5, 0.82), (39.0, 0.37), (58.4, 0.03)):
        assert abs(f(d / gs.RADIUS_PX) - want) < 0.07, (d, f(d / gs.RADIUS_PX))


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
