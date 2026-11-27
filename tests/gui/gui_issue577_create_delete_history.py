"""#577 Interactive Creation while it waits for the height drag (Maya keeps the primitive out of the scene until its
last step): Delete History (Alt+Shift+D) leaves the cube being drawn alone, so the height drag that follows still sizes
it; picking another tool (Q, W) finishes it as a height click would (flat, scale 0 along the drawing plane's normal) and
keeps that tool."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, win  # noqa: E402

C = {}


def mod(name):
    return import_module(MODULE + name)


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def at(f, g):
    _a, r = main_view()
    return r.x + int(r.width * f), r.y + int(r.height * g)


def running():
    """A primitive is being drawn (the tool's press modal runs)."""
    return any(op.bl_idname == "ALLSET_OT_interactive_create" for op in win().modal_operators)


TOOL = "allset.interactive_create_tool"


def tool():
    t = win().workspace.tools.from_space_view3d_mode('OBJECT', create=False)
    return t.idname if t else None


def key(k):
    x, y = at(0.5, 0.5)
    ev(k, 'PRESS', x=x, y=y)
    ev(k, 'RELEASE', x=x, y=y)


def start(kind):
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind=kind)


def prefs():
    return mod(".preferences").get()


def new_objects():
    return [o for o in bpy.data.objects if o.name not in C["before"]]


def world_z(ob):
    zs = [(ob.matrix_world @ v.co).z for v in ob.data.vertices]
    return min(zs), max(zs)


def node(ob):
    return mod(".operators.prim_history").node_of(ob)[1]


def mark():
    C["before"] = {o.name for o in bpy.data.objects}


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    area, region = main_view()
    rv3d = region.data
    rv3d.view_perspective = 'PERSP'
    # look down at the grid from the front and above, the origin in the middle of the view
    from mathutils import Euler
    rv3d.view_rotation = Euler((1.0, 0.0, 0.0)).to_quaternion()
    rv3d.view_location = (0.0, 0.0, 0.0)
    rv3d.view_distance = 30.0 * mod(".operators.units").maya_unit(bpy.context.scene)
    prefs().interactive_creation = True
    prefs().exit_on_completion = True
    mark()


@step
def s_cube_start():
    start('CUBE')


@step
def s_cube_running():
    check(f"the creation tool is current and waits for a drag ({tool()})", tool() == TOOL and not running()
          and not new_objects())
    ev('MOUSEMOVE', 'NOTHING', x=at(0.45, 0.45)[0], y=at(0.45, 0.45)[1])


@step
def s_base_press():
    x, y = at(0.45, 0.45)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_base_drag1():
    x, y = at(0.50, 0.40)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_base_drag2():
    x, y = at(0.55, 0.35)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_base_release():
    x, y = at(0.55, 0.35)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_base_done():
    obs = new_objects()
    check(f"one primitive while drawing ({[o.name for o in obs]})", len(obs) == 1)
    ob = obs[0]
    C["cube"] = ob.name
    a = node(ob)["attrs"]
    check(f"the base has a width and depth ({a['width']:.3f} x {a['depth']:.3f})", a["width"] > 0.5 and a["depth"] > 0.5)
    check(f"the height starts flat ({a['height']:.4f})", a["height"] < 1e-3)
    check("the primitive is still being drawn for the height", running() and tool() == TOOL)



def node_attrs():
    n = mod(".operators.prim_history").node_of(bpy.data.objects[C["cube"]])
    return n[1]["attrs"] if n and n[1] else None


@step
def s_dh_key():
    x, y = at(0.5, 0.5)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('D', 'PRESS', x=x, y=y, shift=True, alt=True)
    ev('D', 'RELEASE', x=x, y=y, shift=True, alt=True)


@step
def s_after_dh():
    check(f"Alt+Shift+D keeps the creation node of the cube being drawn ({node_attrs() is not None})",
          node_attrs() is not None)
    check("... and the cube still waits for its height", running() and tool() == TOOL)
    x, y = at(0.55, 0.35)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_h1():
    x, y = at(0.55, 0.45)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_h2():
    x, y = at(0.55, 0.55)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_h3():
    x, y = at(0.55, 0.55)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_height_check():
    ob = bpy.data.objects[C["cube"]]
    a = node_attrs()
    h = a["height"] if a else None
    check(f"the height drag after it sizes the cube (height {h}, dims z {ob.dimensions.z:.3f})",
          a is not None and a["height"] > 0.5 and ob.dimensions.z > 0.5 and tuple(ob.scale) == (1.0, 1.0, 1.0))
    check(f"the cube is finished ({tool()})", not running())
    mark()


def base_then(key_name, name):
    step(lambda: start('CUBE'))

    def s_move():
        ev('MOUSEMOVE', 'NOTHING', x=at(0.45, 0.45)[0], y=at(0.45, 0.45)[1])

    def s_press():
        x, y = at(0.45, 0.45)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)

    def s_d1():
        x, y = at(0.50, 0.40)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)

    def s_d2():
        x, y = at(0.55, 0.35)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)

    def s_release():
        x, y = at(0.55, 0.35)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)

    def s_key():
        check(f"{key_name}: a cube waits for its height", len(new_objects()) == 1 and running())
        C[name] = new_objects()[0].name if new_objects() else ""
        key(key_name)

    def s_check():
        ob = bpy.data.objects.get(C[name])
        check(f"{key_name} during the height wait keeps the cube, flat ({ob and tuple(ob.scale)})",
              ob is not None and ob.scale.z == 0.0 and ob.scale.x == 1.0 and ob.scale.y == 1.0)
        a = mod(".operators.prim_history").node_of(ob)[1]["attrs"] if ob else {}
        check(f"... its height is the default ({a.get('height')})", ob is not None and a.get("height", 0) > 0.5)
        check(f"... and {key_name}'s tool is current ({tool()})", not running() and tool() != TOOL)
        mark()

    for f in (s_move, s_press, s_d1, s_d2, s_release, s_key, s_check):
        step(f)


base_then('Q', "q_cube")
base_then('W', "w_cube")


run()
