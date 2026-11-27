"""Shader graph middle-mouse drop (Maya): the dragged node's default output goes to the chosen input of the node it is
dropped on; Ctrl = the default connection (first free input of the output's kind); the keys sit on the Node Editor
keymap ahead of Blender's pan and pass through off a node."""

from importlib import import_module

import bpy

import kit


def _hc():
    return import_module(kit.MODULE + ".ui.hypershade_connect")


def _tree():
    mat = bpy.data.materials.new("conn")
    try:
        mat.use_nodes = True
    except AttributeError:
        pass
    tree = mat.node_tree
    shader = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    return tree, shader


def test_default_output_and_list():
    hc = _hc()
    tree, shader = _tree()
    tex = tree.nodes.new("ShaderNodeTexChecker")
    assert hc.default_output(tex).identifier == "Color"
    names = [s.name for s in hc.inputs_of(shader)]
    assert names[:3] == ["Base Color", "Metallic", "Roughness"], names[:3]
    assert all(s.enabled for s in hc.inputs_of(shader))


def test_connect_chosen_input_and_default():
    hc = _hc()
    tree, shader = _tree()
    tex = tree.nodes.new("ShaderNodeTexChecker")
    link = hc.connect(tree, tex, shader, shader.inputs["Roughness"].identifier)
    assert link is not None and link.from_socket == tex.outputs["Color"] and link.to_socket == shader.inputs["Roughness"]
    assert hc.connect(tree, tex, tex, "Vector") is None          # onto itself: nothing
    # Ctrl drop: the first free colour input (Base Color), then the next free colour input
    first = hc.default_input(shader, hc.default_output(tex))
    assert first == shader.inputs["Base Color"], first.name
    tree.links.new(tex.outputs["Color"], first)
    second = hc.default_input(shader, hc.default_output(tex))
    assert second.type == 'RGBA' and second != first and not second.is_linked, second.name
    # a value output onto a node without value inputs of its kind: the first free input
    val = tree.nodes.new("ShaderNodeValue")
    mix = tree.nodes.new("ShaderNodeMixShader")
    assert hc.default_input(mix, hc.default_output(val)) == mix.inputs[0]


def test_keys_on_the_node_editor_first():
    mp = import_module(kit.MODULE + ".keymap.maya_patches")
    assert "allset.hs_mmb_drag" in mp.PASS_THROUGH_FIRST
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.get("Node Editor")
    assert km is not None
    found = {(k.type, k.ctrl) for k in km.keymap_items if k.idname == "allset.hs_mmb_drag"}
    assert found == {('MIDDLEMOUSE', False), ('MIDDLEMOUSE', True)}, found
