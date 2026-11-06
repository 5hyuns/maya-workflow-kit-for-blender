"""#335: a double-click on the Time Slider highlights the whole visible range (Maya) instead of running Blender's
channel-editability toggle, whose redo panel then sat over the Time Slider. GUI: tests/gui/gui_issue335_time_slider.py."""

from importlib import import_module

import bpy

import kit

ts = import_module(kit.MODULE + ".ui.time_slider")


def _double_click_items(km_name):
    km = kit.maya_kc().keymaps[km_name]
    return [k.idname for k in km.keymap_items
            if k.active and k.type == 'LEFTMOUSE' and k.value == 'DOUBLE_CLICK'
            and not (k.shift or k.ctrl or k.alt or k.oskey)]


def test_double_click_items_first():
    for km in ("Dopesheet", "Time Scrub"):
        items = _double_click_items(km)
        assert items and items[0] == "allset.time_range_all", (km, items)
    assert "anim.channels_editable_toggle" in _double_click_items("Dopesheet"), "Blender's item stays for the Dope Sheet"


def _timeline():
    win = bpy.context.window_manager.windows[0]
    for area in win.screen.areas:
        if area.type == 'DOPESHEET_EDITOR' and area.spaces.active.mode == 'TIMELINE':
            region = next(r for r in area.regions if r.type == 'WINDOW')
            return win, area, region
    raise LookupError("no timeline area on the window's screen")


def _run(win, area, region):
    with bpy.context.temp_override(window=win, screen=win.screen, area=area, region=region):
        return bpy.ops.allset.time_range_all()


def test_whole_playback_range():
    wm, scene = bpy.context.window_manager, bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 48
    scene.use_preview_range = False
    wm.allset_time_range_on = False
    assert _run(*_timeline()) == {'FINISHED'}
    assert wm.allset_time_range_on and tuple(wm.allset_time_range) == (1, 48), tuple(wm.allset_time_range)
    scene.use_preview_range = True
    scene.frame_preview_start, scene.frame_preview_end = 10, 20
    assert _run(*_timeline()) == {'FINISHED'}
    assert tuple(wm.allset_time_range) == (10, 20), "the preview range is the visible range when it is on"
    scene.use_preview_range = False
    wm.allset_time_range_on = False


def test_passes_through_outside_the_time_slider():
    win = bpy.context.window_manager.windows[0]
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win, screen=win.screen, area=area, region=region):
        assert bpy.ops.allset.time_range_all() == {'PASS_THROUGH'}


def test_hide_redo_panels_without_a_panel():
    assert ts.hide_redo_panels() is None     # no HUD region in a fresh timeline: nothing to do, no error
    _win, area, _region = _timeline()
    assert area.spaces.active.show_region_hud, "untouched until Blender has shown the panel"
