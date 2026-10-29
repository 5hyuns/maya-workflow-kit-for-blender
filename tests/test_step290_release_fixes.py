"""Step 290 (0.7.0 release check): two Python errors the seeded monkey found. Select > Similar in edit mode with
nothing selected reports Blender's refusal instead of a Python traceback; Effects > Fire / Smoke with a fluid
container in the selection makes the other meshes emitters instead of failing inside Blender's quick_smoke."""

import bpy

import kit


def _scene():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _menu(item):
    """Run a Maya menu item; return (result, error text) — an ERROR report raises RuntimeError at the caller."""
    try:
        return bpy.ops.allset.menu_item(item=item), ""
    except RuntimeError as ex:
        return None, str(ex)


def test_select_similar_with_nothing_selected():
    _scene()
    bpy.ops.allset.create(kind='CUBE')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    res, err = _menu("Select/Similar")
    assert "Traceback" not in err, err
    assert res in (None, {'CANCELLED'}, {'FINISHED'}), res
    bpy.ops.object.mode_set(mode='OBJECT')


def test_fire_with_a_fluid_container_selected():
    _scene()
    bpy.ops.allset.create(kind='SPHERE')
    sphere = bpy.context.active_object
    _res, err = _menu("Fluids/3D Container")
    assert "Traceback" not in err, err
    containers = [o for o in bpy.data.objects if any(m.type == 'FLUID' for m in o.modifiers)]
    for o in bpy.data.objects:
        o.select_set(o is sphere or o in containers)
    bpy.context.view_layer.objects.active = sphere
    res, err = _menu("Effects/Fire")
    assert "Traceback" not in err and "fluid_type" not in err, err
    assert any(m.type == 'FLUID' and m.fluid_type == 'FLOW' for m in sphere.modifiers), \
        [(m.type, getattr(m, "fluid_type", None)) for m in sphere.modifiers]


def test_fire_with_only_a_container_selected_warns():
    _scene()
    bpy.ops.allset.create(kind='SPHERE')
    bpy.ops.object.modifier_add(type='FLUID')
    bpy.context.active_object.modifiers[-1].fluid_type = 'DOMAIN'
    res, err = _menu("Effects/Fire")
    assert "Traceback" not in err and "fluid_type" not in err, err
