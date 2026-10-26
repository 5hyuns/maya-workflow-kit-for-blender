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


def test_no_split_faces_by_edges():
    """'Split Faces by Edges' is Blender's name, in no Maya Edit Mesh menu (2022-2027); Maya's tool is Detach."""
    data = import_module(kit.MODULE + ".ui.menu_data")
    mm = import_module(kit.MODULE + ".ui.menu_map")
    labels = [it[0] for it in data.MENUS["mainEditMeshMenu"][3]]
    assert "Split Faces by Edges" not in labels and "Detach" in labels
    assert "Edit Mesh/Split Faces by Edges" not in mm.MAP
    assert mm.MAP["Edit Mesh/Detach"] == "allset.detach"


class _Ops:
    """A stand-in UILayout recording operator ids in draw order."""

    def __init__(self, log):
        self.log = log

    def __getattr__(self, name):
        if name in ("row", "column", "box", "split"):
            return lambda *a, **k: _Ops(self.log)
        if name == "operator":
            def op(idname, **kw):
                self.log.append(idname)
                from types import SimpleNamespace
                return SimpleNamespace()
            return op
        return lambda *a, **k: None

    def __setattr__(self, name, value):
        if name == "log":
            object.__setattr__(self, name, value)


def test_header_extras_off_and_search_under_layouts():
    """No Maya viewport header has a mode picker or a pulse: both are add-on preferences, off by default. The Tool
    Box Search button sits under the layout / Outliner buttons (Maya 2022.1+ Maya-379), and the column
    keeps Maya's checked width (no +3 px)."""
    from types import SimpleNamespace
    prefs = import_module(kit.MODULE + ".preferences").get()
    assert prefs.armature_mode_header is False and prefs.armature_mode_pulse is False
    pulse = import_module(kit.MODULE + ".ui.armature_mode_pulse")
    assert not pulse.wanted()
    tb = import_module(kit.MODULE + ".ui.toolbox")
    assert tb.column_width() == round(tb.TOOLBAR_PX * bpy.context.preferences.system.ui_scale)
    log = []
    tb.ALLSET_PT_toolbox_layouts.draw(SimpleNamespace(layout=_Ops(log)), bpy.context)
    assert log[-1] == "allset.viewport_search" and log[-2] == "allset.open_editor", log
    # the header picker draws nothing with the preference off
    log = []
    bpy.ops.object.armature_add()
    tb._draw_armature_mode_header(SimpleNamespace(layout=_Ops(log)), bpy.context)
    assert not log, log
