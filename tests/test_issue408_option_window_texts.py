"""Issue #408: option windows show their title, command buttons, field names, choices and "Not in Blender" lines in
Blender's interface language (ja_JP, zh_HANS, zh_HANT) like the rest of the kit; Copy / Mirror Skin Weights Options
first. The strings are in the English translation template too.

The language is switched in this process only (sandbox factory preferences, never saved)."""

import json
import os
from importlib import import_module

import bpy

import kit

i18n = import_module(kit.MODULE + ".i18n")
ow = import_module(kit.MODULE + ".operators.option_windows")
LOCALES = ("ja_JP", "zh_HANS", "zh_HANT")


def _texts(w):
    """Every text a window shows (as the window draws it, before translation)."""
    out = {w.title, w.action, w.apply_text}
    for f in w.fields:
        out.update(t for t in (f.label.rstrip(":"), f.text) if t)
        if f.kind == "enum":
            out.update(f.items)
    out.update(w.missing)
    return {t for t in out if isinstance(t, str) and any(c.isalpha() for c in t) and len(t.strip()) > 1}


def _missing(keys, locale):
    table = i18n.LANGUAGES[locale]
    return {w.key: sorted(t for t in _texts(w) if t not in table) for w in ow.WINDOWS if w.key in keys or not keys}


def test_skin_weight_windows_are_translated():
    for locale in LOCALES:
        bad = {k: v for k, v in _missing({"copy_skin_weights", "mirror_skin_weights"}, locale).items() if v}
        assert not bad, (locale, bad)


def test_every_option_window_is_translated():
    for locale in LOCALES:
        bad = {k: v for k, v in _missing(set(), locale).items() if v}
        assert not bad, (locale, len(bad), sum(len(v) for v in bad.values()), dict(list(bad.items())[:3]))


def test_window_texts_are_in_the_template():
    path = os.path.join(os.path.dirname(i18n.__file__), "template_en.json")
    with open(path, encoding="utf-8") as fh:
        every = set().union(*(set(b) for b in json.load(fh)["sections"].values()))
    missing = sorted({t for w in ow.WINDOWS for t in _texts(w)} - every)
    assert not missing, (len(missing), missing[:10])


class _Draw:
    def __init__(self):
        self.labels = []

    def column(self, **_kw):
        return self

    def label(self, text="", **kw):
        self.labels.append((text, kw.get("translate", True)))


def test_not_in_blender_lines_follow_the_language():
    """The greyed lines are indented: the kit translates them itself (Blender only knows the text without the
    indent)."""
    view = bpy.context.preferences.view
    config = os.path.normcase(os.path.abspath(bpy.utils.user_resource('CONFIG')))
    assert os.sep + "tmp" + os.sep in config, config
    saved = (view.language, view.use_translate_interface)
    w = ow._BY_KEY["mirror_skin_weights"]
    try:
        view.language, view.use_translate_interface = "ja_JP", True
        lay = _Draw()
        ow.draw_missing(w, lay)
        shown = [i18n.iface(t) if tr else t for t, tr in lay.labels]
        want = i18n.LANGUAGES["ja_JP"]
        assert shown[0] == want["Not in Blender:"], shown
        for name, line in zip(w.missing, shown[1:]):
            assert line.strip() == want.get(name), (name, line)
    finally:
        view.language, view.use_translate_interface = saved
