# SPDX-License-Identifier: GPL-3.0-or-later
"""Translations of the kit's own labels and tooltips.

The kit follows Blender's Preferences > Interface > Language and its "Translate" toggles (Interface, Tooltips):
the tables are handed to Blender with ``bpy.app.translations.register``, so every label Blender draws from a
``text=`` / ``bl_label`` / property name is translated by Blender itself. Blender's own translation of a string wins
over the kit's (Blender looks in add-on tables only for strings it doesn't know).

Text the kit composes or sizes itself (menu items with a right-aligned hotkey and the option box mark, marking
menus, the shelf tabs, wrapped paragraphs) is translated here first with ``iface`` / ``tip`` and drawn with
``translate=False``.

``<locale>.py`` = ``STRINGS = {English: translation}`` (no ``bpy``: ``tools/i18n_strings.py`` reads them for its
coverage report). Add a language by adding a module and listing it in ``LANGUAGES``.
"""

from . import ja_JP, zh_HANS

LANGUAGES = {"ja_JP": ja_JP.STRINGS, "zh_HANS": zh_HANS.STRINGS}
# Blender's default context ("*": labels, menus, panels, properties) and its operator context (operator buttons
# with their own text, operator names)
CONTEXTS = ("*", "Operator")
ARROW = " ▸"
_registered = []


def table():
    """{locale: {(context, English): translation}} for ``bpy.app.translations.register``."""
    return {locale: {(ctx, en): tr for en, tr in strings.items() for ctx in CONTEXTS}
            for locale, strings in LANGUAGES.items()}


def mark(text):
    """Marks a constant as translatable (``tools/i18n_strings.py`` lists it); it is translated where it is shown."""
    return text


def iface(text):
    """``text`` as the interface shows it (the language and "Translate Interface" decide)."""
    if not text:
        return text
    try:
        import bpy
        return bpy.app.translations.pgettext_iface(text)
    except (ImportError, AttributeError):
        return text


def tip(text):
    """``text`` as a tooltip shows it (the language and "Translate Tooltips" decide)."""
    if not text:
        return text
    try:
        import bpy
        return bpy.app.translations.pgettext_tip(text)
    except (ImportError, AttributeError):
        return text


def core(text, fn=iface):
    """``text`` translated without its padding: leading / trailing spaces and a submenu arrow stay as they are."""
    if not text:
        return text
    tail = ""
    if text.endswith(ARROW):
        text, tail = text[:-len(ARROW)], ARROW
    body = text.strip()
    if not body:
        return text + tail
    start = text.index(body)
    return text[:start] + fn(body) + text[start + len(body):] + tail


def path(text, fn=iface):
    """A Maya menu path ("Edit Mesh/Bevel") with each part translated."""
    return "/".join(fn(part) for part in text.split("/")) if text else text


def _wide(ch):
    return ord(ch) >= 0x1100 and not 0xFF61 <= ord(ch) <= 0xFFDC


def width(text):
    """Display width in Latin character cells (CJK characters take two)."""
    return sum(2 if _wide(ch) else 1 for ch in text)


def wrap(text, columns):
    """``text`` broken into lines of at most ``columns`` Latin cells: at spaces, and between CJK characters."""
    import textwrap
    if not any(_wide(ch) for ch in text):
        return textwrap.wrap(text, columns)
    lines = []
    for para in text.split("\n"):
        line, w = "", 0
        for word in split_points(para):
            ww = width(word)
            if line and w + ww > columns:
                lines.append(line.rstrip())
                line, w = word.lstrip(), width(word.lstrip())
            else:
                line, w = line + word, w + ww
        if line.strip():
            lines.append(line.rstrip())
    return lines


def split_points(text):
    """Break points: every CJK character on its own, Latin words with their following space."""
    out, word = [], ""
    for ch in text:
        if _wide(ch):
            if word:
                out.append(word)
                word = ""
            out.append(ch)
        else:
            word += ch
            if ch == " ":
                out.append(word)
                word = ""
    if word:
        out.append(word)
    return out


def register():
    import bpy
    name = __package__
    if name in _registered:
        return
    try:
        bpy.app.translations.register(name, table())
    except ValueError:        # left over from a module reload: replace it
        bpy.app.translations.unregister(name)
        bpy.app.translations.register(name, table())
    _registered.append(name)


def unregister():
    import bpy
    for name in _registered:
        bpy.app.translations.unregister(name)
    _registered.clear()
