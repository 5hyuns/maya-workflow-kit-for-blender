"""Opaque depth repair must not turn transparent or displaced materials into occluders."""
from importlib import import_module
import bpy
import kit

grid = import_module(kit.MODULE + '.ui.maya_grid')


def test_opaque_material_boundaries():
    material = bpy.data.materials.new('grid_depth_test')
    try:
        assert grid.opaque_material(None)
        material.use_nodes = True
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


def test_cache_invalidates_on_scene_changes():
    for event in ('depsgraph_update_post', 'frame_change_post', 'load_post', 'undo_post', 'redo_post'):
        assert grid._clear_depth in getattr(bpy.app.handlers, event), event
    grid._depth_batches['stale'] = None
    grid._clear_depth(bpy.context.scene)
    assert not grid._depth_batches
