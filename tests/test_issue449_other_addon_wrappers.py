"""Another add-on that wraps the timeline header's draw_header / draw_collapsible, the toolbar's tools_from_context or
space_toolsystem_common.activate_by_id while Maya mode is on keeps its wrapper when Maya mode is switched off; the
kit's function inside it then only calls what it wrapped (#449). An add-on enabled before Maya mode keeps its
function too. The sample add-ons are a few functions inside the test."""

from importlib import import_module

import bpy
from bl_ui import space_toolsystem_common as stc
from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as TOOLBAR

import kit

switch = import_module(kit.MODULE + ".switch")
time_slider = import_module(kit.MODULE + ".ui.time_slider")
toolbox = import_module(kit.MODULE + ".ui.toolbox")
kit_wraps = import_module(kit.MODULE + ".ui.kit_wraps")

_MISSING = object()
calls = {}


def _count(name):
    calls[name] = calls.get(name, 0) + 1


def _targets():
    buttons, menus = time_slider.header_classes()
    return ((buttons, "draw_header"), (menus, "draw_collapsible"), (TOOLBAR, "tools_from_context"),
            (stc, "activate_by_id"))


# --- an add-on enabled before Maya mode: it replaces each function with its own -------------------------------

def _base_header(cls, context, layout):
    _count("base draw_header")


def _base_menus(cls, context, layout):
    _count("base draw_collapsible")


def _base_tools(cls, context, mode=None):
    _count("base tools_from_context")
    yield from ("base tool",)


def _base_activate(context, space_type, idname, *, as_fallback=False):
    _count("base activate_by_id")
    return True


BASE = {"draw_header": lambda: classmethod(_base_header), "draw_collapsible": lambda: classmethod(_base_menus),
        "tools_from_context": lambda: classmethod(_base_tools), "activate_by_id": lambda: _base_activate}
_blender = {}
_base = {}


def base_on():
    for owner, name in _targets():
        _blender[name] = vars(owner).get(name, _MISSING)
        _base[name] = BASE[name]()
        setattr(owner, name, _base[name])


def base_off():
    for owner, name in _targets():
        old = _blender.pop(name)
        if old is _MISSING:
            if name in vars(owner):
                delattr(owner, name)
        else:
            setattr(owner, name, old)


# --- an add-on enabled while Maya mode is on: it wraps what it finds and puts it back when it turns off ---------

_found = {}
_wrappers = {}


def sample_on():
    for owner, name in _targets():
        found = vars(owner)[name]
        _found[name] = found
        if name == "activate_by_id":
            def wrapper(*args, _f=found, **kw):
                _count("sample activate_by_id")
                return _f(*args, **kw)
        elif name == "tools_from_context":
            def wrapper(cls, *args, _f=found, **kw):
                _count("sample tools_from_context")
                yield from _f.__func__(cls, *args, **kw)
            wrapper = classmethod(wrapper)
        else:
            def wrapper(cls, *args, _f=found, _n=name, **kw):
                _count("sample " + _n)
                return _f.__func__(cls, *args, **kw)
            wrapper = classmethod(wrapper)
        _wrappers[name] = wrapper
        setattr(owner, name, wrapper)


def sample_off():
    for owner, name in _targets():
        setattr(owner, name, _found.pop(name))


# --- the kit's own content: recorded instead of drawn --------------------------------------------------------

class _Patched:
    def __enter__(self):
        self.keep = (time_slider._is_timeline, time_slider.draw_header, toolbox.note_tool_click)
        time_slider._is_timeline = lambda context: True
        time_slider.draw_header = lambda context, layout: _count("kit draw_header")
        toolbox.note_tool_click = lambda context, idname, now=None: _count("kit activate_by_id") or False
        return self

    def __exit__(self, *exc):
        time_slider._is_timeline, time_slider.draw_header, toolbox.note_tool_click = self.keep


def _call_all():
    calls.clear()
    buttons, menus = time_slider.header_classes()
    with _Patched():
        buttons.draw_header(bpy.context, None)
        menus.draw_collapsible(bpy.context, None)
        tools = list(TOOLBAR.tools_from_context(bpy.context))
        stc.activate_by_id(bpy.context, 'VIEW_3D', "builtin.move")
    return dict(calls), tools


def test_other_addon_wrappers_stay_when_maya_mode_goes_off():
    switch.set_mode(False, layout=False)
    base_on()
    try:
        switch.set_mode(True, layout=False)
        assert switch.is_on(), switch.last_error[0]
        got, _tools = _call_all()
        assert got.get("kit draw_header") == 1 and "base draw_header" not in got, got
        assert got.get("kit activate_by_id") == 1 and got.get("base activate_by_id") == 1, got
        sample_on()
        switch.set_mode(False, layout=False)
        for owner, name in _targets():
            assert vars(owner).get(name) is _wrappers[name], f"{name}: the other add-on's wrapper should stay"
        got, tools = _call_all()
        for name in ("draw_header", "draw_collapsible", "tools_from_context", "activate_by_id"):
            assert got.get("sample " + name) == 1 and got.get("base " + name) == 1, (name, got)
        assert "kit draw_header" not in got and "kit activate_by_id" not in got, got
        assert tools == ["base tool"], tools
        # the other add-on turns off and puts back what it found (the kit's functions): still no kit content
        sample_off()
        got, tools = _call_all()
        assert "kit draw_header" not in got and "kit activate_by_id" not in got, got
        assert got.get("base draw_header") == 1 and tools == ["base tool"], (got, tools)
        # Maya mode on again: the kit's content once, Maya mode off: the earlier add-on's functions are back
        switch.set_mode(True, layout=False)
        assert switch.is_on(), switch.last_error[0]
        got, _tools = _call_all()
        assert got.get("kit draw_header") == 1 and got.get("kit activate_by_id") == 1, got
        switch.set_mode(False, layout=False)
        for owner, name in _targets():
            assert vars(owner).get(name) is _base[name], f"{name}: the earlier add-on's function should be back"
    finally:
        switch.set_mode(False, layout=False)
        base_off()


def test_maya_mode_on_and_off_again_after_that():
    switch.set_mode(True, layout=False)
    assert switch.is_on() and switch._registered[0], switch.last_error[0]
    switch.set_mode(False, layout=False)
    buttons, menus = time_slider.header_classes()
    assert "draw_collapsible" not in vars(menus)
    assert not kit_wraps.is_wrapped(TOOLBAR, "tools_from_context")
    assert not getattr(stc.activate_by_id, "_allset_wrapped", False)
