"""Viewport settings memory (ui/viewport_settings.py): a panel's display settings survive a JSON round trip
and come back on apply; save writes only when something changed."""

import json
import os
import tempfile
from importlib import import_module

import bpy

import kit

vs = import_module(kit.MODULE + ".ui.viewport_settings")


def _screen_area():
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                return screen, area
    raise AssertionError("no 3D View in the startup file")


def test_capture_round_trips_through_json_and_apply():
    screen, area = _screen_area()
    space = area.spaces.active
    saved = json.loads(json.dumps(vs.capture(screen, area)))      # what the file stores
    old_type, old_gizmo = space.shading.type, space.show_gizmo
    space.shading.type = 'WIREFRAME' if old_type != 'WIREFRAME' else 'SOLID'
    space.show_gizmo = not old_gizmo
    vs.apply(screen, area, saved)
    assert space.shading.type == old_type
    assert space.show_gizmo == old_gizmo
    assert "view" not in saved            # camera placement belongs to the scene


def test_save_writes_once_per_change():
    with tempfile.TemporaryDirectory() as d:
        target = os.path.join(d, vs.FILE)
        real_path = vs.path
        vs.path = lambda: target
        try:
            vs._data.clear()
            vs._data["panels"] = {"Maya/persp": {"shading": {"type": 'SOLID'}}}
            vs._dirty = True
            vs.save()
            with open(target, encoding="utf-8") as fh:
                assert json.load(fh)["panels"]["Maya/persp"]["shading"]["type"] == 'SOLID'
            os.remove(target)
            vs.save()                          # nothing changed: no write
            assert not os.path.exists(target)
        finally:
            vs.path = real_path
            vs._data.clear()
            vs._dirty = False
