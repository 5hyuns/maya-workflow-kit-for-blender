"""Another workflow add-on that swaps a header's draw while Maya mode is on can take the kit's function for Blender's
own and put it back into the header when it turns off, after Maya mode is already off (#426). That kept kit function
then draws Blender's own header, never the kit's (whose buttons and properties are gone, which raised an error once
in the Dope Sheet's icon row). The sample add-on is a few functions inside the test."""

from importlib import import_module

import bpy

import kit

switch = import_module(kit.MODULE + ".switch")
own_draw = import_module(kit.MODULE + ".ui.own_draw")

HEADERS = ("DOPESHEET_HT_header", "GRAPH_HT_header", "OUTLINER_HT_header", "TOPBAR_HT_upper_bar",
           "VIEW3D_HT_header", "STATUSBAR_HT_header", "INFO_HT_header", "NLA_HT_header")

_saved = {}


def _sample_draw(self, context):
    pass


def _funcs(name):
    return getattr(bpy.types, name)._dyn_ui_initialize()


def sample_on():
    """Swaps what it takes for the header's own draw: an entry named ``<class>.draw``, else the first one."""
    for name in HEADERS:
        funcs = _funcs(name)
        i = next((i for i, f in enumerate(funcs) if getattr(f, "__qualname__", "") == f"{name}.draw"), 0)
        _saved[name] = funcs[i]
        funcs[i] = _sample_draw


def sample_off():
    for name, fn in _saved.items():
        funcs = _funcs(name)
        if _sample_draw in funcs:
            funcs[funcs.index(_sample_draw)] = fn
    _saved.clear()


class _Recorder:
    def __init__(self):
        self.calls = 0

    def __call__(self, menu, context):
        self.calls += 1


def test_kept_kit_draw_draws_blender():
    switch.set_mode(False, layout=False)
    switch.set_mode(True, layout=False)
    assert switch.is_on(), switch.last_error[0]
    sample_on()
    # the kit functions it took that stand in for Blender's own draw (a kit row prepended to a header draws nothing
    # with Maya mode off)
    taken = {name: fn for name, fn in _saved.items() if (name, fn) in own_draw._saved}
    switch.set_mode(False, layout=False)
    sample_off()
    try:
        assert taken, "the sample add-on should have taken some kit draw functions"
        for name, fn in taken.items():
            assert fn in _funcs(name), f"{name}: the sample add-on should have put the kit function back"
            rec = _Recorder()
            keep = own_draw._own.get(name)
            own_draw._own[name] = rec
            try:
                fn(None, bpy.context)      # a kit draw would use self.layout and the kit's operators
            finally:
                if keep is None:
                    own_draw._own.pop(name, None)
                else:
                    own_draw._own[name] = keep
            assert rec.calls == 1, f"{name}: the kept kit function {fn.__qualname__} should draw Blender's own header"
    finally:
        for name, fn in taken.items():   # put Blender's own draw back for the next test file run
            funcs = _funcs(name)
            if fn in funcs and own_draw._own.get(name) is not None:
                funcs[funcs.index(fn)] = own_draw._own[name]


def test_maya_mode_on_again_after_that():
    switch.set_mode(True, layout=False)
    assert switch.is_on() and switch._registered[0], switch.last_error[0]
    switch.set_mode(False, layout=False)
