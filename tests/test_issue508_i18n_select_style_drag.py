"""#508: in Japanese the toolkits' selection style row (Pick/Marquee · Drag · Tweak/Marquee) reads "ドラッグ" for Drag,
while Fields / Solvers > Drag (the air resistance field) keeps "抵抗": the row draws its text in the kit's own
translation context, and a locale table can give a text a different translation in such a context.

The language is switched in this process only (sandbox factory preferences, never saved)."""

import inspect
import os
from importlib import import_module

import bpy

import kit

i18n = import_module(kit.MODULE + ".i18n")
uv_toolkit = import_module(kit.MODULE + ".ui.uv_toolkit")
modeling_toolkit = import_module(kit.MODULE + ".ui.modeling_toolkit")
WANT = {"ja_JP": ("ドラッグ", "抵抗")}


class _Language:
    def __init__(self, locale):
        self.locale = locale

    def __enter__(self):
        config = os.path.normcase(os.path.abspath(bpy.utils.user_resource('CONFIG')))
        assert os.sep + "tmp" + os.sep in config, f"not a sandbox config: {config}"
        view = bpy.context.preferences.view
        self.saved = (view.language, view.use_translate_interface)
        view.language, view.use_translate_interface = self.locale, True
        return self

    def __exit__(self, *exc):
        view = bpy.context.preferences.view
        view.language, view.use_translate_interface = self.saved


def _usable(locale):
    items = bpy.context.preferences.view.bl_rna.properties["language"].enum_items
    return locale in {it.identifier for it in items}


def test_tables_have_the_context_entry():
    for locale, table in i18n.CONTEXT_LANGUAGES.items():
        assert (i18n.CTX_SELECT_STYLE, "Drag") in table, locale
        for (ctx, en), tr in table.items():
            assert ctx and en and tr, (locale, ctx, en)
    assert i18n.CONTEXT_LANGUAGES["ja_JP"][(i18n.CTX_SELECT_STYLE, "Drag")] == "ドラッグ"
    assert i18n.LANGUAGES["ja_JP"]["Drag"] == "抵抗", "the plain text keeps the Fields / Solvers translation"


def test_lookup_by_context():
    for locale, (in_row, elsewhere) in WANT.items():
        if not _usable(locale):
            raise kit.Skip(f"{locale} is not in this Blender build")
        with _Language(locale):
            assert bpy.app.translations.pgettext_iface("Drag", i18n.CTX_SELECT_STYLE) == in_row
            assert i18n.iface("Drag", i18n.CTX_SELECT_STYLE) == in_row
            assert i18n.iface("Drag") == elsewhere
            assert bpy.app.translations.pgettext_iface("Drag") == in_row, "Blender's own text for a plain label"
            assert i18n.iface("Pick/Marquee", i18n.CTX_SELECT_STYLE) == i18n.LANGUAGES[locale]["Pick/Marquee"], \
                "a text without its own context entry keeps its usual translation"


def test_toolkit_rows_draw_in_the_context():
    for fn in (uv_toolkit.ALLSET_PT_uv_toolkit.draw, modeling_toolkit):
        src = inspect.getsource(fn)
        block = src[src.index("PICK:"):][:400]
        assert "text_ctxt=i18n.CTX_SELECT_STYLE" in block, fn
