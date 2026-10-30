"""A group's pivot (an Empty) moves with Blender's own Move in pivot mode, so V / X / C can snap it.

Blender's Affect Only Origins skips objects without data: the group stayed where it was. The GUI side (D + V + MMB
drag onto a child's vertex) is tests/gui/gui_group_pivot_snap.py."""
from importlib import import_module

import bpy

import kit
from test_pivot_tap_components import _cube

hold = import_module(kit.MODULE+'.operators.hold')
pivot = import_module(kit.MODULE+'.operators.pivot')


def _group():
    child = _cube()
    group = bpy.data.objects.new('group1', None)
    bpy.context.collection.objects.link(group)
    child.parent = group
    bpy.context.view_layer.update()
    for ob in bpy.context.view_layer.objects:
        ob.select_set(ob == group)
    bpy.context.view_layer.objects.active = group
    return group, child


def _pivot_mode(on):
    hold.set_pivot_mode(bpy.context.tool_settings, on)


def test_a_group_alone_moves_with_origins_off_then_they_come_back():
    _group()
    _pivot_mode(True)
    ts = bpy.context.tool_settings
    try:
        assert pivot.origins_for_groups(bpy.context)
        assert not ts.use_transform_data_origin and ts.use_transform_skip_children
        pivot._origins_back(bpy.context)
        assert ts.use_transform_data_origin
        pivot._origins_back(bpy.context)      # only once
        assert ts.use_transform_data_origin
    finally:
        _pivot_mode(False)


def test_a_mesh_in_the_selection_keeps_origins_only():
    group, child = _group()
    child.select_set(True)
    _pivot_mode(True)
    ts = bpy.context.tool_settings
    try:
        assert not pivot.origins_for_groups(bpy.context)
        assert ts.use_transform_data_origin
    finally:
        _pivot_mode(False)


def test_outside_pivot_mode_nothing_changes():
    _group()
    _pivot_mode(False)
    ts = bpy.context.tool_settings
    assert not pivot.origins_for_groups(bpy.context)
    assert not ts.use_transform_data_origin


def test_origins_stay_off_when_the_d_hold_ended_during_the_drag():
    _group()
    ts = bpy.context.tool_settings
    hold.begin(ts, 'pivot')
    try:
        assert pivot.origins_for_groups(bpy.context)
    finally:
        hold.end(ts, 'pivot')
    pivot._origins_back(bpy.context)
    assert not ts.use_transform_data_origin
