"""Issue #344: the Graph Editor / Dope Sheet Stats fields (the selected keys' time and value) are read once per
playback, not on every played frame.

The editors' toolbar row redraws on each played frame; reading every listed curve's keys there made a Graph Editor
or Dope Sheet beside the viewport cost more the more curves and keys the scene had. While playback runs the selected
keys don't change, so the text found on the first played frame is shown again; a key change (an Action update),
playback starting or stopping and a file load read them again. Without playback every draw reads them (a click
that picks other keys shows at once)."""

import time
from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

CURVES = 3000
KEYS = 60


def _m(name):
    return import_module(kit.MODULE + "." + name)


def _curves():
    """A skeleton-less object with CURVES keyed curves of KEYS keys; the last key of curve 7 is selected."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)
    ob = bpy.data.objects.new("animated", None)
    bpy.context.scene.collection.objects.link(ob)
    for i in range(CURVES):
        ob[f"p{i}"] = 0.0
        ob.keyframe_insert(f'["p{i}"]', frame=1)
    fcs = list(_m("compat").id_fcurves(ob))
    assert len(fcs) == CURVES, len(fcs)
    for i, fc in enumerate(fcs):
        fc.keyframe_points.clear()
        fc.keyframe_points.add(KEYS)
        co = []
        for f in range(KEYS):
            co += [f + 1, 0.5 * i + f]
        fc.keyframe_points.foreach_set("co", co)
        fc.keyframe_points.foreach_set("select_control_point", [False] * KEYS)
        fc.update()
    fcs[7].keyframe_points[-1].select_control_point = True
    return ob, fcs


class _Context:
    """What the Stats getter reads from ``bpy.context``: the screen (playing or not), the area, the editor's curves
    (counted: one read of the curves per Stats read)."""

    def __init__(self, fcs, playing):
        self._fcs = fcs
        self.reads = 0
        self.screen = SimpleNamespace(is_animation_playing=playing)
        self.area = SimpleNamespace(as_pointer=lambda: 4242)

    @property
    def editable_fcurves(self):
        self.reads += 1
        return self._fcs


def _getters(ctx):
    row = _m("ui.editor_icon_row")
    real = row.bpy
    row.bpy = SimpleNamespace(context=ctx)
    return row, real


def test_stats_are_read_once_while_playing():
    _ob, fcs = _curves()
    row = _m("ui.editor_icon_row")
    row.drop_stats()
    sc = bpy.context.scene
    ctx = _Context(fcs, playing=True)
    row_, real = _getters(ctx)
    try:
        get_time, get_value = row._stats_get("time"), row._stats_get("value")
        entry = _m("ui.cb_entry")
        assert get_time(sc) == entry.fmt_number(60.0), get_time(sc)
        assert get_value(sc) == entry.format_value(0.5 * 7 + 59, "NONE", sc), get_value(sc)
        first = ctx.reads
        t = time.perf_counter()
        for _frame in range(100):
            get_time(sc)
            get_value(sc)
        per = (time.perf_counter() - t) / 100 * 1000
        assert ctx.reads == first, f"the curves were read again while playing ({ctx.reads - first} reads)"
        print(f"Stats while playing: {per:.4f} ms per frame ({CURVES} curves, {CURVES * KEYS} keys)")
        assert per < 0.05, f"Stats {per:.3f} ms per played frame"
        # a key changes while playing (its Action updates): read again
        fcs[7].keyframe_points[-1].co.y = 100.0
        _m("ui.editor_chrome")._drop_stats_on_keys(sc, None)
        assert get_value(sc) == entry.format_value(100.0, "NONE", sc) and ctx.reads == first + 1, (get_value(sc), ctx.reads)
        # playback stops: the next draw reads them
        row.drop_stats()
        ctx.screen.is_animation_playing = False
        fcs[7].keyframe_points[-1].select_control_point = False
        fcs[9].keyframe_points[0].select_control_point = True
        assert get_time(sc) == entry.fmt_number(1.0) and get_time(sc) == entry.fmt_number(1.0)
        assert ctx.reads == first + 3, "without playback every draw reads the selected keys"
    finally:
        row_.bpy = real
        row.drop_stats()


def test_stats_drops_are_registered():
    chrome = _m("ui.editor_chrome")
    for name in ("animation_playback_pre", "animation_playback_post", "load_post"):
        assert chrome._drop_stats in getattr(bpy.app.handlers, name), name
    assert chrome._drop_stats_on_keys in bpy.app.handlers.depsgraph_update_post
