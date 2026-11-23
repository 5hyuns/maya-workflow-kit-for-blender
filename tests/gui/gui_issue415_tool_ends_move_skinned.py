"""Issue #415 (report @cnzim): picking another tool ends Skin > Move Skinned Joints, like Maya.

Move Skinned Joints on (joints in Edit Mode) -> W (even with the Move tool already active) / E / a toolbar tool = back
to Pose with that tool; a Blender tool only Edit Mode has (Roll) keeps it on; the one-tool carry after entering it
keeps it on; a click away leaves it on in Object Mode and Q then ends it (the next joint pick poses)."""

import os
import sys
from importlib import import_module

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, tap, win  # noqa: E402

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


def at(f, g):
    _a, r = main_view()
    return r.x + int(r.width * f), r.y + int(r.height * g)


def rig():
    return bpy.data.objects[C["rig"]]


def tool_id():
    with ov():
        return bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname


def on():
    return bool(rig().get(mod(".operators.joint_selection").MOVE_SKINNED))


def msj():
    with ov():
        bpy.ops.allset.menu_item(item="Skin/Move Skinned Joints")


def park():
    x, y = at(0.5, 0.85)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_rig():
    for ob in list(bpy.data.objects):
        if ob.type in {'MESH', 'ARMATURE'}:
            bpy.data.objects.remove(ob)
    arm_data = bpy.data.armatures.new("skel")
    arm = bpy.data.objects.new("skel", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    with ov():
        bpy.ops.object.mode_set(mode='EDIT')
        prev = None
        for i in range(3):
            eb = arm_data.edit_bones.new(f"joint{i + 1}")
            eb.head, eb.tail = Vector((0, 0, i)), Vector((0, 0, i + 1))
            if prev is not None:
                eb.parent, eb.use_connect = prev, True
            prev = eb
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=3, location=(0, 0, 1.5))
    mesh = bpy.context.active_object
    mesh.modifiers.new("Armature", 'ARMATURE').object = arm
    C["rig"], C["mesh"] = arm.name, mesh.name
    mesh.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    with ov():
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
    msj()


@step
def s_carry_keeps():
    # the Rotate tool carried into Edit Mode after entering it is set by the kit, not picked: still on
    check(f"Move Skinned Joints on = Edit Mode ({rig().mode}, on {on()})", rig().mode == 'EDIT' and on())
    park()


@step
def s_carry_checked():
    check(f"the tool carried into Edit Mode keeps it on ({rig().mode}, {tool_id()})", rig().mode == 'EDIT' and on())
    with ov():
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
    # the Move tool picked (toolbar / menu) while on ends it
    check(f"picking the Move tool ends it: Pose ({rig().mode}, on {on()}, {tool_id()})",
          rig().mode == 'POSE' and not on() and tool_id() == "builtin.move")
    msj()


@step
def s_w_again():
    with ov(), mod(".operators.joint_selection").kit_tool_set():
        bpy.ops.wm.tool_set_by_id(name="builtin.move")      # the Move tool carried into Edit Mode
    check(f"on again with the Move tool active ({rig().mode})", rig().mode == 'EDIT' and on()
          and tool_id() == "builtin.move")
    park()
    tap('W')


@step
def s_w_ended():
    check(f"W ends it even with the Move tool active: Pose ({rig().mode}, on {on()}, {tool_id()})",
          rig().mode == 'POSE' and not on() and tool_id() == "builtin.move")
    msj()


@step
def s_e():
    check(f"on again ({rig().mode})", rig().mode == 'EDIT' and on())
    park()
    tap('E')


@step
def s_e_ended():
    check(f"E ends it: Pose with the Rotate tool ({rig().mode}, on {on()}, {tool_id()})",
          rig().mode == 'POSE' and not on() and tool_id() == "builtin.rotate")
    msj()


@step
def s_roll():
    check(f"on again ({rig().mode})", rig().mode == 'EDIT' and on())
    with ov():
        bpy.ops.wm.tool_set_by_id(name="builtin.roll")
    check(f"an Edit-Mode-only Blender tool (Roll) keeps it on ({rig().mode}, on {on()}, {tool_id()})",
          rig().mode == 'EDIT' and on() and tool_id() == "builtin.roll")
    with ov():
        bpy.ops.object.mode_set(mode='OBJECT')       # what a click away does: Object Mode, still on
    check(f"Object Mode keeps it on ({rig().mode}, on {on()})", rig().mode == 'OBJECT' and on())
    park()
    tap('Q')


@step
def s_q_ended():
    check(f"Q in Object Mode ends it ({on()}, {tool_id()})", not on() and tool_id() == "builtin.select_box")
    js = mod(".operators.joint_selection")
    check(f"the skinned joints pose again ({js.joint_mode(rig())})", js.joint_mode(rig()) == 'POSE')


run()
