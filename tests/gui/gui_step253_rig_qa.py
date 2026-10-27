"""Step 253 (#169) rig QA: one Maya user's rigging session in the real UI, every stage checked against the Maya 2026
rules (research/maya/re/060_rig.md, 060_rig_lane.md) — Joint Tool (front view, 3 clicks) -> move the elbow (Edit, #156)
-> Orient Joint -> Mirror Joints (YZ) -> Create IK Handle (2 clicks) + Pole Vector -> Bind Skin -> Paint Skin Weights
(one stroke) -> Mirror Skin Weights -> S keys at frames 1 / 10 + Set IK/FK Key -> Ctrl+Z -> save + open.
Shots: gui_step253_<nn>_<stage>.png (the dogfood report reads them, docs/steps/step_253.md)."""

GUI_TIMEOUT = 420

import math
import os
import sys
import tempfile
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402
import maya2026_rig as rig  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
CLICKS = [(1, 10, 0), (5, 9, 0), (9, 10, 0)]        # Maya front view: shoulder, elbow (bent down), wrist


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, f"gui_step253_{name}.png"))


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def ov():
    area, region = main_view()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def k():
    return C["unit"]


def B(p):
    return rig.to_blender(p, k())


def screen_of(world):
    _a, r = main_view()
    p = view3d_utils.location_3d_to_region_2d(r, r.data, world)
    return int(round(r.x + p.x)), int(round(r.y + p.y))


def click_at(x, y):
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


def sk():
    return bpy.data.objects[C["rig"]]


def head(name):
    """A joint's world position (Blender), right in edit mode too (pose bones lag there)."""
    return rig.to_blender(rig.joint_world(sk(), name, k())[0], k())


def frame_of(name):
    return rig.joint_world(sk(), name, k())[1]


def key_tap(key, **mods):
    _a, r = main_view()
    x, y = r.x + r.width // 2, r.y + 40
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev(key, 'PRESS', x=x, y=y, **mods)
    ev(key, 'RELEASE', x=x, y=y, **mods)


# --- 1 Joint Tool ----------------------------------------------------------------------------------------------------

@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_front():
    for ob in list(bpy.data.objects):
        if ob.type in {'MESH', 'ARMATURE', 'EMPTY'} and not ob.get("allset_startup_camera"):
            bpy.data.objects.remove(ob)
    C["unit"] = mod(".operators.units").maya_unit()
    _a, r = main_view()
    rv3d = r.data
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = Euler((math.radians(90), 0, 0)).to_quaternion()
    rv3d.view_location = B((0, 8, 0))
    rv3d.view_distance = 30 * k()
    with ov():
        bpy.ops.allset.joint_tool('INVOKE_DEFAULT')


for _i, _p in enumerate(CLICKS):
    def _make(p):
        def s_click():
            click_at(*screen_of(B(p)))
        return s_click
    step(_make(_p))


@step
def s_enter():
    key_tap('RET')


@step
def s_created():
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    check(f"Joint Tool: one skeleton ({len(arms)})", len(arms) == 1)
    C["rig"] = arms[0].name
    names = [b.name for b in sk().data.bones]
    C["names"] = names
    check(f"three joints (the end joint is a bone too) ({names})", len(names) == 3)
    radii = [round(b.get("allset_radius", 0.0), 3) for b in sk().data.bones]
    want = 0.5 + (math.hypot(4, 1) - 1) / 29 * 1.5            # Maya variable bone radius (060_rig_lane.md A10)
    check(f"Maya joint radius r(4.12) = {want:.3f} ({radii})", all(abs(r - want) < 0.01 for r in radii))
    sk().data.show_axes = True
    shot("01_joint_tool")


# --- 2 move the elbow (#156: the parent keeps its Maya frame, 060_rig.md §1) -----------------------------------------

@step
def s_w():
    key_tap('W')                                   # Move tool on joints = Edit mode (step 241)


@step
def s_pick_elbow():
    C["f1_before"] = frame_of(C["names"][0])
    C["elbow0"] = head(C["names"][1]).copy()
    click_at(*screen_of(C["elbow0"]))


@step
def s_drag_press():
    x, y = screen_of(C["elbow0"])
    C["drag"] = (x, y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


for _j in range(1, 6):
    def _mv(j):
        def s_drag_move():
            x, y = C["drag"]
            ev('MOUSEMOVE', 'NOTHING', x=x, y=y - 4 * j)
        return s_drag_move
    step(_mv(_j))


@step
def s_drag_release():
    x, y = C["drag"]
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y - 20)


@step
def s_settle():
    pass                                           # the kit's 0.05 s frame watch (step 243) runs between ticks


@step
def s_moved():
    bpy.context.view_layer.update()
    d = (head(C["names"][1]) - C["elbow0"]) / k()
    check(f"W-drag moved the elbow ({d.length:.3f}, {tuple(round(c, 3) for c in d)})", d.length > 0.1)
    f0, f1 = C["f1_before"], frame_of(C["names"][0])
    d = max((f0.col[i] - f1.col[i]).length for i in range(3))
    check(f"moving a joint leaves the parent's Maya frame alone (060_rig.md §1) ({d:.1e})", d < 1e-4)
    shot("02_moved")


# --- 3 Orient Joint (aos rule, 060_rig.md §2) -------------------------------------------------------------------------

@step
def s_pick_root():
    C["mode_after_move"] = bpy.context.mode
    click_at(*screen_of(head(C["names"][0])))        # Maya: click joint1


@step
def s_orient():
    C["picked"] = mod(".operators.joints").selected_joint_names(sk())
    with ov():
        C["orient"] = bpy.ops.allset.menu_item(item="Skeleton/Orient Joint")


@step
def s_oriented():
    check(f"clicking joint1 picks it for the Skeleton menu ({C['mode_after_move']}, {C['picked']})",
          C["picked"] == [C["names"][0]])
    check(f"Skeleton > Orient Joint ({C['orient']})", C["orient"] == {'FINISHED'})
    p = [rig.to_maya(head(n), k()) for n in C["names"]]          # Maya coordinates, like frame_of
    f = frame_of(C["names"][0])
    aim = (p[1] - p[0]).normalized()
    # root: n = (P1 - P0) x (P2 - P0), kept when n . worldUp(Maya +Y = Blender +Z) >= 0
    # Maya's front-view clicks lie exactly in Maya Z = 0, so n . worldUp = 0 there and n is kept (strict < 0 flips);
    # the kit's clicks carry pixel noise, its TIE treats it as that 0 — compare with the exact-plane n, sign included
    q = [Vector((v.x, v.y, 0.0)) for v in p]
    n = (q[1] - q[0]).cross(q[2] - q[0]).normalized()
    check(f"joint1 Maya X at the elbow ({f.col[0].dot(aim):.5f})", f.col[0].dot(aim) > 0.9999)
    check(f"joint1 Maya Y = the bend normal n = (P1-P0) x (P2-P0), kept on the tie (Maya +Z here, mayapy "
          f"tmp/p253/oj_down.json) ({f.col[1].dot(n):.5f})", f.col[1].dot(n) > 0.9999)
    shot("03_oriented")


# --- 4 Mirror Joints across YZ (Maya factory XY; the arm mirrors across YZ) ------------------------------------------

@step
def s_mirror():
    with ov():
        C["mirror"] = bpy.ops.allset.mirror_joints(plane="YZ")


@step
def s_mirrored():
    ob = sk()
    names = [b.name for b in (ob.data.edit_bones if ob.mode == 'EDIT' else ob.data.bones)]     # edit bones lead
    check(f"Mirror Joints made the other arm ({C['mirror']}, {names})", len(names) == 2 * len(C["names"]))
    new = [n for n in names if n not in C["names"]]
    C["mirrored"] = new
    if new:
        e = max((head(m) - Vector((-head(o).x, head(o).y, head(o).z))).length for o, m in zip(C["names"], new)) / k()
        check(f"mirrored joints at -X ({e:.1e})", e < 1e-3)
    shot("04_mirrored")


# --- 5 IK handle + Pole Vector -----------------------------------------------------------------------------------------

@step
def s_ik_tool():
    with ov():
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.allset.menu_item(item="Skeleton/Create IK Handle")


@step
def s_ik_start():
    click_at(*screen_of(head(C["names"][0])))


@step
def s_ik_end():
    tail = sk().matrix_world @ sk().pose.bones[C["names"][1]].tail
    click_at(*screen_of(tail))


@step
def s_handle():
    h = bpy.data.objects.get("ikHandle1")
    check("Create IK Handle made ikHandle1", h is not None)
    if h is None:
        return
    C["h"] = h.name
    ik_rp = mod(".operators.ik_rp")
    pv = Vector([h[n] for n in ik_rp.PV])
    check(f"Maya default pole vector length 2 x jointDisplayScale ({pv.length:.4f})", abs(pv.length - 2.0) < 1e-3)
    loc = bpy.data.objects.new("poleLocator", None)
    bpy.context.scene.collection.objects.link(loc)
    loc.location = B((5, 5, -3))
    with ov():
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for ob in bpy.context.scene.objects:
            ob.select_set(ob in (loc, h))
        bpy.context.view_layer.objects.active = h
        C["pole"] = bpy.ops.allset.pole_vector()


@step
def s_pole():
    bpy.context.view_layer.update()
    h = bpy.data.objects[C["h"]]
    ik_rp = mod(".operators.ik_rp")
    pv = Vector([h[n] for n in ik_rp.PV])
    want = Vector((5, 5, -3)) - Vector(CLICKS[0])
    check(f"Pole Vector: pv = locator - start joint (Maya) ({tuple(round(c, 3) for c in pv)})",
          C["pole"] == {'FINISHED'} and (pv - want).length < 0.05)     # clicks land on whole pixels
    shot("05_ik_pole")


# --- 6 Bind Skin ---------------------------------------------------------------------------------------------------------

@step
def s_bind():
    me = bpy.data.meshes.new("pCylinder1")
    bm = bmesh.new()
    rings = []
    for i in range(21):                                  # Maya X -10 .. 10, around Maya Y = 9.3
        x = -10 + i
        ring = []
        for j in range(8):
            a = 2 * math.pi * j / 8
            ring.append(bm.verts.new(B((x, 9.3 + 0.8 * math.cos(a), 0.8 * math.sin(a)))))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for j in range(8):
            bm.faces.new((r0[j], r0[(j + 1) % 8], r1[(j + 1) % 8], r1[j]))
    bm.to_mesh(me)
    bm.free()
    cyl = bpy.data.objects.new("pCylinder1", me)
    bpy.context.scene.collection.objects.link(cyl)
    C["cyl"] = cyl.name
    with ov():
        for ob in bpy.context.scene.objects:
            ob.select_set(ob in (sk(), cyl))
        bpy.context.view_layer.objects.active = cyl
        C["bind"] = bpy.ops.allset.bind_skin()


@step
def s_bound():
    cyl = bpy.data.objects[C["cyl"]]
    groups = {g.index: g.name for g in cyl.vertex_groups}
    bones = set(b.name for b in sk().data.bones)
    worst_sum, most = 0.0, 0
    for v in cyl.data.vertices:
        ws = [g.weight for g in v.groups if groups.get(g.group) in bones and g.weight > 0]
        worst_sum = max(worst_sum, abs(sum(ws) - 1.0))
        most = max(most, len(ws))
    check(f"Bind Skin: every vertex sums to 1 ({worst_sum:.1e}), at most 5 influences ({most})",
          C["bind"] == {'FINISHED'} and worst_sum < 1e-4 and most <= 5)
    shot("06_bound")


# --- 7 Paint Skin Weights (one stroke on the +X elbow) ------------------------------------------------------------------

@step
def s_paint():
    cyl = bpy.data.objects[C["cyl"]]
    with ov():
        for ob in bpy.context.scene.objects:
            ob.select_set(ob == cyl)
        bpy.context.view_layer.objects.active = cyl
        bpy.ops.allset.paint_skin_weights()
    cyl.vertex_groups.active_index = cyl.vertex_groups[C["names"][0]].index
    C["stroke"] = [screen_of(B((x, 9.3, 0.8))) for x in (4.0, 4.5, 5.0, 5.5, 6.0)]
    x, y = C["stroke"][0]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_press():
    C["w_before"] = _weights(C["names"][0], 4.0, 6.0)
    x, y = C["stroke"][0]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_drag():
    for x, y in C["stroke"][1:]:
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_release():
    x, y = C["stroke"][-1]
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


def _weights(group, x0, x1, side=1):
    cyl = bpy.data.objects[C["cyl"]]
    g = cyl.vertex_groups.get(group)
    out = {}
    for v in cyl.data.vertices:
        mx = (v.co.x / k()) * side
        if x0 <= mx <= x1 and v.co.y < 0:
            out[v.index] = next((e.weight for e in v.groups if g is not None and e.group == g.index), 0.0)
    return out


@step
def s_painted():
    after = _weights(C["names"][0], 4.0, 6.0)
    up = sum(1 for i, w in after.items() if w > C["w_before"].get(i, 0.0) + 1e-3)
    check(f"one stroke raised joint1 on the elbow's front ({up} vertices)", up > 0)
    shot("07_painted")
    with ov():
        bpy.ops.object.mode_set(mode='OBJECT')
        cyl = bpy.data.objects[C["cyl"]]
        for ob in bpy.context.scene.objects:
            ob.select_set(ob == cyl)
        bpy.context.view_layer.objects.active = cyl
        C["mirror_w"] = bpy.ops.allset.mirror_skin_weights(plane="YZ", positive_to_negative=True)


# --- 8 Mirror Skin Weights ---------------------------------------------------------------------------------------------

@step
def s_mirror_weights():
    cyl = bpy.data.objects[C["cyl"]]
    pos = _weights(C["names"][0], 4.0, 6.0)
    neg = _weights(C["mirrored"][0], 4.0, 6.0, side=-1) if C.get("mirrored") else {}
    by_pos = {(round(cyl.data.vertices[i].co.x / k(), 3), round(cyl.data.vertices[i].co.y, 4),
               round(cyl.data.vertices[i].co.z, 4)): w for i, w in pos.items()}
    worst = 0.0
    for i, w in neg.items():
        co = cyl.data.vertices[i].co
        twin = by_pos.get((round(-co.x / k(), 3), round(co.y, 4), round(co.z, 4)))
        if twin is not None:
            worst = max(worst, abs(twin - w))
    check(f"Mirror Skin Weights +X -> -X: the mirrored joint's weights match ({C['mirror_w']}, {worst:.1e})",
          C["mirror_w"] == {'FINISHED'} and neg and worst < 1e-3)
    shot("08_mirror_weights")


# --- 9 keys: S at 1 and 10, Set IK/FK Key --------------------------------------------------------------------------------

@step
def s_key1():
    h = bpy.data.objects[C["h"]]
    with ov():
        for ob in bpy.context.scene.objects:
            ob.select_set(ob == h)
        bpy.context.view_layer.objects.active = h
    bpy.context.scene.frame_set(1)
    key_tap('S')


@step
def s_key10():
    h = bpy.data.objects[C["h"]]
    bpy.context.scene.frame_set(10)
    h.location = h.location + B((0, 1.5, 0))
    bpy.context.view_layer.update()
    key_tap('S')


@step
def s_ikfk():
    h = bpy.data.objects[C["h"]]
    fcs = {fc.data_path for fc in mod(".compat").id_fcurves(h)}
    loc = next((fc for fc in mod(".compat").id_fcurves(h) if fc.data_path == "location" and fc.array_index == 2), None)
    check(f"S keyed the handle at 1 and 10 ({sorted(fcs)})",
          loc is not None and [round(p.co.x) for p in loc.keyframe_points] == [1, 10])
    bpy.ops.ed.undo_push(message="keys")
    with ov():
        C["ikfk"] = bpy.ops.allset.menu_item(item="Key/IK/FK Keys/Set IK/FK Key")


@step
def s_ikfk_keys():
    h = bpy.data.objects[C["h"]]
    pole = bpy.data.objects["poleLocator"]
    paths = {fc.data_path for fc in mod(".compat").id_fcurves(h)}
    pole_paths = {fc.data_path for fc in mod(".compat").id_fcurves(pole)} if pole.animation_data else set()
    check(f"Set IK/FK Key keys Twist + Ik Blend on the handle and the pole locator (Maya R18) ({sorted(paths)}, "
          f"{sorted(pole_paths)})", '["twist"]' in paths and '["ikBlend"]' in paths and "location" in pole_paths)
    bpy.context.scene.frame_set(5)
    shot("09_keyed_f5")
    key_tap('Z', ctrl=True)


@step
def s_undone():
    pole = bpy.data.objects["poleLocator"]
    check("Ctrl+Z undoes Set IK/FK Key (the pole locator has no keys again)",
          pole.animation_data is None or not list(mod(".compat").id_fcurves(pole)))
    path = os.path.join(tempfile.gettempdir(), "gui_step253_rig.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    bpy.ops.wm.open_mainfile(filepath=path)


@step
def s_reopened():
    h = bpy.data.objects.get("ikHandle1")
    cyl = bpy.data.objects.get("pCylinder1")
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    check("after open: skeleton, handle, skinned cylinder", h is not None and cyl is not None and len(arms) == 1
          and any(m.type == 'ARMATURE' for m in cyl.modifiers))
    bpy.context.scene.frame_set(10)
    shot("10_reopened_f10")


run()
