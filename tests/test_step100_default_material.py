"""The default material (lambert1, like Maya) — every new shape joins initialShadingGroup = lambert1 (color 0.5, lambert;
Maya: lambert1.color (0.5, 0.5, 0.5), diffuse 0.8, Delete Unused Nodes keeps it, a new Lambert is
lambert2)."""

from importlib import import_module

import bpy

import kit

material = import_module(kit.MODULE + ".operators.material")
create = import_module(kit.MODULE + ".operators.create")
ae = import_module(kit.MODULE + ".ui.attribute_editor")


def _clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for m in list(bpy.data.materials):
        bpy.data.materials.remove(m)


def _principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def test_new_cubes_share_lambert1():
    _clear()
    a = create.create(bpy.context, 'CUBE')
    b = create.create(bpy.context, 'CUBE')
    ma, mb = a.active_material, b.active_material
    assert ma is not None and ma.name == "lambert1", ma
    assert ma == mb, (ma, mb)
    assert len(a.material_slots) == 1 and material.is_default(ma)
    assert ma.get("allset_type") == "lambert" and ma.use_fake_user
    # a plain Principled BSDF with Blender's own values
    ref = bpy.data.materials.new("blender_ref")
    ref.use_nodes = True
    for name in ("Base Color", "Roughness", "Emission Color", "Emission Strength"):
        got, want = _principled(ma).inputs[name].default_value, _principled(ref).inputs[name].default_value
        got, want = (tuple(got), tuple(want)) if hasattr(got, "__len__") else ((got,), (want,))
        assert all(abs(x - y) < 1e-6 for x, y in zip(got, want)), (name, got, want)
    bpy.data.materials.remove(ref)
    assert material.diffuse_node(ma) is None
    assert material.shading_group_name(ma) == "initialShadingGroup"


def test_new_material_is_blender_named_and_purge_keeps_lambert1():
    _clear()
    create.create(bpy.context, 'CUBE')
    m = material.new_material()
    assert m.name == "Material", m.name
    assert material.shading_group_name(m) == "MaterialSG"
    bpy.data.materials.remove(m)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.data.orphans_purge(do_recursive=True)
    assert material.default_material(create=False) is not None, "lambert1 survives an orphan purge (Delete Unused)"


def test_new_material_before_any_mesh_is_material():
    _clear()
    m = material.new_material()
    assert m.name == "Material" and material.default_material(create=False) is None, "no lambert1 for the name"


def test_ae_shading_group_tab():
    _clear()
    ob = create.create(bpy.context, 'CUBE')
    keys = [(k, label, t) for k, label, t in ae.tabs(ob)]
    sg = keys.index(("SG:0", "initialShadingGroup", "shadingEngine"))
    assert keys[sg + 1] == ("MAT:0", "lambert1", "Principled BSDF"), keys
    assert ae.tab_target(ob, "SG:0") == ob.active_material


def test_blender_add_gets_lambert1():
    _clear()
    material.default_material()
    material._baseline()
    bpy.ops.mesh.primitive_cube_add()
    bpy.context.view_layer.update()   # depsgraph_update_post: the new object is found
    ob = bpy.context.active_object
    assert ob.active_material is not None and material.is_default(ob.active_material), ob.active_material


def test_existing_objects_keep_no_material_and_legacy_lambert1_is_adopted():
    _clear()
    me = bpy.data.meshes.new("old")
    old = bpy.data.objects.new("old", me)
    bpy.context.scene.collection.objects.link(old)
    material._baseline()                       # as after loading a file: not a new object
    bpy.context.view_layer.update()
    assert not old.material_slots
    legacy = bpy.data.materials.new("lambert1")
    legacy["allset_type"] = "lambert"
    assert material.default_material() == legacy and material.is_default(legacy)
