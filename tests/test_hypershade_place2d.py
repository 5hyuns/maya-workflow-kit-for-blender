"""Map button File / Checker: the texture gets a place2dTexture in front (UV coordinates -> Mapping node), whose
Scale repeats the texture like Maya's Repeat UV and Location moves it like Offset; the new texture node is the one
the Hypershade Property Editor shows (Maya goes to the new file node)."""

from importlib import import_module

import bpy

import kit
from test_step67_render import _clear


def _material(name):
    mat = bpy.data.materials.new(name)
    try:
        mat.use_nodes = True
    except AttributeError:
        pass
    return mat


def _feeds(node, socket):
    link = node.inputs[socket].links[0] if node.inputs[socket].is_linked else None
    return link.from_node if link else None


def test_file_and_checker_get_a_place2d():
    _clear()
    for kind in ('FILE', 'CHECKER'):
        mat = _material(f"m_{kind}")
        assert bpy.ops.allset.ae_map_connect(material=mat.name, socket="Base Color", kind=kind) == {'FINISHED'}
        tex = next(n for n in mat.node_tree.nodes if n.type in ('TEX_IMAGE', 'TEX_CHECKER'))
        place = _feeds(tex, "Vector")
        assert place is not None and place.type == 'MAPPING' and place.label == "place2dTexture", (kind, place)
        assert place.vector_type == 'POINT'
        coord = _feeds(place, "Vector")
        assert coord is not None and coord.type == 'TEX_COORD', coord
        assert place.inputs["Vector"].links[0].from_socket.name == "UV"
        panes = import_module(kit.MODULE + ".ui.hypershade_panes")
        assert panes.shown_node(mat) == tex, (kind, mat.node_tree.nodes.active)



def test_connected_map_button_goes_to_the_node():
    """The map button's list on a connected attribute starts with the connected node; it selects that node, which
    the Hypershade Property Editor then shows."""
    _clear()
    mat = _material("goto")
    bpy.ops.allset.ae_map_connect(material=mat.name, socket="Roughness", kind='NOISE')
    tree = mat.node_tree
    noise = next(n for n in tree.nodes if n.type == 'TEX_NOISE')
    shader = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for n in tree.nodes:
        n.select = n == shader
    tree.nodes.active = shader
    assert bpy.ops.allset.ae_map_goto(material=mat.name, socket="Roughness") == {'FINISHED'}
    assert tree.nodes.active == noise and [n for n in tree.nodes if n.select] == [noise]
    panes = import_module(kit.MODULE + ".ui.hypershade_panes")
    assert panes.shown_node(mat) == noise
    assert bpy.ops.allset.ae_map_goto(material=mat.name, socket="Metallic") == {'CANCELLED'}
