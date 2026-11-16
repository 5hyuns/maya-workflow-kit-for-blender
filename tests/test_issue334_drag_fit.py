"""#334: the layout fit never warps the mouse pointer while a window is being dragged or resized. ``_windows_still``
is True only when the UI scale and the place and size of every window are what the previous fit tick saw (a window
dragged onto a monitor with other display scaling changes Blender's UI scale); a window that opens or closes is not a
move. While the windows move an armed fit waits (its time window counts from then). The real window:
tests/gui/gui_issue334_drag_scale.py."""

from importlib import import_module

import kit

lf = import_module(kit.MODULE + ".ui.layout_fit")


class _Win:
    def __init__(self, ptr, x, y, w, h):
        self.ptr, self.x, self.y, self.width, self.height = ptr, x, y, w, h

    def as_pointer(self):
        return self.ptr


class _Ctx:
    def __init__(self, scale, windows):
        self.preferences = type("P", (), {"system": type("S", (), {"ui_scale": scale})()})()
        self.window_manager = type("W", (), {"windows": windows})()


def test_windows_still():
    lf._still["snap"] = None
    main, graph = _Win(1, 0, 0, 1600, 900), _Win(2, 200, 80, 900, 600)
    assert lf._windows_still(_Ctx(1.0, [main, graph]))             # nothing seen before
    assert lf._windows_still(_Ctx(1.0, [main, graph]))             # the same again
    graph.x = 380                                                  # dragged
    assert not lf._windows_still(_Ctx(1.0, [main, graph]))
    assert lf._windows_still(_Ctx(1.0, [main, graph]))             # it stopped there
    assert not lf._windows_still(_Ctx(1.25, [main, graph]))        # crossed onto a monitor with other scaling
    graph.width, graph.height = 1125, 750                          # and Windows resized it
    assert not lf._windows_still(_Ctx(1.25, [main, graph]))
    assert lf._windows_still(_Ctx(1.25, [main, graph]))
    main.width = 1500                                              # the main window resized
    assert not lf._windows_still(_Ctx(1.25, [main, graph]))
    assert lf._windows_still(_Ctx(1.25, [main]))                   # a window closed: not a move
    assert lf._windows_still(_Ctx(1.25, [main, _Win(3, 10, 10, 300, 200)]))   # one opened: not a move
    lf._still["snap"] = None
