# SPDX-License-Identifier: GPL-3.0-or-later
"""Kit windows reopen where they were (#203).

Maya keeps every window's last size and place (top / left edge, width, height) under the window's name and opens
the window there again. The kit's floating windows (Hypershade, Render
Settings, Script Editor, the editors of Windows > ...) are ``screen.area_dupli`` copies of an area, and Blender
gives a new window exactly the size and place of the area it copies; Python can't move or resize a window. So:

- while a kit window is open, a timer keeps its last rect (``Window.x / y / width / height``, screen px) per kind,
  saved in ``window_places.json`` in the extension's user folder (not in the .blend, kept across files and
  sessions). The timer only reads the window: nothing moves it back, and the file is written once the window
  stands still, not while it is dragged or resized (a window may go to another monitor: its place there is what is
  remembered);
- opening that kind again carves an area of the remembered size and place out of the largest area of the window
  the command runs in (one split per tick: Blender lays areas out only between ticks), runs the opening command
  again, which copies that piece into the new window, and reverses the splits, so the main layout is as it was. A remembered rect is first fitted inside that area: the kit can only place a window over
  the window it opens from, which also brings a window that was on another monitor or off the
  screen back into view.
- the pieces split off become an Info editor at once (``PIECE``): a piece joined back is never a 3D View (a gizmo
  tooltip waiting on a freed 3D View region crashed Blender), and a panel of the four view is never split: the four
  view is folded into one panel for the carve and comes back afterwards (``four_view.fold`` / ``unfold``).

``open_window(context, area, kind)`` in ``operators/menu_extras.py`` is the one place every kit window opens.
"""

import json
import os

import bpy

from .. import live_refs

FILE = "window_places.json"
MIN_MARGIN = 40          # px: a margin smaller than this is not split off (the window grows by it instead)
MIN_SIZE = 120           # px: smallest window the kit reopens
TICK = 0.5               # s between rect samples of the open kit windows
# px a carved piece may differ from its target: each split's border takes ~2 px, and a place with margins on all
# four sides is cut twice per axis (Blender 5.2: 340 x 120 carved to 338 x 116, 3 px higher).
# More than that is a failed carve, and the window copies the whole area instead.
CARVE_SLACK = 6

_places = {}             # kind -> [x, y, width, height] (screen px, bottom-left origin)
_tracked = {}            # window pointer -> kind
_last = {}               # window pointer -> the rect the previous tick saw (another rect now = it is being moved)
_state = {"loaded": False, "dirty": False}


# --- storage ---------------------------------------------------------------------------------------------------

def _package():
    return __package__.rpartition(".")[0]


def path():
    try:
        folder = bpy.utils.extension_path_user(_package(), create=True)
    except (ValueError, AttributeError):      # not installed as an extension (legacy add-on)
        return None
    return os.path.join(folder, FILE)


def load():
    _state["loaded"] = True
    p = path()
    if not p or not os.path.isfile(p):
        return
    try:
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return
    if isinstance(data, dict):
        for kind, rect in data.items():
            if isinstance(rect, list) and len(rect) == 4 and all(isinstance(v, int) for v in rect):
                _places[kind] = rect


def save():
    p = path()
    if not p:
        return
    try:
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(_places, fh, indent=1, sort_keys=True)
        _state["dirty"] = False
    except OSError as ex:
        print("Maya Workflow Kit: could not save window places:", ex)


def place(kind):
    """The remembered rect of ``kind`` or None."""
    if not _state["loaded"]:
        load()
    return _places.get(kind)


def remember(kind, rect):
    if not _state["loaded"]:
        load()                      # what is on disk first, then this rect over it
    rect = [int(v) for v in rect]
    if _places.get(kind) != rect:
        _places[kind] = rect
        _state["dirty"] = True


# --- maths (no bpy) ------------------------------------------------------------------------------------------------

def fit(rect, bounds, min_size=MIN_SIZE):
    """``rect`` (x, y, w, h) moved / shrunk to lie inside ``bounds`` (x, y, w, h); None when bounds are too small."""
    bx, by, bw, bh = bounds
    if bw < min_size or bh < min_size:
        return None
    x, y, w, h = rect
    w = max(min_size, min(w, bw))
    h = max(min_size, min(h, bh))
    x = max(bx, min(x, bx + bw - w))
    y = max(by, min(y, by + bh - h))
    return (x, y, w, h)


def snap_margins(rect, bounds, margin=MIN_MARGIN):
    """Margins thinner than ``margin`` are given to the window (an area can't be that thin)."""
    x, y, w, h = rect
    bx, by, bw, bh = bounds
    if x - bx < margin:
        w, x = w + (x - bx), bx
    if (bx + bw) - (x + w) < margin:
        w = bx + bw - x
    if y - by < margin:
        h, y = h + (y - by), by
    if (by + bh) - (y + h) < margin:
        h = by + bh - y
    return (x, y, w, h)


def cuts(rect, bounds):
    """The splits that carve ``rect`` out of ``bounds``: [(direction, coordinate)] in window px — left, right
    (VERTICAL at x), bottom, top (HORIZONTAL at y), only where a margin is left."""
    x, y, w, h = rect
    bx, by, bw, bh = bounds
    out = []
    if x > bx:
        out.append(('VERTICAL', x))
    if x + w < bx + bw:
        out.append(('VERTICAL', x + w))
    if y > by:
        out.append(('HORIZONTAL', y))
    if y + h < by + bh:
        out.append(('HORIZONTAL', y + h))
    return out


def carved(got, rect, slack=CARVE_SLACK):
    """True when the piece ``got`` (x, y, w, h) is the carved ``rect`` (within the split borders)."""
    return all(abs(g - t) <= slack for g, t in zip(got, rect))


def target_in_window(kind, window, area, default=None):
    """The remembered rect of ``kind`` (else ``default``, screen px) in ``window``-relative px, fitted inside ``area``;
    None = no place."""
    rect = place(kind) or default
    if rect is None:
        return None
    rel = (rect[0] - window.x, rect[1] - window.y, rect[2], rect[3])
    bounds = (area.x, area.y, area.width, area.height)
    fitted = fit(rel, bounds)
    return snap_margins(fitted, bounds) if fitted is not None else None


# --- carving and opening -------------------------------------------------------------------------------------------

def _rect(a):
    return (a.x, a.y, a.width, a.height)


def _contains(a, px, py):
    return a.x <= px < a.x + a.width and a.y <= py < a.y + a.height


def _area(window, ptr):
    return next((a for a in window.screen.areas if a.as_pointer() == ptr), None)


def _carved_piece(window, rect, preferred=()):
    """Find the isolated area matching ``rect``; never select the full source area."""
    x, y, width, height = rect
    cx, cy = x + width / 2, y + height / 2
    preferred = set(preferred)
    candidates = [a for a in window.screen.areas if _contains(a, cx, cy)]
    if not candidates:
        return None

    def score(area):
        ax, ay, aw, ah = _rect(area)
        origin_penalty = 0 if area.as_pointer() in preferred else 100000
        return (origin_penalty + abs(aw - width) * 4 + abs(ah - height) * 4
                + abs(ax - x) + abs(ay - y))

    best = min(candidates, key=score)
    ax, ay, aw, ah = _rect(best)
    # Blender split borders and display scaling can introduce small pixel deltas.
    tolerance_x = max(32, int(width * 0.08))
    tolerance_y = max(32, int(height * 0.08))
    if abs(aw - width) > tolerance_x or abs(ah - height) > tolerance_y:
        return None
    return best


def dupli(context, window, area):
    before = set(context.window_manager.windows[:])
    with context.temp_override(window=window, area=area):
        bpy.ops.screen.area_dupli('INVOKE_DEFAULT')
    new = [w for w in context.window_manager.windows if w not in before]
    return new[0] if new else None


def calling_operator():
    """The kit operator whose execute / invoke is opening the window (to run it again once the place is
    carved), or None."""
    import sys
    frame = sys._getframe(2)
    while frame is not None:
        op = frame.f_locals.get("self")
        if isinstance(op, bpy.types.Operator) and op.bl_idname.startswith("ALLSET_OT_"):
            return op
        frame = frame.f_back
    return None


class _Carve:
    """Splits ``area`` one cut per tick (Blender lays the areas out only between ticks) until one piece covers the
    target rect, then runs the opening operator again, which copies that piece (``open_at``), and rejoins the pieces
    afterwards. ``op_call`` is (operator idname, keywords), or a function that gets the new window (None when it
    could not open) instead of the operator running again. ``piece_type``: the editor each area split off becomes at
    once. ``fold``: ``area`` is a panel of the four view, which is folded into one panel first (the rect is fitted
    into that panel again, ``default`` as in ``target_in_window``) and unfolded after the pieces are joined."""

    def __init__(self, kind, window, area, rect, op_call, piece_type=None, fold=False, default=None):
        self.kind, self.rect, self.call, self.piece_type = kind, rect, op_call, piece_type or PIECE
        self.fold, self.default = (1 if fold else 0), default
        self.win, self.source = window.as_pointer(), area.as_pointer()
        self.piece, self.made, self.last = area.as_pointer(), [], None
        self.joins = []
        self.todo = cuts(rect, _rect(area))
        self.wait = 0

    def _window(self):
        return live_refs.window(self.win)

    def tick(self):
        window = self._window()
        if window is None:
            _pending.pop(self.kind, None)
            return None
        if self.fold == 1:                     # the four view into one panel first: no panel of it is split
            from . import four_view
            with bpy.context.temp_override(window=window):
                kept = four_view.fold(bpy.context, window, keep=_area(window, self.source))
            if kept is None:
                self.fold = 0
                return self.finish(window, ok=False)
            self.fold = 2
            self.source = self.piece = kept.as_pointer()
            return TICK_FAST                   # the joined panel gets its size on the next tick
        piece = _area(window, self.piece)
        if piece is None:
            return self.finish(window, ok=False)
        if self.fold == 2:                     # folded and laid out: the place in the whole view
            self.fold = 3
            rect = target_in_window(self.kind, window, piece, self.default)
            if rect is None:
                return self.finish(window, ok=False)
            self.rect, self.todo = rect, cuts(rect, _rect(piece))
        if self.last is not None:
            new = _area(window, self.last)
            if new is not None and new.width == 0 and self.wait < 20:     # not laid out yet
                self.wait += 1
                return TICK_FAST
            cx, cy = self.rect[0] + self.rect[2] / 2, self.rect[1] + self.rect[3] / 2
            piece = next((a for a in (piece, new) if a is not None and _contains(a, cx, cy)), piece)
            self.piece, self.last = piece.as_pointer(), None
        while self.todo:
            direction, at = self.todo.pop(0)
            span = (piece.x, piece.width) if direction == 'VERTICAL' else (piece.y, piece.height)
            factor = (at - span[0]) / span[1] if span[1] else 0
            if not 0.02 < factor < 0.98:
                continue
            before = {a.as_pointer() for a in window.screen.areas}
            with bpy.context.temp_override(window=window, screen=window.screen, area=piece):
                bpy.ops.screen.area_split(direction=direction, factor=factor)
            new = [a for a in window.screen.areas if a.as_pointer() not in before]
            if new:
                new[0].ui_type = self.piece_type
                self.last = new[0].as_pointer()
                self.made.append(self.last)
                self.joins.append((piece.as_pointer(), self.last))
                self.wait = 0
            return TICK_FAST
        got = _rect(piece)
        ok = carved(got, self.rect)
        return self.finish(window, ok)

    def finish(self, window, ok):
        _pending.pop(self.kind, None)
        if self.kind in STRICT:
            # Only an area of the asked size will do; without one the window does not open
            # (instead of copying the whole calling area).
            target = _carved_piece(window, self.rect, [self.piece, *self.made])
            _ready[self.kind] = target.as_pointer() if target is not None else None
        else:
            _ready[self.kind] = self.piece if ok else None
        source = _area(window, self.source) or max(window.screen.areas, key=lambda a: a.width * a.height)
        try:
            if callable(self.call):
                with bpy.context.temp_override(window=window, screen=window.screen, area=source):
                    new = open_at(bpy.context, source, self.kind)
                self.call(new)
            else:
                idname, kwargs = self.call
                module, _sep, name = idname.partition("_OT_")
                op = getattr(getattr(bpy.ops, module.lower()), name)
                with bpy.context.temp_override(window=window, screen=window.screen, area=source):
                    try:
                        op('EXEC_DEFAULT', **kwargs)
                    except RuntimeError:
                        op('INVOKE_DEFAULT', **kwargs)
        except (RuntimeError, TypeError, ReferenceError) as ex:
            print("Maya Workflow Kit: reopening a window failed:", ex)
        finally:
            _ready.pop(self.kind, None)
        joins = list(self.joins)
        ptr = self.win
        folded = self.source if self.fold else 0
        bpy.app.timers.register(lambda: _close_later(ptr, joins, folded), first_interval=TICK_FAST)
        return None


def _close_later(win_ptr, joins, folded=0):
    window = live_refs.window(win_ptr)
    if window is None:
        return None
    try:
        _join_back(window, joins)
    finally:
        if folded:                       # the four view comes back once the pieces are joined: now when laid out
            _unfold_later(win_ptr, folded)
    return None


def _unfold_later(win_ptr, panel_ptr, tries=3):
    from . import four_view
    window, panel = live_refs.find_area(panel_ptr, win_ptr)
    window = window or live_refs.window(win_ptr)
    if window is None:
        four_view._folded.discard(win_ptr)
        return None
    whole = four_view.state(window.screen).get("rect")
    if panel is not None and whole and not four_view.laid_out(panel, whole) and tries > 0:
        # the joined panel gets its rect on the next tick
        bpy.app.timers.register(lambda: _unfold_later(win_ptr, panel_ptr, tries - 1), first_interval=TICK_FAST)
        return None
    try:
        with bpy.context.temp_override(window=window):
            four_view.unfold(bpy.context, window, panel)
    except (ReferenceError, RuntimeError):
        four_view._folded.discard(win_ptr)
    return None


def _join_back(window, joins):
    # Reverse each split: area_close can give a piece to the Outliner or dock instead of the viewport.
    for keep_ptr, remove_ptr in reversed(joins):
        keep, remove = _area(window, keep_ptr), _area(window, remove_ptr)
        if keep is None or remove is None:
            return
        with bpy.context.temp_override(window=window, screen=window.screen):
            try:
                outcome = bpy.ops.screen.area_join(
                    source_xy=(keep.x + keep.width // 2, keep.y + keep.height // 2),
                    target_xy=(remove.x + remove.width // 2, remove.y + remove.height // 2))
                if outcome != {'FINISHED'}:
                    print('Maya Workflow Kit: window split join cancelled')
                    return
            except RuntimeError as ex:
                print("Maya Workflow Kit: window split join failed:", ex)
                return


TICK_FAST = 0.02
PIECE = 'INFO'           # what a carved piece becomes at once (never a 3D View, see the module docstring)
STRICT = set()           # kinds that open nothing rather than a copy of the whole calling area (set by their modules)
_pending = {}            # kind -> _Carve running
_ready = {}              # kind -> pointer of the carved piece while the operator runs again (None = plain)
_deferred = [False]


def deferred():
    """True right after ``open_at`` returned None because the window opens on a later tick."""
    return _deferred[0]


def reopening(kind):
    """True while the opening operator runs again to copy the carved piece of ``kind`` (its first run did the rest
    of its work already)."""
    return kind in _ready


def open_at(context, area, kind, default=None, then=None, piece_type=None):
    """A new window copying ``area``: at the remembered place of ``kind`` (else at ``default``, screen px) when there
    is one. When that place first has to be carved out of ``area``, None is returned (``deferred()`` True) and the
    calling kit operator runs again once the piece is ready — or, given ``then``, ``then(new window)`` is called
    instead. ``piece_type``: the editor the pieces split off become (default ``PIECE``). When ``area`` is a panel of
    the four view, the place is carved out of the whole view folded into one panel (``_Carve`` ``fold``)."""
    _deferred[0] = False
    window = context.window
    if kind in _ready:                         # the second run: copy the carved piece
        ptr = _ready[kind]
        piece = _area(window, ptr) if ptr else None
        if piece is None and kind in STRICT:
            return None
        new = dupli(context, window, piece or area)
    else:
        rect = target_in_window(kind, window, area, default) if kind and not bpy.app.background else None
        call = None
        if rect is not None and rect != _rect(area):
            if then is not None:
                call = then
            else:
                op = calling_operator()
                call = (op.bl_idname, op.as_keywords()) if op is not None else None
        if call is not None and kind not in _pending:
            from . import four_view
            fold = four_view.pane_of(window.screen, area)
            carve = _pending[kind] = _Carve(kind, window, area, rect, call, piece_type, fold, default)
            bpy.app.timers.register(carve.tick, first_interval=0.0)
            _deferred[0] = True
            return None
        if kind in _pending:
            _deferred[0] = True
            return None
        new = dupli(context, window, area)
    if new is not None and kind:
        track(new, kind)
    return new


# --- tracking open kit windows ---------------------------------------------------------------------------------------

def track(window, kind):
    _tracked[window.as_pointer()] = kind
    remember(kind, (window.x, window.y, window.width, window.height))
    if not bpy.app.timers.is_registered(_tick):
        bpy.app.timers.register(_tick, first_interval=TICK, persistent=True)


def settled(ptr, rect):
    """True when ``rect`` is what the previous tick saw of window ``ptr``: it is not being moved or resized now."""
    prev = _last.get(ptr)
    _last[ptr] = rect
    return prev == rect


def _tick():
    moving = False
    for ptr, kind in list(_tracked.items()):
        w = live_refs.window(ptr)
        if w is None:
            del _tracked[ptr]          # closed: its last rect stays remembered
            _last.pop(ptr, None)
            continue
        rect = (w.x, w.y, w.width, w.height)
        remember(kind, rect)
        if not settled(ptr, rect):
            moving = True
    # written once every tracked window stands still: no disk write while the user drags or resizes one
    if _state["dirty"] and not moving:
        save()
    return TICK if _tracked else None


def register():
    _state["loaded"] = False
    _places.clear()


def unregister():
    if bpy.app.timers.is_registered(_tick):
        bpy.app.timers.unregister(_tick)
    if _state["dirty"]:
        save()
    _tracked.clear()
    _last.clear()
