"""Skin Tools (#127) in a real UI: a skinned cylinder (three joints) -> Initialize Skin Layers + a new layer ->
Skin > Paint Skin Weights opens the Skin Tools window (not the classic tool) -> pick joint2, Paint -> a brush stroke on
the cylinder lands on the layer -> after the stroke the skin's joint2 weights follow the layer."""

import os
import sys
from importlib import import_module

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name, window=None):
    if SHOTS:
        with bpy.context.temp_override(window=window or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def screen_of(world):
    _area, r = main_view()
    p = view3d_utils.location_3d_to_region_2d(r, r.data, world)
    return r.x + int(p.x), r.y + int(p.y)


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def cyl():
    return bpy.data.objects["pCylinder1"]


def tools_window():
    mw = mod(".ui.marked_window")
    w = mw.find_window(bpy.context, "SKIN_TOOLS")
    return w, (next((a for a in w.screen.areas if mw.kind_of(a) == "SKIN_TOOLS"), None) if w else None)


def in_tools(op, **kw):
    """Run a Skin Tools button's operator in its window (what the click does)."""
    w, area = tools_window()
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=w, area=area, region=region):
        return op(**kw)


def layer_joint2():
    layers = mod(".operators.skin_layers")
    ob = cyl()
    st = layers.state(ob)
    return float(layers.layer_matrix(ob, st.layers[0], layers.influence_names(ob))[:, 1].sum())


def skin_joint2():
    ob = cyl()
    vg = ob.vertex_groups["joint2"]
    return sum(g.weight for v in ob.data.vertices for g in v.groups if g.group == vg.index)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    joints = mod(".operators.joints")
    k = mod(".operators.units").maya_unit()
    area, r = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        bpy.ops.allset.create(kind='CYLINDER')
        c = bpy.context.active_object
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(c.data)
        vertical = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-9]
        bmesh.ops.subdivide_edges(bm, edges=vertical, cuts=9, use_grid_fill=True)
        bm.to_mesh(c.data)
        bm.free()
        bpy.ops.object.select_all(action='DESELECT')
        sk = joints.new_skeleton(bpy.context)
        parent = None
        for z in (-1.0, 0.0, 1.0):
            parent = joints.add_joint(sk, Vector((0, 0, z * k)), parent, length=k)
        joints.finish(bpy.context, sk, ["joint1", "joint2", "joint3"])
        bpy.ops.object.mode_set(mode='OBJECT')
        for o in bpy.context.scene.objects:
            if o.visible_get():
                o.select_set(o.name in ("pCylinder1", "skeleton1"))
        bpy.context.view_layer.objects.active = c
        C["bind"] = bpy.ops.allset.bind_skin()
        bpy.ops.object.select_all(action='DESELECT')
        c.select_set(True)
        bpy.context.view_layer.objects.active = c
        bpy.ops.allset.frame(selected=False)
        bpy.ops.allset.skin_layers_init()
        bpy.ops.allset.skin_layer_add()
        C["menu"] = bpy.ops.allset.menu_item(item="Skin/Paint Skin Weights")
    C["k"] = k
    check(f"skinned cylinder ({C['bind']})", C["bind"] == {'FINISHED'})


@step
def s_opened():
    redraw()


@step
def s_window():
    w, area = tools_window()
    check(f"Skin > Paint Skin Weights on a skin with layers opens Skin Tools ({C['menu']})",
          w is not None and area is not None)
    check(f"... and not the classic paint tool ({bpy.context.mode})", bpy.context.mode == 'OBJECT')
    if w is None:
        return
    check("Skin Tools: one area, no Blender header", len(w.screen.areas) == 1
          and not area.spaces.active.show_region_header)
    in_tools(bpy.ops.allset.skin_tools_pick, name="joint2")
    C["paint"] = in_tools(bpy.ops.allset.skin_tools_paint)
    redraw()


@step
def s_painting():
    layers = mod(".operators.skin_layers")
    ob = cyl()
    check(f"Paint: weight paint on the layer ({C.get('paint')}, {bpy.context.mode}, "
          f"{ob.vertex_groups.active.name if ob.vertex_groups.active else None})",
          bpy.context.mode == 'PAINT_WEIGHT' and layers.painting(ob)
          and ob.vertex_groups.active.name == layers.WORK + "joint2")
    w, _a = tools_window()
    if w is not None:
        shot("gui_step332_skin_tools_window.png", w)
    C["layer0"], C["skin0"] = layer_joint2(), skin_joint2()
    k = C["k"]
    C["stroke"] = [screen_of(Vector((x * k, -k, 0.6 * k))) for x in (-0.6, -0.2, 0.2, 0.6)]
    x, y = C["stroke"][0]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_stroke_press():
    x, y = C["stroke"][0]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_stroke_move():
    for x, y in C["stroke"][1:]:
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_stroke_release():
    x, y = C["stroke"][-1]
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_wait():
    redraw()


@step
def s_painted():
    lw, sw = layer_joint2(), skin_joint2()
    check(f"the stroke lands on the layer's joint2 ({C['layer0']:.2f} -> {lw:.2f})", lw > C["layer0"] + 0.5)
    check(f"the skin's joint2 weights follow the layer ({C['skin0']:.2f} -> {sw:.2f})", sw > C["skin0"] + 0.3)
    ob = cyl()
    total = [sum(g.weight for g in v.groups if not ob.vertex_groups[g.group].name.startswith(".st:"))
             for v in ob.data.vertices]
    check(f"skin weights stay normalised ({min(total):.3f} .. {max(total):.3f})",
          all(abs(t - 1.0) < 1e-3 for t in total if t > 0))
    redraw()


@step
def s_shots():
    shot("gui_step332_painted.png")
    w, _a = tools_window()
    if w is not None:
        shot("gui_step332_skin_tools_after.png", w)


@step
def s_stop():
    in_tools(bpy.ops.allset.skin_tools_paint)


@step
def s_stopped():
    layers = mod(".operators.skin_layers")
    ob = cyl()
    check(f"Stop Painting leaves weight paint ({bpy.context.mode}) and removes the working groups",
          bpy.context.mode == 'OBJECT' and not layers.painting()
          and not any(vg.name.startswith(layers.WORK) for vg in ob.vertex_groups))


run()
