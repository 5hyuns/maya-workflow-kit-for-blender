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


def test_off_by_default_and_the_preference_starts_it():
    """Remember Panel Settings is off after install: no timer, no file; on, it reads the file and samples every
    TICK; off again stops."""
    prefs = import_module(kit.MODULE + ".preferences").get()
    assert prefs.remember_panel_settings is False
    assert not bpy.app.timers.is_registered(vs._tick) and not vs._running[0]
    with tempfile.TemporaryDirectory() as d:
        target = os.path.join(d, vs.FILE)
        saved = {"panels": {"Maya/persp": {"shading": {"type": 'WIREFRAME'}}}, "range_bar": {"900,1.0": 2}}
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(saved))
        real_path = vs.path
        vs.path = lambda: target
        try:
            prefs.remember_panel_settings = True
            assert bpy.app.timers.is_registered(vs._tick) and vs._running[0]
            assert vs._data["panels"]["Maya/persp"]["shading"]["type"] == 'WIREFRAME'
            prefs.remember_panel_settings = False
            assert not bpy.app.timers.is_registered(vs._tick) and not vs._running[0] and not vs._data
            vs.sample()                                   # off: nothing is read or written
            assert not vs._data
        finally:
            prefs.remember_panel_settings = False
            vs.path = real_path
            vs._data.clear()
            vs._dirty = False
            import_module(kit.MODULE + ".ui.range_bar")._settled.pop((900, 1.0), None)


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
