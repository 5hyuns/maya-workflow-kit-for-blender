"""INPUTS rows are channels (#230, #222): a history attribute (here a Subdivision modifier's levels and a Bevel's
width) can be selected in the Channel Box, changed by the MMB virtual slider and by dragging its value, keyed, and
reads its key state like Translate X; integer attributes step by whole numbers; every selected object with the same
history node changes too."""

from importlib import import_module

import bpy

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")


def _scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    obs = []
    for x in (0.0, 3.0):
        bpy.ops.mesh.primitive_cube_add(location=(x, 0.0, 0.0))
        ob = bpy.context.active_object
        ob.modifiers.new("subdiv", 'SUBSURF').levels = 1
        ob.modifiers.new("bevel", 'BEVEL').width = 0.1
        obs.append(ob)
    a, b = obs
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = a
    for mod in a.modifiers:        # INPUTS nodes start collapsed (Maya): open them so their rows exist
        cb.set_open(a, cb.mod_node(mod))
    cb.rebuild_rows()
    return a, b


def _row(kind, name):
    return next(r for r in bpy.context.scene.allset_cb.rows if r.kind == kind and r.name == name)


def test_inputs_rows_have_channel_keys():
    a, b = _scene()
    row = _row("INPUT", "levels")
    key = cb.row_key(row)
    assert cb.is_input_key(key), key
    assert cb.has_channel(a, key) and cb.has_channel(b, key)
    assert cb.get_value(a, key) == 1
    assert cb.channel_label(key) == a.modifiers["subdiv"].bl_rna.properties["levels"].name
    assert key in cb.drawn_keys(a)
    # selecting the row selects the channel
    row.sel = True
    assert cb.selected_channels() == [key] and row.sel
    # its value cell is a Channel Box cell (drag / click edit go through the kit, not Blender's text field)
    i = list(bpy.context.scene.allset_cb.rows).index(row)
    assert cb.cell_key(f"allset_cb.rows[{i}].text", bpy.context.scene) == (key, "VALUE")
    assert cb.field_owner(bpy.context, key) == (row, "text")
    cb.set_selected_channels([])


def test_virtual_slider_steps_integer_history_attributes_on_every_selected_object():
    a, b = _scene()
    key = cb.row_key(_row("INPUT", "levels"))
    cb.set_selected_channels([key])
    pairs = cb.slider_targets(bpy.context)
    assert (a, key) in pairs and (b, key) in pairs, pairs
    starts = {p: cb.get_value(*p) for p in pairs}
    cb.slider_apply(starts, 150)            # 150 px * 0.01 = 1.5 -> 2 levels more (whole numbers)
    assert a.modifiers["subdiv"].levels == 3 and b.modifiers["subdiv"].levels == 3
    cb.slider_apply(starts, 0)
    assert a.modifiers["subdiv"].levels == 1
    cb.set_selected_channels([])


def test_float_history_attribute_drag_and_slider():
    a, b = _scene()
    key = cb.row_key(_row("INPUT", "width"))
    starts = cb.field_drag_starts(bpy.context, key)
    assert (a, key) in starts, starts
    cb.set_selected_channels([key])
    cb.slider_apply({(a, key): 0.1}, 10)
    assert abs(a.modifiers["bevel"].width - 0.2) < 1e-6
    assert abs(b.modifiers["bevel"].width - 0.1) < 1e-6     # not in the starts given
    cb.set_selected_channels([])


def test_inputs_channel_keys_and_state():
    a, _b = _scene()
    key = cb.row_key(_row("INPUT", "width"))
    bpy.context.scene.frame_set(1)
    assert cb.channel_state(a, key) is None
    assert cb.keyframe(a, key)
    fc = cb.fcurve(a, key)
    assert fc is not None and fc.data_path == 'modifiers["bevel"].width', fc
    assert cb.channel_state(a, key) == 'KEYED'
    bpy.context.scene.frame_set(5)
    assert cb.channel_state(a, key) == 'ANIMATED'
    assert cb.remove_channel_curves(a, key) and cb.fcurve(a, key) is None
    bpy.context.scene.frame_set(1)


def test_a_typed_value_still_goes_to_every_selected_object():
    a, b = _scene()
    row = _row("INPUT", "levels")
    row.text = "2"
    assert a.modifiers["subdiv"].levels == 2 and b.modifiers["subdiv"].levels == 2


def test_creation_node_attributes_are_channels():
    """pCube1's polyCube1 in INPUTS: Subdivisions Height is selectable, the MMB slider / value drag steps it on every
    selected cube (whole numbers) and rebuilds the shapes."""
    ph = import_module(kit.MODULE + ".operators.prim_history")
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    cubes = []
    for _i in range(2):
        bpy.ops.allset.create(kind='CUBE')
        cubes.append(bpy.context.view_layer.objects.active)
    a, b = cubes
    for ob in cubes:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = a
    _owner, node = ph.node_of(a)
    assert node is not None
    key = cb.HISTORY_PREFIX + "subdivisionsHeight"
    assert key not in cb.drawn_keys(a)             # collapsed node: no rows
    cb.set_open(a, cb.history_node(node["name"]))
    assert key in cb.drawn_keys(a)
    assert cb.cell_key("allset_creation.subdivisionsHeight_text") == (key, "VALUE")
    assert cb.cell_key("allset_creation.subdivisionsHeight_sel") == (key, "NAME")
    assert cb.channel_label(key) == "Subdivisions Height"
    bpy.context.scene.allset_creation.subdivisionsHeight_sel = True
    assert cb.selected_channels() == [key]
    n0 = len(a.data.vertices)
    pairs = cb.slider_targets(bpy.context)
    assert (a, key) in pairs and (b, key) in pairs, pairs
    starts = {p: cb.get_value(*p) for p in pairs}
    cb.slider_apply(starts, 150)                   # 1 + 1.5 -> 3 (whole numbers)
    for ob in cubes:
        assert ph.attrs(ph.node_of(ob)[0])["subdivisionsHeight"] == 3, ph.attrs(ph.node_of(ob)[0])
    assert len(a.data.vertices) > n0
    assert cb.field_drag_starts(bpy.context, key)
    assert not cb.keyframe(a, key) and cb.channel_state(a, key) is None
    cb.set_selected_channels([])


def test_a_drag_stays_in_the_soft_range():
    """The MMB slider / value drag stop at the property's soft limit (Blender's UI does the same): Levels 6."""
    a, b = _scene()
    key = cb.row_key(_row("INPUT", "levels"))
    cb.slider_apply({(a, key): 1}, 5000)
    assert a.modifiers["subdiv"].levels == 6, a.modifiers["subdiv"].levels
    _row("INPUT", "levels").text = "8"           # typing may go further, up to the hard limit
    assert a.modifiers["subdiv"].levels == 8
    a.modifiers["subdiv"].levels = 1
    b.modifiers["subdiv"].levels = 1
