"""Step 186: the Maya Time Slider ruler in the Maya Workflow Kit layout (docs/steps/step_186.md).


The step rule (frames between ticks / labels) against the steps Maya 2022 draws:
the cases the kit's model reproduces, and the few it doesn't (listed, [U] in the spec)."""

from importlib import import_module

from kit import MODULE

# (widget px, first frame, last frame, Maya's step)
MAYA = [
    (1292, 1, 120, 5), (1292, 1, 24, 1), (1292, 1, 48, 1), (1292, 1, 200, 5), (1292, 1, 500, 10),
    (1292, 1, 1000, 20), (1292, 1, 3000, 100), (1292, 1, 10000, 400), (1292, 101, 160, 2), (692, 1, 120, 10),
    (692, 1, 48, 2), (692, 1, 1000, 50), (892, 1, 120, 5), (1592, 1, 120, 5), (1592, 1, 10, 1), (1592, 1, 60, 2),
    (1292, 1, 49, 1), (1292, 1, 50, 1), (1292, 1, 52, 2), (1292, 1, 55, 2), (1292, 1, 60, 2), (1292, 1, 215, 10),
    (1292, 1, 230, 10), (1292, 1, 250, 10), (1292, 1, 280, 10), (1292, 1, 520, 20), (1292, 1, 560, 20),
    (1292, 1, 600, 20), (1292, 101, 200, 2), (1292, 101, 230, 5), (1292, 1001, 1100, 4), (1292, 1001, 1200, 5),
    (1292, 1, 2000, 50), (1292, 1, 5000, 200), (1292, 1, 20000, 1000), (1292, 1, 100000, 4000), (1292, 1, 12, 1),
    (1292, 1, 6, 1), (1292, 1, 2, 1), (692, 1, 100, 5), (692, 1, 130, 10), (692, 1, 110, 10), (692, 1, 500, 20),
]


def _ts():
    return import_module(MODULE + ".ui.time_slider")


def _kit_step(w, a, b):
    return _ts().tick_step(a, b, (w - 10) / (b - a + 1))


def test_step_rule_matches_maya():
    ts = _ts()
    got = {(w, a, b): _kit_step(w, a, b) for w, a, b, _s in MAYA}
    same = [c for c in MAYA if got[c[:3]] == c[3]]
    known = set(ts.STEP_DEVIATIONS)
    other = [c for c in MAYA if got[c[:3]] != c[3] and c[:3] not in known]
    assert not other, f"new deviations from Maya: {other}"
    assert len(same) >= ts.STEP_MATCHES, (len(same), ts.STEP_MATCHES)
    # Maya's default scene (1-120 in a 1292 px slider) and the common short ranges are exact
    for c in ((1292, 1, 120), (1292, 1, 24), (1292, 1, 48), (1292, 1, 200), (1292, 1, 500), (1292, 1, 1000)):
        assert c not in known


def test_ticks_and_rows():
    ts = _ts()
    assert ts.ruler_ticks(5, 0.3, 21.7) == [0, 5, 10, 15, 20]
    assert ts.ruler_ticks(1, 3.0, 5.0) == [2, 3, 4, 5, 6]
    y0, y1 = ts._rows("tick", 32.0)
    assert (y0, y1) == (32 - 28, 32 - 13), "Maya rows 13-27 of 32 (top-down) as region y (bottom-up)"
    y0, y1 = ts._rows("label", 64.0)
    assert (y0, y1) == (64 - 9, 64 - 1), "ruler stays at the top at its normal height"
    for name in ("label", "strip", "bookmark"):
        rows = ts.ROWS_BOOKMARKS if name in ("strip", "bookmark") else ts.ROWS
        normal = ts._rows(name, 32, rows)
        tall = ts._rows(name, 320, rows)
        assert tuple(320 - y for y in tall) == tuple(32 - y for y in normal), name
    # #190, Maya 2026: the current frame number stays at the bottom, ticks keep their bottom end and
    # grow into half the room under the frame numbers
    assert ts._rows("current_label", 320) == ts._rows("current_label", 32) == (8, 16)
    assert ts._rows("tick", 40) == (4, 4 + 15), "a little taller: the normal tick"
    y0, y1 = ts._rows("tick", 320)
    assert y0 == 4 and abs(y1 - ((320 - 9 + 4) / 2 - ts.TICK_HALF_PAD)) < 1e-9, (y0, y1)
    assert y1 < 320 / 2, "ticks never reach up to the frame numbers"
    y0, y1 = ts._rows("tick", 320, scale=2)
    assert y0 == 8 and abs(y1 - ((320 - 18 + 8) / 2 - 2 * ts.TICK_HALF_PAD)) < 1e-9, (y0, y1)
    y0, y1 = ts._rows("tick", 320, ts.ROWS_BOOKMARKS)
    assert y0 == 4 and abs(y1 - ((320 - 19 + 4) / 2 - ts.TICK_HALF_PAD)) < 1e-9, (y0, y1)
    assert ts._rows("band", 320) == (0, 3), "bottom band stays at the bottom"
    assert ts._rows("tick", 16) == (2, 9.5), "small regions still fit the ruler"
    assert ts.label_digits(-12) == 3 and ts.label_digits(1000) == 4


def test_ruler_text_size_does_not_follow_height():
    from types import SimpleNamespace
    from unittest.mock import patch
    import blf
    import gpu
    import gpu_extras.batch

    ts = _ts()
    bookmarks = import_module(MODULE + ".operators.bookmarks")
    class View:
        def view_to_region(self, x, y, clip=False):
            return (x * 10, y)

        def region_to_view(self, x, y):
            return (x / 10, y)

    class Shader:
        def uniform_float(self, *args):
            pass

    scene = SimpleNamespace(use_preview_range=False, frame_start=1, frame_end=120, frame_current=123)
    scale = SimpleNamespace(ui_scale=1.0)
    context = SimpleNamespace(scene=scene, preferences=SimpleNamespace(system=scale))
    batch = SimpleNamespace(draw=lambda shader: None)
    with patch.object(bookmarks, "markers", return_value=[]), \
            patch.object(gpu.shader, "from_builtin", return_value=Shader()), \
            patch.object(gpu.state, "blend_set"), \
            patch.object(gpu_extras.batch, "batch_for_shader", return_value=batch), \
            patch.object(blf, "size") as size, patch.object(blf, "color"), \
            patch.object(blf, "position"), patch.object(blf, "draw"):
        for height in (32, 64, 320):
            ts._draw_ruler(context, SimpleNamespace(width=800, height=height, view2d=View()))
        assert [call.args[1] for call in size.call_args_list] == [ts.RULER_FONT_SIZE] * 3
        scale.ui_scale = 2.0
        ts._draw_ruler(context, SimpleNamespace(width=800, height=320, view2d=View()))
        assert size.call_args.args[1] == 2 * ts.RULER_FONT_SIZE


def test_playback_range():
    import bpy
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 120
    sc.use_preview_range = False
    assert _ts().playback_range(sc) == (1, 120)
    sc.use_preview_range = True
    sc.frame_preview_start, sc.frame_preview_end = 10, 40
    try:
        assert _ts().playback_range(sc) == (10, 40)
    finally:
        sc.use_preview_range = False
