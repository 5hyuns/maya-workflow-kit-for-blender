"""Step 100: Maya's default material — every new shape joins initialShadingGroup = lambert1 (color 0.5, lambert;
measured with mayapy: lambert1.color (0.5, 0.5, 0.5), diffuse 0.8, Delete Unused Nodes keeps it, a new Lambert is
lambert2). Plan: docs/steps/step_100.md."""

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
    col = tuple(_principled(ma).inputs["Base Color"].default_value)
    assert all(abs(c - 0.5) < 1e-6 for c in col[:3]), col   # mayapy lambert1.color = (0.5, 0.5, 0.5)
    inc = tuple(_principled(ma).inputs["Emission Color"].default_value)
    assert inc[:3] == (0.0, 0.0, 0.0), inc   # mayapy lambert1.incandescence = (0, 0, 0)
    assert material.shading_group_name(ma) == "initialShadingGroup"


def test_new_lambert_is_lambert2_and_purge_keeps_lambert1():
    _clear()
    create.create(bpy.context, 'CUBE')
    m = material.new_material('LAMBERT')
    assert m.name == "lambert2", m.name   # mayapy: shadingNode lambert -> lambert2
    assert material.shading_group_name(m) == "lambert2SG"
    bpy.data.materials.remove(m)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.data.orphans_purge(do_recursive=True)
    assert material.default_material(create=False) is not None, "lambert1 survives an orphan purge (Delete Unused)"


def test_new_lambert_before_any_mesh_is_still_lambert2():
    _clear()
    m = material.new_material('LAMBERT')
    assert m.name == "lambert2" and material.default_material(create=False).name == "lambert1"


def test_ae_shading_group_tab():
    _clear()
    ob = create.create(bpy.context, 'CUBE')
    keys = [(k, label, t) for k, label, t in ae.tabs(ob)]
    sg = keys.index(("SG:0", "initialShadingGroup", "shadingEngine"))
    assert keys[sg + 1] == ("MAT:0", "lambert1", "lambert"), keys
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
