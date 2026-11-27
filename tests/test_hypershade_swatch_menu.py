"""Hypershade Browser swatch RMB: Maya's swatch menu items on top of the button menu, in Maya's order, and what
each one does to the swatch's material."""

import types
from importlib import import_module

import bpy

import kit
from test_step67_render import Rec, _clear


def _sw():
    return import_module(kit.MODULE + ".ui.hypershade_swatch")


def _material(name):
    mat = bpy.data.materials.new(name)
    try:
        mat.use_nodes = True
    except AttributeError:
        pass
    return mat


def _cube(name, mat=None):
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    ob.name = name
    if mat is not None:
        ob.data.materials.append(mat)
    return ob


def _swatch_context(mat):
    prop = mat.bl_rna.properties["allset_hs_pick"]
    return types.SimpleNamespace(button_pointer=mat, button_prop=prop)


def test_menu_items_in_maya_order_only_on_a_swatch():
    _clear()
    mat = _material("blinn1")
    sw = _sw()
    rec = Rec()
    sw.draw_button_menu(types.SimpleNamespace(layout=rec), _swatch_context(mat))
    got = [(e[2]["text"], e[3].action, e[3].material) for e in rec.log if e[0] == "operator"]
    want = ["Assign Material To Viewport Selection", "Paint Assign Shader", "Select Objects with Material",
            "Refresh Swatch", "Graph Network", "Frame Objects with Material", "Select Input Nodes", "Rename", "Help"]
    assert [g[0] for g in got] == want, got
    assert all(g[2] == "blinn1" for g in got), got
    # another button (the material's name field) or no button: Blender's menu only
    for ctx in (types.SimpleNamespace(button_pointer=mat, button_prop=mat.bl_rna.properties["name"]),
                types.SimpleNamespace()):
        rec = Rec()
        sw.draw_button_menu(types.SimpleNamespace(layout=rec), ctx)
        assert not rec.log, rec.log


def test_assign_select_and_graph():
    _clear()
    mat = _material("lambert2")
    other = _material("other")
    a = _cube("a")
    b = _cube("b", other)
    c = _cube("c", mat)
    for ob in bpy.context.view_layer.objects:
        ob.select_set(ob in (a, b))
    bpy.context.view_layer.objects.active = a
    assert bpy.ops.allset.hs_swatch_cmd(material=mat.name, action='ASSIGN') == {'FINISHED'}
    assert a.active_material == mat and b.active_material == mat, (a.active_material, b.active_material)
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    assert bpy.ops.allset.hs_swatch_cmd(material=mat.name, action='SELECT_OBJECTS') == {'FINISHED'}
    assert {o.name for o in bpy.context.selected_objects} == {"a", "b", "c"}, bpy.context.selected_objects
    assert bpy.ops.allset.hs_swatch_cmd(material=other.name, action='SELECT_OBJECTS') == {'FINISHED'}
    assert not bpy.context.selected_objects       # b now uses mat
    assert bpy.ops.allset.hs_swatch_cmd(material=mat.name, action='GRAPH') == {'FINISHED'}
    assert bpy.context.window_manager.allset_hs_material == mat.name
    assert bpy.ops.allset.hs_swatch_cmd(material=mat.name, action='SELECT_INPUTS') == {'FINISHED'}
    chosen = {n.type for n in mat.node_tree.nodes if n.select}
    assert chosen == {'BSDF_PRINCIPLED'}, chosen
    assert bpy.ops.allset.hs_swatch_cmd(material=mat.name, action='PAINT') == {'CANCELLED'}
    assert bpy.ops.allset.hs_swatch_cmd(material=mat.name, action='REFRESH') == {'FINISHED'}
    assert c.active_material == mat
