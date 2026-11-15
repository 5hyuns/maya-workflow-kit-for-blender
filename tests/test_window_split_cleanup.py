"""Restoring a floating window must join its own pieces, never the neighboring panels."""

from contextlib import nullcontext
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import patch

import kit

wp = import_module(kit.MODULE + '.ui.window_places')


def test_cleanup_reverses_the_splits_and_keeps_neighboring_panels():
    def area(ptr, x, width):
        return SimpleNamespace(as_pointer=lambda: ptr, x=x, y=0, width=width, height=800)

    left, kept, right = area(2, 300, 200), area(1, 500, 800), area(3, 1300, 200)
    outliner, dock = area(4, 0, 300), area(5, 1500, 300)
    window = SimpleNamespace(screen=SimpleNamespace(areas=[outliner, dock, kept, left, right]))
    calls = []

    def join(source_xy, target_xy):
        source = next(a for a in window.screen.areas if a.x <= source_xy[0] < a.x + a.width)
        target = next(a for a in window.screen.areas if a.x <= target_xy[0] < a.x + a.width)
        calls.append((source.as_pointer(), target.as_pointer()))
        end = max(source.x + source.width, target.x + target.width)
        source.x = min(source.x, target.x)
        source.width = end - source.x
        window.screen.areas.remove(target)
        return {'FINISHED'}

    fake_bpy = SimpleNamespace(context=SimpleNamespace(temp_override=lambda **kw: nullcontext()),
                               ops=SimpleNamespace(screen=SimpleNamespace(area_join=join)))
    with patch.object(wp, 'bpy', fake_bpy), patch.object(wp.live_refs, 'window', return_value=window):
        assert wp._close_later(7, [(1, 2), (1, 3)]) is None
    assert calls == [(1, 3), (1, 2)]
    assert (kept.x, kept.width) == (300, 1200)
    assert window.screen.areas == [outliner, dock, kept]
    assert (outliner.x, outliner.width, dock.x, dock.width) == (0, 300, 1500, 300)
