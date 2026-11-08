"""#338: Modify > Match Transformations follows the selection order with rig controls too. The last picked node
(object or pose bone) is the source; every node picked before it receives the transform. The report: an IK hand
control (a pose bone) picked first and a locator (an Empty) picked last must put the control on the locator, not the
whole rig; the kit leaves Pose mode when the locator is picked after the control, keeping the control selected."""

import math
from importlib import import_module

import bpy
from mathutils import Euler, Matrix, Vector

import kit

snap = import_module(kit.MODULE + ".operators.snap_align")
joint_selection = import_module(kit.MODULE + ".operators.joint_selection")

TOL = 1e-4
HAND, FOOT = "c_hand_ik", "c_foot_ik"


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def _rig():
    """An armature away from the origin with two control bones at different places."""
    arm = bpy.data.armatures.new("rig")
    ob = bpy.data.objects.new("rig", arm)
    bpy.context.scene.collection.objects.link(ob)
    ob.matrix_world = Matrix.LocRotScale(Vector((0.3, -0.2, 0.1)), Euler((0, 0, math.radians(20))), None)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    for name, head in ((HAND, (1.0, 0.0, 2.0)), (FOOT, (-1.0, 0.5, 0.2))):
        eb = arm.edit_bones.new(name)
        eb.head = head
        eb.tail = Vector(head) + Vector((0, 0.5, 0))
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.select_set(False)
    bpy.context.view_layer.objects.active = None
    bpy.context.view_layer.update()
    return ob


def _locator(name, loc, rot_deg=(0, 0, 0), scale=(1, 1, 1)):
    ob = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ob)
    ob.matrix_world = Matrix.LocRotScale(Vector(loc), Euler([math.radians(a) for a in rot_deg]), Vector(scale))
    ob.select_set(False)
    bpy.context.view_layer.update()
    return ob


def _cube(name, loc):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.select_set(False)
    bpy.context.view_layer.update()
    return ob


def _pick_object(ob, shift=False):
    """A click on an object in the viewport or the Outliner: Pose mode ends, the picked joints stay selected."""
    ctx = bpy.context
    if ctx.mode != 'OBJECT' and ctx.active_object is not None:
        joint_selection.leave(ctx, clear_selection=not shift)
    if not shift:
        for o in ctx.scene.objects:
            o.select_set(False)
    ob.select_set(True)
    ctx.view_layer.objects.active = ob
    ctx.view_layer.update()


def _pick_joint(arm, name, shift=False):
    """A click on a joint / control: the kit's own pick (Pose mode on its rig, the bone selected and active)."""
    assert joint_selection.select(bpy.context, arm, name, shift, False)
    bpy.context.view_layer.update()


def _frame(node):
    bpy.context.view_layer.update()
    return snap._maya_frame(node)


def _same(m1, m2, what):
    t1, r1, s1 = m1.decompose()
    t2, r2, s2 = m2.decompose()
    assert (t1 - t2).length < TOL, f"{what}: translation {tuple(t1)} != {tuple(t2)}"
    assert math.degrees(r1.rotation_difference(r2).angle) < 1e-3, f"{what}: rotation {r1} != {r2}"
    assert (s1 - s2).length < TOL, f"{what}: scale {tuple(s1)} != {tuple(s2)}"


def _match(kind='ALL'):
    r = bpy.ops.allset.match_transform(kind=kind)
    bpy.context.view_layer.update()
    return r


def test_control_then_locator_moves_the_control():
    # the report: the IK hand control first, the locator last -> the control lands on the locator, the rig stays
    _clear()
    arm = _rig()
    loc = _locator("locator", (3, 1, 0.5), (10, 20, 30))
    rig_before = arm.matrix_world.copy()
    foot_before = _frame(arm.pose.bones[FOOT])
    locator_before = loc.matrix_world.copy()
    _pick_joint(arm, HAND)
    _pick_object(loc, shift=True)
    assert bpy.context.view_layer.objects.active is loc and arm.select_get() and arm.pose.bones[HAND].select
    assert _match() == {'FINISHED'}
    _same(_frame(arm.pose.bones[HAND]), locator_before, "#338: the control must take the locator's transform")
    _same(arm.matrix_world, rig_before, "#338: the rig object must stay")
    _same(_frame(arm.pose.bones[FOOT]), foot_before, "an unpicked control must stay")
    _same(loc.matrix_world, locator_before, "the locator (last picked) must stay")


def test_locator_then_control_moves_the_locator():
    # the other order: the locator first, the control last -> the locator lands on the control
    _clear()
    arm = _rig()
    loc = _locator("locator", (3, 1, 0.5), (10, 20, 30))
    hand_before = _frame(arm.pose.bones[HAND])
    rig_before = arm.matrix_world.copy()
    _pick_object(loc)
    _pick_joint(arm, HAND, shift=True)
    assert bpy.context.mode == 'POSE' and loc.select_get()
    assert _match() == {'FINISHED'}
    _same(loc.matrix_world, hand_before, "the locator must take the control's transform")
    _same(_frame(arm.pose.bones[HAND]), hand_before, "the control (last picked) must stay")
    _same(arm.matrix_world, rig_before, "the rig object must stay")


def test_rig_still_in_pose_mode_with_the_locator_active():
    # a rig left in Pose mode while the locator became active (Blender's own selection paths): same rule
    _clear()
    arm = _rig()
    loc = _locator("locator", (-2, 2, 1), (0, 45, 0))
    rig_before = arm.matrix_world.copy()
    locator_before = loc.matrix_world.copy()
    _pick_joint(arm, HAND)
    loc.select_set(True)
    bpy.context.view_layer.objects.active = loc
    bpy.context.view_layer.update()
    if arm.mode != 'POSE':
        raise kit.Skip("this Blender leaves Pose mode when another object becomes active")
    assert _match() == {'FINISHED'}
    _same(_frame(arm.pose.bones[HAND]), locator_before, "the control must take the locator's transform")
    _same(arm.matrix_world, rig_before, "the rig object must stay")


def test_two_controls_follow_the_locator():
    _clear()
    arm = _rig()
    loc = _locator("locator", (0, 3, 2), (0, 0, 90))
    locator_before = loc.matrix_world.copy()
    _pick_joint(arm, HAND)
    _pick_joint(arm, FOOT, shift=True)
    _pick_object(loc, shift=True)
    assert _match() == {'FINISHED'}
    for name in (HAND, FOOT):
        _same(_frame(arm.pose.bones[name]), locator_before, f"{name} must take the locator's transform")


def test_translation_rotation_scale_variants_on_a_control():
    _clear()
    arm = _rig()
    loc = _locator("locator", (2, 2, 2), (30, 0, 60), (2, 2, 2))
    lt, lr, ls = loc.matrix_world.decompose()
    for kind in ('TRANSLATE', 'ROTATE', 'SCALE'):
        _pick_joint(arm, HAND)
        pb = arm.pose.bones[HAND]
        t0, r0, s0 = _frame(pb).decompose()
        _pick_object(loc, shift=True)
        assert _match(kind) == {'FINISHED'}
        t, r, s = _frame(pb).decompose()
        want = Matrix.LocRotScale(lt if kind == 'TRANSLATE' else t0, lr if kind == 'ROTATE' else r0,
                                  ls if kind == 'SCALE' else s0)
        _same(Matrix.LocRotScale(t, r, s), want, f"Match {kind}")


def test_objects_follow_the_selection_order():
    _clear()
    a = _locator("a", (1, 0, 0), (0, 0, 10))
    b = _locator("b", (0, 2, 0), (0, 30, 0), (1, 2, 3))
    a0, b0 = a.matrix_world.copy(), b.matrix_world.copy()
    _pick_object(a)
    _pick_object(b, shift=True)
    assert _match() == {'FINISHED'}
    _same(a.matrix_world, b0, "a (first) must take b's transform")
    _same(b.matrix_world, b0, "b (last) must stay")
    a.matrix_world = a0
    _pick_object(b)
    _pick_object(a, shift=True)
    assert _match() == {'FINISHED'}
    _same(b.matrix_world, a0, "b (first) must take a's transform")
    _same(a.matrix_world, a0, "a (last) must stay")


def test_match_pivots_takes_the_control_as_the_target():
    # Match Pivots: a control picked last gives the pivot point; a control picked first has no pivot of its own
    _clear()
    arm = _rig()
    cube = _cube("pCube1", (4, 0, 0))
    hand_point = _frame(arm.pose.bones[HAND]).translation.copy()
    _pick_object(cube)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    arm.data.bones.active = arm.data.bones[HAND]
    assert bpy.context.mode == 'OBJECT'
    assert bpy.ops.allset.match_pivots() == {'FINISHED'}
    bpy.context.view_layer.update()
    assert (cube.matrix_world.translation - hand_point).length < TOL, tuple(cube.matrix_world.translation)
    assert (Vector(cube.location) - Vector((4, 0, 0))).length < TOL, "the cube itself must not move"
    # the control first, the cube last: nothing has a pivot to move, the rig object must not be touched
    rig_before = arm.matrix_world.copy()
    _pick_joint(arm, HAND)
    _pick_object(cube, shift=True)
    assert bpy.ops.allset.match_pivots() == {'CANCELLED'}
    bpy.context.view_layer.update()
    _same(arm.matrix_world, rig_before, "the rig object must stay")
