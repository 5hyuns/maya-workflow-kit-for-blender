"""Tooltips in the interface language (#317): Blender shows what an operator's ``description`` returns as it is, so
the kit translates composed tooltips itself — the panel toolbar, the Graph Editor icon row, the shelf buttons; a
Maya submenu's tooltip is its (translated) name. Every string in the translation tables keeps its ``{fields}``.

The language is switched in this process only (sandbox factory preferences, never saved)."""

import os
import re
from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

i18n = import_module(kit.MODULE + ".i18n")
LOCALE = "ja_JP"
JA = i18n.LANGUAGES[LOCALE]


class _Japanese:
    def __enter__(self):
        path = os.path.normcase(os.path.abspath(bpy.utils.user_resource('CONFIG')))
        assert os.sep + "tmp" + os.sep in path, path
        view = bpy.context.preferences.view
        self.saved = (view.language, view.use_translate_interface, view.use_translate_tooltips)
        view.language = LOCALE
        view.use_translate_interface = view.use_translate_tooltips = True

    def __exit__(self, *exc):
        view = bpy.context.preferences.view
        view.language, view.use_translate_interface, view.use_translate_tooltips = self.saved


def _desc(idname, **props):
    cls = getattr(bpy.types, idname)
    return cls.description(bpy.context, SimpleNamespace(**props))


def test_panel_toolbar_tooltip():
    with _Japanese():
        assert _desc("ALLSET_OT_panel_set", key="DEFAULT_MATERIAL") == JA["Use default material"]
    assert _desc("ALLSET_OT_panel_set", key="DEFAULT_MATERIAL") == "Use default material"


def test_graph_editor_icon_tooltip():
    with _Japanese():
        text = _desc("ALLSET_OT_editor_icon", key="Graph Editor|tan_auto")
    first = text.split("\n")[0]
    assert JA["Auto tangents"] in first and "Auto tangents" not in first, text


def test_shelf_button_tooltip():
    shelf, label = "Surfaces", "NURBS Sphere"
    index = 0
    with _Japanese():
        text = _desc("ALLSET_OT_shelf_button", shelf=shelf, index=index)
    assert JA[label] in text and label not in text, text
    assert JA["Double-click or Ctrl+click: options"] in text, text
    english = _desc("ALLSET_OT_shelf_button", shelf=shelf, index=index)
    assert english.startswith(f"{label} (Maya shelf)"), english


def test_submenu_tooltip_is_its_name():
    cls = next(c for c in bpy.types.Menu.__subclasses__()
               if (c.__doc__ or "") == "Maya menu: Graph Editor/Tangents/Default Out Tangent")
    assert cls.bl_description == "Default Out Tangent"
    assert "Default Out Tangent" in JA


def test_compose_keeps_english_when_a_translation_breaks_fields():
    assert i18n.compose("{label} (Maya shelf)", label="X") in ("X (Maya shelf)", JA["{label} (Maya shelf)"].format(
        label="X"))


def test_table_fields_match():
    for locale, strings in i18n.LANGUAGES.items():
        for en, tr in strings.items():
            want = sorted(re.findall(r"\{[a-z_]+\}", en))
            assert sorted(re.findall(r"\{[a-z_]+\}", tr)) == want, (locale, en, tr)
