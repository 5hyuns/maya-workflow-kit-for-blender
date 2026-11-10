"""#347 in a real UI: a kit cube with a keyed "smile" shape key and keyed translate X, at frame 6. A real Ctrl+D over
the 3D View (Maya Edit > Duplicate) makes pCube2 with the shape the cube shows now, without shape keys, keys or
drivers, translate X at its current value. Editing the original's keys afterwards moves the original only. One Ctrl+Z
takes the duplicate back and leaves the original with its animation. Screenshot with ALLSET_GUI_SHOTS (or --shots)."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
SMILE = 'key_blocks["smile"].value'


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def v3d_ctx():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def fcurves(idb):
    return import_module(MODULE + ".compat").id_fcurve_collection(idb)


def points(name):
    ob = bpy.data.objects[name]
    with v3d_ctx():
        ev_ob = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        return [ev_ob.matrix_world @ v.co for v in ev_ob.data.vertices]


def same(a, b, eps=1e-4):
    return len(a) == len(b) and all((p - q).length < eps for p, q in zip(a, b))


def animated(idb):
    ad = getattr(idb, "animation_data", None)
    return ad is not None and (ad.action is not None or len(ad.drivers) > 0 or len(ad.nla_tracks) > 0)


def set_last_key(idb, path, value, index=0):
    fc = fcurves(idb).find(path, index=index)
    k = fc.keyframe_points[-1]
    k.co.y = k.handle_left.y = k.handle_right.y = value
    fc.update()


@step
def s_setup():
    C["x"], C["y"] = setup()
    load_maya_layout()


@step
def s_build():
    bpy.ops.allset.keymap_activate()
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 24
    with v3d_ctx():
        bpy.ops.allset.create(kind='CUBE')
        ob = bpy.context.view_layer.objects.active
        C["name"] = ob.name
        ob.shape_key_add(name="Basis")
        sk = ob.shape_key_add(name="smile", from_mix=False)
        for v in sk.data:
            if v.co.z > 0:
                v.co.z += ob.dimensions.z
        keys = ob.data.shape_keys
        sk.value = 0.0
        keys.keyframe_insert(SMILE, frame=1)
        sk.value = 1.0
        keys.keyframe_insert(SMILE, frame=11)
        ob.location.x = 0.0
        ob.keyframe_insert("location", index=0, frame=1)
        ob.location.x = 0.1
        ob.keyframe_insert("location", index=0, frame=11)
        sc.frame_set(6)
        for o in bpy.context.view_layer.objects:
            o.select_set(o is ob)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.view3d.view_selected()
        bpy.ops.ed.undo_push(message="keyed cube")        # Ctrl+Z later comes back here
    C["n"] = len(bpy.data.objects)
    C["shown"] = points(C["name"])
    C["x0"] = bpy.data.objects[C["name"]].location.x
    check(f"keyed, shape-keyed {C['name']} at frame 6 (translate X {C['x0']:.4f})",
          C["name"] == "pCube1" and abs(C["x0"] - 0.05) < 1e-6 and animated(keys))
    redraw()


@step
def s_hover():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])


@step
def s_ctrl_d():
    ev('D', 'PRESS', ctrl=True)
    ev('D', 'RELEASE', ctrl=True)


@step
def s_copied():
    redraw()
    copy = bpy.data.objects.get("pCube2")
    ok = copy is not None
    check(f"Ctrl+D made pCube2 ({[o.name for o in bpy.data.objects]})", ok and len(bpy.data.objects) == C["n"] + 1)
    check("the copy is selected and active", ok and copy.select_get() and bpy.context.view_layer.objects.active == copy)
    check("the copy has no keys and no drivers", ok and not animated(copy) and not animated(copy.data))
    check("the copy has no shape keys (no blend shape)", ok and copy.data.shape_keys is None)
    check(f"translate X keeps its current value ({copy.location.x if ok else None})",
          ok and abs(copy.location.x - C["x0"]) < 1e-6)
    check("the copy shows the shape the cube shows now", ok and same(points("pCube2"), C["shown"]))
    orig = bpy.data.objects[C["name"]]
    check("the original keeps its shape keys and keys",
          orig.data.shape_keys is not None and animated(orig) and animated(orig.data.shape_keys))
    shot("gui_issue347_copy.png")


@step
def s_edit_original():
    orig = bpy.data.objects[C["name"]]
    set_last_key(orig, "location", 0.3)
    set_last_key(orig.data.shape_keys, SMILE, 0.25)
    bpy.context.scene.frame_set(11)
    redraw()


@step
def s_edited():
    orig = bpy.data.objects[C["name"]]
    copy = bpy.data.objects["pCube2"]
    check(f"the original follows its edited keys (translate X {orig.location.x:.4f})",
          abs(orig.location.x - 0.3) < 1e-6)
    check(f"the copy stays (translate X {copy.location.x:.4f})", abs(copy.location.x - C["x0"]) < 1e-6)
    check("the copy keeps its shape", same(points("pCube2"), C["shown"]))
    shot("gui_issue347_edited.png")
    bpy.context.scene.frame_set(6)
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])


@step
def s_undo():
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_undone():
    redraw()
    orig = bpy.data.objects.get(C["name"])
    check(f"one Ctrl+Z takes the duplicate back ({[o.name for o in bpy.data.objects]})",
          "pCube2" not in bpy.data.objects and len(bpy.data.objects) == C["n"])
    check("the original still has its shape keys and keys",
          orig is not None and orig.data.shape_keys is not None and animated(orig) and animated(orig.data.shape_keys))


@step
def s_options():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    with bpy.context.temp_override(window=win()):
        res = bpy.ops.allset.opt_duplicate_special_maya('INVOKE_DEFAULT')
    check("Duplicate Special Options opens", res == {'RUNNING_MODAL'})


@step
def s_options_wait():
    pass


@step
def s_options_shot():
    shot("gui_issue347_options.png")
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')
    check("done", True)


run()
