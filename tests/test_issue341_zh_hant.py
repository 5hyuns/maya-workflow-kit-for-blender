"""Traditional Chinese (#341): the zh_HANT table has a text for every string of the English template, keeps the English
text's format fields, ellipses, padding and submenu arrows, is written in Traditional characters, and Blender's
Traditional Chinese interface language shows it in labels, tooltips and the Maya menus.

The language is switched in this process only (sandbox factory preferences, never saved)."""

import json
import os
import re
from importlib import import_module

import bpy

import kit

i18n = import_module(kit.MODULE + ".i18n")
oc = import_module(kit.MODULE + ".ui.option_click")
LOCALE = "zh_HANT"
SAMPLES = ("Channel Box / Layer Editor", "Save Scene As...", "Smooth Mesh Preview to Polygons")
FIELDS = re.compile(r"\{[^{}]*\}")
PERCENT = re.compile(r"%[-+ #0]*\d*(?:\.\d+)?[sdifr%]")
# Simplified forms of common characters: a Traditional text uses the Traditional form instead
SIMPLIFIED = ("选线动关编辑边择对单键图显节为设视标项时换将属转变间开网顶权层创绘组数击当缩没轴摄复环场记连删颜导状类区"
              "笔围称画约质过隐缓输参级发无运闭双绑该钮认长纹离启响仅侧势锁样圆载驱纵挤贴缝预滚个会从两来写书学实处历"
              "内与壳径态枢带块签减随栏静请则览夹义断热纲脚规结独积员获题齐递细传调刚进这帮镜统执软阵链盘滤轨产见轮顺"
              "拟资终浏计雾续给宽针绕现础络话桥联销阶弹扩栈")
# words with the wrong one of two Traditional characters (象 / 像, 面 / 麵, 表 / 錶, 余 / 餘, 回 / 迴, 划 / 劃, 制 / 製)
WRONG_WORDS = (re.compile(r"對像(?!素)"), re.compile("曲麵"), re.compile("錶格"), re.compile("冗余"),
               re.compile("返迴"), re.compile("划動"), re.compile("複制"))


def _template_strings():
    path = os.path.join(os.path.dirname(i18n.__file__), "template_en.json")
    with open(path, encoding="utf-8") as fh:
        sections = json.load(fh)["sections"]
    return set().union(*(set(block) for block in sections.values()))


def _sandboxed():
    config = os.path.normcase(os.path.abspath(bpy.utils.user_resource('CONFIG')))
    assert os.sep + "tmp" + os.sep in config, f"not a sandbox config: {config}"


class _Language:
    def __init__(self, locale):
        self.locale = locale

    def __enter__(self):
        _sandboxed()
        view = bpy.context.preferences.view
        self.saved = (view.language, view.use_translate_interface, view.use_translate_tooltips)
        view.language = self.locale
        view.use_translate_interface = view.use_translate_tooltips = True
        return self

    def __exit__(self, *exc):
        view = bpy.context.preferences.view
        view.language, view.use_translate_interface, view.use_translate_tooltips = self.saved


def _usable(locale):
    items = bpy.context.preferences.view.bl_rna.properties["language"].enum_items
    return locale in {it.identifier for it in items}


def test_registered():
    assert LOCALE in i18n.LANGUAGES
    data = i18n.table()
    for ctx in i18n.CONTEXTS:
        assert data[LOCALE][(ctx, SAMPLES[0])] == i18n.LANGUAGES[LOCALE][SAMPLES[0]]


def test_every_template_string_has_a_text():
    table = i18n.LANGUAGES[LOCALE]
    every = _template_strings()
    missing = sorted(s for s in every if s not in table)
    assert not missing, (len(missing), missing[:10])
    extra = sorted(s for s in table if s not in every)
    assert not extra, (len(extra), extra[:10])
    empty = [en for en, tr in table.items() if not isinstance(tr, str) or not tr.strip()]
    assert not empty, empty[:10]


def test_texts_keep_fields_and_padding():
    bad = []
    for en, tr in i18n.LANGUAGES[LOCALE].items():
        if sorted(FIELDS.findall(en)) != sorted(FIELDS.findall(tr)):
            bad.append(("format fields", en, tr))
        if sorted(PERCENT.findall(en)) != sorted(PERCENT.findall(tr)):
            bad.append(("% fields", en, tr))
        if en.endswith("...") and not tr.endswith("..."):
            bad.append(("ellipsis", en, tr))
        if en.endswith(i18n.ARROW) != tr.endswith(i18n.ARROW):
            bad.append(("submenu arrow", en, tr))
        if (en[:1] == " ") != (tr[:1] == " ") or (en[-1:] == " ") != (tr[-1:] == " "):
            bad.append(("padding", en, tr))
        if "\r" in tr or "\t" in tr:
            bad.append(("control character", en, tr))
    assert not bad, (len(bad), bad[:5])


def test_traditional_characters():
    simplified = set(SIMPLIFIED)
    found = sorted((ch, en) for en, tr in i18n.LANGUAGES[LOCALE].items() for ch in set(tr) & simplified)
    assert not found, (len(found), found[:10])
    wrong = [(pat.pattern, en, tr) for en, tr in i18n.LANGUAGES[LOCALE].items() for pat in WRONG_WORDS
             if pat.search(tr)]
    assert not wrong, (len(wrong), wrong[:5])
    # its own table, not the Simplified one
    hans = i18n.LANGUAGES["zh_HANS"]
    assert all(i18n.LANGUAGES[LOCALE][s] != hans[s] for s in SAMPLES)


def test_interface_language_shows_it():
    if not _usable(LOCALE):
        print(f"skip {LOCALE}: not in this Blender build")
        return
    table = i18n.LANGUAGES[LOCALE]
    with _Language(LOCALE):
        assert bpy.app.translations.locale == LOCALE
        for s in SAMPLES:
            assert bpy.app.translations.pgettext_iface(s) == table[s], s
            assert i18n.iface(s) == table[s], s
        assert bpy.app.translations.pgettext_iface(SAMPLES[0], "Operator") == table[SAMPLES[0]]
        tip = "No Blender equivalent in Maya Workflow Kit yet"
        assert bpy.app.translations.pgettext_tip(tip) == table[tip]
        assert i18n.tip(tip) == table[tip]
        _rows, texts = oc.rows("File")
        assert texts["File/Save Scene As..."].startswith(table["Save Scene As..."]), texts["File/Save Scene As..."]
    with _Language("zh_HANS"):
        assert i18n.iface(SAMPLES[0]) == i18n.LANGUAGES["zh_HANS"][SAMPLES[0]]
