"""Another workflow add-on that clears the sidebar's Tool tab while it is on (#423): it unregisters every registered
3D View sidebar panel of the Tool category that isn't its own (Blender's Active Tool panel and the kit's panels) and
registers them again when it turns off. Maya mode still starts and stops cleanly in every order, and nothing of the
kit is left behind. The sample add-on is a few functions inside the test.
GUI (a layout made from the window's workspace): tests/gui/gui_issue423_workspace_copy.py."""

from importlib import import_module

import bpy

import kit

switch = import_module(kit.MODULE + ".switch")
safe_reg = import_module(kit.MODULE + ".safe_reg")

_taken = []


def sample_on():
    """The sample add-on turns on: Blender's and other add-ons' Tool-tab panels out of the sidebar."""
    for cls in list(bpy.types.Panel.__subclasses__()):
        if cls.__name__.startswith("SAMPLE423_") or not getattr(cls, "is_registered", False):
            continue
        if (getattr(cls, "bl_space_type", "") == 'VIEW_3D' and getattr(cls, "bl_region_type", "") == 'UI'
                and getattr(cls, "bl_category", "") == "Tool"):
            try:
                bpy.utils.unregister_class(cls)
                _taken.append(cls)
            except RuntimeError:
                pass
    return len(_taken)


def sample_off():
    """The sample add-on turns off: everything it took is registered again (a child once its parent is back)."""
    left = list(_taken)
    while left:
        missed = []
        for cls in left:
            try:
                bpy.utils.register_class(cls)
            except (RuntimeError, ValueError):
                missed.append(cls)
        if len(missed) == len(left):
            break
        left = missed
    _taken.clear()


def _kit_panels():
    return [c for c in kit._all_panels() if c.__module__.startswith(kit.MODULE + ".") and c.is_registered]


def _active_tool():
    from bl_ui.space_view3d import VIEW3D_PT_active_tool
    return VIEW3D_PT_active_tool


def _kit_draws(cls):
    """The kit's Maya mode draw functions on ``cls`` (the Maya / Blender switch stays in both modes)."""
    return [f for f in kit._draw_funcs(cls) if ".allset." in f and ".allset.switch." not in f]


def _maya_off_clean(before, label):
    d = kit.diff(before, kit.snapshot())
    assert not d, f"{label}: left behind:\n" + "\n".join(d)
    assert not _kit_draws(_active_tool()), f"{label}: kit draw functions left on the Active Tool panel"
    assert not _kit_draws(bpy.types.TOPBAR_HT_upper_bar), f"{label}: the kit's top bar left in Blender mode"
    assert not _kit_draws(bpy.types.VIEW3D_HT_tool_header), f"{label}: the kit's tool header left in Blender mode"


def test_maya_mode_starts_with_the_tool_tab_cleared():
    switch.set_mode(False, layout=False)
    before = kit.snapshot()
    try:
        assert sample_on() > 0
        assert not hasattr(bpy.types, "VIEW3D_PT_active_tool"), "the sample add-on should take Blender's panel"
        switch.set_mode(True, layout=False)
        assert switch.is_on() and switch._registered[0], f"Maya mode did not start: {switch.last_error[0]}"
        assert _kit_draws(_active_tool()), "the kit's tool settings should stay on Blender's Active Tool panel"
        switch.set_mode(False, layout=False)
        assert not switch.is_on()
    finally:
        sample_off()
    assert hasattr(bpy.types, "VIEW3D_PT_active_tool")
    _maya_off_clean(before, "Maya mode on and off while the sample add-on was on")


def test_kit_panels_taken_and_given_back():
    switch.set_mode(False, layout=False)
    before = kit.snapshot()
    switch.set_mode(True, layout=False)
    mine = _kit_panels()
    assert mine, "the kit should have sidebar panels in Maya mode"
    try:
        sample_on()
        taken = [c for c in mine if not c.is_registered]
        assert taken, "the sample add-on should take some of the kit's Tool-tab panels"
        switch.set_mode(False, layout=False)
        assert not switch._mode_done, "every Maya mode module should be taken back"
    finally:
        sample_off()          # registers the kit's panels again although Maya mode is off
    # Maya mode on again starts cleanly from that state and takes everything back again
    switch.set_mode(True, layout=False)
    assert switch.is_on() and switch._registered[0], f"Maya mode did not start again: {switch.last_error[0]}"
    assert all(c.is_registered for c in mine), [c.__name__ for c in mine if not c.is_registered]
    switch.set_mode(False, layout=False)
    assert not _kit_panels(), [c.__name__ for c in _kit_panels()]
    _maya_off_clean(before, "the sample add-on took and gave back the kit's panels")


def test_blender_class_lookup():
    cls = _active_tool()
    assert safe_reg.blender_class("VIEW3D_PT_active_tool") is cls
    bpy.utils.unregister_class(cls)
    try:
        assert safe_reg.blender_class("VIEW3D_PT_active_tool") is cls
    finally:
        bpy.utils.register_class(cls)


def test_tool_header_left_in_another_list_draws_nothing():
    """Another add-on that swaps the tool header's own draw can keep the kit's Status Line function in the header's
    list after Maya mode went off; drawn then, it draws nothing instead of failing on the missing Maya properties."""
    switch.set_mode(True, layout=False)
    fn = import_module(kit.MODULE + ".ui.status_line").draw_tool_header
    switch.set_mode(False, layout=False)

    class Header:
        layout = None       # any use of the layout would fail

    fn(Header(), bpy.context)
