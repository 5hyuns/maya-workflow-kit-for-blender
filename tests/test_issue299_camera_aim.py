"""#299: Create > Cameras > Camera and Aim / Camera, Aim and Up.

Like Maya: camera1 and camera1_aim (and camera1_up) under camera1_group; the camera looks at the aim with world up,
the up node rolls it; each node moves on its own and moving the group moves the whole rig."""

import math
from importlib import import_module

import bpy
from mathutils import Vector

import kit

menu_map = import_module(kit.MODULE + ".ui.menu_map")


def _clean():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _make(kind):
    _clean()
    assert bpy.ops.allset.create(kind=kind) == {'FINISHED'}
    bpy.context.view_layer.update()
    return {ob.name: ob for ob in bpy.data.objects}


def _view_dir(cam):
    # a Blender camera looks along its local -Z
    return (cam.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()


def _up_dir(cam):
    return (cam.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()


def test_menu_items_reach_the_rigs():
    assert menu_map.MAP["Create/Cameras/Camera"] == ("allset.create", {"kind": 'CAMERA'})
    assert menu_map.MAP["Create/Cameras/Camera and Aim"] == ("allset.create", {"kind": 'CAMERA_AIM'})
    assert menu_map.MAP["Create/Cameras/Camera, Aim and Up"] == ("allset.create", {"kind": 'CAMERA_AIM_UP'})
    assert "Create/Cameras" not in menu_map.MAP, "Cameras must open its submenu"


def test_camera_and_aim():
    obs = _make('CAMERA_AIM')
    assert set(obs) == {"camera1", "camera1_aim", "camera1_group"}, set(obs)
    cam, aim, group = obs["camera1"], obs["camera1_aim"], obs["camera1_group"]
    assert cam.type == 'CAMERA' and aim.type == 'EMPTY' and group.type == 'EMPTY'
    assert cam.parent == group and aim.parent == group and group.parent is None
    # looks at the aim, 5 units ahead
    to_aim = (aim.matrix_world.translation - cam.matrix_world.translation)
    assert abs(to_aim.length - 5.0) < 1e-4, to_aim.length
    assert _view_dir(cam).angle(to_aim.normalized()) < 1e-4
    # the aim moves on its own; the camera follows it and stays level (world up)
    aim.location = Vector((3.0, 5.0, 2.0))
    bpy.context.view_layer.update()
    to_aim = (aim.matrix_world.translation - cam.matrix_world.translation).normalized()
    assert _view_dir(cam).angle(to_aim) < 1e-4
    right = (cam.matrix_world.to_3x3() @ Vector((1.0, 0.0, 0.0)))
    assert abs(right.z) < 1e-4, "no roll without an up node"
    # moving the group moves the whole rig
    group.location = Vector((10.0, 0.0, 0.0))
    bpy.context.view_layer.update()
    assert abs(cam.matrix_world.translation.x - 10.0) < 1e-4
    assert abs(aim.matrix_world.translation.x - 13.0) < 1e-4


def test_camera_aim_and_up():
    obs = _make('CAMERA_AIM_UP')
    assert set(obs) == {"camera1", "camera1_aim", "camera1_up", "camera1_group"}, set(obs)
    cam, up = obs["camera1"], obs["camera1_up"]
    assert up.parent == obs["camera1_group"]
    assert _up_dir(cam).z > 0.99, "camera starts upright"
    # the up node to the side rolls the camera towards it
    up.location = Vector((5.0, 0.0, 0.0))
    bpy.context.view_layer.update()
    to_aim = (obs["camera1_aim"].matrix_world.translation - cam.matrix_world.translation).normalized()
    assert _view_dir(cam).angle(to_aim) < 1e-3
    roll = _up_dir(cam)
    assert roll.x > 0.5, roll
    assert math.degrees(roll.angle(Vector((0.0, 0.0, 1.0)))) > 30.0


def test_plain_camera_unchanged():
    obs = _make('CAMERA')
    assert set(obs) == {"camera1"}, set(obs)
    assert not obs["camera1"].constraints


lines = import_module(kit.MODULE + ".ui.camera_aim_lines")


def _segs():
    bpy.context.view_layer.update()
    return lines.segments(bpy.context.view_layer)


def _close(a, b):
    return (Vector(a) - Vector(b)).length < 1e-4


def test_aim_line_follows_the_rig():
    obs = _make('CAMERA_AIM')
    cam, aim, group = obs["camera1"], obs["camera1_aim"], obs["camera1_group"]
    for ob in obs.values():
        ob.select_set(False)
    segs = _segs()
    assert len(segs) == 1, segs
    p0, p1, col = segs[0]
    assert _close(p0, cam.matrix_world.translation) and _close(p1, aim.matrix_world.translation)
    assert col == lines.DORMANT
    # kept up to date as either end moves
    aim.location = Vector((3.0, 6.0, 2.0))
    cam.location = Vector((-1.0, 0.0, 1.0))
    (p0, p1, _), = _segs()
    assert _close(p0, (-1.0, 0.0, 1.0)) and _close(p1, (3.0, 6.0, 2.0)), (p0, p1)
    # the camera or the aim selected: still dark blue; the group selected: its selection colour
    cam.select_set(True)
    bpy.context.view_layer.objects.active = cam
    assert _segs()[0][2] == lines.DORMANT
    cam.select_set(False)
    group.select_set(True)
    bpy.context.view_layer.objects.active = group
    assert _segs()[0][2] == lines.LEAD
    bpy.context.view_layer.objects.active = aim
    assert _segs()[0][2] == lines.SELECTED
    # Display Connector off hides the line; a hidden aim draws no line
    assert group[lines.CONNECTOR] is True or group[lines.CONNECTOR] == 1
    group[lines.CONNECTOR] = False
    assert _segs() == []
    group[lines.CONNECTOR] = True
    aim.hide_set(True)
    assert _segs() == []


def test_up_line_and_plain_cameras():
    obs = _make('CAMERA_AIM_UP')
    segs = _segs()
    ends = sorted(round((p1 - p0).length, 4) for p0, p1, _ in segs)
    assert len(segs) == 2, segs
    up, aim = obs["camera1_up"], obs["camera1_aim"]
    targets = {tuple(round(v, 4) for v in p1) for _, p1, _ in segs}
    assert targets == {tuple(round(v, 4) for v in up.matrix_world.translation),
                       tuple(round(v, 4) for v in aim.matrix_world.translation)}, (targets, ends)
    # a plain camera or a user's own Track To (target outside the camera's group) draws nothing
    _make('CAMERA')
    cam = bpy.data.objects["camera1"]
    target = bpy.data.objects.new("target", None)
    bpy.context.scene.collection.objects.link(target)
    cam.constraints.new('TRACK_TO').target = target
    assert _segs() == []
