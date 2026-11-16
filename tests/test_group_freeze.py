"""Freeze Transformations on a group, like Maya: the group's translate / rotate / scale go to 0 / 0 / 1 with its pivot
where it was; the children freeze too and their values are in the group's frame, so a child's pivot reads its place
in that frame, an instance or a camera keeps its place by taking the group's change, and Unparent, a second Freeze,
Reset Transformations and Center Pivot give the values Maya gives. Nothing moves in the view."""

import math

import bpy
from mathutils import Euler, Vector

TOL = 1e-4


def _clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _pick(*obs):
    for ob in bpy.context.scene.objects:
        ob.select_set(ob in obs)
    bpy.context.view_layer.objects.active = obs[-1]


def _cube(name, t=(0, 0, 0), r=(0, 0, 0)):
    me = bpy.data.meshes.new(name + "Shape")
    me.from_pydata([(-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, 0.5)], [],
                   [(0, 1, 2), (0, 2, 3)])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = t
    ob.rotation_euler = Euler([math.radians(a) for a in r])
    return ob


def _group(name, kids, t=(0, 0, 0), r=(0, 0, 0), s=(1, 1, 1)):
    _pick(*kids)
    assert bpy.ops.allset.group() == {'FINISHED'}
    g = bpy.context.view_layer.objects.active
    g.name = name
    g.location = t
    g.rotation_euler = Euler([math.radians(a) for a in r])
    g.scale = s
    bpy.context.view_layer.update()
    return g


def _world(ob):
    bpy.context.view_layer.update()
    return [ob.matrix_world @ v.co for v in ob.data.vertices]


def _close(a, b):
    return all(abs(x - y) < TOL for x, y in zip(a, b))


def _zero(ob):
    return (_close(ob.location, (0, 0, 0)) and _close(ob.rotation_euler, (0, 0, 0))
            and _close(ob.scale, (1, 1, 1)))


def _freeze(*obs):
    _pick(*obs)
    assert bpy.ops.allset.freeze_transform() == {'FINISHED'}
    bpy.context.view_layer.update()


def test_child_pivot_reads_its_place_in_the_frozen_group():
    _clear()
    cube = _cube("pCube1", t=(0, 0, 3))
    g = _group("group1", [cube], t=(5, 0, 0))
    before = _world(cube)
    _freeze(g)
    assert _zero(g) and _zero(cube)
    assert _close(g.delta_location, (5, 0, 0))
    assert _close(cube.delta_location, (5, 0, 3))          # in the group's frame, not from the group's pivot
    assert all(_close(a, b) for a, b in zip(_world(cube), before))
    _freeze(g)                                               # a second Freeze changes nothing
    assert _close(cube.delta_location, (5, 0, 3)) and all(_close(a, b) for a, b in zip(_world(cube), before))


def test_rotated_scaled_and_nested_groups_freeze_all_channels():
    _clear()
    cube = _cube("pCube1", t=(1, 0, 0), r=(0, 0, 30))
    inner = _group("inner", [cube], t=(0, 2, 0), r=(30, 0, 0))
    outer = _group("outer", [inner], t=(5, 0, 0), r=(0, 45, 0), s=(2, 1, 1))
    before = _world(cube)
    pivot = cube.matrix_world.translation.copy()
    _freeze(outer)
    assert _zero(outer) and _zero(inner) and _zero(cube)
    assert _close(cube.delta_location, pivot)                # the frame of every frozen level is the world here
    assert _close(cube.matrix_world.translation, pivot)
    assert all(_close(a, b) for a, b in zip(_world(cube), before))


def test_instance_and_camera_keep_their_place_with_the_groups_change():
    _clear()
    src = _cube("pCube1")
    _pick(src)
    assert bpy.ops.allset.duplicate_special(geometry_type='INSTANCE') == {'FINISHED'}
    inst = bpy.context.view_layer.objects.active
    inst.location = (0, 2, 0)
    cam = bpy.data.objects.new("camera1", bpy.data.cameras.new("cameraShape1"))
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (1, 0, 0)
    g = _group("group1", [inst, cam], t=(5, 0, 0), r=(0, 0, 45))
    inst_world, cam_world = inst.matrix_world.copy(), cam.matrix_world.copy()
    _freeze(g)
    assert _zero(g)
    assert _close(inst.location, inst_world.translation) and inst.data is src.data    # not frozen, in place
    assert _close(cam.location, cam_world.translation)                                 # a camera isn't frozen
    assert abs(math.degrees(cam.rotation_euler.z) - 45.0) < TOL
    assert _close(cam.matrix_world.translation, cam_world.translation)


def test_a_camera_or_light_alone_is_not_frozen():
    _clear()
    for kind, data in (("camera1", bpy.data.cameras.new("c")), ("pointLight1", bpy.data.lights.new("l", 'POINT'))):
        ob = bpy.data.objects.new(kind, data)
        bpy.context.scene.collection.objects.link(ob)
        ob.location, ob.rotation_euler = (1, 2, 3), (0.1, 0.2, 0.3)
        _freeze(ob)
        assert _close(ob.location, (1, 2, 3)) and _close(ob.rotation_euler, (0.1, 0.2, 0.3)), kind
        assert _close(ob.delta_location, (0, 0, 0)), kind


def test_unparent_reset_and_center_pivot_after_a_group_freeze():
    _clear()
    cube = _cube("pCube1", t=(0, 0, 3))
    g = _group("group1", [cube], t=(5, 0, 0))
    _freeze(g)
    frozen = _world(cube)
    _pick(cube)
    assert bpy.ops.allset.unparent() == {'FINISHED'}
    bpy.context.view_layer.update()
    assert cube.parent is None and _zero(cube) and _close(cube.delta_location, (5, 0, 3))
    assert all(_close(a, b) for a, b in zip(_world(cube), frozen))

    _clear()
    cube = _cube("pCube1", t=(0, 0, 3))
    g = _group("group1", [cube], t=(5, 0, 0))
    _freeze(g)
    frozen = _world(cube)
    g.location.x, cube.location.y = 1.0, 1.0
    _pick(g, cube)
    assert bpy.ops.allset.reset_transform() == {'FINISHED'}
    bpy.context.view_layer.update()
    assert _zero(g) and _zero(cube)
    assert _close(g.delta_location, (0, 0, 0)) and _close(cube.delta_location, (0, 0, 0))   # pivots at the origin
    assert all(_close(a, b) for a, b in zip(_world(cube), frozen))      # the geometry back where the freeze left it

    _clear()
    cube = _cube("pCube1", t=(0, 0, 3))
    g = _group("group1", [cube], t=(5, 0, 0))
    _freeze(g)
    before = _world(cube), tuple(cube.location), tuple(cube.delta_location)
    _pick(g)
    assert bpy.ops.allset.center_pivot() == {'FINISHED'}
    bpy.context.view_layer.update()
    assert all(_close(a, b) for a, b in zip(_world(cube), before[0]))
    assert _close(cube.location, before[1]) and _close(cube.delta_location, before[2])   # the child's values stay


def test_parenting_into_a_frozen_group_uses_its_frame():
    _clear()
    cube = _cube("pCube1", t=(0, 0, 3))
    g = _group("group1", [cube], t=(5, 0, 0))
    _freeze(g)
    other = _cube("pCube2", t=(2, 0, 0))
    _pick(other, g)
    assert bpy.ops.allset.parent() == {'FINISHED'}
    bpy.context.view_layer.update()
    assert other.parent is g and _close(other.location, (2, 0, 0))      # the frozen group's frame is the world
    assert _close(other.matrix_world.translation, Vector((2, 0, 0)))


def _sorted_world(ob):
    bpy.context.view_layer.update()
    return sorted(tuple(round(c, 4) for c in ob.matrix_world @ v.co) for v in ob.data.vertices)


def test_separate_pieces_sit_in_the_groups_frame():
    """Mesh > Separate of a moved, turned mesh with its pivot away from its origin: the pieces read translate 0 and
    pivot 0 in the new group's frame, nothing moves; Ungroup then keeps them in place."""
    _clear()
    for x in (0.0, 3.0):
        _cube(f"part{int(x)}", t=(x, 0, 0))
    _pick(*bpy.context.scene.objects)
    assert bpy.ops.allset.combine() == {'FINISHED'}
    ob = bpy.context.view_layer.objects.active
    ob.location = (1, 2, 0)
    ob.rotation_euler.z = math.radians(30)
    before = _sorted_world(ob)
    _pick(ob)
    assert bpy.ops.allset.separate() == {'FINISHED'}
    grp = next(o for o in bpy.context.scene.objects if o.type == 'EMPTY')
    pieces = list(grp.children)
    assert len(pieces) == 2
    assert sorted(sum((_sorted_world(p) for p in pieces), [])) == before
    for p in pieces:
        assert _zero(p) and _close(p.delta_location, (0, 0, 0)), (p.name, p.location[:])
    _pick(grp)
    assert bpy.ops.allset.ungroup() == {'FINISHED'}
    assert sorted(sum((_sorted_world(p) for p in pieces), [])) == before
