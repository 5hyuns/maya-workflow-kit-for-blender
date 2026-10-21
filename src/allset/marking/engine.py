# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya marking menu and hotbox logic, without Blender (docs/steps/step_9.md 「계획」 2-3).

Coordinates are region pixels (y up, as Blender's ``mouse_region_*``). Text
width comes from a ``measure(text) -> width`` callback (``blf`` in Blender, a
character count in tests), so everything here is testable headless.

Behaviour sources: research/maya/hotkeys_and_menus.md §4-§5 (radial slots, list
under the ring, hotbox zones and rows), interaction.md:26-29 (press/release,
tap vs hold); timings and distances marked [K] are from Maya use, not files.
"""

import math

from ..names import PRODUCT
from . import menus as mm

# Sector order for atan2 angles (0 = east, counter-clockwise, 45 degrees each).
_SECTORS = ("E", "NE", "N", "NW", "W", "SW", "S", "SE")
_UNIT = {name: (math.cos(math.radians(45 * i)), math.sin(math.radians(45 * i)))
         for i, name in enumerate(_SECTORS)}


class Params:
    """Sizes in pixels at UI scale 1 (``scaled`` multiplies them)."""
    radius = 80.0          # centre -> radial item anchor
    dead = 12.0            # no direction inside this (= Blender pie_menu_threshold)
    item_h = 22.0
    pad = 8.0              # text padding inside an item
    opt_w = 16.0           # option box square
    list_gap = 10.0
    show_delay = 0.15      # s before the menu is drawn: faster strokes are "marks" [K]
    click_time = 0.25      # s: a shorter press-release in the dead zone = click mode [K]

    def scaled(self, k):
        p = Params()
        for name in ("radius", "dead", "item_h", "pad", "opt_w", "list_gap"):
            setattr(p, name, getattr(self, name) * k)
        p.show_delay, p.click_time = self.show_delay, self.click_time
        return p


def direction(dx, dy, dead):
    """Radial sector of a vector, or None inside the dead zone."""
    if math.hypot(dx, dy) < dead:
        return None
    angle = math.degrees(math.atan2(dy, dx)) % 360.0
    return _SECTORS[int((angle + 22.5) // 45) % 8]


class Item:
    __slots__ = ("label", "action", "kind", "key", "rect", "opt_rect", "enabled", "sub", "option")

    def __init__(self, label, action, kind, key, rect, opt_rect, enabled, option):
        self.label = label
        self.action = action
        self.kind = kind              # "radial" | "list"
        self.key = key                # radial name or list index
        self.rect = rect              # (x0, y0, x1, y1), relative to the layout centre
        self.opt_rect = opt_rect      # option box rect or None
        self.enabled = enabled
        self.sub = action if isinstance(action, mm.Sub) else None
        self.option = option

    def __repr__(self):
        return f"Item({self.label!r}, {self.key!r})"


def _inside(rect, x, y):
    return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]


TOGGLE_OPS = ("wm.context_toggle", "allset.manip_option", "allset.symmetry", "allset.component_mask",
              "allset.pivot_option")
# Shift+Q pick mask: Poly Vertices / Poly Edges / Faces are check boxes, "All Components on" is a command (step 93).
MASK_CHECKS = ("VERT", "EDGE", "FACE")


def is_toggle(action):
    """An on/off item (Maya check box menu item): shows its state in the menu."""
    if not (isinstance(action, tuple) and len(action) == 2 and action[0] in TOGGLE_OPS):
        return False
    return action[0] != "allset.component_mask" or action[1].get("kind") in MASK_CHECKS


class Layout:
    """Item rectangles of one (sub)menu around its centre (Maya placement)."""

    def __init__(self, sub, measure, params, enabled=None):
        self.sub = sub
        self.params = p = params
        enabled = enabled or (lambda action: action is not None and not mm.is_unavailable(action))
        self.radial = {}
        self.items = []
        h = p.item_h
        for key in mm.RADIALS:
            if key not in sub.radial:
                continue
            label, action = sub.radial[key]
            opt = label in sub.options and action is not None and not isinstance(action, mm.Sub)
            w = measure(self._text(label, action)) + 2 * p.pad + (p.opt_w if opt else 0)
            ux, uy = _UNIT[key]
            ax, ay = ux * p.radius, uy * p.radius
            if key in ("N", "S"):
                x0 = ax - w / 2
            elif key in ("E", "NE", "SE"):
                x0 = ax
            else:
                x0 = ax - w
            rect = (x0, ay - h / 2, x0 + w, ay + h / 2)
            item = Item(label, action, "radial", key, rect, self._opt(rect, opt), enabled(action), opt)
            self.radial[key] = item
            self.items.append(item)
        # Linear list under the ring (or from the centre when there is no ring).
        rows = [e for e in sub.items]
        if rows:
            widths = [measure(self._text(e[0], e[1])) for e in rows if e != mm.DIVIDER]
            w = max(widths or [0]) + 2 * p.pad + p.opt_w
            if self.radial:
                top = min([it.rect[1] for it in self.radial.values()] + [-p.radius]) - p.list_gap
                x0 = -w / 2
            else:
                top = h / 2
                x0 = p.dead
            y = top
            for i, entry in enumerate(rows):
                if entry == mm.DIVIDER:
                    y -= p.list_gap / 2
                    continue
                label, action = entry
                opt = label in sub.options and action is not None and not isinstance(action, mm.Sub)
                rect = (x0, y - h, x0 + w, y)
                self.items.append(Item(label, action, "list", i, rect, self._opt(rect, opt),
                                       enabled(action), opt))
                y -= h

    @staticmethod
    def _text(label, action):
        # Toggles keep room on the right for their check box (draw.py, step 26).
        # A Blender menu ("menu", id) opens as a submenu too (e.g. Assign Existing Material).
        sub = isinstance(action, mm.Sub) or (isinstance(action, tuple) and action[0] == "menu")
        return label + (" ▸" if sub else "    " if is_toggle(action) else "")

    def _opt(self, rect, on):
        if not on:
            return None
        s = self.params.opt_w
        return (rect[2] - s, rect[1] + (rect[3] - rect[1] - s) / 2,
                rect[2], rect[1] + (rect[3] - rect[1] + s) / 2)

    def hit(self, dx, dy, rects_only=False):
        """(item, on_option_box) under a point relative to the centre, or (None, False).

        Rectangles win (list rows, option boxes, radial boxes); otherwise the
        direction picks the radial item of that sector (not with ``rects_only``).
        """
        for it in self.items:
            if it.opt_rect and _inside(it.opt_rect, dx, dy):
                return it, True
            if _inside(it.rect, dx, dy):
                return it, False
        if rects_only:
            return None, False
        d = direction(dx, dy, self.params.dead)
        if d and d in self.radial:
            return self.radial[d], False
        return None, False


def _move(item, dx, dy):
    r = item.rect
    item.rect = (r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy)
    if item.opt_rect:
        o = item.opt_rect
        item.opt_rect = (o[0] + dx, o[1] + dy, o[2] + dx, o[3] + dy)


def _bbox(items):
    return (min(i.rect[0] for i in items), min(i.rect[1] for i in items),
            max(i.rect[2] for i in items), max(i.rect[3] for i in items))


def _slide(lo, hi, low, high):
    """Offset that moves [lo, hi] inside [low, high] (towards ``low`` if it can't fit)."""
    if hi - lo > high - low:
        return low - lo
    return max(low - lo, min(0.0, high - hi))


MIN_COLUMN_ROWS = 4


def _columns(rows, top, floor, w):
    """Re-flow list rows (in order, divider gaps kept) into columns of width ``w`` from ``top`` down to
    ``floor``; the first column stays where it is."""
    x_first = rows[0].rect[0]
    col, y, prev_bottom = 0, top, None
    for it in rows:
        r = it.rect
        height = r[3] - r[1]
        gap = (prev_bottom - r[3]) if prev_bottom is not None else 0.0
        prev_bottom = r[1]
        row_top = y - gap
        if row_top - height < floor and y != top:
            col += 1
            row_top = top
        _move(it, x_first + col * w - r[0], row_top - r[3])
        y = row_top - height


def fit_ring(layout, center, bounds):
    """Keep a menu's items inside ``bounds`` (region x0, y0, x1, y1) without moving its
    centre, the press point the gesture directions are measured from (step 33 「계획」).

    Radial boxes slide inside; the list goes under the ring (Maya), else above it, else
    beside it (right, then left), else is pushed up from under the ring."""
    cx, cy = center
    x0, y0, x1, y1 = bounds[0] - cx, bounds[1] - cy, bounds[2] - cx, bounds[3] - cy  # centre-relative
    for it in layout.radial.values():
        _move(it, _slide(it.rect[0], it.rect[2], x0, x1), _slide(it.rect[1], it.rect[3], y0, y1))
    rows = [it for it in layout.items if it.kind == "list"]
    if not rows:
        return
    lx0, ly0, lx1, ly1 = _bbox(rows)
    if not layout.radial:
        dx, dy = _slide(lx0, lx1, x0, x1), _slide(ly0, ly1, y0, y1)
    else:
        gap = layout.params.list_gap
        r = layout.params.radius
        rx0, ry0, rx1, ry1 = _bbox(list(layout.radial.values()))
        rx0, ry0, rx1, ry1 = min(rx0, -r), min(ry0, -r), max(rx1, r), max(ry1, r)
        h, w = ly1 - ly0, lx1 - lx0
        if ly0 < y0 and ly1 <= y1 and ly1 - y0 >= MIN_COLUMN_ROWS * layout.params.item_h:
            # Maya keeps the list under the ring (14_marking_menu_object.png, where it runs off the screen);
            # here the rows that don't fit continue in more columns, still under the ring (step 52).
            _columns(rows, ly1, y0, w)
            bx0, _by0, bx1, _by1 = _bbox(rows)
            dx = -(bx0 + bx1) / 2
            dx += _slide(bx0 + dx, bx1 + dx, x0, x1)
            for it in rows:
                _move(it, dx, 0.0)
            return
        below = (0.0, 0.0)                                    # as laid out (under the ring)
        above = (0.0, ry1 + gap - ly0)
        right = (rx1 + gap - lx0, -h / 2 - ly0)
        left = (rx0 - gap - lx1, -h / 2 - ly0)
        dx = dy = None
        for cdx, cdy in (below, above):
            if ly0 + cdy >= y0 and ly1 + cdy <= y1:
                dx, dy = cdx + _slide(lx0 + cdx, lx1 + cdx, x0, x1), cdy
                break
        else:
            for cdx, cdy in (right, left):
                if lx0 + cdx >= x0 and lx1 + cdx <= x1 and h <= y1 - y0:
                    dx, dy = cdx, cdy + _slide(ly0 + cdy, ly1 + cdy, y0, y1)
                    break
            else:
                dx, dy = _slide(lx0, lx1, x0, x1), _slide(ly0, ly1, y0, y1)
        if w > x1 - x0:
            dx = x0 - lx0
    for it in rows:
        _move(it, dx, dy)


class Session:
    """One marking-menu interaction.

    ``press``-driven: created on the button press at ``origin``; feed
    ``move`` / ``release`` / ``click``. ``result`` becomes
    ``("RUN", item, option)`` or ``("CANCEL", None, False)``; ``None`` while open.
    """

    def __init__(self, menu, origin, t0, measure, params=None, enabled=None, bounds=None):
        """``bounds`` = (x0, y0, x1, y1): the visible part of the region; list
        submenus that would cross it are moved inside (step 29)."""
        self.params = params or Params()
        self.bounds = bounds
        root = Layout(menu, measure, self.params, enabled)
        if bounds is not None:
            fit_ring(root, origin, bounds)
        self.measure = measure
        self.enabled = enabled
        self.t0 = t0
        self.stack = [(root, origin)]
        # Per stack level: the item of the level below that opened it, when it is a list row's cascade (a Qt
        # menu submenu beside the row, step 129): the menus under a cascade stay drawn and hit-tested. In-place
        # radial submenus (None) replace the menu, like Maya's.
        self.openers = [None]
        self.mode = "PRESS"           # "PRESS" (button held) | "CLICK" (menu stays open)
        self.pos = origin
        self.trail = [origin]
        self.hover = (None, False)
        self.result = None
        self.max_dist = 0.0

    # -- state --------------------------------------------------------------
    @property
    def layout(self):
        return self.stack[-1][0]

    @property
    def center(self):
        return self.stack[-1][1]

    def visible(self, t):
        """Draw the menu? Not during a quick stroke (mark without looking)."""
        return self.mode == "CLICK" or len(self.stack) > 1 or t - self.t0 >= self.params.show_delay

    def _rel(self, x, y):
        return x - self.center[0], y - self.center[1]

    def layers(self):
        """[(layout, centre, (hovered item, on option box))] to draw, bottom first: the top menu and, under an
        open cascade, the menus it hangs from (their hovered row = the cascade's opener)."""
        top = len(self.stack) - 1
        level = top
        while self.openers[level] is not None:
            level -= 1
        out = []
        for k in range(level, top + 1):
            lay, center = self.stack[k]
            out.append((lay, center, self.hover if k == top else (self.openers[k + 1], False)))
        return out

    def _push(self, item, at, cascade=False):
        layout = Layout(item.sub, self.measure, self.params, self.enabled)
        if self.bounds is not None and layout.items and not layout.radial:
            at = self._inside_bounds(layout, at)
        elif self.bounds is not None and layout.items:
            fit_ring(layout, at, self.bounds)   # in-place radial submenu: centre = pointer
        self.stack.append((layout, at))
        self.openers.append(item if cascade else None)
        self.hover = (None, False)

    def _pop_to(self, level):
        del self.stack[level + 1:]
        del self.openers[level + 1:]

    def _hit_stack(self, x, y):
        """(level, item, on option box) under (x, y): the top menu first (directions included); when it has
        nothing there and is a cascade, the boxes / rows of the menus it hangs from (step 129, #5: dragging on
        down the list after passing a submenu row closed the whole menu)."""
        top = len(self.stack) - 1
        lay, (cx, cy) = self.stack[top]
        item, opt = lay.hit(x - cx, y - cy)
        level = top
        while item is None and self.openers[level] is not None:
            level -= 1
            lay, (cx, cy) = self.stack[level]
            item, opt = lay.hit(x - cx, y - cy, rects_only=True)
            if item is not None:
                return level, item, opt
        return top, item, opt

    def _inside_bounds(self, layout, at):
        """Shift a list submenu up / left so all its rows are inside ``bounds``."""
        x0, y0, x1, y1 = self.bounds
        lx0 = min(it.rect[0] for it in layout.items)
        ly0 = min(it.rect[1] for it in layout.items)
        lx1 = max(it.rect[2] for it in layout.items)
        ly1 = max(it.rect[3] for it in layout.items)
        x, y = at
        x = max(x0 - lx0, min(x, x1 - lx1))
        y = min(y1 - ly1, max(y, y0 - ly0))
        return (x, y)

    # -- input ----------------------------------------------------------------
    def move(self, x, y, t):
        self.pos = (x, y)
        self.trail.append((x, y))
        ox, oy = self.stack[0][1]
        self.max_dist = max(self.max_dist, math.hypot(x - ox, y - oy))
        level, item, opt = self._hit_stack(x, y)
        if level < len(self.stack) - 1:
            if item is self.openers[level + 1]:
                # back on the row whose cascade is open: keep it (close deeper ones)
                self._pop_to(level + 1)
                self.hover = (item, opt)
                return
            self._pop_to(level)   # another row of a menu under the cascade: the cascade closes
        dx, dy = self._rel(x, y)
        self.hover = (item, opt)
        if item is None or item.sub is None or not item.enabled:
            return
        # Dragging onto a submenu opens it in place (also the second stroke of a
        # zig-zag mark): radial once the pointer reaches the ring, list on hover.
        if item.kind == "radial" and math.hypot(dx, dy) >= self.params.radius:
            self._push(item, (x, y))
        elif item.kind == "list" and _inside(item.rect, dx, dy):
            self._push(item, (self.center[0] + item.rect[2], self.center[1] + item.rect[3]), cascade=True)

    def release(self, x, y, t):
        """The button that opened the menu was released."""
        if self.mode != "PRESS":
            return self.result
        self.move(x, y, t)
        item, opt = self.hover
        if item is not None and item.sub is None:
            return self._finish(item, opt)
        if item is None and len(self.stack) == 1 and self.max_dist < self.params.dead \
                and t - self.t0 < self.params.click_time:
            self.mode = "CLICK"   # quick click: the menu stays up
            return None
        if item is not None and item.sub is not None:
            self.mode = "CLICK"   # released on a submenu: keep it open to pick from
            return None
        return self._cancel()

    def click(self, x, y, t):
        """A button press while in click mode."""
        self.move(x, y, t)
        item, opt = self.hover
        if item is None:
            return self._cancel()
        if item.sub is not None:
            if len(self.stack) and self.layout.sub is not item.sub:
                self._push(item, (x, y), cascade=item.kind == "list")
            return None
        return self._finish(item, opt)

    def cancel(self):
        return self._cancel()

    def _finish(self, item, opt):
        if not item.enabled:
            return self._cancel()
        self.result = ("RUN", item, opt)
        return self.result

    def _cancel(self):
        self.result = ("CANCEL", None, False)
        return self.result


# --- hotbox ---------------------------------------------------------------------------

class HotboxLayout:
    """Maya hotbox (HotboxMenus.mel:57, 187-237; docs/steps/step_52.md 「계획」 2): menu rows above the cursor
    (``rows``, top first), the cursor row (``side`` = left / right boxes beside the centre box), rows under it
    (``below``, top first), zone lines on the diagonals. Sizes are Maya's at scale 1 (13_hotbox.png: row pitch
    35 = box 26 + gap 9; the centre box is the title with padding)."""

    ROW_H, ROW_GAP, SIDE_GAP = 26.0, 9.0, 88.0
    LINE_GAP, LINE_LEN = 20.0, 28.0     # zone lines: start past the rows, length per axis [measured, step 52]

    def __init__(self, rows, center, measure, params=None, style="ALL", scale=1.0, bounds=None,
                 below=(), side=None, title=PRODUCT):
        """``bounds`` = (x0, y0, x1, y1): where the hotbox may draw (step 52: the window's screen areas,
        in region pixels); rows are wrapped / moved to stay inside it (steps 17, 33)."""
        self.params = p = (params or Params()).scaled(scale) if scale != 1.0 else (params or Params())
        self.center = center
        self.style = style
        self.bounds = bounds
        self.title = title
        h, gap = self.ROW_H * scale, self.ROW_GAP * scale
        self.row_h = h
        cx, cy = center
        cw = max(measure(title) + 4 * p.pad, 2 * h)
        self.center_rect = (cx - cw / 2, cy - h / 2, cx + cw / 2, cy + h / 2)
        self.labels = []   # (rect, key, label)
        self.bands = []    # row backgrounds (Maya draws each row as one strip)
        self.zone_lines = []
        if style != "ALL":
            return
        width = bounds[2] - bounds[0] if bounds is not None else None
        above = self._wrap(rows, measure, p.pad, width) if width else [list(r) for r in rows]
        under = self._wrap(below, measure, p.pad, width) if width else [list(r) for r in below]
        pitch = h + gap
        blocks = []
        y = cy + h / 2 + gap + (len(above) - 1) * pitch      # bottom of the top-most row
        for row in above:
            blocks.append(("above", self._row(row, measure, p.pad, cx, y, h, bounds)))
            y -= pitch
        y = cy - h / 2 - gap - h
        for row in under:
            blocks.append(("below", self._row(row, measure, p.pad, cx, y, h, bounds)))
            y -= pitch
        if side:
            left, right = side
            if left:
                w = measure(left[1]) + 2 * p.pad
                x1 = self.center_rect[0] - self.SIDE_GAP * scale
                blocks.append(("side", [((x1 - w, cy - h / 2, x1, cy + h / 2), left[0], left[1])]))
            if right:
                w = measure(right[1]) + 2 * p.pad
                x0 = self.center_rect[2] + self.SIDE_GAP * scale
                blocks.append(("side", [((x0, cy - h / 2, x0 + w, cy + h / 2), right[0], right[1])]))
        if bounds is not None:
            blocks = self._fit_blocks(blocks, bounds, gap)
        for _kind, row in blocks:
            if row:
                self.labels.extend(row)
                self.bands.append((min(r[0] for r, _k, _l in row), min(r[1] for r, _k, _l in row),
                                   max(r[2] for r, _k, _l in row), max(r[3] for r, _k, _l in row)))
        self._zone_lines(scale)

    @staticmethod
    def _row(row, measure, pad, cx, y, h, bounds):
        widths = [measure(label) + 2 * pad for _key, label in row]
        total = sum(widths)
        x = cx - total / 2
        if bounds is not None:
            # centred on the cursor like Maya, slid sideways to stay visible (step 17)
            x = max(bounds[0], min(x, bounds[2] - total))
        out = []
        for (key, label), w in zip(row, widths):
            out.append(((x, y, x + w, y + h), key, label))
            x += w
        return out

    def _fit_blocks(self, blocks, bounds, gap):
        """Rows over the top edge go under the lower rows; rows under the bottom edge go over the upper
        rows (order kept); what still doesn't fit is pushed inside (steps 17, 33)."""
        def span(kind):
            rs = [r for k, row in blocks if k == kind for r, _k, _l in row]
            return (min(r[1] for r in rs), max(r[3] for r in rs)) if rs else None

        def shift(kind, dy):
            return [(k, [((r[0], r[1] + dy, r[2], r[3] + dy), kk, ll) for r, kk, ll in row]) if k == kind else (k, row)
                    for k, row in blocks]
        up, down = span("above"), span("below")
        floor = min(self.center_rect[1], down[0] if down else self.center_rect[1])
        ceil = max(self.center_rect[3], up[1] if up else self.center_rect[3])
        if up and up[1] > bounds[3]:
            dy = floor - gap - up[1]                       # under everything
            if up[0] + dy < bounds[1]:
                dy = bounds[3] - up[1]
            blocks = shift("above", dy)
        elif down and down[0] < bounds[1]:
            dy = ceil + gap - down[0]                      # over everything
            if down[1] + dy > bounds[3]:
                dy = bounds[1] - down[0]
            blocks = shift("below", dy)
        return blocks

    def _zone_lines(self, scale):
        """Maya's four short diagonal lines between the zones (13_hotbox.png), just outside the rows."""
        cx, cy = self.center
        top = max([r[3] for r in self.bands] + [self.center_rect[3]]) - cy
        bottom = cy - min([r[1] for r in self.bands] + [self.center_rect[1]])
        g, n = self.LINE_GAP * scale, self.LINE_LEN * scale
        for sy, ext in ((1, top), (-1, bottom)):
            t0 = ext + g
            for sx in (-1, 1):
                self.zone_lines.append(((cx + sx * t0, cy + sy * t0), (cx + sx * (t0 + n), cy + sy * (t0 + n))))

    @staticmethod
    def _wrap(rows, measure, pad, width):
        """Split rows wider than ``width`` into several (order kept, step 17)."""
        out = []
        for row in rows:
            line, used = [], 0.0
            for key, label in row:
                w = measure(label) + 2 * pad
                if line and used + w > width:
                    out.append(line)
                    line, used = [], 0.0
                used += w
                line.append((key, label))
            if line:
                out.append(line)
        return out

    def label_at(self, x, y):
        for rect, key, label in self.labels:
            if _inside(rect, x, y):
                return key
        return None

    def zone(self, x, y):
        """Zone whose marking menu a click at (x, y) opens."""
        if _inside(self.center_rect, x, y):
            return "C"
        if self.style == "CENTER":
            return None
        dx, dy = x - self.center[0], y - self.center[1]
        if abs(dy) >= abs(dx):
            return "N" if dy > 0 else "S"
        return "E" if dx > 0 else "W"


TAP_TIME = 0.4  # HotboxMenus.mel:244 (-noClickDelay 0.4)


def is_tap(press_t, release_t, clicked):
    """Space released quickly without picking anything = pane toggle (panePopAt)."""
    return not clicked and release_t - press_t < TAP_TIME
