"""Issue #327: T in mesh edit mode cycles to the Transform tool (wm.tool_set_by_id with cycle). Blender's cycling walks
every tool group, so a kit tool must not leave an empty (separator) entry inside a group."""

import bpy

import kit

MODES = ('OBJECT', 'EDIT_MESH', 'EDIT_CURVE', 'EDIT_ARMATURE', 'POSE')


def _groups(mode):
    from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
    cls = ToolSelectPanelHelper._tool_class_from_space_type('VIEW_3D')
    return [g for g in cls.tools_from_context(bpy.context, mode=mode) if type(g) is tuple]


def test_no_empty_entry_inside_a_tool_group():
    for mode in MODES:
        for group in _groups(mode):
            assert None not in group, (mode, [None if t is None else t.idname for t in group])


def test_smart_extrude_still_in_the_extrude_group():
    ids = [[t.idname for t in g] for g in _groups('EDIT_MESH')]
    group = next((g for g in ids if "builtin.extrude_region" in g), None)
    assert group is not None and "allset.smart_extrude_tool" in group, ids


def test_t_cycles_to_transform_in_edit_mode():
    area = next((a for a in bpy.context.screen.areas if a.type == 'VIEW_3D'), None) if bpy.context.screen else None
    if area is None:
        return
    region = next(r for r in area.regions if r.type == 'WINDOW')
    bpy.ops.mesh.primitive_cube_add()
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            assert bpy.ops.wm.tool_set_by_id(name="builtin.transform", cycle=True) == {'FINISHED'}
            tool = bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH', create=False)
            assert tool.idname == "builtin.transform", tool.idname
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')


def test_maya_mode_off_keeps_groups_clean():
    kit.disable()
    try:
        for group in _groups('EDIT_MESH'):
            assert None not in group
    finally:
        kit.enable()


# --- T = Show Manipulator Tool: the last kit operation's manipulator + In-View Editor ---------------------------

from importlib import import_module  # noqa: E402
from types import SimpleNamespace  # noqa: E402

import bmesh  # noqa: E402

ex = import_module(kit.MODULE + ".operators.extrude")
modify = import_module(kit.MODULE + ".operators.modify_maya")
in_view = import_module(kit.MODULE + ".ui.in_view")
taphold = import_module(kit.MODULE + ".operators.taphold")


def _t_items(km_name):
    km = kit.maya_kc().keymaps[km_name]
    return [k.idname for k in km.keymap_items if k.active and k.type == 'T' and k.value == 'PRESS'
            and not (k.ctrl or k.shift or k.alt)]


def test_t_runs_show_manipulator():
    for km in ("Object Mode", "Mesh"):
        items = _t_items(km)
        assert items and items[0] == "allset.show_manipulator", (km, items)
        assert "wm.tool_set_by_id" not in items, (km, items)


def _cube_top_extruded():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(f.normal.z > 0.9)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.extrude() == {'FINISHED'}
    return ob


def _shown(ob):
    space = SimpleNamespace(type='VIEW_3D', show_region_toolbar=False, show_region_header=True,
                            show_region_ui=False, show_object_viewport_mesh=True)
    return in_view.record(SimpleNamespace(space_data=space, edit_object=ob))[1] is not None


def test_t_brings_back_the_extrude_manipulator_after_w():
    ob = _cube_top_extruded()
    taphold.get_binding("tool_move").tap(bpy.context)        # W: Move manipulator instead
    assert not _shown(ob)
    assert modify.show_last_input(bpy.context) is True        # T
    assert _shown(ob)


def test_t_in_edit_mode_with_another_selection_falls_back():
    ob = _cube_top_extruded()
    taphold.get_binding("tool_move").tap(bpy.context)
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(f.normal.z < -0.9)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    assert modify.show_last_input(bpy.context) is False       # the Transform tool instead (like Maya: no node)


def test_t_in_object_mode_opens_the_last_extrusion():
    ob = _cube_top_extruded()
    caps = set(ex.current(ob).cap_faces)
    bpy.ops.object.mode_set(mode='OBJECT')
    for p in ob.data.polygons:
        p.select = False
    assert modify.show_last_input(bpy.context) is True
    assert ob.mode == 'EDIT' and _shown(ob)
    bm = bmesh.from_edit_mesh(ob.data)
    assert {f.index for f in bm.faces if f.select} == caps
    bpy.ops.object.mode_set(mode='OBJECT')


def test_t_without_history_is_not_shown():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cube_add(size=1)
    assert modify.show_last_input(bpy.context) is False
    assert bpy.context.active_object.mode == 'OBJECT'
