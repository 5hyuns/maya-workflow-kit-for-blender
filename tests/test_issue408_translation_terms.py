"""#408: the option windows' Japanese and Chinese texts use the same words as the kit's other translations, so a
window reads like the menu that opens it.

- Every "<X> Options" window title contains the translation of the menu item X.
- The option window texts don't use a second word for a term the translations already name one way (Traditional
  Chinese 對象 / 創建 / 組件 / 關鍵格 / 選擇 / 設置 ..., Simplified Chinese 父级 / 缩放约束, Japanese ワイヤー /
  ポールベクター).
"""

import importlib.util
import os
import re
from importlib import import_module

import kit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALES = ("ja_JP", "zh_HANS", "zh_HANT")
SUFFIX = " Options"

# a word the translations don't use -> the word they use for it
OTHER_WORDS = {
    "ja_JP": {r"ワイヤ(?!ー)": "ワイヤー", "極ベクトル": "ポールベクター"},
    "zh_HANS": {"父化": "父级", "比例约束": "缩放约束"},
    "zh_HANT": {"物件": "對象", "建立": "創建", "元件": "組件", "影格": "格", "選取": "選擇", "設定": "設置",
                "重設": "重置", "群組": "分組", "智慧": "智能", "貼齊": "捕捉", "新增": "新建", "偏好角度": "首選角度",
                "套用": "應用", "父化": "父級", "比例約束": "縮放約束", "清單": "列表", "支援": "支持", "階層": "層級",
                "覆寫": "取代"},
}


def _tool():
    spec = importlib.util.spec_from_file_location("tool_i18n_strings", os.path.join(ROOT, "tools", "i18n_strings.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _table(locale):
    return import_module(f"{kit.MODULE}.i18n.{locale}").STRINGS


def _window_texts():
    texts = set(_tool().option_windows())
    tips = import_module(kit.MODULE + ".ui.panel_image_plane").TIPS
    return texts | set(tips.values())


def test_option_window_titles_use_the_menu_items_translation():
    bad = {}
    for locale in LOCALES:
        table = _table(locale)
        for key, text in table.items():
            if key.endswith(SUFFIX) and key[:-len(SUFFIX)] in table:
                item = table[key[:-len(SUFFIX)]]
                if item not in text:
                    bad.setdefault(locale, []).append((key, text, item))
    assert not bad, {loc: (len(rows), rows[:8]) for loc, rows in bad.items()}


def test_option_window_texts_use_the_translations_words():
    texts = _window_texts()
    bad = {}
    for locale in LOCALES:
        table = _table(locale)
        for pattern, word in OTHER_WORDS[locale].items():
            rx = re.compile(pattern)
            rows = [(k, table[k]) for k in sorted(texts) if k in table and rx.search(table[k])]
            if rows:
                bad[f"{locale} {pattern} (use {word})"] = (len(rows), rows[:4])
    assert not bad, bad
