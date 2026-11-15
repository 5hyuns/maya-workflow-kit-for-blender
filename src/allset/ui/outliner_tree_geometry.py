# SPDX-License-Identifier: GPL-3.0-or-later
"""Where the kit tree's rows sit and the shapes drawn in them: row height (``unit``), scroll position per Outliner
(``SCROLL``, ``first_row``), the row under a region y (``row_index_at``) and its rectangle (``row_rect``), the
scrollbar and the visibility column (``scrollbar``, ``eye_x``), and the node icons, expand arrows and eyes added to
the draw batches (``_icon``, ``_triangle``, ``_eye``). The draw itself: outliner_tree._draw.
"""

import math

import bpy

SCROLL = {}               # area pointer -> first shown row


# --- geometry ------------------------------------------------------------------------------------------------------

def unit(prefs=None):
    """Blender's Outliner row height UI_UNIT_Y in pixels."""
    system = (prefs or bpy.context.preferences).system
    return int(int(18.0 * system.ui_scale + 0.5) + 2 * system.pixel_size)


def _font_size(prefs):
    styles = prefs.ui_styles
    points = getattr(styles[0].widget, "points", 11.0) if len(styles) else 11.0
    return points * prefs.system.ui_scale


def page_rows(region, u):
    return max(1, region.height // u)


def first_row(area, region, n, u):
    """First shown row of ``area`` (scroll), clamped so the last page is full."""
    top = max(0, n - page_rows(region, u))
    first = min(max(0, SCROLL.get(area.as_pointer(), 0)), top)
    SCROLL[area.as_pointer()] = first
    return first


def row_index_at(area, region, y, u, n):
    """Row under region y, or None (below the last row)."""
    if y < 0 or y >= region.height:
        return None
    k = first_row(area, region, n, u) + int((region.height - 1 - y) // u)
    return k if 0 <= k < n else None


def row_rect(area, region, k, u, n):
    """(y0, y1) region pixels of row ``k`` (it may lie outside the region)."""
    j = k - first_row(area, region, n, u)
    y1 = region.height - j * u
    return y1 - u, y1


SCROLLBAR = 0.35      # x UI unit: the scrollbar width at the right edge


def scrollbar(region, u, n, first):
    """(x0, x1, thumb y0, thumb y1) of the scrollbar, or None when every row fits."""
    page = page_rows(region, u)
    if n <= page:
        return None
    h = region.height
    thumb = max(u, h * page / n)
    y1 = h - (h - thumb) * first / max(1, n - page)
    x1 = region.width - 2
    return x1 - max(4, round(SCROLLBAR * u)), x1, y1 - thumb, y1


# --- drawing -------------------------------------------------------------------------------------------------------

def _quad(pos, col, x0, y0, x1, y1, rgba):
    pos.extend(((x0, y0), (x1, y0), (x1, y1), (x0, y0), (x1, y1), (x0, y1)))
    col.extend((rgba,) * 6)


_ICON_PARTS = {}          # (kind, cx, cy, r, rgba) -> the icon's (tris, tcol, lines, lcol) made by ``_icon_parts``


def _icon(tris, tcol, lines, lcol, kind, cx, cy, r, rgba):
    """Add a node icon's shapes; an icon drawn at the same place and colour before reuses the points made then."""
    key = (kind, cx, cy, r, rgba)
    got = _ICON_PARTS.get(key)
    if got is None:
        made = ([], [], [], [])
        _icon_parts(*made, kind, cx, cy, r, rgba)
        if len(_ICON_PARTS) > 1024:
            _ICON_PARTS.clear()
        got = _ICON_PARTS[key] = tuple(tuple(m) for m in made)
    tris.extend(got[0])
    tcol.extend(got[1])
    lines.extend(got[2])
    lcol.extend(got[3])


def _icon_parts(tris, tcol, lines, lcol, kind, cx, cy, r, rgba):
    from .hypergraph_layout import icon_shapes
    for prim in icon_shapes(kind):
        name, a = prim[0], prim[1:]
        if name == "rect":
            _quad(tris, tcol, cx + a[0] * r, cy + a[1] * r, cx + a[2] * r, cy + a[3] * r, rgba)
        elif name == "frame":
            x0, y0, x1, y1 = cx + a[0] * r, cy + a[1] * r, cx + a[2] * r, cy + a[3] * r
            lines.extend(((x0, y0), (x1, y0), (x1, y0), (x1, y1), (x1, y1), (x0, y1), (x0, y1), (x0, y0)))
            lcol.extend((rgba,) * 8)
        elif name == "line":
            lines.extend(((cx + a[0] * r, cy + a[1] * r), (cx + a[2] * r, cy + a[3] * r)))
            lcol.extend((rgba,) * 2)
        elif name in ("ring", "disc"):
            ox, oy, rr = cx + a[0] * r, cy + a[1] * r, a[2] * r
            pts = [(ox + rr * math.cos(2 * math.pi * i / 12), oy + rr * math.sin(2 * math.pi * i / 12))
                   for i in range(12)]
            for i in range(12):
                p, q = pts[i], pts[(i + 1) % 12]
                if name == "ring":
                    lines.extend((p, q))
                    lcol.extend((rgba,) * 2)
                else:
                    tris.extend(((ox, oy), p, q))
                    tcol.extend((rgba,) * 3)
        elif name == "tri":
            tris.extend(((cx + a[0] * r, cy + a[1] * r), (cx + a[2] * r, cy + a[3] * r),
                         (cx + a[4] * r, cy + a[5] * r)))
            tcol.extend((rgba,) * 3)


def _triangle(tris, tcol, cx, cy, r, down, rgba):
    if down:
        pts = ((cx - r, cy + r * 0.5), (cx + r, cy + r * 0.5), (cx, cy - r * 0.7))
    else:
        pts = ((cx - r * 0.5, cy + r), (cx - r * 0.5, cy - r), (cx + r * 0.7, cy))
    tris.extend(pts)
    tcol.extend((rgba,) * 3)


ICON_RGB = (0.741, 0.741, 0.741)      # kit icon grey
JOINT_RGB = (0.282, 0.667, 0.710)     # kit icon teal
CHILD_SELECTED = 0.33                 # share of the selection highlight on a row with a selected node below it


def _eye(tris, tcol, lines, lcol, cx, cy, u, shown, rgba):
    """An eye (open: outline + pupil; closed: the lower lid only)."""
    rx, ry = 0.36 * u, 0.2 * u
    n = 12
    upper = [(cx - rx + 2 * rx * i / n, cy + ry * math.sin(math.pi * i / n)) for i in range(n + 1)]
    lower = [(cx - rx + 2 * rx * i / n, cy - ry * math.sin(math.pi * i / n)) for i in range(n + 1)]
    for pts in ((upper, lower) if shown else (lower,)):
        for i in range(n):
            lines.extend((pts[i], pts[i + 1]))
            lcol.extend((rgba,) * 2)
    if shown:
        r = 0.1 * u
        pts = [(cx + r * math.cos(2 * math.pi * i / 10), cy + r * math.sin(2 * math.pi * i / 10)) for i in range(10)]
        for i in range(10):
            tris.extend(((cx, cy), pts[i], pts[(i + 1) % 10]))
            tcol.extend((rgba,) * 3)


def eye_x(region, u, n, first):
    """Centre x of the visibility column (Display > Visibility Column), left of the scrollbar."""
    bar = scrollbar(region, u, n, first)
    right = bar[0] if bar is not None else region.width
    return right - 0.9 * u
