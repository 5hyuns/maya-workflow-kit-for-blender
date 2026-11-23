"""No default material: new shapes have no material (Blender's grey), whichever way they are made; a material
made by an entry (Assign New Material ...) is Blender's new material. A lambert1 that an older kit version left in a
scene is a plain material: it keeps its objects but is given to no new shape."""

from importlib import import_module

import bmesh
import bpy

import kit

material = import_module(kit.MODULE + ".operators.material")
create = import_module(kit.MODULE + ".operators.create")
ae = import_module(kit.MODULE + ".ui.attribute_editor")
cmds = import_module(kit.MODULE + ".command_line.cmds_shim")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for m in list(bpy.data.materials):
        bpy.data.materials.remove(m)


def _old_lambert1():
    """lambert1 as an older kit version saved it."""
    mat = bpy.data.materials.new("lambert1")
    mat["allset_type"] = "lambert"
    mat["allset_default"] = True
    mat.use_fake_user = True
    mat.use_nodes = True
    return mat


def test_new_shapes_have_no_material():
    _clear()
    for kind in ('CUBE', 'SPHERE', 'PLANE', 'NURBS_SPHERE'):
        ob = create.create(bpy.context, kind)
        for part in [ob, *ob.children]:
            assert not any(s.material for s in part.material_slots), (kind, part.name)
    bpy.ops.mesh.primitive_cube_add()                 # Blender's Add menu too
    bpy.context.view_layer.update()
    assert not bpy.context.active_object.material_slots
    assert not bpy.data.materials, [m.name for m in bpy.data.materials]


def test_new_material_is_blender_named():
    _clear()
    create.create(bpy.context, 'CUBE')
    m = material.new_material()
    assert m.name == "Material", m.name
    assert material.shading_group_name(m) == "MaterialSG"
    assert material.new_material().name == "Material.001"


def test_ae_shading_group_tab():
    _clear()
    ob = create.create(bpy.context, 'CUBE')
    assert not [k for k, _l, _t in ae.tabs(ob) if k.startswith(("SG:", "MAT:"))], "no material, no tabs"
    mat = material.new_material()
    material.assign_object(ob, mat)
    keys = [(k, label, t) for k, label, t in ae.tabs(ob)]
    sg = keys.index(("SG:0", "MaterialSG", "shadingEngine"))
    assert keys[sg + 1] == ("MAT:0", "Material", "Principled BSDF"), keys
    assert ae.tab_target(ob, "SG:0") == ob.active_material


def test_old_lambert1_is_a_plain_material():
    _clear()
    lam = _old_lambert1()
    old = create.create(bpy.context, 'CUBE')
    old.data.materials.append(lam)
    new = create.create(bpy.context, 'SPHERE')
    assert not new.material_slots, "a new shape doesn't get the old lambert1"
    assert old.active_material == lam
    assert material.shading_group_name(lam) == "lambert1SG"
    # Hypershade Delete Unused: lambert1 goes like any unused material once no object uses it
    bpy.data.objects.remove(old)
    assert bpy.ops.allset.hs_edit(action='DELETE_UNUSED') == {'FINISHED'}
    assert "lambert1" not in bpy.data.materials


def test_hypershade_delete_any_material():
    _clear()
    lam = _old_lambert1()
    bpy.context.window_manager.allset_hs_material = lam.name
    assert bpy.ops.allset.hs_edit(action='DELETE') == {'FINISHED'}
    assert "lambert1" not in bpy.data.materials


def test_face_assignment_leaves_the_other_faces_without_material():
    _clear()
    ob = create.create(bpy.context, 'CUBE')
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    bm.faces[2].select = True
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.assign_new_material() == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    assert [s.material.name if s.material else None for s in ob.material_slots] == [None, "Material"]
    idx = [p.material_index for p in ob.data.polygons]
    assert idx[2] == 1 and all(i == 0 for n, i in enumerate(idx) if n != 2), idx


def test_command_line_initial_shading_group():
    _clear()
    a = create.create(bpy.context, 'CUBE')
    b = create.create(bpy.context, 'SPHERE')
    mat = material.new_material()
    material.assign_object(b, mat)
    bpy.context.view_layer.update()
    # initialShadingGroup = the shapes without a material
    got = cmds.sets("initialShadingGroup", q=True)
    assert got == [a.data.name], got
    assert cmds.objExists("initialShadingGroup") and not cmds.objExists("lambert1")
    groups = cmds.ls(type="shadingEngine")
    assert "MaterialSG" in groups and "initialShadingGroup" in groups, groups
    # forceElement into initialShadingGroup = the shape loses its material
    cmds.sets(b.name, e=True, forceElement="initialShadingGroup")
    assert not any(s.material for s in b.material_slots)
    assert sorted(cmds.sets("initialShadingGroup", q=True)) == sorted([a.data.name, b.data.name])
    # shadingNode makes Blender's new material and returns its name
    name = cmds.shadingNode("lambert", asShader=True)
    assert name == "Material.001" and cmds.nodeType(name) == "standardSurface", (name, cmds.nodeType(name))
    cmds.setAttr(f"{name}.baseColor", 0.2, 0.4, 0.6, type="double3")
    bsdf = next(n for n in bpy.data.materials[name].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    assert all(abs(x - y) < 1e-6 for x, y in zip(bsdf.inputs["Base Color"].default_value, (0.2, 0.4, 0.6)))
    assert abs(cmds.getAttr(f"{name}.specularRoughness") - bsdf.inputs["Roughness"].default_value) < 1e-6
    for attr in ("eccentricity", "cosinePower"):
        try:
            cmds.getAttr(f"{name}.{attr}")
        except (RuntimeError, ValueError) as ex:
            print("expected:", ex)
        else:
            raise AssertionError(f"{attr}: no such attribute")
