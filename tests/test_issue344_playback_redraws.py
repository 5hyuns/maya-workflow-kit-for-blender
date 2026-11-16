"""Issue #344: what Maya mode redraws on each frame of playback.

The Tool Box column is a narrow 3D View: while playing, Blender's "3D Viewport" playback redraws are off on the screens
that have it (marked, so stopping, saving and loading put them back) and the kit redraws the other 3D Views' main
regions after each frame. The user's own playback settings are left alone. Maya's Play key (Alt+V), the Time Slider's
play buttons and Playback > Play start playback from the main viewport (``allset.play``), so a playback started over
the Time Slider doesn't redraw the kit's shelf and Status Line rows (Image Editors) on every frame."""

from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

pr = import_module(kit.MODULE + ".ui.playback_redraw")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
mapping = import_module(kit.MODULE + ".keymap.mapping")


class _Screen(dict):
    def __init__(self, areas, play_3d=True, play_anim=True):
        super().__init__()
        self.areas = areas
        self.use_play_3d_editors = play_3d
        self.use_play_animation_editors = play_anim


def _area(kind, ptr, regions=('HEADER', 'WINDOW')):
    return SimpleNamespace(type=kind, as_pointer=lambda: ptr, regions=[SimpleNamespace(type=r, ptr=ptr) for r in regions])


def _columns(screen):
    return [a for a in screen.areas if a.as_pointer() == 1]       # area 1 = the Tool Box column


def test_turn_off_only_screens_with_the_column():
    layout = _Screen([_area('VIEW_3D', 1, ('TOOLS', 'WINDOW')), _area('VIEW_3D', 2), _area('OUTLINER', 3)])
    plain = _Screen([_area('VIEW_3D', 4)])
    skip = pr.turn_off([SimpleNamespace(screen=layout), SimpleNamespace(screen=plain), SimpleNamespace(screen=None)],
                       columns=_columns)
    assert skip == {1}
    assert not layout.use_play_3d_editors and layout.get(pr.MARK) == 1
    assert plain.use_play_3d_editors and pr.MARK not in plain
    regions = pr.views_to_redraw([SimpleNamespace(screen=layout), SimpleNamespace(screen=plain)], skip)
    assert [(r.ptr, r.type) for r in regions] == [(2, 'WINDOW'), (4, 'WINDOW')]     # no column, no header


def test_users_playback_settings_are_left_alone():
    for play_3d, play_anim in ((False, True), (True, False), (False, False)):
        screen = _Screen([_area('VIEW_3D', 1), _area('VIEW_3D', 2)], play_3d, play_anim)
        assert pr.turn_off([SimpleNamespace(screen=screen)], columns=_columns) == set()
        assert (screen.use_play_3d_editors, screen.use_play_animation_editors) == (play_3d, play_anim)
        assert pr.MARK not in screen


def test_restore_puts_the_switch_back_on_marked_screens():
    marked, other = _Screen([], play_3d=False), _Screen([], play_3d=False)
    marked[pr.MARK] = 1
    assert pr.restore([marked, other]) == 1
    assert marked.use_play_3d_editors and pr.MARK not in marked
    assert not other.use_play_3d_editors            # turned off by the user: stays off


def test_real_screen_saved_while_playing_is_put_back_on_load():
    screen = bpy.data.screens[0]
    screen.use_play_3d_editors = False
    screen[pr.MARK] = 1
    try:
        pr._on_load()
        assert screen.use_play_3d_editors and pr.MARK not in screen
        screen.use_play_3d_editors = False
        screen[pr.MARK] = 1
        pr._on_save_pre()                            # a saved file never keeps the switch off
        assert screen.use_play_3d_editors and pr.MARK not in screen
    finally:
        screen.use_play_3d_editors = True
        screen.pop(pr.MARK, None)


def test_handlers_registered_while_enabled():
    h = bpy.app.handlers
    for lst, fn in ((h.animation_playback_pre, pr._on_playback_pre), (h.animation_playback_post, pr._on_playback_post),
                    (h.frame_change_post, pr._on_frame), (h.load_post, pr._on_load), (h.save_pre, pr._on_save_pre)):
        assert fn in lst, fn.__name__
    pr._on_frame()                                    # not playing: nothing to do, no error
    assert not pr._state["on"]


def test_play_starts_from_the_viewport():
    assert hasattr(bpy.ops.allset, "play")
    assert mapping.ENTRIES["PlaybackToggle"]["check"] == ("Frames", "allset.play", {})
    assert menu_map.MAP["Playback/Play"] == "allset.play"
    assert menu_map.MAP["Playback/Backward"] == ("allset.play", {"reverse": True})
    src = open(import_module(kit.MODULE + ".ui.time_slider_header").__file__, encoding="utf-8").read()
    assert '"screen.animation_play"' not in src and src.count('"allset.play"') == 3
