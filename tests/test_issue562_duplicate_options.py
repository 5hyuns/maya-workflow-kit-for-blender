"""#562: Edit Mesh > Duplicate has its option window (Duplicate Face Options: Separate duplicated faces, on by
default, and Offset), opened by the menu's option box from any editor; the window's Duplicate keeps its values and a
plain menu click then runs with them, so with Separate off the copy stays in the mesh, like Maya."""

from importlib import import_module

import bmesh
import bpy

import kit


def m(name):
    return import_module(f"{kit.MODULE}.{name}")


def _cube():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    ob = bpy.context.active_object
    ob.name = "pCube1"
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(ob.data)
    top = max(bm.faces, key=lambda f: f.calc_center_median().z)
    for f in bm.faces:
        f.select_set(f is top)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    return ob


def test_option_box_opens_the_window():
    menu_option_box = m("ui.menu_option_box")
    option_windows = m("operators.option_windows")
    assert menu_option_box.option_kind("Edit Mesh/Duplicate") == "window"
    w = option_windows.find_path("Edit Mesh/Duplicate")
    assert w is not None and w.title == "Duplicate Face Options" and w.action == "Duplicate"
    assert w.defaults() == {"separate": True, "offset": 0.0}
    assert option_windows.find(("v3d", "allset.duplicate_face", {})) is w


def test_saved_separate_off_keeps_the_copy_in_the_mesh():
    option_windows = m("operators.option_windows")
    old = option_windows.saved("duplicate_face")
    try:
        ob = _cube()
        # the window's Duplicate: runs with Separate off and keeps the values
        assert bpy.ops.allset.opt_duplicate_face('EXEC_DEFAULT', separate=False) == {'FINISHED'}
        assert option_windows.saved("duplicate_face")["separate"] is False
        assert bpy.context.mode == 'EDIT_MESH' and len(bpy.data.objects) == 1
        assert len(bmesh.from_edit_mesh(ob.data).faces) == 7
        # a plain menu click now duplicates with the saved values: still one object
        ob = _cube()
        assert bpy.ops.allset.menu_item(item="Edit Mesh/Duplicate") == {'FINISHED'}
        assert bpy.context.mode == 'EDIT_MESH' and len(bpy.data.objects) == 1
        assert len(bmesh.from_edit_mesh(ob.data).faces) == 7
        # Separate back on: the copy becomes an object of its own
        option_windows.store("duplicate_face", {"separate": True, "offset": 0.0})
        _cube()
        assert bpy.ops.allset.menu_item(item="Edit Mesh/Duplicate") == {'FINISHED'}
        assert bpy.context.mode == 'OBJECT' and len(bpy.context.selected_objects) == 1
    finally:
        option_windows.store("duplicate_face", old)
