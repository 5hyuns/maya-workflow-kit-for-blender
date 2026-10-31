"""Joints drawn like Maya's: world-size wire spheres (half the Radius x Joint Size), pyramid bones from the parent's
sphere to the child's, Maya's colours with the selection passed down the hierarchy, Blender's bones off in the Maya
layout views and given back on disable. GUI: tests/gui/gui_maya_joints.py."""

from importlib import import_module

import bpy
from mathutils import Matrix, Vector

import kit

mj = import_module(kit.MODULE + ".ui.maya_joints")
joints = import_module(kit.MODULE + ".operators.joints")
units = import_module(kit.MODULE + ".operators.units")
cb = import_module(kit.MODULE + ".ui.channel_box")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)


def _chain():
    """joint1 > joint2 > joint3 along +X, 2 apart, plus joint4 branching from joint2 up +Z."""
    _clear()
    arm = joints.new_skeleton(bpy.context)
    j1 = joints.add_joint(arm, Vector((0, 0, 0)), None, length=0.5)
    j2 = joints.add_joint(arm, Vector((2, 0, 0)), j1, length=0.5)
    j3 = joints.add_joint(arm, Vector((4, 0, 0)), j2, length=0.5)
    j4 = joints.add_joint(arm, Vector((2, 0, 2)), j2, length=0.5)
    joints.finish(bpy.context, arm, [j1, j2, j3, j4])
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    return arm, [j1, j2, j3, j4]


def test_drawn_radius_is_half_the_radius_times_joint_size():
    arm, names = _chain()
    scene = bpy.context.scene
    bone = arm.data.bones[names[0]]
    bone[joints.RADIUS] = 2.0
    k = units.maya_unit(scene)
    assert abs(mj.drawn_radius(bone, scene) - 1.0 * k) < 1e-9
    scene.allset_joint_size = 2.0
    try:
        assert abs(mj.drawn_radius(bone, scene) - 2.0 * k) < 1e-9, "Joint Size scales the drawing"
        assert abs(mj.drawn_radius(bone, scene, 3.0) - 6.0 * k) < 1e-9, "and so does the skeleton's scale"
    finally:
        scene.allset_joint_size = 1.0
    del bone[joints.RADIUS]
    assert abs(mj.drawn_radius(bone, scene) - 0.5 * k) < 1e-9, "Radius 1 by default"


def test_sphere_is_three_great_circles_of_the_drawn_radius():
    frame = Matrix.Identity(3)
    c = Vector((1, 2, 3))
    pts = mj.sphere_lines(c, frame, 0.5)
    assert len(pts) == 3 * 2 * mj.SEGMENTS
    assert all(abs((p - c).length - 0.5) < 1e-6 for p in pts)
    # each circle lies in one of the local planes
    n = mj.SEGMENTS * 2
    for ring, axis in zip((pts[:n], pts[n:2 * n], pts[2 * n:]), (2, 0, 1)):
        assert all(abs((p - c)[axis]) < 1e-6 for p in ring), axis


def test_bone_pyramid_from_sphere_to_sphere():
    J = mj.Joint
    p = J("a", None, Vector((0, 0, 0)), Matrix.Identity(3), 0.5)
    q = J("b", "a", Vector((4, 0, 0)), Matrix.Identity(3), 0.25)
    pts = mj.bone_lines(p, q)
    assert len(pts) == 16, "8 edges: 4 round the base, 4 to the apex"
    corners = {tuple(round(c, 6) for c in v) for v in pts[0::2]}
    assert len(corners) == 4
    for v in corners:
        v = Vector(v)
        assert abs(v.x - 0.5) < 1e-6 and abs(Vector((0, v.y, v.z)).length - 0.5) < 1e-6, v   # on the parent's sphere
    apex = pts[3]
    assert (apex - Vector((3.75, 0, 0))).length < 1e-6, "apex on the child's sphere"
    # base corners follow the parent's Y / Z axes
    assert any(abs(Vector(v).y - 0.5) < 1e-6 and abs(Vector(v).z) < 1e-6 for v in corners)
    assert mj.bone_lines(p, J("c", "a", Vector((0.6, 0, 0)), Matrix.Identity(3), 0.25)) == [], "spheres overlap"


def test_colours_pass_down_the_hierarchy():
    arm, (j1, j2, j3, j4) = _chain()
    js = mj.skeleton(arm, bpy.context.scene)
    assert set(js) == {j1, j2, j3, j4}
    assert sorted(js[j2].children) == sorted([j3, j4]) and not js[j3].children
    col = mj.colours(js, set(), None)
    assert set(col.values()) == {mj.UNSELECTED}
    col = mj.colours(js, {j2}, j2)
    assert col[j1] == mj.UNSELECTED and col[j2] == col[j3] == col[j4] == mj.LEAD, "below the lead: green"
    col = mj.colours(js, {j1, j4}, j4)
    assert col[j1] == col[j2] == col[j3] == mj.SELECTED and col[j4] == mj.LEAD


def test_selection_in_pose_and_object_mode():
    arm, (j1, j2, j3, j4) = _chain()
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    js = mj.skeleton(arm, bpy.context.scene)
    assert mj.selection(arm, js) == (set(), None)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    assert mj.selection(arm, js) == ({j1}, j1), "a selected skeleton object = its root joint"
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        cb.set_bone_selected(pb, pb.name in (j3, j4))
    arm.data.bones.active = arm.data.bones[j4]
    assert mj.selection(arm, js) == ({j3, j4}, j4)
    bpy.ops.object.mode_set(mode='OBJECT')


def test_frames_follow_the_pose():
    arm, (j1, j2, j3, j4) = _chain()
    bpy.ops.object.mode_set(mode='POSE')
    pb = arm.pose.bones[j1]
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    before = mj.skeleton(arm, bpy.context.scene)[j3].centre.copy()
    pb.rotation_euler = (0.0, 0.0, 1.5707963)
    bpy.context.view_layer.update()
    after = mj.skeleton(arm, bpy.context.scene)[j3].centre
    assert (after - before).length > 1.0, "posed joints draw where the pose puts them"
    bpy.ops.object.mode_set(mode='OBJECT')


def test_release_gives_blender_bones_back():
    screen = bpy.data.screens[0]
    views = [a.spaces.active for a in screen.areas if a.type == 'VIEW_3D']
    for s in views:
        s.overlay.show_bones = False
    screen[mj.SETTLED] = True
    mj.release_all()
    assert mj.SETTLED not in screen
    from importlib import import_module as im
    toolbox = im(kit.MODULE + ".ui.toolbox")
    assert all(s.overlay.show_bones for s in views if not toolbox.is_toolbox(s))


def test_drawn_spheres_match_the_per_joint_lines():
    """The view's batch builds all spheres at once; the points equal the per-joint lines picking uses."""
    arm, names = _chain()
    arm.rotation_euler = (0.3, -0.2, 0.7)
    bpy.context.view_layer.update()
    js = mj.skeleton(arm, bpy.context.scene)
    pts, order = mj._sphere_array(js)
    assert order and len(pts) == len(order) * 3 * 2 * mj.SEGMENTS
    per = 3 * 2 * mj.SEGMENTS
    for k, n in enumerate(order):
        ref = mj.sphere_lines(js[n].centre, js[n].frame, js[n].radius)
        got = pts[k * per:(k + 1) * per]
        assert max((Vector(tuple(g)) - r).length for g, r in zip(got, ref)) < 1e-5, n
