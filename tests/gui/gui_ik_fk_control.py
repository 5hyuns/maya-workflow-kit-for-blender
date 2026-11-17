"""Maya IK / FK in a real UI: rotating a joint of an IK chain with Blender's rotate (R) in Pose mode turns the joint
and the IK handle follows the end joint while the mouse moves (Enable IK Handle Snap, IK/FK control off); the arm
then settles (no endless updates); one undo takes back the turn and the handle move together. The Skeleton menu's
Enable IK/FK Control check greys out Enable IK Handle Snap."""

import os
import sys
from importlib import import_module

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

C = {}


def mod(name):
    return import_module(MODULE + name)


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def ov():
    area, region = main_view()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def screen_of(world):
    _a, r = main_view()
    p = view3d_utils.location_3d_to_region_2d(r, r.data, world)
    return int(r.x + p.x), int(r.y + p.y)


def arm():
    return bpy.data.objects[C["arm"]]


def handle():
    return bpy.data.objects[C["handle"]]


def con():
    return arm().pose.bones["elbow"].constraints[0]


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    units, skin = mod(".operators.units"), mod(".operators.skin")
    k = units.maya_unit()
    pts = [Vector((0, 0, 0)), Vector((4, 1, 0)), Vector((8, 0, 0))]
    with ov():
        ob = bpy.data.objects.new("skeleton1", bpy.data.armatures.new("skeleton1"))
        bpy.context.scene.collection.objects.link(ob)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode='EDIT')
        prev = None
        for name, a, b in (("shoulder", pts[0], pts[1]), ("elbow", pts[1], pts[2]),
                           ("wrist", pts[2], pts[2] + Vector((1, 0, 0)))):
            eb = ob.data.edit_bones.new(name)
            eb.head, eb.tail = a * k, b * k
            if prev is not None:
                eb.parent, eb.use_connect = prev, True
            prev = eb
        bpy.ops.object.mode_set(mode='OBJECT')
        h = skin.create_ik(bpy.context, ob, ("shoulder", 'HEAD'), ("wrist", 'HEAD'))
        h.location = Vector((6, 0, 2)) * k
    C["arm"], C["handle"], C["k"] = ob.name, h.name, k
    ctl = mod(".operators.ik_fk_control")
    ctl._STATE["control"], ctl._STATE["snap"] = False, True
    ctl.forget()
    with ov():
        bpy.ops.view3d.view_all()


@step
def s_pose():
    ob = arm()
    with ov():
        for o in bpy.context.selected_objects:
            o.select_set(False)
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode='POSE')
        cb_nodes = mod(".ui.cb_nodes")
        for pb in ob.pose.bones:
            cb_nodes.set_bone_selected(pb, pb.name == "shoulder")
        ob.data.bones.active = ob.data.bones["shoulder"]
        bpy.ops.ed.undo_push(message="before turn")
    C["h0"] = handle().matrix_world.translation.copy()
    C["rot0"] = tuple(ob.pose.bones["shoulder"].rotation_quaternion)


@step
def s_start():
    x, y = screen_of(arm().matrix_world @ arm().pose.bones["elbow"].head)
    C["drag"] = (x + 120, y)
    ev('MOUSEMOVE', 'NOTHING', x=x + 120, y=y)
    with ov():
        bpy.ops.transform.rotate('INVOKE_DEFAULT')


for _i in range(1, 5):
    def s_move(i=_i):
        x, y = C["drag"]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y + 25 * i)
    s_move.__name__ = f"s_move{_i}"
    step(s_move)


@step
def s_during():
    moved = (handle().matrix_world.translation - C["h0"]).length
    check(f"the handle follows the end joint while the joint turns ({moved:.3f})", moved > 0.05 * C["k"])


@step
def s_confirm():
    x, y = C["drag"]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y + 100)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y + 100)


@step
def s_after():
    ik_fk = mod(".operators.ik_fk")
    ob = arm()
    end = ik_fk.fk_end(ob, ob.pose.bones["elbow"], con())
    wrist = ob.matrix_world @ ob.pose.bones["wrist"].head
    turned = Vector(ob.pose.bones["shoulder"].rotation_quaternion).dot(Vector(C["rot0"]))
    check(f"the shoulder kept its turn ({turned:.4f})", abs(turned) < 0.9999)
    check(f"the handle sits on the FK end joint ({tuple(handle().matrix_world.translation)} / {tuple(end)})",
          (handle().matrix_world.translation - end).length < 1e-3 * C["k"])
    check(f"the wrist is where the turned chain puts it ({tuple(wrist)} / {tuple(end)})",
          (wrist - end).length < 1e-2 * C["k"])
    ctl = mod(".operators.ik_fk_control")
    C["writes"] = [0]
    real = ctl._set_channels

    def counting(pb, values):
        C["writes"][0] += 1
        real(pb, values)
    ctl._set_channels = counting
    C["real"] = real


@step
def s_idle1():
    ev('MOUSEMOVE', 'NOTHING', x=C["drag"][0] + 3, y=C["drag"][1])


@step
def s_idle2():
    ev('MOUSEMOVE', 'NOTHING', x=C["drag"][0], y=C["drag"][1] + 3)


@step
def s_settled():
    ctl = mod(".operators.ik_fk_control")
    ctl._set_channels = C["real"]
    check(f"the arm settles: no channel writes while idle ({C['writes'][0]})", C["writes"][0] == 0)
    with ov():
        bpy.ops.ed.undo()


@step
def s_undone():
    back = (handle().matrix_world.translation - C["h0"]).length
    rot = Vector(arm().pose.bones["shoulder"].rotation_quaternion).dot(Vector(C["rot0"]))
    check(f"one undo takes back the turn and the handle move ({back:.5f}, {rot:.5f})",
          back < 1e-4 * C["k"] and abs(rot) > 0.99999)


@step
def s_menu_grey():
    draw = mod(".ui.menu_item_draw")
    menu_map = mod(".ui.menu_map")
    wm = bpy.context.window_manager
    s = menu_map.normalize(menu_map.MAP["Skeleton/Enable IK Handle Snap"])
    got = {}

    class L:
        enabled = True

        def row(self):
            r = L()
            got["row"] = r
            return r

        def prop(self, owner, attr, **kw):
            got["enabled"] = self.enabled

    wm.allset_ik_fk_control = True
    draw.draw_prop(L(), "Enable IK Handle Snap", s[1], s[2], "Skeleton/Enable IK Handle Snap")
    wm.allset_ik_fk_control = False
    check(f"Enable IK Handle Snap is greyed while IK/FK control is on ({got})", got.get("enabled") is False)


run()
