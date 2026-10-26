"""PR #125 follow-up (0.5.0): Maya checks of the merged PR (C:/Repos/bmk-strategy/PR125_MAYA_CHECK.md,
PR125_MAYA_LATER.md) — idle Channel Box poll, wheel step, Joint Tool branching, menu data, header extras,
Select Priority off. GUI parts: tests/gui/gui_pr125_window_close.py, tests/integration/."""

from importlib import import_module

import bpy

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")
maya_dock = import_module(kit.MODULE + ".ui.maya_dock")


def _cube():
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    ob.select_set(True)
    return ob


def test_idle_poll_draws_nothing():
    """The 0.1 s live-value poll redraws the dock only when the lead's channels changed (or a transform runs)."""
    ob = _cube()
    calls = []
    real = maya_dock.redraw
    maya_dock.redraw = lambda *a, **k: calls.append(1)
    try:
        cb._poll_transform_values()
        calls.clear()
        for _ in range(5):
            cb._poll_transform_values()
        assert not calls, f"idle ticks redrew the dock {len(calls)} times"
        ob.location.x += 1.0
        cb._poll_transform_values()
        assert len(calls) == 1, calls
        cb._poll_transform_values()
        assert len(calls) == 1, "the same values again: no redraw"
    finally:
        maya_dock.redraw = real


def test_wheel_is_three_lines():
    """Maya: one wheel notch = QScrollBar single step 15 px x wheelScrollLines 3 = 45 px, about 3 rows."""
    assert cb.WHEEL_LINES == 3
