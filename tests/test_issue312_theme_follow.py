"""Issue #312: the panels the kit draws itself (Graph Editor / Dope Sheet list, Time Slider ruler, Range Slider)
follow the Blender theme: unchanged with the factory theme, light with a light theme."""

from importlib import import_module

import bpy

import kit

tf = import_module(kit.MODULE + ".ui.theme_follow")
ec = import_module(kit.MODULE + ".ui.editor_chrome")
ts = import_module(kit.MODULE + ".ui.time_slider")
rb = import_module(kit.MODULE + ".ui.range_bar")


def _close(a, b):
    return all(abs(x - y) < 1e-4 for x, y in zip(a, b))


def test_factory_theme_keeps_the_maya_greys():
    for editor in ("graph_editor", "dopesheet_editor"):
        for field in tf.FIELDS:
            assert _close(tf.theme_color(editor, field), tf.FACTORY[field]), (editor, field, tf.theme_color(editor, field))
    assert _close(tf.follow(ec.BACK, "graph_editor", "back"), ec.BACK)
    assert _close(ts._themed(ts.RULER_BG, "back"), ts.RULER_BG)
    assert _close(rb._themed(rb.TEXT_RGB, "text"), rb.TEXT_RGB)


def test_light_theme_turns_the_panels_light_with_dark_text():
    th = bpy.context.preferences.themes[0]
    keep = {e: (tuple(getattr(th, e).space.back), tuple(getattr(th, e).space.text))
            for e in ("graph_editor", "dopesheet_editor")}
    try:
        for e in keep:
            getattr(th, e).space.back = (0.8, 0.8, 0.8)
            getattr(th, e).space.text = (0.1, 0.1, 0.1)
        back = tf.follow(ec.BACK, "graph_editor", "back")
        text = tf.follow(ec.TEXT, "graph_editor", "text")
        assert back[0] > 0.8 and text[0] < 0.4, (back, text)
        assert back[3] == ec.BACK[3], "alpha kept"
        assert ts._themed(ts.RULER_BG, "back")[0] > 0.7 and ts._themed(ts.RULER_LABEL, "text")[0] < 0.2
        assert rb._themed(rb.TRACK_RGB, "back")[0] > 0.7 and rb._themed(rb.TEXT_RGB, "text")[0] < 0.4
        assert ec.SELECT == (0.322, 0.522, 0.651, 1.0), "selection blue stays"
    finally:
        for e, (b, t) in keep.items():
            getattr(th, e).space.back, getattr(th, e).space.text = b, t
