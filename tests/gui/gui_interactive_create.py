"""Create > Polygon Primitives > Interactive Creation (#225): picking a primitive makes the Interactive Creation tool
current; a cube drawn with two drags (base, then height) sits on the grid with its Maya name and creation node and
Exit On Completion switches to the Select tool; a single click makes a default sphere there; with Exit On Completion
off the tool stays and keeps drawing, Esc keeps it, Q leaves it; Enter waits on a height step and a click skips it
(flat); torus section, Shift cube, front view; Esc mid-shape drops it and keeps the tool; Q mid-shape drops it and
leaves; Y comes back."""

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


@step
def s_height_press():
    x, y = at(0.55, 0.35)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_height_drag1():
    x, y = at(0.55, 0.45)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_height_drag2():
    x, y = at(0.55, 0.55)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_height_release():
    x, y = at(0.55, 0.55)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_cube_done():
    ob = bpy.data.objects[C["cube"]]
    n = node(ob)
    a = n["attrs"]
    check(f"Maya name and creation node ({ob.name}, {n['name']})", ob.name.startswith("pCube") and
          n["name"].startswith("polyCube"))
    check(f"dragging up gave a height ({a['height']:.3f})", a["height"] > 0.5)
    lo, hi = world_z(ob)
    check(f"the cube sits on the grid (z {lo:.4f} .. {hi:.4f})", abs(lo) < 1e-4 and hi > 0)
    check(f"Exit On Completion switched to the Select tool ({tool()})", not running() and tool() == "builtin.select_box")
    check("the new cube is selected and active", ob.select_get() and bpy.context.view_layer.objects.active == ob)
    check("lambert1", ob.active_material is not None)
    mark()


@step
def s_sphere_start():
    start('SPHERE')


@step
def s_sphere_click():
    x, y = at(0.35, 0.5)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_sphere_release():
    x, y = at(0.35, 0.5)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_sphere_done():
    obs = new_objects()
    check(f"a single click made one sphere ({[o.name for o in obs]})", len(obs) == 1 and obs[0].name.startswith("pSphere"))
    a = node(obs[0])["attrs"]
    check(f"default radius 1 ({a['radius']:.3f})", abs(a["radius"] - 1.0) < 1e-6)
    loc = obs[0].matrix_world.translation
    check(f"centred on the clicked grid point, off the origin ({tuple(round(c, 4) for c in loc)})",
          abs(loc.z) < 1e-6 and loc.x < -1e-3)
    check(f"tool ended: Select tool ({tool()})", not running() and tool() == "builtin.select_box")
    prefs().exit_on_completion = False
    mark()


@step
def s_multi_start():
    start('CUBE')


@step
def s_multi_click1():
    x, y = at(0.6, 0.5)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_multi_release1():
    x, y = at(0.6, 0.5)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_multi_click2():
    x, y = at(0.4, 0.6)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_multi_release2():
    x, y = at(0.4, 0.6)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_multi_check():
    obs = new_objects()
    check(f"Exit On Completion off: two cubes, tool still current ({[o.name for o in obs]}, {tool()})",
          len(obs) == 2 and tool() == TOOL and not running())
    key('ESC')


@step
def s_multi_esc():
    check(f"Esc with nothing started keeps the tool and the cubes ({tool()})",
          tool() == TOOL and not running() and len(new_objects()) == 2)
    key('Q')


@step
def s_multi_done():
    check(f"Q leaves the tool for the Select tool ({tool()})", tool() == "builtin.select_box" and
          len(new_objects()) == 2)
    prefs().exit_on_completion = True
    mark()


@step
def s_cyl_start():
    start('CYLINDER')


@step
def s_cyl_press():
    x, y = at(0.5, 0.5)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_cyl_drag():
    x, y = at(0.56, 0.5)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_cyl_release():
    x, y = at(0.56, 0.5)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_cyl_enter():
    ev('RET', 'PRESS', x=at(0.56, 0.5)[0], y=at(0.56, 0.5)[1])


@step
def s_cyl_enter_up():
    ev('RET', 'RELEASE', x=at(0.56, 0.5)[0], y=at(0.56, 0.5)[1])


@step
def s_cyl_waits():
    check("Enter on the height step waits for the height drag", running() and len(new_objects()) == 1)
    x, y = at(0.56, 0.6)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_cyl_skip():
    x, y = at(0.56, 0.6)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_cyl_done():
    obs = new_objects()
    check(f"one cylinder ({[o.name for o in obs]})", len(obs) == 1 and obs[0].name.startswith("pCylinder"))
    a = node(obs[0])["attrs"]
    ob = obs[0]
    check(f"a click on the height step keeps the default height, flat ({a['height']:.3f}, scale {tuple(ob.scale)})",
          abs(a["height"] - 2.0) < 1e-6 and abs(ob.scale.z) < 1e-9 and a["radius"] > 0.1)
    lo, hi = world_z(ob)
    check(f"flat on the grid ({lo:.5f} .. {hi:.5f})", abs(lo) < 1e-6 and abs(hi) < 1e-6)
    check(f"tool ended ({tool()})", not running() and tool() == "builtin.select_box")
    # one undo removes the cylinder
    with bpy.context.temp_override(window=win()):
        bpy.ops.ed.undo()
    C["undone"] = True


@step
def s_undo_check():
    names = {o.name for o in bpy.data.objects}
    check(f"one undo step per primitive (cylinder gone, cubes kept: {sorted(names)})",
          not any(n.startswith("pCylinder") for n in names) and any(n.startswith("pCube") for n in names))
    mark()


def drag(name, a, b, then=None):
    """Steps: press at a, two moves to b, release (``shift`` on every event)."""
    kw = dict(shift=True) if then == "shift" else {}

    def press():
        x, y = at(*a)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y, **kw)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y, **kw)

    def move1():
        x, y = at((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y, **kw)

    def move2():
        x, y = at(*b)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y, **kw)

    def release():
        x, y = at(*b)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y, **kw)

    for i, fn in enumerate((press, move1, move2, release)):
        fn.__name__ = f"s_{name}_{i}"
        step(fn)


step(lambda: start('TORUS'))
drag("torus_r", (0.5, 0.5), (0.58, 0.5))
drag("torus_s", (0.58, 0.5), (0.62, 0.5))


@step
def s_torus_done():
    obs = new_objects()
    check(f"one torus ({[o.name for o in obs]})", len(obs) == 1 and obs[0].name.startswith("pTorus"))
    a = node(obs[0])["attrs"]
    _a, r = main_view()
    px = (at(0.62, 0.5)[0] - at(0.58, 0.5)[0]) / (bpy.context.preferences.system.ui_scale or 1.0)
    check(f"section radius = 0.5 + 0.1 per px dragged sideways ({a['sectionRadius']:.4f}, {px:.1f} px)",
          abs(a["sectionRadius"] - (0.5 + 0.1 * px)) < 1e-6)
    lo, hi = world_z(obs[0])
    check(f"a torus is centred on the grid ({lo:.4f} .. {hi:.4f})", abs(lo + hi) < 1e-4)
    check(f"tool ended ({tool()})", not running() and tool() == "builtin.select_box")
    mark()


step(lambda: start('CUBE'))
drag("shift_cube", (0.45, 0.45), (0.52, 0.40), then="shift")


@step
def s_shift_done():
    obs = new_objects()
    check(f"Shift: one drag made a cube ({[o.name for o in obs]})", len(obs) == 1 and not running()
          and tool() == "builtin.select_box")
    a = node(obs[0])["attrs"]
    check(f"equal sides ({a['width']:.3f} {a['depth']:.3f} {a['height']:.3f})",
          abs(a["width"] - a["depth"]) < 1e-6 and abs(a["width"] - a["height"]) < 1e-6 and a["width"] > 0.1)
    lo, _hi = world_z(obs[0])
    check(f"from its base ({lo:.4f})", abs(lo) < 1e-4)
    # front orthographic view (looking along +Y)
    _area, region = main_view()
    from mathutils import Euler
    region.data.view_perspective = 'ORTHO'
    region.data.view_rotation = Euler((1.5707963, 0.0, 0.0)).to_quaternion()
    mark()


step(lambda: start('PLANE'))
drag("front_plane", (0.45, 0.55), (0.55, 0.45))


@step
def s_front_done():
    obs = new_objects()
    check(f"one plane in the front view ({[o.name for o in obs]})", len(obs) == 1)
    ob = obs[0]
    ys = [(ob.matrix_world @ v.co).y for v in ob.data.vertices]
    check(f"drawn on the view plane through the origin (y {min(ys):.5f} .. {max(ys):.5f})",
          max(abs(y) for y in ys) < 1e-4)
    zs = [(ob.matrix_world @ v.co).z for v in ob.data.vertices]
    check(f"standing up in the front view (z span {max(zs) - min(zs):.3f})", max(zs) - min(zs) > 0.5)
    n = node(ob)["attrs"]
    check(f"rotation 0, the node's axis faces the viewer ({tuple(ob.rotation_euler)}, "
          f"{(n['axisX'], n['axisY'], n['axisZ'])})",
          max(abs(c) for c in ob.rotation_euler) < 1e-9 and (n["axisX"], n["axisY"], n["axisZ"]) == (0.0, 0.0, 1.0))
    mark()


step(lambda: start('CUBE'))
drag("esc_cube", (0.45, 0.45), (0.52, 0.40))


@step
def s_esc_press():
    check("a base is being drawn", len(new_objects()) == 1)
    ev('ESC', 'PRESS', x=at(0.5, 0.5)[0], y=at(0.5, 0.5)[1])


@step
def s_esc_release():
    ev('ESC', 'RELEASE', x=at(0.5, 0.5)[0], y=at(0.5, 0.5)[1])


@step
def s_esc_check():
    check(f"Esc drops the unfinished cube and the tool stays ({tool()})", not new_objects() and not running()
          and tool() == TOOL)
    key('ESC')


@step
def s_esc_end():
    check(f"a second Esc with nothing started keeps the tool ({tool()})", tool() == TOOL and not running())


drag("again_cube", (0.45, 0.45), (0.52, 0.40))


@step
def s_again_check():
    obs = new_objects()
    check(f"the next drag after Esc starts a new cube ({[o.name for o in obs]})", len(obs) == 1 and running())
    key('Q')


@step
def s_q_mid_shape():
    check(f"Q during the height step drops the unfinished cube and picks the Select tool ({tool()})",
          not new_objects() and not running() and tool() == "builtin.select_box")
    key('Y')


@step
def s_y_back():
    check(f"Y (last tool) comes back to the creation tool ({tool()})", tool() == TOOL)
    key('Q')
    prefs().interactive_creation = False


run()
