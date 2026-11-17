"""#334: the layout fit never warps the mouse pointer while a window is being dragged or resized. ``_windows_still``
is True only when the place, size and own UI scale of every window are what the previous fit tick saw (a window
dragged onto a monitor with other display scaling draws with that monitor's scale); a window that opens or closes is
not a move. While the windows move an armed fit waits (its time window counts from then).

Blender keeps one UI scale for all windows and sets it to the scale of the window drawn last, so with two monitors of
different scaling the scale a timer reads goes back and forth between the windows' scales. Each window's own scale is
noted when it draws its 3D View toolbar (``note_scale``); that back and forth is no move, and the fit leaves a window
alone while the scale is another window's (``_scale_is_own``). The real windows: tests/gui/gui_issue334_drag_scale.py,
tests/gui/gui_issue334_mixed_scale.py."""

from importlib import import_module

import kit

lf = import_module(kit.MODULE + ".ui.layout_fit")


class _Win:
    def __init__(self, ptr, x, y, w, h):
        self.ptr, self.x, self.y, self.width, self.height = ptr, x, y, w, h

    def as_pointer(self):
        return self.ptr


def _system(scale, pixel=1):
    return type("S", (), {"ui_scale": scale, "pixel_size": pixel})()


class _Ctx:
    def __init__(self, scale, windows, window=None):
        self.preferences = type("P", (), {"system": _system(scale)})()
        self.window_manager = type("W", (), {"windows": windows})()
        self.window = window


def test_windows_still():
    lf._still["snap"] = None
    lf._drawn.clear()
    main, graph = _Win(1, 0, 0, 1600, 900), _Win(2, 200, 80, 900, 600)
    lf.note_scale(_Ctx(1.0, [], main))
    lf.note_scale(_Ctx(1.0, [], graph))
    assert lf._windows_still(_Ctx(1.0, [main, graph]))             # nothing seen before
    assert lf._windows_still(_Ctx(1.0, [main, graph]))             # the same again
    graph.x = 380                                                  # dragged
    assert not lf._windows_still(_Ctx(1.0, [main, graph]))
    assert lf._windows_still(_Ctx(1.0, [main, graph]))             # it stopped there
    lf.note_scale(_Ctx(1.25, [], graph))                           # crossed onto a monitor with other scaling
    assert not lf._windows_still(_Ctx(1.25, [main, graph]))
    graph.width, graph.height = 1125, 750                          # and Windows resized it
    assert not lf._windows_still(_Ctx(1.25, [main, graph]))
    assert lf._windows_still(_Ctx(1.25, [main, graph]))
    main.width = 1500                                              # the main window resized
    assert not lf._windows_still(_Ctx(1.25, [main, graph]))
    assert lf._windows_still(_Ctx(1.25, [main]))                   # a window closed: not a move
    assert 2 not in lf._drawn                                      # (its scale is forgotten: pointers are reused)
    assert lf._windows_still(_Ctx(1.25, [main, _Win(3, 10, 10, 300, 200)]))   # one opened: not a move
    lf._still["snap"] = None
    lf._drawn.clear()


def test_two_monitor_scales():
    lf._still["snap"] = None
    lf._drawn.clear()
    main, graph = _Win(1, 0, 0, 1600, 900), _Win(2, 2700, 80, 900, 600)
    lf.note_scale(_Ctx(1.25, [], main))                            # main window on a 125 % monitor
    lf.note_scale(_Ctx(1.0, [], graph))                            # Graph Editor window on a 100 % one
    assert lf._windows_still(_Ctx(1.0, [main, graph]))
    for scale in (1.25, 1.0, 1.25, 1.0):                           # whichever window drew last: no move
        assert lf._windows_still(_Ctx(scale, [main, graph]))
    assert lf._scale_is_own(main, _system(1.25)) and not lf._scale_is_own(main, _system(1.0))
    assert lf._scale_is_own(graph, _system(1.0)) and not lf._scale_is_own(graph, _system(1.25))
    assert not lf._scale_is_own(main, _system(1.25, 2))            # a Retina window's pixel size counts too
    assert lf._scale_is_own(_Win(9, 0, 0, 10, 10), _system(1.0))   # a window that never drew a toolbar
    lf._still["snap"] = None
    lf._drawn.clear()
