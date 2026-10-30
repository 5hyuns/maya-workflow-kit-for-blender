"""Skin Tools (#127): skin weight layers on a kit skin — Initialize, the layer list, Set Weights, mask, Mirror,
Assign from Closest Joint, painting a layer through the working groups, save / load, undo, and Skin > Paint Skin
Weights opening Skin Tools once the skin has layers.
Kit: operators/skin_layers.py, ui/skin_tools.py."""

import os
import tempfile
from importlib import import_module

import bpy
import numpy as np
from mathutils import Vector

import kit

layers = import_module(kit.MODULE + ".operators.skin_layers")
skin_tools = import_module(kit.MODULE + ".ui.skin_tools")
marked_window = import_module(kit.MODULE + ".ui.marked_window")

NAMES = ["root", "armL", "armR"]
XS = (-2.0, -1.0, 0.0, 1.0, 2.0)


def _reset():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.armatures):
        for d in list(coll):
            coll.remove(d)


def _scene():
    """A strip along X (two rows of five vertices) skinned to root (centre), armL (+X), armR (-X)."""
    _reset()
    arm = bpy.data.armatures.new("skeleton1")
    rig = bpy.data.objects.new("skeleton1", arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    root = arm.edit_bones.new("root")
    root.head, root.tail = (0, 0, 0), (0, 0, 1)
    for name, sx in (("armL", 1), ("armR", -1)):
        b = arm.edit_bones.new(name)
        b.head, b.tail = (sx, 0, 0), (2 * sx, 0, 0)
        b.parent = root
    bpy.ops.object.mode_set(mode='OBJECT')
    me = bpy.data.meshes.new("body")
    verts = [(x, y, 0.0) for y in (0.0, 0.5) for x in XS]
    faces = [(i, i + 1, i + 6, i + 5) for i in range(4)]
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new("body", me)
    bpy.context.scene.collection.objects.link(ob)
    md = ob.modifiers.new("skinCluster1", 'ARMATURE')
    md.object = rig
    for n in NAMES:
        ob.vertex_groups.new(name=n)
    for i, (x, _y, _z) in enumerate(verts):
        name = "root" if x == 0 else ("armL" if x > 0 else "armR")
        ob.vertex_groups[name].add([i], 1.0, 'REPLACE')
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    return ob


def _groups(ob):
    return layers.read_groups(ob, layers.influence_names(ob))


def test_initialize_makes_a_base_layer_from_the_current_weights():
    ob = _scene()
    before = _groups(ob)
    assert not layers.is_initialized(ob)
    assert bpy.ops.allset.skin_layers_init() == {'FINISHED'}
    st = layers.state(ob)
    assert layers.is_initialized(ob) and len(st.layers) == 1
    assert st.layers[0].name == layers.BASE_NAME
    assert layers.influence_names(ob) == NAMES          # skeleton order
    assert np.allclose(layers.layer_matrix(ob, st.layers[0], NAMES), before)
    assert layers.recomposite(ob)
    assert np.allclose(_groups(ob), before)


def test_layer_list_add_duplicate_move_remove():
    ob = _scene()
    bpy.ops.allset.skin_layers_init()
    st = layers.state(ob)
    bpy.ops.allset.skin_layer_add()
    assert [lay.name for lay in st.layers] == ["Layer", layers.BASE_NAME] and st.active_index == 0
    bpy.ops.allset.skin_layer_add()
    assert [lay.name for lay in st.layers] == ["Layer 1", "Layer", layers.BASE_NAME]
    st.active_index = 2
    bpy.ops.allset.skin_layer_add(duplicate=True)          # a copy of the base above it
    assert [lay.name for lay in st.layers] == ["Layer 1", "Layer", "Base Weights 1", layers.BASE_NAME]
    assert np.allclose(layers.layer_matrix(ob, st.layers[2], NAMES), layers.layer_matrix(ob, st.layers[3], NAMES))
    bpy.ops.allset.skin_layer_move(direction="UP")
    assert st.layers[1].name == "Base Weights 1" and st.active_index == 1
    # the weights travel with the moved item
    assert np.allclose(layers.layer_matrix(ob, st.layers[1], NAMES), layers.layer_matrix(ob, st.layers[3], NAMES))
    bpy.ops.allset.skin_layer_remove()
    assert len(st.layers) == 3 and "Base Weights 1" not in [lay.name for lay in st.layers]
    while len(st.layers) > 1:
        bpy.ops.allset.skin_layer_remove()
    assert bpy.ops.allset.skin_layer_remove() == {'CANCELLED'}       # the last layer stays
    bpy.ops.allset.skin_layers_delete()
    assert not layers.is_initialized(ob)


def test_set_weights_on_a_layer_composites_by_opacity_and_mask():
    ob = _scene()
    bpy.ops.allset.skin_layers_init()
    st = layers.state(ob)
    bpy.ops.allset.skin_layer_add()
    wm = bpy.context.window_manager
    wm.allset_st_mode, wm.allset_st_intensity = "REPLACE", 1.0
    bpy.ops.allset.skin_tools_pick(name="armL")
    assert bpy.ops.allset.skin_tools_set_weights() == {'FINISHED'}      # object mode: every vertex
    assert np.allclose(_groups(ob)[:, 1], 1.0)                           # the top layer covers everything
    st.layers[0].opacity = 0.25
    g = _groups(ob)
    assert np.allclose(g[0], [0.0, 0.25, 0.75])                          # x = -2: armR 1 below
    assert np.allclose(g[2], [0.75, 0.25, 0.0])
    st.layers[0].enabled = False
    assert np.allclose(_groups(ob)[0], [0.0, 0.0, 1.0])
    st.layers[0].enabled = True
    st.layers[0].opacity = 1.0
    # mask: only vertices 3, 4, 8, 9 (x > 0) — selected in Edit mode
    bpy.ops.allset.skin_tools_pick(mask=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for i in (3, 4, 8, 9):
        ob.data.vertices[i].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    wm.allset_st_intensity = 1.0
    assert bpy.ops.allset.skin_tools_set_weights() == {'FINISHED'}
    assert ob.mode == 'EDIT'
    bpy.ops.object.mode_set(mode='OBJECT')
    mask = layers.layer_mask(ob, st.layers[0])
    assert np.allclose(mask, [0, 0, 0, 1, 1, 0, 0, 0, 1, 1])
    g = _groups(ob)
    assert np.allclose(g[0], [0, 0, 1]) and np.allclose(g[2], [1, 0, 0]) and np.allclose(g[3], [0, 1, 0])
    # Smooth on the mask spreads it to the neighbours
    wm.allset_st_mode, wm.allset_st_intensity, wm.allset_st_iterations = "SMOOTH", 0.5, 1
    for v in ob.data.vertices:
        v.select = False
    bpy.ops.allset.skin_tools_set_weights()
    assert 0.0 < layers.layer_mask(ob, st.layers[0])[2] < 1.0


def test_mirror_layer_pairs_joints_and_vertices():
    ob = _scene()
    bpy.ops.allset.skin_layers_init()
    st = layers.state(ob)
    bpy.ops.allset.skin_layer_add()
    lay = st.layers[0]
    w = np.zeros((10, 3))
    w[4, 1] = 1.0                     # x = 2 -> armL
    w[3, 0], w[3, 1] = 0.5, 0.5       # x = 1 -> half root, half armL
    layers.set_layer_matrix(lay, NAMES, w)
    layers.set_layer_mask(lay, [0, 0, 0, 0.5, 1, 0, 0, 0, 0, 0])
    wm = bpy.context.window_manager
    wm.allset_st_axis, wm.allset_st_positive = "X", True
    assert bpy.ops.allset.skin_tools_mirror() == {'FINISHED'}
    out = layers.layer_matrix(ob, lay, NAMES)
    assert np.allclose(out[0], [0, 0, 1]) and np.allclose(out[1], [0.5, 0, 0.5])
    assert np.allclose(out[4], [0, 1, 0])                                 # source side kept
    mask = layers.layer_mask(ob, lay)
    assert np.allclose(mask[:5], [1, 0.5, 0, 0.5, 1])


def test_assign_from_closest_joint():
    ob = _scene()
    bpy.ops.allset.skin_layers_init()
    bpy.ops.allset.skin_layer_add()
    bpy.ops.allset.skin_tools_assign_closest()
    st = layers.state(ob)
    w = layers.layer_matrix(ob, st.layers[0], NAMES)
    assert np.allclose(w.sum(axis=1), 1.0)
    assert w[2, 0] == 1.0                     # on the root
    layers.assign_closest(ob, picked=["armL", "armR"])
    w = layers.layer_matrix(ob, st.layers[0], NAMES)
    assert w[4, 1] == 1.0 and w[0, 2] == 1.0 and w[2].sum() == 1.0


def test_paint_session_reads_working_groups_back():
    ob = _scene()
    bpy.ops.allset.skin_layers_init()
    st = layers.state(ob)
    bpy.ops.allset.skin_layer_add()
    bpy.ops.allset.skin_tools_pick(name="armL")
    assert bpy.ops.allset.skin_tools_paint() == {'FINISHED'}
    assert ob.mode == 'WEIGHT_PAINT' and layers.painting(ob)
    names = [vg.name for vg in ob.vertex_groups]
    assert layers.WORK + "armL" in names and layers.WORK_MASK in names
    assert ob.vertex_groups.active.name == layers.WORK + "armL"
    # a "stroke": vertex 0 painted 1.0 on the layer's armL
    ob.vertex_groups[layers.WORK + "armL"].add([0], 1.0, 'REPLACE')
    assert layers.sync(ob)
    assert np.allclose(layers.layer_matrix(ob, st.layers[0], NAMES)[0], [0, 1, 0])
    assert np.allclose(_groups(ob)[0], [0, 1, 0])
    # picking a joint's own group (Ctrl+click on the joint) switches to its working group
    ob.vertex_groups.active_index = ob.vertex_groups["armR"].index
    layers.follow_pick(ob)
    assert st.influence == "armR" and ob.vertex_groups.active.name == layers.WORK + "armR"
    # painting armR 0.5 on vertex 0: armL makes room
    ob.vertex_groups[layers.WORK + "armR"].add([0], 0.5, 'REPLACE')
    layers.sync(ob)
    assert np.allclose(layers.layer_matrix(ob, st.layers[0], NAMES)[0], [0, 0.5, 0.5])
    assert np.allclose(layers.read_groups(ob, [layers.WORK + "armL"])[0, 0], 0.5)
    # leaving weight paint ends the session: working groups go
    bpy.ops.object.mode_set(mode='OBJECT')
    layers._tick()
    assert not layers.painting()
    assert not any(vg.name.startswith(layers.WORK) for vg in ob.vertex_groups)
    assert np.allclose(_groups(ob)[0], [0, 0.5, 0.5])


def test_layers_survive_save_and_load():
    ob = _scene()
    bpy.ops.allset.skin_layers_init()
    bpy.ops.allset.skin_layer_add()
    st = layers.state(ob)
    st.layers[0].name = "L_Arm"
    st.layers[0].opacity = 0.5
    wm = bpy.context.window_manager
    wm.allset_st_mode, wm.allset_st_intensity = "REPLACE", 1.0
    bpy.ops.allset.skin_tools_pick(name="armL")
    bpy.ops.allset.skin_tools_set_weights()
    layers.set_layer_mask(st.layers[0], [1.0] * 5 + [0.0] * 5)
    layers.recomposite(ob)
    before = _groups(ob)
    path = os.path.join(tempfile.mkdtemp(), "skin_layers.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    bpy.ops.wm.open_mainfile(filepath=path)
    ob = bpy.data.objects["body"]
    st = layers.state(ob)
    assert [lay.name for lay in st.layers] == ["L_Arm", layers.BASE_NAME]
    assert abs(st.layers[0].opacity - 0.5) < 1e-6
    assert np.allclose(layers.layer_mask(ob, st.layers[0]), [1.0] * 5 + [0.0] * 5)
    assert np.allclose(layers.layer_matrix(ob, st.layers[0], NAMES)[:, 1], 1.0)
    assert np.allclose(_groups(ob), before)


def test_undo_restores_the_layer_and_the_skin():
    ob = _scene()
    bpy.ops.ed.undo_push(message="test start")
    bpy.ops.allset.skin_layers_init('EXEC_DEFAULT', True)
    bpy.ops.allset.skin_layer_add('EXEC_DEFAULT', True)
    bpy.ops.allset.skin_tools_pick('EXEC_DEFAULT', True, name="armL")
    wm = bpy.context.window_manager
    wm.allset_st_mode, wm.allset_st_intensity = "REPLACE", 1.0
    before = _groups(bpy.data.objects["body"])
    bpy.ops.allset.skin_tools_set_weights('EXEC_DEFAULT', True)
    ob = bpy.data.objects["body"]
    assert np.allclose(_groups(ob)[:, 1], 1.0)
    bpy.ops.ed.undo()
    ob = bpy.data.objects["body"]
    st = layers.state(ob)
    assert len(st.layers) == 2
    assert not np.any(layers.layer_matrix(ob, st.layers[0], NAMES))
    assert np.allclose(_groups(ob), before)
    bpy.ops.ed.undo()
    bpy.ops.ed.undo()
    bpy.ops.ed.undo()
    ob = bpy.data.objects["body"]
    assert not layers.is_initialized(ob)


def test_paint_skin_weights_opens_skin_tools_once_initialized():
    ob = _scene()
    # without layers: the classic tool (paint mode)
    try:
        bpy.ops.allset.paint_skin_weights()
    except RuntimeError:
        pass                                        # background: no tool system for the brush tool
    assert ob.mode == 'WEIGHT_PAINT'
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.allset.skin_layers_init()
    bpy.ops.allset.paint_skin_weights()             # Skin Tools (no window in background): stays in object mode
    assert ob.mode == 'OBJECT'
    pairs = [frozenset(v) for v in marked_window.KINDS.values()]
    assert len(pairs) == len(set(pairs))                  # the window's mark is its own


def test_topology_change_is_refused():
    ob = _scene()
    bpy.ops.allset.skin_layers_init()
    ob.data.vertices.add(1)
    assert not layers.recomposite(ob)
    assert bpy.ops.allset.skin_layer_add() == {'CANCELLED'}
