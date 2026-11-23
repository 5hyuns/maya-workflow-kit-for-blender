"""Issue #344 follow-up: the Time Slider shows the picked joints' keys as they are now after the rig's data is
replaced around playback: a key set while playing, undo (which stops playback) and redo, the rig deleted and a new one
made while playing, the file reverted while playing, and a held scrub after them. Each time the Time Slider redraws
and Blender stays up."""

import os
import sys
import tempfile
from importlib import import_module

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

C = {}


def mod(name):
    return import_module(MODULE + name)


def main_view():
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D']
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def ov():
    area, region = main_view()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def redraw_time_slider():
    for a in win().screen.areas:
        if a.type == 'DOPESHEET_EDITOR':
            a.tag_redraw()


def make_rig(name, keys):
    """A 4-joint skeleton keyed on its joints' rotation at ``keys``, in Pose Mode with every joint picked."""
    if bpy.context.mode != 'OBJECT':
        with ov():
            bpy.ops.object.mode_set(mode='OBJECT')
    arm = bpy.data.objects.new(name, bpy.data.armatures.new(name))
    bpy.context.scene.collection.objects.link(arm)
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    with ov():
        bpy.ops.object.mode_set(mode='EDIT')
        prev = None
        for i in range(4):
            eb = arm.data.edit_bones.new(f"j{i}")
            eb.head, eb.tail = Vector((0, 0, i)), Vector((0, 0, i + 1))
            eb.parent = prev
            prev = eb
        bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        for f in keys:
            pb.rotation_euler.x = f * 0.01
            pb.keyframe_insert("rotation_euler", frame=f)
    cb = mod(".ui.channel_box")
    for pb in arm.pose.bones:
        cb.set_bone_selected(pb, True)
    arm.data.bones.active = arm.data.bones["j3"]
    return arm


def timeline():
    for area in win().screen.areas:
        if area.type == 'DOPESHEET_EDITOR' and area.spaces.active.mode == 'TIMELINE':
            return area, next(r for r in area.regions if r.type == 'WINDOW')
    raise LookupError("no Time Slider")


def tx(frame):
    _area, r = timeline()
    return r.x + int(r.view2d.view_to_region(frame, 0, clip=False)[0]), r.y + r.height // 2


def scrub(name, want, frames=(3, 12, 18, 8)):
    """Steps: press on the Time Slider, drag over ``frames`` (the Time Slider redraws while the scrub is held),
    release; checks the keys the held scrub shows."""
    def s_press():
        x, y = tx(frames[0])
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    s_press.__name__ = f"s_{name}_press"
    step(s_press)
    for k, f in enumerate(frames[1:]):
        def s_move(f=f):
            x, y = tx(f)
            ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
            redraw_time_slider()
        s_move.__name__ = f"s_{name}_move{k}"
        step(s_move)

    def s_release():
        held = list(mod(".ui.time_slider")._HELD.values())
        scrubbing = mod(".ui.maya_joints").scrubbing()
        frames_held = [[f for f, _bd in h] for h in held]
        check(f"{name}: a held scrub shows the joints' keys (scrubbing {scrubbing}, {frames_held})",
              scrubbing and frames_held and all(h == want for h in frames_held))
        x, y = tx(frames[-1])
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
        redraw_time_slider()
    s_release.__name__ = f"s_{name}_release"
    step(s_release)


def shown():
    ts = mod(".ui.time_slider")
    return [f for f, _bd in ts.key_frames(ts.tick_nodes(bpy.context), True)]


def play():
    with ov():
        bpy.ops.screen.animation_play()
    redraw_time_slider()


def stop():
    if win().screen.is_animation_playing:
        with ov():
            bpy.ops.screen.animation_cancel(restore_frame=False)


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_rig():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 40
    make_rig("rigA", (1, 10, 20))
    bpy.ops.ed.undo_push(message="rig")
    play()


@step
def s_playing_cached():
    ts = mod(".ui.time_slider")
    check(f"playing: the Time Slider read the picked joints' keys ({len(ts._bone_curves)} joints kept)",
          win().screen.is_animation_playing and len(ts._bone_curves) >= 4)
    arm = bpy.data.objects["rigA"]
    for pb in arm.pose.bones:
        pb.keyframe_insert("rotation_euler", frame=30)
    bpy.ops.ed.undo_push(message="key 30")
    redraw_time_slider()


@step
def s_keyed():
    check(f"a key set while playing shows ({shown()})", shown() == [1.0, 10.0, 20.0, 30.0])
    with ov():
        bpy.ops.ed.undo()
    redraw_time_slider()


@step
def s_undone():
    check(f"undo (it stops playback): the key is gone ({shown()})", shown() == [1.0, 10.0, 20.0])
    with ov():
        bpy.ops.ed.redo()
    redraw_time_slider()


@step
def s_redone():
    check(f"redo: the key is back ({shown()})", shown() == [1.0, 10.0, 20.0, 30.0])
    play()


@step
def s_replay():
    check("playing again", win().screen.is_animation_playing)
    arm = bpy.data.objects["rigA"]
    with ov():
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects.remove(arm)
    make_rig("rigB", (5, 15))
    redraw_time_slider()


@step
def s_new_rig():
    check(f"rig deleted and a new one made while playing: its keys show ({shown()})",
          win().screen.is_animation_playing and shown() == [5.0, 15.0])
    stop()


scrub("new rig", [5.0, 15.0])


@step
def s_save():
    path = os.path.join(tempfile.gettempdir(), "allset_gui_issue344_bone_keys.blend")
    C["path"] = path
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=False)
    arm = bpy.data.objects["rigB"]
    for pb in arm.pose.bones:
        pb.keyframe_insert("rotation_euler", frame=25)
    play()


@step
def s_before_revert():
    check(f"playing again with a new key ({shown()})", shown() == [5.0, 15.0, 25.0])
    bpy.ops.wm.revert_mainfile()


@step
def s_reverted():
    ob = bpy.data.objects.get("rigB")
    if ob is not None and bpy.context.view_layer.objects.active is ob and ob.mode == 'POSE':
        play()
        redraw_time_slider()
    check(f"file reverted: the saved keys ({shown() if ob is not None else None})",
          ob is not None and shown() == [5.0, 15.0])


@step
def s_stop_after_revert():
    stop()
    redraw_time_slider()


scrub("reverted file", [5.0, 15.0])


@step
def s_end():
    stop()
    check("Blender is still running after all of it", True)
    try:
        os.remove(C["path"])
    except (OSError, KeyError):
        pass


run()
