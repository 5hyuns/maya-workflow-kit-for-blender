# SPDX-License-Identifier: GPL-3.0-or-later
"""Marking menu geometry without Blender: sizes at UI scale 1 (``Params``), the radial sector of a stroke
(``direction``), the item rectangles of one (sub)menu around its centre (``Layout``, ``Item``: radial boxes and the
list under the ring) and which items are check boxes (``is_toggle``). Used by ``engine`` (``Session``) and
``hotbox_engine``; ``draw.py`` reads them through ``engine``."""

import math

from . import menus as mm


# Sector order for atan2 angles (0 = east, counter-clockwise, 45 degrees each).
_SECTORS = ("E", "NE", "N", "NW", "W", "SW", "S", "SE")
_UNIT = {name: (math.cos(math.radians(45 * i)), math.sin(math.radians(45 * i)))
         for i, name in enumerate(_SECTORS)}


class Params:
    """Sizes in pixels at UI scale 1 (``scaled`` multiplies them)."""
    # Radial ring = Maya 2022's (#99):
    # N / S box centres and E / W near sides ``radius`` from the press point, diagonal boxes with their corner at
    # (±d, ±d), d = radius·cos 45°; boxes 21 px high, text + 2 × 25 px wide (+ 5 with an option box).
    radius = 55.0          # centre -> radial item anchor
    dead = 12.0            # no direction inside this (= Blender pie_menu_threshold)
    item_h = 22.0          # list rows
    pad = 8.0              # text padding inside a list row / hotbox label
    opt_w = 16.0           # option box square
    list_gap = 10.0
    ring_h = 21.0          # radial box height
    ring_pad = 25.0        # text padding inside a radial box (a submenu arrow sits in the right one)
    ring_opt = 5.0         # extra radial box width for an option box
    ring_list_gap = 21.0   # ring bottom -> list top
    show_delay = 0.15      # s before the menu is drawn: faster strokes are "marks"
    click_time = 0.25      # s: a shorter press-release in the dead zone = click mode
    # Options (add-on preferences, both off by default; marking/modal.py copies them in):
    # quick_gestures (mm_quick_gestures): the menu stays hidden while the pointer keeps moving and shows after a
    # pause of ``show_delay`` (then stays); a radial submenu entered by a hidden mark stays hidden too; a hidden mark
    # picks radial items only, by the stroke's heading (gesture_recognition.py), and draw.py shows the names of the
    # submenus it passed. Off: the menu shows ``show_delay`` after the press and once a submenu opens.
    quick_gestures = False
    # submenu_guides (mm_submenu_guides): a radial submenu is linked to the centre it opened from, with a ring there;
    # resting within ``anchor_r`` of it for ``return_dwell`` s goes back to that menu (``Session._dwell_back``); the
    # line from the centre to the pointer shows only near a centre.
    submenu_guides = False
    anchor_r = 33.0
    return_dwell = 0.7

    SIZES = ("radius", "dead", "item_h", "pad", "opt_w", "list_gap", "ring_h", "ring_pad", "ring_opt",
             "ring_list_gap", "anchor_r")
    FLAGS = ("show_delay", "click_time", "return_dwell", "quick_gestures", "submenu_guides")

    def scaled(self, k):
        p = Params()
        for name in self.SIZES:
            setattr(p, name, getattr(self, name) * k)
        for name in self.FLAGS:
            setattr(p, name, getattr(self, name))
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


TOGGLE_OPS = ("wm.context_toggle", "allset.prevent_negative_scale", "allset.xform_constraint", "allset.manip_option", "allset.symmetry", "allset.component_mask",
              "allset.pivot_option", "allset.mm_camera_based")
# Shift+Q pick mask: Poly Vertices / Poly Edges / Faces are check boxes, "All Components on" is a command.
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
            item = Item(label, action, "radial", key, self.ring_rect(key, measure(self.ring_text(label, action)), opt),
                        None, enabled(action), opt)
            item.opt_rect = self._opt(item.rect, opt)
            self.radial[key] = item
            self.items.append(item)
        # Linear list under the ring (or from the centre when there is no ring).
        rows = [e for e in sub.items]
        if rows:
            widths = [measure(self._text(e[0], e[1])) for e in rows if e != mm.DIVIDER]
            w = max(widths or [0]) + 2 * p.pad + p.opt_w
            if self.radial:
                top = min([it.rect[1] for it in self.radial.values()] + [-p.radius]) - p.ring_list_gap
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

    def ring_rect(self, key, text_w, opt=False):
        """Rect of the radial box ``key`` whose text is ``text_w`` wide: Maya 2022's placement.
        y is up here, so N is +y."""
        p = self.params
        r, h = p.radius, p.ring_h
        d = r * math.cos(math.radians(45.0))
        w = text_w + 2 * p.ring_pad + (p.ring_opt if opt else 0.0)
        if key in ("N", "S"):
            x0 = -w / 2
            cy = r if key == "N" else -r
            return (x0, cy - h / 2, x0 + w, cy + h / 2)
        x0 = r if key == "E" else -r - w if key == "W" else d if key in ("NE", "SE") else -d - w
        if key in ("E", "W"):
            y0 = -h / 2
        else:   # diagonal: the outer side on the diagonal anchor, the box hanging towards the horizontal axis
            y0 = d - h if key in ("NE", "NW") else -d
        return (x0, y0, x0 + w, y0 + h)

    @staticmethod
    def has_arrow(action):
        """A submenu item: Maya draws a ▸ at the box / row's right (a Blender ("menu", id) opens as one too)."""
        return isinstance(action, mm.Sub) or (isinstance(action, tuple) and action[0] == "menu")

    @staticmethod
    def ring_text(label, action):
        """Text that sizes a radial box: the arrow lives in the right padding,
        toggles keep room for their check box."""
        return label + ("    " if is_toggle(action) and not Layout.has_arrow(action) else "")

    @staticmethod
    def _text(label, action):
        # Toggles keep room on the right for their check box (draw.py).
        # A Blender menu ("menu", id) opens as a submenu too (e.g. Assign Existing Material).
        return label + (" ▸" if Layout.has_arrow(action) else "    " if is_toggle(action) else "")

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
