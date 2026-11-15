"""Opaque depth repair must not turn transparent or displaced materials into occluders."""
from importlib import import_module
import bpy
import kit

grid = import_module(kit.MODULE + '.ui.maya_grid')
compat = import_module(kit.MODULE + '.compat')


def test_opaque_material_boundaries():
    material = bpy.data.materials.new('grid_depth_test')
    try:
        assert grid.opaque_material(None)
        compat.ensure_material_nodes(material)
        nodes = material.node_tree.nodes
        bsdf = nodes.get('Principled BSDF')
        output = nodes.get('Material Output')
        assert grid.opaque_material(material)
        bsdf.inputs['Alpha'].default_value = 0.5
        assert not grid.opaque_material(material)
        bsdf.inputs['Alpha'].default_value = 1.0
        bsdf.inputs['Transmission Weight'].default_value = 1.0
        assert not grid.opaque_material(material)
        bsdf.inputs['Transmission Weight'].default_value = 0.0
        value = nodes.new('ShaderNodeValue')
        value.outputs[0].default_value = 1.0
        link = material.node_tree.links.new(value.outputs[0], bsdf.inputs['Alpha'])
        assert not grid.opaque_material(material)
        material.node_tree.links.remove(link)
        material.use_backface_culling = True
        assert not grid.opaque_material(material)
        material.use_backface_culling = False
        link = material.node_tree.links.new(value.outputs[0], output.inputs['Displacement'])
        assert not grid.opaque_material(material)
        material.node_tree.links.remove(link)
        assert grid.opaque_material(material)
        transparent = nodes.new('ShaderNodeBsdfTransparent')
        material.node_tree.links.new(transparent.outputs[0], output.inputs['Surface'])
        assert not grid.opaque_material(material)
    finally:
        bpy.data.materials.remove(material)


def test_on_by_default():
    """Like Maya, the grid stays behind meshes in shaded views: the pass is on after install and can be turned off."""
    prefs = import_module(kit.MODULE + '.preferences').get()
    assert prefs.grid_depth_pass is True and grid.depth_pass_on()
    try:
        prefs.grid_depth_pass = False
        assert not grid.depth_pass_on()
    finally:
        prefs.grid_depth_pass = True


def test_cache_invalidates_on_scene_changes():
    for event, fn in (('depsgraph_update_post', grid._depth_on_depsgraph), ('frame_change_post', grid._depth_on_frame),
                      ('load_post', grid._clear_depth), ('undo_post', grid._clear_depth),
                      ('redo_post', grid._clear_depth)):
        assert fn in getattr(bpy.app.handlers, event), event
    grid._depth_batches['stale'] = (0, None, False)
    grid._clear_depth(bpy.context.scene)
    assert not grid._depth_batches


def test_cache_keeps_what_did_not_change():
    """A move keeps an object's batch (drawn with the live matrix); a geometry edit drops it; a frame change drops
    only the batches of objects whose geometry can change with time."""
    mesh = bpy.data.meshes.new('depth_cache')
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    ob = bpy.data.objects.new('depth_cache', mesh)
    bpy.context.scene.collection.objects.link(ob)
    try:
        bpy.context.view_layer.update()
        uid = ob.session_uid
        grid._depth_batches.clear()
        grid._depth_batches[uid] = (1, None, False)
        grid._depth_batches[-1] = (1, None, True)              # a deforming object's batch
        ob.location.x += 1.0
        bpy.context.view_layer.update()
        assert uid in grid._depth_batches, "a move keeps the batch"
        grid._depth_on_frame(bpy.context.scene)
        assert uid in grid._depth_batches and -1 not in grid._depth_batches, "a frame change drops the timed one"
        mesh.vertices[0].co.x = 0.5
        mesh.update()
        bpy.context.view_layer.update()
        assert uid not in grid._depth_batches, "a geometry edit drops it"
    finally:
        grid._depth_batches.clear()
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(mesh)
