"""In a real UI, like Maya: Delete or Backspace deletes the selected object even while a Time Slider range is
highlighted or a key frame was just clicked, with the mouse over the Time Slider or over the viewport; with a face
selected it deletes the face. The keys stay (the range's keys are removed from the Time Slider's right-click menu)."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, view3d, win, load_maya_layout  # noqa: E402

KEYS = ((1, 0.0), (5, 1.0), (10, 2.0), (15, 3.0), (20, 4.0))


def timeline():
    for area in win().screen.areas:
        if area.type == 'DOPESHEET_EDITOR' and area.spaces.active.mode == 'TIMELINE':
            return area, next(r for r in area.regions if r.type == 'WINDOW')
    raise LookupError("no timeline")


def tx(frame):
    _area, r = timeline()
    return r.x + int(r.view2d.view_to_region(frame, 0, clip=False)[0]), r.y + r.height // 2


def vx():
    _area, r = view3d()
    return r.x + r.width // 2, r.y + r.height // 2


def wm():
    return bpy.context.window_manager


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def scene(face=False):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    ob = bpy.context.active_object
    ob.name = "Cube"
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 24
    for f, v in KEYS:
        ob.location.x = v
        ob.keyframe_insert("location", index=0, frame=f)
    sc.frame_set(1)
    for o in bpy.context.view_layer.objects:
        o.select_set(o is ob)
    bpy.context.view_layer.objects.active = ob
    wm().allset_time_range_on = False
    area, r = timeline()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        bpy.ops.anim.scene_range_frame()
    if face:
        import bmesh
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        bm = bmesh.from_edit_mesh(ob.data)
        for f in bm.faces:
            f.select_set(f.index == 1)
        bmesh.update_edit_mesh(ob.data)
    bpy.ops.ed.undo_push(message="keys")
    redraw()


def faces():
    ob = bpy.data.objects.get("Cube")
    if ob is None:
        return None
    if ob.mode == 'EDIT':
        import bmesh
        return len(bmesh.from_edit_mesh(ob.data).faces)
    return len(ob.data.polygons)


def keys():
    ob = bpy.data.objects.get("Cube")
    if ob is None:
        return None
    fcs = import_module(MODULE + ".ui.channel_box")._fcurves(ob)
    fc = fcs.find("location", index=0) if fcs is not None else None
    return [round(k.co.x) for k in fc.keyframe_points] if fc is not None else []


def shift_drag(f0, f1):
    def s1():
        ev('LEFT_SHIFT', 'PRESS')
        ev('MOUSEMOVE', 'NOTHING', x=tx(f0)[0], y=tx(f0)[1], shift=True)

    def s2():
        ev('LEFTMOUSE', 'PRESS', shift=True)

    def s3():
        ev('MOUSEMOVE', 'NOTHING', x=(tx(f0)[0] + tx(f1)[0]) // 2, y=tx(f0)[1], shift=True)

    def s4():
        ev('MOUSEMOVE', 'NOTHING', x=tx(f1)[0], y=tx(f1)[1], shift=True)

    def s5():
        ev('LEFTMOUSE', 'RELEASE', shift=True)
        ev('LEFT_SHIFT', 'RELEASE')
    for s in (s1, s2, s3, s4, s5):
        step(s)


def click(frame):
    def s1():
        ev('MOUSEMOVE', 'NOTHING', x=tx(frame)[0], y=tx(frame)[1])

    def s2():
        ev('LEFTMOUSE', 'PRESS')

    def s3():
        ev('LEFTMOUSE', 'RELEASE')
    for s in (s1, s2, s3):
        step(s)


def case(name, pick, where, key, face=False):
    step(lambda: scene(face))
    if pick == "range":
        shift_drag(4, 12)

        @step
        def s_range():
            check(f"{name}: Shift-drag highlights a range ({tuple(wm().allset_time_range)})",
                  wm().allset_time_range_on and tuple(sorted(wm().allset_time_range)) == (4, 12))
    else:
        click(5)

        @step
        def s_frame():
            check(f"{name}: the click sets frame 5 ({bpy.context.scene.frame_current})",
                  bpy.context.scene.frame_current == 5)

    @step
    def s_move():
        x, y = tx(12) if where == "slider" else vx()
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)

    @step
    def s_key():
        ev(key, 'PRESS')
        ev(key, 'RELEASE')

    @step
    def s_check():
        if face:
            check(f"{name}: one face deleted, keys kept ({faces()} faces, keys {keys()})",
                  faces() == 5 and keys() == [f for f, _v in KEYS])
            return
        check(f"{name}: the cube is deleted ({'gone' if 'Cube' not in bpy.data.objects else keys()})",
              "Cube" not in bpy.data.objects)

    @step
    def s_undo():
        ev('Z', 'PRESS', ctrl=True)
        ev('Z', 'RELEASE', ctrl=True)

    @step
    def s_undo_check():
        check(f"{name}: one Ctrl+Z brings it back with its keys ({keys()}, {faces()} faces)",
              keys() == [f for f, _v in KEYS] and faces() == 6)


@step
def s_setup():
    setup()
    load_maya_layout()
    bpy.ops.allset.keymap_activate()


for _pick in ("range", "key"):
    for _where in ("slider", "view"):
        case(f"{_pick} + Delete over the {_where}", _pick, _where, 'DEL')
case("range + Backspace over the slider", "range", "slider", 'BACK_SPACE')
case("face + range + Delete over the slider", "range", "slider", 'DEL', face=True)
case("face + key + Backspace over the slider", "key", "slider", 'BACK_SPACE', face=True)


run()
