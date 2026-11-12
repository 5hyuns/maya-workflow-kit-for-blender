"""#356: Modify > Center Pivot in component mode, like Maya — the object's pivot goes to the centre of the selected
components (the whole bounding box when nothing is selected) and the command ends in object mode with the object
selected; the geometry and the translate channels stay; one undo brings back component mode, the mesh and the
pivot."""

from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit

hold = import_module(kit.MODULE + ".operators.hold")


def close(a, b, eps=1e-5):
    return (Vector(a) - Vector(b)).length < eps


def _fresh():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    sc = bpy.context.scene
    sc.cursor.location = (0.0, 0.0, 0.0)
    sc.tool_settings.transform_pivot_point = 'MEDIAN_POINT'


def _cube(location=(3.0, 0.0, 0.0), name="pCube1"):
    bpy.ops.mesh.primitive_cube_add(location=location)
    ob = bpy.context.active_object
    ob.name = name
    return ob


def _edit(ob, pick, mode='FACE'):
    """Component mode on ``ob`` with the elements whose centre satisfies ``pick`` selected."""
    for o in bpy.context.view_layer.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type=mode)
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(ob.data)
    elems = bm.faces if mode == 'FACE' else bm.verts
    for e in elems:
        centre = e.calc_center_median() if mode == 'FACE' else e.co
        if pick(centre):
            e.select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _world_points(ob):
    mw = ob.matrix_world
    return [tuple(mw @ v.co) for v in ob.data.vertices]


def _center():
    return bpy.ops.allset.center_pivot('EXEC_DEFAULT', True)     # True: one undo step, like the menu item


def test_face():
    _fresh()
    ob = _cube()
    _edit(ob, lambda c: c.z > 0.9)                 # the top face, centre (3, 0, 1) in the world
    bpy.ops.object.mode_set(mode='OBJECT')
    before = _world_points(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    assert _center() == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'
    assert ob.select_get() and bpy.context.view_layer.objects.active == ob
    assert close(ob.matrix_world.translation, (3.0, 0.0, 1.0)), ob.matrix_world.translation
    assert close(ob.location, (3.0, 0.0, 0.0)), ob.location          # translate stays, like Maya
    assert all(close(a, b) for a, b in zip(before, _world_points(ob)))


def test_vertex():
    _fresh()
    ob = _cube()
    _edit(ob, lambda c: c.x < -0.9 and c.y < -0.9 and c.z < -0.9, mode='VERT')
    assert _center() == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'
    assert close(ob.matrix_world.translation, (2.0, -1.0, -1.0)), ob.matrix_world.translation


def test_nothing_selected_uses_the_whole_box():
    _fresh()
    ob = _cube()
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.co.z += 2.0                              # the geometry above its pivot
    bmesh.update_edit_mesh(ob.data)
    bpy.ops.mesh.select_all(action='DESELECT')
    assert _center() == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'
    assert close(ob.matrix_world.translation, (3.0, 0.0, 2.0)), ob.matrix_world.translation


def test_only_objects_with_picked_components():
    _fresh()
    a = _cube((3.0, 0.0, 0.0), "pCube1")
    b = _cube((-3.0, 0.0, 0.0), "pCube2")
    for o in (a, b):
        o.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(a.data)
    for f in bm.faces:
        f.select_set(f.calc_center_median().z > 0.9)
    bmesh.update_edit_mesh(a.data)
    assert _center() == {'FINISHED'}
    assert close(a.matrix_world.translation, (3.0, 0.0, 1.0))
    assert close(b.matrix_world.translation, (-3.0, 0.0, 0.0))        # no picked components: untouched
    assert a.select_get() and not b.select_get()


def test_one_undo_restores_mesh_pivot_and_component_mode():
    _fresh()
    ob = _cube()
    _edit(ob, lambda c: c.z > 0.9)
    name = ob.name
    me = ob.data.name
    bpy.ops.ed.undo_push(message="before center pivot")
    assert _center() == {'FINISHED'}
    assert close(bpy.data.objects[name].matrix_world.translation, (3.0, 0.0, 1.0))
    bpy.ops.ed.undo()
    ob = bpy.data.objects[name]
    assert bpy.context.mode == 'EDIT_MESH', bpy.context.mode
    assert close(ob.matrix_world.translation, (3.0, 0.0, 0.0)), ob.matrix_world.translation
    assert close(ob.delta_location, (0.0, 0.0, 0.0)), ob.delta_location
    bpy.ops.object.mode_set(mode='OBJECT')
    zs = sorted({round(v.co.z, 4) for v in bpy.data.meshes[me].vertices})
    assert zs == [-1.0, 1.0], zs                   # the mesh is back around its old pivot


def test_menu_item_in_component_mode():
    _fresh()
    ob = _cube()
    _edit(ob, lambda c: c.z > 0.9)
    assert bpy.ops.allset.menu_item(item="Modify/Center Pivot") == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'
    assert close(ob.matrix_world.translation, (3.0, 0.0, 1.0))


def test_a_component_pivot_ends_with_it():
    """A pivot placed with Insert in component mode is gone after Center Pivot (the object manipulator sits on the
    object pivot again)."""
    _fresh()
    ob = _cube()
    _edit(ob, lambda c: c.z > 0.9)
    sc = bpy.context.scene
    bpy.ops.wm.tool_set_by_id(name="builtin.move", space_type='VIEW_3D')    # the pivot is edited with Move
    bpy.ops.allset.pivot_toggle()
    sc.cursor.location = (4.5, 0.5, 2.0)
    bpy.ops.allset.pivot_toggle()
    assert hold.COMPONENT.custom and sc.tool_settings.transform_pivot_point == 'CURSOR'
    assert _center() == {'FINISHED'}
    assert not hold.COMPONENT.custom
    assert sc.tool_settings.transform_pivot_point != 'CURSOR'
    assert close(ob.matrix_world.translation, (3.0, 0.0, 1.0))


def test_object_mode_unchanged_and_other_ops_stay_object_only():
    _fresh()
    ob = _cube()
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.co.x += 1.0
    bmesh.update_edit_mesh(ob.data)
    assert not bpy.ops.allset.freeze_transform.poll()
    assert not bpy.ops.allset.reset_transform.poll()
    bpy.ops.object.mode_set(mode='OBJECT')
    assert _center() == {'FINISHED'}
    assert close(ob.matrix_world.translation, (4.0, 0.0, 0.0))
