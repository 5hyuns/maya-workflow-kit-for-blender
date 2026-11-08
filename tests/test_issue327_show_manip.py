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


def _object_ctx(ob):
    space = SimpleNamespace(type='VIEW_3D', show_region_toolbar=False, show_region_header=True,
                            show_region_ui=False, show_object_viewport_mesh=True)
    return SimpleNamespace(space_data=space, mode='OBJECT', active_object=ob, edit_object=None)


def _object_shown(ob):
    """The node the 3D View shows for ``ob`` in object mode (manipulator / In-View Editor), or None."""
    return in_view.record(_object_ctx(ob))[1]


def test_t_in_object_mode_stays_in_object_mode():
    ob = _cube_top_extruded()
    name = ex.current(ob).name
    bpy.ops.object.mode_set(mode='OBJECT')
    for p in ob.data.polygons:
        p.select = False
    assert _object_shown(ob) is None                          # nothing before T
    assert modify.show_last_input(bpy.context) is True
    assert ob.mode == 'OBJECT' and bpy.context.mode == 'OBJECT'
    rec = _object_shown(ob)
    assert rec is not None and rec.name == name, rec
    assert rec.spec.view_fields == ex.FIELDS                  # Thickness ... Keep Faces Together
    assert in_view.arrow_visible(_object_ctx(ob))             # the extrude manipulator too
    centre, _axes, _k = in_view.manip_frame(ob, rec)
    assert abs(centre.z - 0.5) < 1e-5, centre                 # on the extruded top face
    assert modify.show_last_input(bpy.context) is True        # T again: still shown (not a toggle)
    assert _object_shown(ob) is rec


def test_tool_key_ends_what_t_showed_in_object_mode():
    ob = _cube_top_extruded()
    bpy.ops.object.mode_set(mode='OBJECT')
    assert modify.show_last_input(bpy.context) is True
    taphold.get_binding("tool_move").tap(bpy.context)        # W
    assert _object_shown(ob) is None
    other = bpy.data.objects.new("other", None)
    bpy.context.collection.objects.link(other)
    assert modify.show_last_input(bpy.context) is True
    bpy.context.view_layer.objects.active = other              # another object: not shown on it
    assert in_view.record(_object_ctx(other))[1] is None
    bpy.context.view_layer.objects.active = ob
    ob.select_set(False)                                       # deselected: hidden
    assert _object_shown(ob) is None
    ob.select_set(True)
    assert _object_shown(ob) is not None


def test_object_mode_edits_rerun_the_node_without_edit_mode():
    ob = _cube_top_extruded()
    bpy.ops.object.mode_set(mode='OBJECT')
    assert modify.show_last_input(bpy.context) is True
    rec = _object_shown(ob)
    unit = ex.units.maya_unit(bpy.context.scene)
    top = max(v.co.z for v in ob.data.vertices)
    in_view.preview(bpy.context, ob, rec, dict(rec.params, local_translate_z=0.5), unit)   # a drag
    assert ob.mode == 'OBJECT'
    assert abs(max(v.co.z for v in ob.data.vertices) - (top + 0.5 * unit)) < 1e-5
    assert ex.object_record(ob) is rec and _object_shown(ob) is rec       # still the node
    assert in_view.commit(bpy.context, rec, {"local_translate_z": 0.25}) == {'FINISHED'}   # release
    assert ob.mode == 'OBJECT' and bpy.context.mode == 'OBJECT'
    assert abs(max(v.co.z for v in ob.data.vertices) - (top + 0.25 * unit)) < 1e-5
    assert ex.object_record(ob).params["local_translate_z"] == 0.25


def _pcube():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    prim_history = import_module(kit.MODULE + ".operators.prim_history")
    return prim_history.create_object(bpy.context, 'CUBE')


POLYCUBE_ROWS = ("width", "height", "depth", "subdivisionsWidth", "subdivisionsHeight", "subdivisionsDepth")
POLYCUBE_LABELS = ("Width", "Height", "Depth", "Subdivisions Width", "Subdivisions Height", "Subdivisions Depth")


def test_t_on_a_polycube_shows_its_in_view_editor_only():
    ob = _pcube()
    assert modify.show_last_input(bpy.context) is True
    assert ob.mode == 'OBJECT'
    node = _object_shown(ob)
    assert node is not None and node.name == "polyCube1", node
    assert node.spec.view_fields == POLYCUBE_ROWS
    assert tuple(node.spec.labels[f] for f in node.spec.view_fields) == POLYCUBE_LABELS
    assert [in_view.value_text(node, f) for f in node.spec.view_fields] == ["1"] * 6, \
        [in_view.value_text(node, f) for f in node.spec.view_fields]
    assert not in_view.arrow_visible(_object_ctx(ob))         # no manipulator, like Maya
    k = node.node["unit"]
    assert in_view.commit(bpy.context, node, {"width": 2.0}) == {'FINISHED'}
    assert abs(ob.dimensions.x - 2.0 * k) < 1e-5 and abs(ob.dimensions.y - 1.0 * k) < 1e-5, ob.dimensions[:]
    assert _object_shown(ob).params["width"] == 2.0
    assert in_view.commit(bpy.context, _object_shown(ob), {"subdivisionsHeight": 0}) == {'FINISHED'}
    assert _object_shown(ob).params["subdivisionsHeight"] == 1      # the node's own limit
    assert len(ob.data.polygons) == 6


def test_t_on_polycube_faces_shows_nothing():
    ob = _pcube()
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(f.normal.z > 0.9)
    bmesh.update_edit_mesh(ob.data)
    assert modify.show_last_input(bpy.context) is False       # components only: no node shown, no error
    assert ob.mode == 'EDIT'
    bpy.ops.object.mode_set(mode='OBJECT')


def test_the_node_picked_in_channel_box_inputs_wins():
    cb = import_module(kit.MODULE + ".ui.channel_box")
    ob = _pcube()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(f.normal.z > 0.9)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.transform_component() == {'FINISHED'}    # polyMoveFace1 leaves the mesh as it is
    bpy.ops.object.mode_set(mode='OBJECT')
    cb.reset_open()
    assert modify.show_last_input(bpy.context) is True
    assert _object_shown(ob).name == "polyMoveFace1"         # the newest input node
    assert bpy.ops.allset.cb_node_toggle(node=cb.history_node("polyCube1")) == {'FINISHED'}   # click its name
    node = _object_shown(ob)
    assert node is not None and node.name == "polyCube1" and node.spec.view_fields == POLYCUBE_ROWS
    assert not in_view.arrow_visible(_object_ctx(ob))
    assert bpy.ops.allset.cb_node_toggle(node=cb.history_node("polyMoveFace1")) == {'FINISHED'}
    assert _object_shown(ob).name == "polyMoveFace1"         # the last one clicked open
    assert in_view.arrow_visible(_object_ctx(ob))
    bpy.ops.allset.cb_node_toggle(node=cb.history_node("polyMoveFace1"))   # clicked closed: no pick
    assert _object_shown(ob).name == "polyMoveFace1"
    bpy.ops.allset.cb_node_toggle(node=cb.history_node("polyCube1"))       # polyCube1 closed ...
    bpy.ops.allset.cb_node_toggle(node=cb.history_node("polyCube1"))       # ... and picked again
    assert _object_shown(ob).name == "polyCube1"
    cb.reset_open()                                                         # another lead / file: no pick
    assert _object_shown(ob).name == "polyMoveFace1"


def test_t_without_history_is_not_shown():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cube_add(size=1)
    assert modify.show_last_input(bpy.context) is False
    assert bpy.context.active_object.mode == 'OBJECT'
