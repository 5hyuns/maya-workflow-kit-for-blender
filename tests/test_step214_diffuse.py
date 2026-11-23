"""Kit materials are plain Principled BSDF materials; older kit materials with a "Maya Diffuse" node keep working.

A new material is Blender's Principled BSDF with Blender's own values and Blender's name. Materials saved by older kit versions have a Mix node ("Maya Diffuse": factor = diffuse,
A = black, B = the colour or texture) in front of Base Color: they render as saved, their Color / Diffuse rows edit
that node, File > Export links the colour straight to Base Color while it writes, and Lighting/Shading > Convert Old
Kit Materials turns them into plain Principled materials once."""

import os
import types
from importlib import import_module

import bpy

import kit

material = import_module(kit.MODULE + ".operators.material")
maps = import_module(kit.MODULE + ".operators.shading_maps")
ae_layout = import_module(kit.MODULE + ".ui.ae_layout")
ae = import_module(kit.MODULE + ".ui.attribute_editor")
menu_items = import_module(kit.MODULE + ".operators.menu_items")
menu_map = import_module(kit.MODULE + ".ui.menu_map")

OLD_TYPES = {'LAMBERT': "lambert", 'BLINN': "blinn", 'PHONG': "phong"}


class Rec:
    """Records every layout call (as in tests/test_step67_render.py)."""

    def __init__(self, log=None):
        object.__setattr__(self, "log", [] if log is None else log)

    def __getattr__(self, name):
        def call(*args, **kw):
            self.log.append((name, args, kw))
            if name == "panel":
                return Rec(self.log), Rec(self.log)
            if name == "operator":
                props = types.SimpleNamespace()
                self.log[-1] = (name, args, kw, props)
                return props
            return Rec(self.log)
        return call

    def __setattr__(self, name, value):
        pass


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


def _bsdf(mat):
    return next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def _close(a, b, eps=1e-5):
    a = a if hasattr(a, "__len__") else (a,)
    b = b if hasattr(b, "__len__") else (b,)
    return all(abs(x - y) < eps for x, y in zip(a, b))


def _sock(node, ident):
    return next(s for s in node.inputs if s.identifier == ident)


def _values(bsdf):
    return {s.identifier: (tuple(s.default_value) if hasattr(s.default_value, "__len__") else s.default_value)
            for s in bsdf.inputs if hasattr(s, "default_value") and s.enabled}


def _old(kind='LAMBERT', colour=(0.5, 0.5, 0.5, 1.0), diffuse=0.8):
    """A material as an older kit version saved it: the Maya Diffuse node in front of Base Color."""
    mat = material.new_material()
    mat[material.TYPE_PROP] = OLD_TYPES[kind]
    tree, bsdf = mat.node_tree, _bsdf(mat)
    base = bsdf.inputs["Base Color"]
    node = tree.nodes.new('ShaderNodeMix')
    node.name = node.label = material.DIFFUSE_NODE
    node.data_type, node.blend_type, node.clamp_result = 'RGBA', 'MIX', False
    _sock(node, "A_Color").default_value = (0.0, 0.0, 0.0, 1.0)
    _sock(node, "B_Color").default_value = colour
    _sock(node, "Factor_Float").default_value = diffuse
    for link in list(base.links):
        tree.links.new(link.from_socket, _sock(node, "B_Color"))
        tree.links.remove(link)
    tree.links.new(node.outputs[2], base)
    base.default_value = colour
    return mat


def test_new_materials_are_plain_principled():
    _clear()
    ref = bpy.data.materials.new("blender_ref")
    ref.use_nodes = True
    want = _values(_bsdf(ref))
    for kind in range(3):
        mat = material.new_material()
        assert material.diffuse_node(mat) is None, kind
        assert not [n for n in mat.node_tree.nodes if n.type == 'MIX'], kind
        bsdf = _bsdf(mat)
        assert _values(bsdf) == want, (kind, {k: v for k, v in _values(bsdf).items() if want.get(k) != v})
        out = next(n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
        assert out.inputs["Surface"].links[0].from_node == bsdf, kind
        assert material.color_socket(mat) == bsdf.inputs["Base Color"], kind
        assert material.maya_input(mat, material.DIFFUSE_SOCKET) is None, kind
        assert _close(mat.allset_diffuse, 1.0), kind
        mat.allset_diffuse = 0.3           # nothing to set: no node is added
        assert material.diffuse_node(mat) is None and _close(mat.allset_diffuse, 1.0), kind
        assert material.TYPE_PROP not in mat, kind
        assert mat.name == ("Material", "Material.001", "Material.002")[kind], mat.name


def test_viewport_colour_is_base_color():
    _clear()
    mat = material.new_material()
    assert _close(mat.diffuse_color[:3], _bsdf(mat).inputs["Base Color"].default_value[:3])
    material.color_socket(mat).default_value = (0.9, 0.1, 0.05, 1.0)
    assert material.sync_display(mat) and _close(mat.diffuse_color, (0.9, 0.1, 0.05, 1.0))


def test_old_material_keeps_its_colour_and_diffuse():
    _clear()
    mat = _old('BLINN', (0.2, 0.4, 0.6, 1.0))
    node = material.diffuse_node(mat)
    assert node is not None and material.color_socket(mat) == _sock(node, "B_Color")
    assert material.maya_input(mat, "Base Color") == _sock(node, "B_Color")
    assert _close(mat.allset_diffuse, 0.8)
    mat.allset_diffuse = 0.3
    assert _close(_sock(node, "Factor_Float").default_value, 0.3) and _close(mat.allset_diffuse, 0.3)
    material.color_socket(mat).default_value = (0.9, 0.1, 0.05, 1.0)
    assert material._sync_base(mat) and _close(_bsdf(mat).inputs["Base Color"].default_value, (0.9, 0.1, 0.05, 1))


def test_ae_diffuse_row_only_on_old_materials():
    _clear()
    bpy.ops.mesh.primitive_uv_sphere_add()
    ob = bpy.context.active_object
    new = material.new_material()
    material.assign_object(ob, new)
    rec = Rec()
    ae.draw_sections(rec, bpy.context, ob, new, ae_layout.PRINCIPLED, "t")
    props = [(e[1][0], e[1][1], e[2].get("text")) for e in rec.log if e[0] == "prop"]
    base = _bsdf(new).inputs["Base Color"]
    assert any(o == base and a == "default_value" and t == "Base Color" for o, a, t in props), props
    assert not any(a == "allset_diffuse" for _o, a, _t in props), "no Diffuse row on a plain material"
    for socket, label in (("Alpha", "Alpha"), ("Emission Color", "Color"), ("Subsurface Weight", "Weight")):
        sock = _bsdf(new).inputs[socket]
        assert any(o == sock and t == label for o, _a, t in props), (label, props)
    old = _old('LAMBERT')
    rec = Rec()
    ae.draw_sections(rec, bpy.context, ob, old, ae_layout.PRINCIPLED, "t")
    props = [(e[1][0], e[1][1], e[2].get("text")) for e in rec.log if e[0] == "prop"]
    b = material.color_socket(old)
    assert any(o == b and a == "default_value" and t == "Base Color" for o, a, t in props), props
    assert any(o == old and a == "allset_diffuse" and t == "Diffuse" for o, a, t in props), props
    sockets = [e[3].socket for e in rec.log if e[0] == "operator" and e[1][0] == "allset.ae_map"]
    assert "Base Color" in sockets and "Diffuse" in sockets, sockets


def test_map_button_connects_into_base_color():
    _clear()
    mat = material.new_material()
    assert bpy.ops.allset.ae_map_connect(material=mat.name, socket="Base Color", kind='CHECKER') == {'FINISHED'}
    base = _bsdf(mat).inputs["Base Color"]
    assert base.is_linked and base.links[0].from_node.type == 'TEX_CHECKER', "the texture straight on Base Color"
    assert bpy.ops.allset.ae_map_break(material=mat.name, socket="Base Color") == {'FINISHED'}
    assert not base.is_linked
    # an older material: the texture goes into its diffuse node's colour, like before
    old = _old('LAMBERT')
    assert bpy.ops.allset.ae_map_connect(material=old.name, socket="Base Color", kind='FILE') == {'FINISHED'}
    b = material.color_socket(old)
    assert b.links[0].from_node.type == 'TEX_IMAGE'
    assert _bsdf(old).inputs["Base Color"].links[0].from_node == material.diffuse_node(old)


def test_checker_materials():
    _clear()
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.allset.checker_shader()
    mat = bpy.context.active_object.active_material
    base = _bsdf(mat).inputs["Base Color"]
    assert base.links[0].from_node.type == 'TEX_IMAGE' and material.diffuse_node(mat) is None
    disp = menu_items._checker_material()
    assert material.color_socket(disp).links[0].from_node.type == 'TEX_IMAGE'
    assert material.diffuse_node(disp) is None


def test_diffuse_bypass_round_trip():
    _clear()
    mat = _old('LAMBERT', (0.25, 0.5, 0.75, 1.0))
    tex = maps.build(mat, "Base Color", 'FILE')
    other = _old('PHONG', (0.1, 0.2, 0.3, 1.0))         # a flat colour
    plain = material.new_material()
    base, obase = _bsdf(mat).inputs["Base Color"], _bsdf(other).inputs["Base Color"]
    before = tuple(obase.default_value)
    with material.diffuse_bypass() as n:
        assert n == 2, n
        assert base.links[0].from_node == tex, "the texture straight into Base Color while writing"
        assert not obase.is_linked and _close(obase.default_value, (0.1, 0.2, 0.3, 1.0))
        assert not _bsdf(plain).inputs["Base Color"].is_linked
    assert base.links[0].from_node == material.diffuse_node(mat)
    assert obase.links[0].from_node == material.diffuse_node(other)
    assert _close(obase.default_value, before)
    assert material.color_socket(mat).links[0].from_node == tex


def test_kit_obj_export_writes_texture():
    _clear()
    tmp = bpy.app.tempdir
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    mat = material.new_material()
    material.assign_object(ob, mat)
    img = bpy.data.images.new("kit214", 4, 4)
    img.filepath_raw = os.path.join(tmp, "kit214.png")
    img.file_format = 'PNG'
    img.save()
    tex = maps.build(mat, "Base Color", 'FILE')
    tex.image = img
    path = os.path.join(tmp, "kit214.obj")
    assert bpy.ops.allset.file_dialog('EXEC_DEFAULT', mode='EXPORT_ALL', export_type='OBJ',
                                      filepath=path) == {'FINISHED'}
    mtl = open(path[:-4] + ".mtl", encoding="utf-8").read()
    assert "map_Kd" in mtl and "kit214.png" in mtl, mtl
    assert _bsdf(mat).inputs["Base Color"].links[0].from_node == tex


def test_convert_old_materials():
    _clear()
    flat = _old('LAMBERT', (0.5, 0.25, 1.0, 1.0), diffuse=0.8)
    textured = _old('BLINN')
    tex = maps.build(textured, "Base Color", 'CHECKER')
    plain = material.new_material()
    plain_before = _values(_bsdf(plain))
    flat_name, tex_name = flat.name, textured.name
    bpy.ops.ed.undo_push(message="before")
    assert bpy.ops.allset.convert_old_materials() == {'FINISHED'}
    flat, textured = bpy.data.materials[flat_name], bpy.data.materials[tex_name]
    for mat in (flat, textured):
        assert material.diffuse_node(mat) is None, mat.name
        assert not [n for n in mat.node_tree.nodes if n.name == material.DIFFUSE_NODE], mat.name
    base = _bsdf(flat).inputs["Base Color"]
    assert not base.is_linked and _close(base.default_value, (0.4, 0.2, 0.8, 1.0)), tuple(base.default_value)
    assert _close(flat.diffuse_color[:3], (0.4, 0.2, 0.8))
    tbase = _bsdf(textured).inputs["Base Color"]
    assert tbase.is_linked and tbase.links[0].from_node.name == tex.name
    assert _values(_bsdf(plain)) == plain_before, "plain materials are left alone"
    assert bpy.ops.allset.convert_old_materials() == {'CANCELLED'}, "nothing left to convert"
    bpy.ops.ed.undo_push(message="converted")
    bpy.ops.ed.undo()
    assert material.diffuse_node(bpy.data.materials[flat_name]) is not None, "one undo step brings the node back"
    # the command sits in Lighting/Shading after Assign Existing Material
    extra = menu_map.EXTRA["Lighting/Shading/Assign Existing Material"]
    assert ("Convert Old Kit Materials",) in extra
    assert menu_map.MAP["Lighting/Shading/Convert Old Kit Materials"] == "allset.convert_old_materials"


def test_undo_of_a_diffuse_edit():
    _clear()
    mat = _old('LAMBERT')
    name = mat.name
    bpy.ops.ed.undo_push(message="before")
    mat.allset_diffuse = 0.25
    bpy.ops.ed.undo_push(message="diffuse")
    bpy.ops.ed.undo()
    assert _close(bpy.data.materials[name].allset_diffuse, 0.8), bpy.data.materials[name].allset_diffuse
