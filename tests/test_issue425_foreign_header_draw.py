"""Another add-on that changes the draw of a header the kit draws in Maya mode (#425). The kit only ever takes the place
of Blender's own draw function in the header's draw list: a function another add-on put in that place, or prepended /
appended to the header, stays in the list while Maya mode is on, and turning Maya mode off gives back the list exactly
as it was. The sample add-on is a few functions inside the test."""

import functools
from importlib import import_module

import bpy

import kit

switch = import_module(kit.MODULE + ".switch")
own_draw = import_module(kit.MODULE + ".ui.own_draw")

# every header whose own draw the kit swaps in Maya mode (a name missing in this Blender is left out)
HEADERS = ("TOPBAR_HT_upper_bar", "STATUSBAR_HT_header", "VIEW3D_HT_header", "VIEW3D_HT_tool_header",
           "OUTLINER_HT_header", "IMAGE_HT_header", "IMAGE_HT_tool_header", "NODE_HT_header", "GRAPH_HT_header",
           "DOPESHEET_HT_header", "GRAPH_HT_playback_controls", "DOPESHEET_HT_playback_controls", "INFO_HT_header",
           "TEXT_HT_header", "NLA_HT_header")


def _headers():
    return [n for n in HEADERS if hasattr(bpy.types, n)]


def _funcs(name):
    return getattr(bpy.types, name)._dyn_ui_initialize()


def _blender_own(name):
    """Blender's own draw in the header's list (None when something took its place)."""
    for f in _funcs(name):
        if getattr(f, "__name__", "") == "draw" and f.__globals__.get("__name__", "").startswith("bl_ui"):
            return f
    return None


_put = {}     # header -> (kind, sample function, what it replaced)


def sample_replace():
    """The sample add-on draws a header of its own: its function (wrapping Blender's) takes Blender's place."""
    for name in _headers():
        funcs = _funcs(name)
        own = _blender_own(name)
        assert own is not None, f"{name}: Blender's own draw should be in the list before the sample add-on"

        @functools.wraps(own)
        def wrapper(self, context, _own=own):
            return _own(self, context)
        funcs[funcs.index(own)] = wrapper
        _put[name] = ("replace", wrapper, own)


def sample_prepend():
    """The sample add-on adds a row in front of each header."""
    for name in _headers():
        def extra(self, context):
            pass
        getattr(bpy.types, name).prepend(extra)
        _put[name] = ("prepend", extra, None)


def sample_off():
    for name, (kind, fn, own) in _put.items():
        funcs = _funcs(name)
        if kind == "replace" and fn in funcs:
            funcs[funcs.index(fn)] = own
        elif kind == "prepend":
            getattr(bpy.types, name).remove(fn)
    _put.clear()


def _lists():
    return {name: list(_funcs(name)) for name in _headers()}


def _kit_in(name):
    return [f for f in _funcs(name) if getattr(f, "__module__", "").startswith(kit.MODULE + ".")
            and not getattr(f, "__module__", "").startswith(kit.MODULE + ".switch")]


def _round_trip(label):
    lists = _lists()
    switch.set_mode(True, layout=False)
    try:
        assert switch.is_on() and switch._registered[0], f"Maya mode did not start: {switch.last_error[0]}"
        for name, (kind, fn, _own) in _put.items():
            assert fn in _funcs(name), f"{label}: {name}: the sample add-on's function left the header's list"
        swapped = [name for name in _put if any(f not in lists[name] for f in _funcs(name))]
        assert len(swapped) >= 5, f"{label}: the kit should draw in most of these headers: {swapped}"
    finally:
        switch.set_mode(False, layout=False)
    after = _lists()
    changed = [name for name in lists if after[name] != lists[name]]
    assert not changed, f"{label}: draw lists not given back exactly: " + ", ".join(
        f"{n}: {[getattr(f, '__qualname__', f) for f in lists[n]]} -> "
        f"{[getattr(f, '__qualname__', f) for f in after[n]]}" for n in changed)


def test_replaced_own_draw_is_kept():
    switch.set_mode(False, layout=False)
    before = _lists()
    sample_replace()
    try:
        _round_trip("another add-on's function in Blender's place")
        # while Maya mode is on, the kit draws beside it and nothing outside its own areas
        switch.set_mode(True, layout=False)
        try:
            for name, (_kind, fn, own) in _put.items():
                for kfn in _kit_in(name):
                    if (name, kfn) not in own_draw._saved:
                        continue          # appended / prepended by the kit, not swapped
                    drawn = own_draw.original(name, kfn)
                    assert drawn is not fn and drawn is not own, f"{name}: the kit would draw the header twice"
        finally:
            switch.set_mode(False, layout=False)
    finally:
        sample_off()
    assert _lists() == before


def test_prepended_function_is_kept():
    switch.set_mode(False, layout=False)
    before = _lists()
    sample_prepend()
    try:
        _round_trip("another add-on's function prepended")
        switch.set_mode(True, layout=False)
        try:
            # where the kit draws instead of Blender, it took Blender's own draw's place, not the prepended one's
            doubled = [n for n in _put if _blender_own(n) is not None
                       and any(k[0] == n and k[1] in _funcs(n) for k in own_draw._saved)]
            assert not doubled, f"Blender's own draw still beside the kit's: {doubled}"
        finally:
            switch.set_mode(False, layout=False)
    finally:
        sample_off()
    assert _lists() == before


def test_kit_function_left_behind_draws_blender():
    """A kit draw function another add-on keeps after Maya mode is off falls back to Blender's own draw."""
    switch.set_mode(True, layout=False)
    kfn = next(k[1] for k in own_draw._saved if k[0] == "OUTLINER_HT_header")
    switch.set_mode(False, layout=False)
    own = own_draw.original("OUTLINER_HT_header", kfn)
    assert own is _blender_own("OUTLINER_HT_header"), own
