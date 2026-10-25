"""Step 186: the Maya Time Slider ruler in the Maya Workflow Kit layout (,
).

The step rule (frames between ticks / labels) against the steps a Maya 2022 drew (*/):
the cases the kit's model reproduces, and the few it doesn't (listed,  in the spec)."""

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
    assert (y0, y1) == (64 - 18, 64 - 2), "scaled to the region height"
    assert ts.label_digits(-12) == 3 and ts.label_digits(1000) == 4


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
