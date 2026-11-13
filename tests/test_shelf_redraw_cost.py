"""The shelf row redraws on every frame change, selection change and while a marking menu or the hotbox is open, so
placing its icons must stay cheap: one redraw reads the shelf layout once, and finding a user-made button never
rebuilds the factory shelf's button list. The layout itself is unchanged (same slot rectangles, separators kept
narrow)."""

from importlib import import_module
from types import SimpleNamespace

import kit

shelf = import_module(kit.MODULE + ".ui.shelf")
shelf_data = import_module(kit.MODULE + ".ui.shelf_data")
shelf_map = import_module(kit.MODULE + ".ui.shelf_map")

SEP = {"label": "Separator", "type": "separator"}
ADDED = {"label": "Mine", "icon": 'SCRIPT', "script": "", "menu": ""}


class _Count:
    """Counts the calls of a module function while installed."""

    def __init__(self, module, name):
        self.module, self.name, self.calls = module, name, 0
        self.real = getattr(module, name)

    def __enter__(self):
        def counted(*a, **k):
            self.calls += 1
            return self.real(*a, **k)
        setattr(self.module, self.name, counted)
        return self

    def __exit__(self, *exc):
        setattr(self.module, self.name, self.real)


def _region(width=1600, height=80):
    return SimpleNamespace(width=width, height=height, tag_redraw=lambda: None, as_pointer=lambda: 7)


def _with_extras(shelf_id, extras):
    """Give factory shelf ``shelf_id`` added buttons; returns an undo callable."""
    data = shelf.user_data()
    saved = data.get("extra")
    data["extra"] = {shelf_id: list(extras)}

    def undo():
        if saved is None:
            data.pop("extra", None)
        else:
            data["extra"] = saved
    return undo


def _reference_rect(region, slot, scale, cur):
    """icon_rect as plain arithmetic: Maya slots, then the added buttons, a separator slot 8 px wide."""
    buttons = shelf.icon_buttons(None)[1]
    n = shelf.factory_count(cur)
    extras = shelf.factory_extras(cur) or []
    seps = {n + k for k, b in enumerate(extras) if b.get("type") == "separator"}
    lay = shelf.row_layout(region.width, len(buttons), scale, (), shelf.LEFT_PX, separators=seps)
    size = min((8 if slot in seps else shelf.ICON_PX) * scale, region.height - 4)
    y = (region.height - size) / 2
    off = region.width + 10 ** 6
    if slot >= len(lay):
        return off, y, size
    row, x = lay[slot]
    rows = lay[-1][0] + 1
    if row != max(0, min(shelf._row.get(cur, 0), rows - 1)):
        return off, y, size
    return x, y, size


def test_factory_count_matches_the_built_button_list():
    for name, _label, _buttons in shelf_data.SHELVES:
        assert shelf.factory_count(name) == len(shelf.all_buttons(name)), name
    assert shelf.factory_count("no such shelf") == 0
    assert shelf.factory_count(shelf.USER_PREFIX + "Custom") == 0


def test_button_record_finds_added_buttons_without_building_the_shelf():
    cur = shelf_data.DEFAULT
    n = shelf.factory_count(cur)
    undo = _with_extras(cur, [ADDED, SEP, ADDED])
    try:
        with _Count(shelf_map, "lookup") as lk, _Count(shelf, "all_buttons") as ab:
            assert shelf.button_record(cur, 0) is None, "a Maya slot has no stored record"
            assert shelf.button_record(cur, n - 1) is None
            assert shelf.button_record(cur, n) is not None and shelf.button_record(cur, n)["label"] == "Mine"
            assert shelf.button_record(cur, n + 1)["type"] == "separator"
            assert shelf.button_record(cur, n + 3) is None, "past the last added button"
        assert lk.calls == 0 and ab.calls == 0, (lk.calls, ab.calls)
    finally:
        undo()
    with _Count(shelf_map, "lookup") as lk:
        assert all(shelf.button_record(cur, i) is None for i in range(n + 2)), "no added buttons: no records"
    assert lk.calls == 0


def test_slot_rects_unchanged_and_one_layout_per_redraw():
    cur = shelf.current(None)
    scale = 1.25
    for width in (1600, 900):
        for extras in ([], [ADDED, SEP, ADDED, SEP]):
            undo = _with_extras(cur, extras)
            shelf._factory_cache.clear()
            try:
                region = _region(width)
                buttons = shelf.icon_buttons(None)[1]
                assert len(buttons) == shelf.factory_count(cur) + len(extras)
                for row in (0, 1):
                    shelf._row[cur] = row
                    plan = shelf._plan(region, scale)
                    for slot in range(len(buttons) + 2):
                        want = _reference_rect(region, slot, scale, cur)
                        assert shelf.icon_rect(region, slot, scale) == want, (width, extras, row, slot)
                        assert shelf._plan_rect(plan, region, slot, scale) == want, (width, extras, row, slot)
                # one redraw = one layout read (it used to read the layout again for every icon)
                with _Count(shelf, "_plan") as pl, _Count(shelf_map, "lookup") as lk:
                    plan = shelf._plan(region, scale)
                    rects = [shelf._plan_rect(plan, region, s, scale) for s in range(len(buttons))]
                    shelf._separators(region, scale, len(buttons), plan)
                assert pl.calls == 1 and lk.calls == 0, (pl.calls, lk.calls)
                assert len(rects) == len(buttons)
            finally:
                shelf._row.pop(cur, None)
                undo()
                shelf._factory_cache.clear()


def test_layout_read_stays_linear_in_the_button_count():
    """Each slot's separator check is a dictionary lookup, not a rebuild of the shelf: the lookups one layout read
    makes do not grow with the number of buttons."""
    cur = shelf.current(None)
    undo = _with_extras(cur, [ADDED] * 30 + [SEP] * 5)
    shelf._factory_cache.clear()
    try:
        shelf.icon_buttons(None)                       # fills the factory cache (one build per shelf)
        with _Count(shelf_map, "lookup") as lk, _Count(shelf, "editable_buttons") as eb:
            shelf._plan(_region(), 1.0)
        n = len(shelf.icon_buttons(None)[1])
        assert lk.calls == 0, lk.calls
        assert eb.calls <= n + 2, (eb.calls, n)
    finally:
        undo()
        shelf._factory_cache.clear()
