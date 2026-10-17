# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya editor chrome helpers: a flat menu bar row at the top of an editor
(Maya panels and docks have one: Channel Box "Channels Edit Object Show", Layer Editor "Layers Options
Help", Outliner "Display Show Help"; , :140-142, ui_layout.md:258-264)
and greyed menu items for Maya entries the kit has no equivalent for."""


def menu_bar(layout, entries):
    """``entries`` = ((label, menu idname), ...): menus drawn flat like a Qt menu bar."""
    row = layout.row(align=True)
    row.alignment = 'LEFT'           # natural widths, left to right like a Qt menu bar
    row.emboss = 'PULLDOWN_MENU'
    for label, idname in entries:
        row.menu(idname, text=label)
    return row


def grey(layout, text):
    """A Maya menu item without a Blender equivalent: shown, not usable (like unmapped menu items)."""
    row = layout.row()
    row.enabled = False
    row.label(text=text)


def paragraph(layout, context, text, alignment='LEFT'):
    """``text`` wrapped to the region width (about 7 px per character at UI scale 1), greyed (step 67)."""
    import textwrap
    region = context.region
    scale = context.preferences.system.ui_scale
    width = region.width if region is not None else 300
    col = layout.column()
    col.active = False
    return wrapped(col, textwrap.wrap(text, max(16, int(width / (7 * scale))) - 2), alignment)


def wrapped(layout, lines, alignment='CENTER'):
    """Several short label lines (Blender labels don't wrap)."""
    col = layout.column(align=True)
    for line in lines:
        row = col.row()
        row.alignment = alignment
        row.label(text=line)
    return col
