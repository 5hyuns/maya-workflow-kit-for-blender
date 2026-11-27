"""Hypershade graph hands in a real UI: a Shader Editor showing a material (Principled -> Output, Image Texture ->
Base Color, Mapping -> Image Texture). RMB on the empty graph / the material / the texture / the output opens the
matching Maya graph marking menu (screenshots); Tab -> type a node name -> Enter makes that node where the mouse was,
selected and active; keys 1 / 2 / 3 collapse the selected node, show only its connected sockets, show them all."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    if SHOTS:
        with bpy.context.temp_override(window=win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def node_area():
    return next(a for a in win().screen.areas if a.type == 'NODE_EDITOR')


def node_region():
    return next(r for r in node_area().regions if r.type == 'WINDOW')


def tree():
    return bpy.data.materials[C["mat"]].node_tree


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def node_point(name):
    """Window point at the middle of node ``name`` (the kit's own node rectangle, which the RMB pick uses)."""
    hands = mod(".ui.hypershade_hands")
    left, bottom, right, top = hands.node_rect(tree().nodes[name])
    r = node_region()
    x, y = r.view2d.view_to_region((left + right) / 2, (top + bottom) / 2, clip=False)
    return r.x + x, r.y + y


def empty_point():
    """A window point of the graph with no node under it."""
    hands = mod(".ui.hypershade_hands")
    r = node_region()
    for fy in (0.12, 0.88, 0.5):
        for fx in (0.08, 0.92, 0.5):
            x, y = int(r.width * fx), int(r.height * fy)
            vx, vy = r.view2d.region_to_view(x, y)
            if hands.node_at(tree(), vx, vy) is None:
                return r.x + x, r.y + y
    return None


def session():
    return mod(".marking.draw").ACTIVE.get("session")


def open_menu_name():
    s = session()
    return getattr(s.stack[0][0].sub, "name", None) if s is not None else None


@step
def s_setup():
    setup()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    mat = bpy.data.materials.new("blinn1")
    mod(".compat").ensure_material_nodes(mat)
    ob.data.materials.append(mat)
    C["mat"] = mat.name
    t = mat.node_tree
    bsdf = next(n for n in t.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    out = next(n for n in t.nodes if n.bl_idname == "ShaderNodeOutputMaterial")
    tex = t.nodes.new("ShaderNodeTexImage")
    mapping = t.nodes.new("ShaderNodeMapping")
    t.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    t.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    bsdf.location, out.location = (0, 300), (400, 300)
    tex.location, mapping.location = (-400, 300), (-750, 300)
    C["nodes"] = {"bsdf": bsdf.name, "out": out.name, "tex": tex.name, "mapping": mapping.name}
    areas = sorted((a for a in win().screen.areas if a.type not in {'TOPBAR', 'STATUSBAR'}),
                   key=lambda a: -a.width * a.height)
    areas[0].ui_type = 'ShaderNodeTree'
    space = areas[0].spaces.active
    space.pin = True
    space.node_tree = t
    redraw()


@step
def s_frame():
    area, region = node_area(), node_region()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.node.view_all()
    redraw()


@step
def s_drawn():
    dims = {k: tuple(tree().nodes[v].dimensions) for k, v in C["nodes"].items()}
    check(f"the nodes are drawn ({dims})", all(d[0] > 0 for d in dims.values()))


def rmb_case(where, menu, shot_name):
    @step
    def s_press():
        p = empty_point() if where is None else node_point(C["nodes"][where])
        C["p"] = p
        if p is None:
            return
        ev('MOUSEMOVE', 'NOTHING', x=p[0], y=p[1])
        ev('RIGHTMOUSE', 'PRESS', x=p[0], y=p[1])

    @step
    def s_open():
        name = open_menu_name()
        check(f"RMB on {where or 'the empty graph'} opens {menu} (got {name})", name == menu)
        if name is not None:
            shot(shot_name)
        if where is not None and name is not None:
            rows = [it.label for it in session().layout.items if it.kind == "list" and it.label]
            node = tree().nodes[C["nodes"][where]]
            # the texture menu lists Edit Texture / Reload Image File above the node's own rows
            check(f"the list holds the node's name row ({rows[:4]})", f"{node.name}..." in rows)

    @step
    def s_close():
        if C["p"] is None:
            return
        ev('RIGHTMOUSE', 'RELEASE', x=C["p"][0], y=C["p"][1])
        if mod(".marking.draw").ACTIVE:
            tap('ESC')

    @step
    def s_closed():
        check(f"the {menu} menu closed", not mod(".marking.draw").ACTIVE)
        sel = [n.name for n in tree().nodes if n.select]
        C.setdefault("sel_after_rmb", sel)


rmb_case(None, "NODE_EMPTY", "gui_hypershade_rmb_empty.png")
rmb_case("bsdf", "NODE_MATERIAL", "gui_hypershade_rmb_material.png")
rmb_case("tex", "NODE_TEXTURE", "gui_hypershade_rmb_texture.png")
rmb_case("out", "NODE_OUTPUT", "gui_hypershade_rmb_output.png")


@step
def s_tab():
    p = empty_point()
    C["tab_p"] = p
    C["before"] = {n.name for n in tree().nodes}
    ev('MOUSEMOVE', 'NOTHING', x=p[0], y=p[1])
    tap('TAB')


@step
def s_type():
    shot("gui_hypershade_tab_field.png")
    for ch in "File":
        ev('TEXTINPUT', 'PRESS', unicode=ch)


@step
def s_enter():
    shot("gui_hypershade_tab_typed.png")
    tap('RET')
    redraw()


@step
def s_made():
    t = tree()
    new = [n for n in t.nodes if n.name not in C["before"]]
    check(f"Tab -> File -> Enter makes one node ({[(n.bl_idname, n.label) for n in new]})",
          len(new) == 1 and new[0].bl_idname == "ShaderNodeTexImage" and new[0].label == "File")
    if len(new) != 1:
        return
    node = new[0]
    r = node_region()
    vx, vy = r.view2d.region_to_view(C["tab_p"][0] - r.x, C["tab_p"][1] - r.y)
    check(f"the node is where the mouse was ({tuple(node.location)} ~ {(round(vx), round(vy))})",
          abs(node.location.x - vx) < 2 and abs(node.location.y - vy) < 2)
    check("the new node is the only selected one and active",
          [n for n in t.nodes if n.select] == [node] and t.nodes.active == node)
    shot("gui_hypershade_tab_made.png")


@step
def s_keys_select():
    t = tree()
    tex = t.nodes[C["nodes"]["tex"]]
    for n in t.nodes:
        n.select = n == tex
    t.nodes.active = tex
    p = empty_point()
    ev('MOUSEMOVE', 'NOTHING', x=p[0], y=p[1])
    tap('TWO')


@step
def s_key_two():
    tex = tree().nodes[C["nodes"]["tex"]]
    shown = [s.name for s in (*tex.inputs, *tex.outputs) if not s.hide]
    check(f"2 shows only the connected sockets of the selected node ({shown})", shown == ["Vector", "Color"])
    bsdf = tree().nodes[C["nodes"]["bsdf"]]
    check("the other nodes keep their sockets", not any(s.hide for s in bsdf.inputs))
    shot("gui_hypershade_key2.png")
    tap('ONE')


@step
def s_key_one():
    tex = tree().nodes[C["nodes"]["tex"]]
    check("1 collapses the selected node", tex.hide)
    tap('THREE')


@step
def s_key_three():
    tex = tree().nodes[C["nodes"]["tex"]]
    check("3 shows every socket again", not tex.hide and not any(s.hide for s in (*tex.inputs, *tex.outputs)))


run()
