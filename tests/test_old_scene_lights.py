"""Scenes saved with older kit versions keep their lights as they were saved.

Older kit versions wrote a light's power from a Maya intensity, stored a Maya Decay Rate on the light data and, for
No Decay / Linear, put a "Maya Decay Rate" Light Falloff node into the light's node tree. The scene here is built
from plain Blender data in that layout, saved and opened again: every light keeps its power, its node tree and links
and its stored values, and showing it in the Attribute Editor and the Channel Box changes none of them."""

import os
import types
from importlib import import_module

import bpy

import kit

ae_nodes = import_module(kit.MODULE + ".ui.ae_nodes")
ae_rows = import_module(kit.MODULE + ".ui.ae_rows")
cb_inputs = import_module(kit.MODULE + ".ui.cb_inputs")

TMP = bpy.app.tempdir or os.environ.get("TEMP", ".")
PATH = os.path.join(TMP, "old_scene_lights.blend")


class Rec:
    def __init__(self, log=None):
        object.__setattr__(self, "log", [] if log is None else log)

    def __getattr__(self, name):
        def call(*args, **kw):
            self.log.append((name, args, kw))
            if name == "panel":
                return Rec(self.log), Rec(self.log)
            if name == "operator":
                return types.SimpleNamespace()
            return Rec(self.log)
        return call

    def __setattr__(self, name, value):
        pass


def _light(name, kind, energy, decay=None, falloff=None):
    data = bpy.data.lights.new(name + "Shape", kind)
    data.energy = energy
    if decay is not None:
        data["allset_decay_rate"] = decay
    if falloff is not None:
        if not data.node_tree:
            data.use_nodes = True
            data["allset_decay_nodes"] = True
        tree = data.node_tree
        emission = next(n for n in tree.nodes if n.type == 'EMISSION')
        node = tree.nodes.new('ShaderNodeLightFalloff')
        node.name = node.label = "Maya Decay Rate"
        node.inputs["Strength"].default_value = falloff[1]
        node.inputs["Smooth"].default_value = 0.0
        tree.links.new(node.outputs[falloff[0]], emission.inputs["Strength"])
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _signature(light):
    tree = light.node_tree
    nodes = links = ()
    if tree is not None:
        nodes = sorted((n.name, n.bl_idname, tuple((s.identifier, round(s.default_value, 6))
                                                     for s in n.inputs if isinstance(getattr(s, "default_value",
                                                                                             None), float)))
                       for n in tree.nodes)
        links = sorted((lk.from_node.name, lk.from_socket.identifier, lk.to_node.name, lk.to_socket.identifier)
                       for lk in tree.links)
    props = tuple(sorted((k, light[k]) for k in light.keys() if k.startswith("allset_")))
    return round(light.energy, 6), light.type, nodes, links, props


def _save_and_open():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for d in list(bpy.data.lights):
        bpy.data.lights.remove(d)
    _light("pointLight1", 'POINT', 39.478, decay=0, falloff=("Constant", 100.0))
    _light("spotLight1", 'SPOT', 3.9478, decay=1, falloff=("Linear", 10.0))
    _light("areaLight1", 'AREA', 0.0974, decay=0)
    _light("directionalLight1", 'SUN', 3.14159)
    before = {d.name: _signature(d) for d in bpy.data.lights}
    bpy.ops.wm.save_as_mainfile(filepath=PATH)
    bpy.ops.wm.open_mainfile(filepath=PATH)
    return before


def test_old_lights_open_unchanged():
    before = _save_and_open()
    assert {d.name: _signature(d) for d in bpy.data.lights} == before


def test_showing_old_lights_changes_nothing():
    before = _save_and_open()
    for ob in bpy.data.objects:
        for key in [t[0] for t in ae_nodes.tabs(ob)]:
            sections, layout_id = ae_nodes.sections_for(ob, key)
            if sections:
                ae_rows.draw_sections(Rec(), bpy.context, ob, ae_nodes.tab_target(ob, key), sections, layout_id)
        cb_inputs.wanted_rows(ob)
    bpy.context.view_layer.update()
    assert {d.name: _signature(d) for d in bpy.data.lights} == before
