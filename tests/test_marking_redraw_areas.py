"""An open marking menu or hotbox redraws only the editors its picture reaches: the picture's bounds come from running
the drawing code itself (every line, box and text it draws lies inside them), editors outside the picture now and at
the last redraw keep their pixels, and an editor the picture leaves is redrawn once more to clear it."""

from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

draw = import_module(kit.MODULE + ".marking.draw")
engine = import_module(kit.MODULE + ".marking.engine")
mm = import_module(kit.MODULE + ".marking.menus")

B = (0.0, 0.0, 1400.0, 1000.0)


def _recording():
    """Stand-ins for the GPU / font calls that record the drawn points (window offset added by the test)."""
    pts = []

    def batch_for_shader(_sh, _kind, data, **_k):
        pts.extend(tuple(p) for p in data["pos"])
        return SimpleNamespace(draw=lambda _s: None)

    def position(_font, x, y, _z):
        pts.append((x, y))
    state = SimpleNamespace(line_width_set=lambda _w: None, blend_set=lambda _m: None)
    fake_blf = SimpleNamespace(size=draw.blf.size, dimensions=draw.blf.dimensions, color=lambda *a: None,
                               position=position, draw=lambda *a: None)
    return pts, {"batch_for_shader": batch_for_shader, "gpu": SimpleNamespace(state=state),
                 "blf": fake_blf, "_sh": lambda: SimpleNamespace(uniform_float=lambda *a: None)}


def _drawn(fn):
    pts, fakes = _recording()
    saved = {k: getattr(draw, k) for k in fakes}
    try:
        for k, v in fakes.items():
            setattr(draw, k, v)
        fn()
    finally:
        for k, v in saved.items():
            setattr(draw, k, v)
    return pts


def _inside(pts, box, origin):
    ox, oy = origin
    return all(box[0] <= x + ox <= box[2] and box[1] <= y + oy <= box[3] for x, y in pts)


def test_the_measured_bounds_hold_everything_a_menu_draws():
    origin = (120.0, 80.0)
    s = engine.Session(mm.RMB_MESH, (700.0, 500.0), 0.0, draw.measure, None, None, B)
    s.move(760.0, 500.0, 0.6)                             # a submenu / hover
    draw.ACTIVE.clear()
    draw.ACTIVE.update(session=s, origin=origin, window=0, region=0)
    try:
        box = draw.extent()
        assert box is not None and box[2] - box[0] > 50 and box[3] - box[1] > 50
        for shown in (True, False):
            pts = _drawn(lambda: draw.draw_session(s, 0.6, shown=shown))
            assert pts and _inside(pts, box, origin), (shown, box)
        rows = [[("a", "File"), ("b", "Edit"), ("c", "Create"), ("d", "Select"), ("e", "Modify")]]
        lay = engine.HotboxLayout(rows, (700.0, 500.0), draw.measure, bounds=B)
        draw.ACTIVE.clear()
        draw.ACTIVE.update(hotbox=lay, hover="c", origin=origin, window=0, region=0)
        box = draw.extent()
        pts = _drawn(lambda: draw.draw_hotbox(draw.ACTIVE, None))
        assert pts and _inside(pts, box, origin), box
    finally:
        draw.ACTIVE.clear()


class _Area:
    def __init__(self, name, x, y, w, h):
        self.name, self.x, self.y, self.width, self.height, self.tagged = name, x, y, w, h, 0

    def tag_redraw(self):
        self.tagged += 1


def test_only_the_editors_the_picture_reaches_are_redrawn():
    areas = [_Area("view", 0, 0, 800, 600), _Area("outliner", 800, 0, 300, 600), _Area("timeline", 0, 600, 1100, 80)]
    window = SimpleNamespace(screen=SimpleNamespace(areas=areas), as_pointer=lambda: 7)
    wm = SimpleNamespace(windows=[window])
    real_ctx, real_extent, real_ptr = draw.bpy.context, draw.extent, draw._window["ptr"]
    boxes = [(300.0, 200.0, 500.0, 400.0)]
    try:
        draw.bpy = SimpleNamespace(context=SimpleNamespace(window_manager=wm), types=bpy.types)
        draw.extent = lambda: boxes[0]
        draw.ACTIVE.clear()
        draw.ACTIVE.update(window=7, origin=(0.0, 0.0))
        draw._LAST[0] = None
        draw.redraw()
        assert [a.tagged for a in areas] == [1, 0, 0], "the picture lies in the view only"
        boxes[0] = (700.0, 200.0, 900.0, 400.0)                    # it moves over the Outliner
        draw.redraw()
        assert [a.tagged for a in areas] == [2, 1, 0]
        boxes[0] = (300.0, 200.0, 500.0, 400.0)                    # back: the Outliner is cleared once more
        draw.redraw()
        assert [a.tagged for a in areas] == [3, 2, 0]
        draw.redraw()
        assert [a.tagged for a in areas] == [4, 2, 0]
        boxes[0] = None                                            # not known: every editor
        draw.redraw()
        assert [a.tagged for a in areas] == [5, 3, 1]
        draw.ACTIVE.clear()                                        # closed: where it was
        draw._window["ptr"] = 7
        draw._LAST[0] = (300.0, 200.0, 500.0, 400.0)
        draw.redraw()
        assert [a.tagged for a in areas] == [6, 3, 1]
    finally:
        draw.bpy = bpy
        draw.extent = real_extent
        draw._window["ptr"] = real_ptr
        draw.ACTIVE.clear()
        draw._LAST[0] = None
        assert draw.bpy.context is real_ctx
