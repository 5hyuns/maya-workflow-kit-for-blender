"""Scenes saved with older kit versions keep their materials as they were saved.

Older kit versions wrote materials the scene still carries: lambert1 (marked as the kit's default material, with a
"Maya Diffuse" Mix node in front of Base Color), Maya-named kit materials (blinn1 ...), and Ramp / Layered / Use
Background set-ups built from extra nodes around the Principled BSDF. The scene here is built from plain Blender data
in that layout, saved and opened again: every material keeps its name, nodes, links and values, the objects keep
their slots and per-face materials, the Attribute Editor and the Hypershade Browser show them, and only Convert Old
Kit Materials changes anything (the Maya Diffuse node; the Ramp and Layered nodes stay)."""

import os
import types
from importlib import import_module

import bmesh
import bpy

import kit

material = import_module(kit.MODULE + ".operators.material")
ae_nodes = import_module(kit.MODULE + ".ui.ae_nodes")
ae_rows = import_module(kit.MODULE + ".ui.ae_rows")
hs_materials = import_module(kit.MODULE + ".ui.hypershade_materials")

TMP = bpy.app.tempdir or os.environ.get("TEMP", ".")
PATH = os.path.join(TMP, "old_scene_materials.blend")
NAMES = ("lambert1", "blinn1", "rampShader1", "layeredShader1", "useBackground1")


class Rec:
    """Records every layout call."""

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


def _sock(node, ident):
    return next(s for s in node.inputs if s.identifier == ident)


def _mat(name, maya_type):
    mat = bpy.data.materials.new(name)
    mat["allset_type"] = maya_type
    if not mat.node_tree:
        mat.use_nodes = True
    return mat, next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def _old_scene():
    """The materials and objects of an older kit scene, from plain bpy data."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)

    lam, bsdf = _mat("lambert1", "lambert")
    lam["allset_default"] = True
    lam.use_fake_user = True
    tree = lam.node_tree
    mix = tree.nodes.new('ShaderNodeMix')
    mix.name = mix.label = "Maya Diffuse"
    mix.data_type, mix.blend_type, mix.clamp_result = 'RGBA', 'MIX', False
    _sock(mix, "A_Color").default_value = (0.0, 0.0, 0.0, 1.0)
    _sock(mix, "B_Color").default_value = (0.5, 0.5, 0.5, 1.0)
    _sock(mix, "Factor_Float").default_value = 0.8
    tree.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)

    blinn, bsdf = _mat("blinn1", "blinn")
    bsdf.inputs["Base Color"].default_value = (0.2, 0.4, 0.6, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.3

    ramp, bsdf = _mat("rampShader1", "rampShader")
    bsdf.inputs["Emission Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    facing = ramp.node_tree.nodes.new('ShaderNodeLayerWeight')
    cramp = ramp.node_tree.nodes.new('ShaderNodeValToRGB')
    for el in cramp.color_ramp.elements:
        el.color = (0.5, 0.5, 0.5, 1.0)
    ramp.node_tree.links.new(facing.outputs["Facing"], cramp.inputs["Fac"])
    ramp.node_tree.links.new(cramp.outputs["Color"], bsdf.inputs["Base Color"])

    layered, bsdf = _mat("layeredShader1", "layeredShader")
    nodes, links = layered.node_tree.nodes, layered.node_tree.links
    out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
    second = nodes.new('ShaderNodeBsdfPrincipled')
    mixs = nodes.new('ShaderNodeMixShader')
    mixs.inputs["Fac"].default_value = 0.0
    links.new(bsdf.outputs["BSDF"], mixs.inputs[1])
    links.new(second.outputs["BSDF"], mixs.inputs[2])
    links.new(mixs.outputs["Shader"], out.inputs["Surface"])

    bg, bsdf = _mat("useBackground1", "useBackground")
    out = next(n for n in bg.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
    hold = bg.node_tree.nodes.new('ShaderNodeHoldout')
    bg.node_tree.links.new(hold.outputs["Holdout"], out.inputs["Surface"])

    # pCube1: lambert1 on most faces, blinn1 on the top face; the others one material each
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = "pCube1"
    cube.data.materials.clear()
    cube.data.materials.append(lam)
    cube.data.materials.append(blinn)
    top = max(cube.data.polygons, key=lambda p: p.center.z).index
    cube.data.polygons[top].material_index = 1
    for name, mat in (("pSphere1", ramp), ("pCylinder1", layered), ("pPlane1", bg)):
        bpy.ops.mesh.primitive_uv_sphere_add() if name == "pSphere1" else \
            bpy.ops.mesh.primitive_cylinder_add() if name == "pCylinder1" else bpy.ops.mesh.primitive_plane_add()
        ob = bpy.context.active_object
        ob.name = name
        ob.data.materials.clear()
        ob.data.materials.append(mat)
    return top


def _value(sock):
    v = getattr(sock, "default_value", None)
    return tuple(round(x, 6) for x in v) if hasattr(v, "__len__") else (None if v is None else round(v, 6))


def _signature(mat):
    """Everything about a material that decides its render: custom props, nodes, input values, links."""
    tree = mat.node_tree
    nodes = sorted((n.name, n.bl_idname, tuple((s.identifier, _value(s)) for s in n.inputs)) for n in tree.nodes)
    links = sorted((lk.from_node.name, lk.from_socket.identifier, lk.to_node.name, lk.to_socket.identifier)
                   for lk in tree.links)
    ramps = sorted((n.name, tuple((round(e.position, 6), tuple(round(c, 6) for c in e.color))
                                  for e in n.color_ramp.elements))
                   for n in tree.nodes if n.type == 'VALTORGB')
    props = (mat.get("allset_type"), bool(mat.get("allset_default")), mat.use_fake_user)
    return props, nodes, links, ramps


def _faces(ob):
    return [p.material_index for p in ob.data.polygons], [s.material.name if s.material else None
                                                        for s in ob.material_slots]


def _save_and_open():
    top = _old_scene()
    before = {name: _signature(bpy.data.materials[name]) for name in NAMES}
    obs = {ob.name: _faces(ob) for ob in bpy.data.objects}
    bpy.ops.wm.save_as_mainfile(filepath=PATH)
    bpy.ops.wm.open_mainfile(filepath=PATH)
    return top, before, obs


def test_old_scene_opens_unchanged():
    _top, before, obs = _save_and_open()
    for name in NAMES:
        mat = bpy.data.materials.get(name)
        assert mat is not None, f"{name} kept its name"
        assert _signature(mat) == before[name], name
    assert {ob.name: _faces(ob) for ob in bpy.data.objects} == obs, "slots and per-face materials as saved"
    # what renders: the Surface output of each material
    def surface(name):
        out = next(n for n in bpy.data.materials[name].node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
        return out.inputs["Surface"].links[0].from_node.type
    assert surface("layeredShader1") == 'MIX_SHADER' and surface("useBackground1") == 'HOLDOUT'
    assert surface("lambert1") == surface("blinn1") == surface("rampShader1") == 'BSDF_PRINCIPLED'


def test_old_scene_shows_in_attribute_editor_and_hypershade():
    _save_and_open()
    for ob in bpy.data.objects:
        keys = [t[0] for t in ae_nodes.tabs(ob)]
        mats = [k for k in keys if k.startswith("MAT:")]
        assert len(mats) == len(ob.material_slots), (ob.name, keys)
        for key in mats:
            sections, layout_id = ae_nodes.sections_for(ob, key)
            assert sections, (ob.name, key)
            rec = Rec()
            ae_rows.draw_sections(rec, bpy.context, ob, ae_nodes.tab_target(ob, key), sections, layout_id)
            assert rec.log, (ob.name, key)
    listed = {item[0] for item in hs_materials.browser_items(bpy.context, 'MATERIALS')}
    assert set(NAMES) <= listed, listed


def test_convert_old_touches_only_the_diffuse_node():
    _save_and_open()
    before = {name: _signature(bpy.data.materials[name]) for name in NAMES}
    assert bpy.ops.allset.convert_old_materials() == {'FINISHED'}
    lam = bpy.data.materials["lambert1"]
    assert not [n for n in lam.node_tree.nodes if n.name == "Maya Diffuse"], "lambert1 is plain Principled now"
    base = next(n for n in lam.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs["Base Color"]
    assert not base.is_linked and all(abs(a - b) < 1e-5 for a, b in zip(base.default_value, (0.4, 0.4, 0.4, 1)))
    for name in NAMES[1:]:
        assert _signature(bpy.data.materials[name]) == before[name], f"{name} left as it was"


def test_old_scene_partial_faces_keep_their_material():
    top, _before, _obs = _save_and_open()
    cube = bpy.data.objects["pCube1"]
    bpy.context.view_layer.objects.active = cube
    for ob in bpy.data.objects:
        ob.select_set(ob == cube)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(cube.data)
    bm.faces.ensure_lookup_table()
    pick = next(f.index for f in bm.faces if f.index != top)
    for f in bm.faces:
        f.select = f.index == pick
    bmesh.update_edit_mesh(cube.data)
    blinn = bpy.data.materials["blinn1"]
    material.assign(bpy.context, blinn, [cube])
    bpy.ops.object.mode_set(mode='OBJECT')
    idx, slots = _faces(cube)
    assert slots == ["lambert1", "blinn1"], slots
    assert idx[top] == 1 and idx[pick] == 1, idx
    assert all(i == 0 for n, i in enumerate(idx) if n not in (pick, top)), "the other faces keep lambert1"
