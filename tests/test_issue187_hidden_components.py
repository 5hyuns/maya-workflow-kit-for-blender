# SPDX-License-Identifier: GPL-3.0-or-later
"""Issue #187: component-mode commands warn instead of editing a hidden active mesh."""

from importlib import import_module

import bpy

import kit


display = import_module(kit.MODULE + ".operators.display")
COMPONENT_MODES = {
    'VERT': (True, False, False),
    'EDGE': (False, True, False),
    'FACE': (False, False, True),
    'MULTI': (True, True, True),
}


def _cube():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.ops.mesh.primitive_cube_add()
    return bpy.context.active_object


def _expect_hidden_cancelled(ob):
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = ob
    assert not ob.visible_get()
    ts = bpy.context.tool_settings
    before = (tuple(ts.mesh_select_mode), ts.use_uv_select_sync, ts.uv_select_mode)
    selected = tuple(bpy.context.selected_objects)
    for kind in COMPONENT_MODES:
        assert bpy.ops.allset.component_mode(type=kind) == {'CANCELLED'}, kind
        assert bpy.context.mode == 'OBJECT' and bpy.context.active_object == ob
        assert not ob.visible_get(), "A component command must not unhide the object"
        assert tuple(bpy.context.selected_objects) == selected
        assert (tuple(ts.mesh_select_mode), ts.use_uv_select_sync, ts.uv_select_mode) == before


def test_component_modes_on_viewport_hidden_mesh_cancel():
    ob = _cube()
    ob.hide_viewport = True
    _expect_hidden_cancelled(ob)


def test_component_modes_on_eye_hidden_mesh_cancel():
    ob = _cube()
    ob.hide_set(True)
    _expect_hidden_cancelled(ob)


def test_component_modes_in_hidden_collection_cancel():
    ob = _cube()
    collection = bpy.data.collections.new("Hidden components")
    bpy.context.scene.collection.children.link(collection)
    collection.objects.link(ob)
    for old in tuple(ob.users_collection):
        if old != collection:
            old.objects.unlink(ob)
    try:
        collection.hide_viewport = True
        _expect_hidden_cancelled(ob)
    finally:
        collection.hide_viewport = False


def test_hidden_mesh_reports_an_actionable_warning():
    ob = _cube()
    ob.hide_viewport = True
    bpy.context.view_layer.update()

    class Command:
        type = 'VERT'

        def __init__(self):
            self.reports = []

        def report(self, kind, message):
            self.reports.append((set(kind), message))

    command = Command()
    assert display.ALLSET_OT_component_mode.execute(command, bpy.context) == {'CANCELLED'}
    assert len(command.reports) == 1
    kind, message = command.reports[0]
    assert kind == {'WARNING'} and ob.name in message
    assert "hidden" in message.lower() and "show" in message.lower()
    assert "Traceback" not in message


def test_visible_mesh_still_enters_and_changes_component_modes():
    ob = _cube()
    for kind, expected in COMPONENT_MODES.items():
        assert bpy.ops.allset.component_mode(type=kind) == {'FINISHED'}
        assert bpy.context.mode == 'EDIT_MESH' and bpy.context.active_object == ob
        assert tuple(bpy.context.tool_settings.mesh_select_mode) == expected
    bpy.ops.object.mode_set(mode='OBJECT')
