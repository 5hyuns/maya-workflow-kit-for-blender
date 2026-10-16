# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya marking menu and hotbox logic, without Blender.

Coordinates are region pixels (y up, as Blender's ``mouse_region_*``). Text
width comes from a ``measure(text) -> width`` callback (``blf`` in Blender, a
character count in tests), so everything here is testable headless.

Behaviour sources: - (radial slots, list
under the ring, hotbox zones and rows), interaction.md:26-29 (press/release,
tap vs hold); timings and distances marked  are from Maya use, not files.
"""

import math

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
    show_delay = 0.15      # s before the menu is drawn: faster strokes are "marks" 
    click_time = 0.25      # s: a shorter press-release in the dead zone = click mode 

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


TOGGLE_OPS = ("wm.context_toggle", "maya_kit.manip_option")


def is_toggle(action):
    """An on/off item (Maya check box menu item): shows its state in the menu."""
    return isinstance(action, tuple) and len(action) == 2 and action[0] in TOGGLE_OPS


class Layout:
    """Item rectangles of one (sub)menu around its centre (Maya placement)."""

    def __init__(self, sub, measure, params, enabled=None):
        self.sub = sub
        self.params = p = params
        enabled = enabled or (lambda action: action is not None)
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

    def hit(self, dx, dy):
        """(item, on_option_box) under a point relative to the centre, or (None, False).

        Rectangles win (list rows, option boxes, radial boxes); otherwise the
        direction picks the radial item of that sector.
        """
        for it in self.items:
            if it.opt_rect and _inside(it.opt_rect, dx, dy):
                return it, True
            if _inside(it.rect, dx, dy):
                return it, False
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


def fit_ring(layout, center, bounds):
    """Keep a menu's items inside ``bounds`` (region x0, y0, x1, y1) without moving its
    centre, the press point the gesture directions are checked from (step 33 「계획」).

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

    def _push(self, item, at):
        layout = Layout(item.sub, self.measure, self.params, self.enabled)
        if self.bounds is not None and layout.items and not layout.radial:
            at = self._inside_bounds(layout, at)
        elif self.bounds is not None and layout.items:
            fit_ring(layout, at, self.bounds)   # in-place radial submenu: centre = pointer
        self.stack.append((layout, at))
        self.hover = (None, False)

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
        dx, dy = self._rel(x, y)
        item, opt = self.layout.hit(dx, dy)
        self.hover = (item, opt)
        if item is None or item.sub is None or not item.enabled:
            return
        # Dragging onto a submenu opens it in place (also the second stroke of a
        # zig-zag mark): radial once the pointer reaches the ring, list on hover.
        if item.kind == "radial" and math.hypot(dx, dy) >= self.params.radius:
            self._push(item, (x, y))
        elif item.kind == "list" and _inside(item.rect, dx, dy):
            self._push(item, (self.center[0] + item.rect[2], self.center[1] + item.rect[3]))

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
                self._push(item, (x, y))
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
    """Menu rows above the cursor, centre box, N/S/E/W zones (Maya, 187-237)."""

    CENTER_W, CENTER_H, ROW_GAP = 130.0, 44.0, 6.0

    def __init__(self, rows, center, measure, params=None, style="ALL", scale=1.0, bounds=None):
        """``bounds`` = (x0, y0, x1, y1): the visible part of the region (not under the
        sidebar/toolbar); menu rows are shifted to stay inside it (step 17)."""
        self.params = p = (params or Params()).scaled(scale) if scale != 1.0 else (params or Params())
        self.center = center
        self.style = style
        self.bounds = bounds
        cw, ch = self.CENTER_W * scale, self.CENTER_H * scale
        cx, cy = center
        self.center_rect = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        self.labels = []   # (rect, key, label)
        if style != "ALL":
            return
        h, gap = p.item_h, self.ROW_GAP * scale
        if bounds is not None:
            rows = self._wrap(rows, measure, p.pad, gap, bounds[2] - bounds[0])
        # rows[0] is drawn top-most; the last row sits just above the centre box.
        y = cy + ch / 2 + gap + len(rows) * (h + gap)
        for row in rows:
            widths = [measure(label) + 2 * p.pad for _key, label in row]
            total = sum(widths) + gap * max(0, len(row) - 1)
            x = cx - total / 2
            if bounds is not None:
                # Centred on the cursor like Maya, slid sideways to stay visible; a row
                # wider than the visible part starts at its left edge.
                x = max(bounds[0], min(x, bounds[2] - total))
            y -= h + gap
            for (key, label), w in zip(row, widths):
                self.labels.append(((x, y, x + w, y + h), key, label))
                x += w + gap
        if bounds is not None and self.labels:
            self._fit_rows(bounds, cy - ch / 2 - gap, cy + ch / 2 + gap)

    def _fit_rows(self, bounds, below_top, above_bottom):
        """Rows that go over the top edge move under the centre box (same order), or down
        as far as needed when there is no room there either (step 33 「계획」 5)."""
        top = max(r[3] for r, _k, _l in self.labels)
        if top <= bounds[3]:
            return
        height = top - above_bottom
        if below_top - height >= bounds[1]:
            dy = below_top - top
        else:
            dy = bounds[3] - top
        self.labels = [((r[0], r[1] + dy, r[2], r[3] + dy), k, l) for r, k, l in self.labels]

    @staticmethod
    def _wrap(rows, measure, pad, gap, width):
        """Split rows wider than ``width`` into several (order kept, step 17)."""
        out = []
        for row in rows:
            line, used = [], 0.0
            for key, label in row:
                w = measure(label) + 2 * pad
                if line and used + gap + w > width:
                    out.append(line)
                    line, used = [], 0.0
                used += (gap if line else 0.0) + w
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


TAP_TIME = 0.4  # Maya (-noClickDelay 0.4)


def is_tap(press_t, release_t, clicked):
    """Space released quickly without picking anything = pane toggle (panePopAt)."""
    return not clicked and release_t - press_t < TAP_TIME
