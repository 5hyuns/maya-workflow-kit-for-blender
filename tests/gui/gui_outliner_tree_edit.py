"""#348 in a real UI: editing in the kit-drawn Maya Outliner tree. Double-click a name, type, Enter = renamed with
Maya's rules (the shape follows); middle-drag a row onto a joint row = parented under that joint (kept in place);
left-drag over rows = those rows selected (Maya); right-click = the Maya Outliner menu; the visibility column's eye
hides an object; F reveals a joint picked in a closed skeleton; Delete removes the selection; a row with a
selected joint below it is dimly highlighted.

Rows are found through the tree's own row model (``outliner_tree.rows_for`` / ``row_rect``)."""

import json
import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, tap, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
POINTS = ((0.0, 0.0, 0.0), (0.0, 0.0, 3.0), (0.0, 0.0, 6.0))
C = {}


def mod(name):
    return import_module(MODULE + name)


def tree():
    return mod(".ui.outliner_tree")


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def outliner():
    area = next(a for a in win().screen.areas if a.type == 'OUTLINER')
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def redraw_all():
    for area in win().screen.areas:
        area.tag_redraw()


def park_mouse():
    _a, r = main_view()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + 20, y=r.y + 20)


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_outliner_tree_edit_{name}.png")
    screenshot(path)


def rows():
    area, region = outliner()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return tree().rows_for(bpy.context, area.spaces.active)


def row_point(label, x_units=3.0, frac=0.5):
    area, region = outliner()
    rs = rows()
    t = tree()
    u = t.unit(bpy.context.preferences)
    k = next(i for i, r in enumerate(rs) if r.label == label)
    y0, y1 = t.row_rect(area, region, k, u, len(rs))
    return region.x + int((rs[k].depth + x_units) * u), region.y + int(y1 - frac * (y1 - y0))


def labels():
    return [(r.kind, r.label, r.depth) for r in rows()]


def click(x, y, button='LEFTMOUSE', **mods):
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev(button, 'PRESS', x=x, y=y, **mods)
    ev(button, 'RELEASE', x=x, y=y, **mods)


def drag(p0, p1, button, steps=6):
    ev('MOUSEMOVE', 'NOTHING', x=p0[0], y=p0[1])
    ev(button, 'PRESS', x=p0[0], y=p0[1])
    for k in range(1, steps + 1):
        ev('MOUSEMOVE', 'NOTHING', x=p0[0] + (p1[0] - p0[0]) * k // steps, y=p0[1] + (p1[1] - p0[1]) * k // steps)
    ev(button, 'RELEASE', x=p1[0], y=p1[1])


TEMP = []


def key_over_outliner(key, idname):
    """Press ``key`` over the Outliner; without the kit's keymap items yet (they come with the kit keymap) the
    operator the key runs is called there instead (Blender's own Outliner items would take the key first)."""
    if C.get("kit_keys"):
        tap(key)
        return
    area, region = outliner()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        getattr(bpy.ops.allset, idname.split(".")[1])('INVOKE_DEFAULT')


def ensure_keys():
    """The tree's keymap items (from the kit's keymap; until then the test adds them itself)."""
    kc = bpy.context.window_manager.keyconfigs.addon
    have = any(k.idname == "allset.outliner_tree_click" for km in kc.keymaps for k in km.keymap_items)
    C["kit_keys"] = have
    if have:
        return
    km = kc.keymaps.new("Outliner", space_type='OUTLINER')
    for idname, key, value, props in (("allset.outliner_tree_click", 'LEFTMOUSE', 'PRESS', {}),
                                      ("allset.outliner_tree_menu", 'RIGHTMOUSE', 'PRESS', {}),
                                      ("allset.outliner_tree_rename", 'RET', 'PRESS', {}),
                                      ("allset.outliner_tree_reveal", 'F', 'PRESS', {}),
                                      ("allset.outliner_tree_delete", 'DEL', 'PRESS', {}),
                                      ("allset.outliner_tree_walk", 'RIGHT_ARROW', 'PRESS', {"direction": 'RIGHT'})):
        k = km.keymap_items.new(idname, key, value, any=idname == "allset.outliner_tree_click")
        for p, v in props.items():
            setattr(k.properties, p, v)
        TEMP.append((km, k))


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    tree().ENABLED = True
    tree().hide_all()
    bpy.ops.allset.keymap_activate()
    ensure_keys()
    k = mod(".operators.units").maya_unit(bpy.context.scene)
    pts = [[c * k for c in p] for p in POINTS]
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        for ob in list(bpy.context.selected_objects):
            ob.select_set(False)
        bpy.ops.allset.joint_tool(points=json.dumps(pts))
        bpy.ops.object.mode_set(mode='OBJECT')
        rig = bpy.data.objects["skeleton1"]
        coll = rig.users_collection[0]
        for name in ("pCube1", "pCylinder1"):
            ob = bpy.data.objects.new(name, bpy.data.meshes.new(name.replace("1", "Shape1")))
            coll.objects.link(ob)
        bpy.data.objects["pCylinder1"].location = (3.0, 0.0, 0.0)
        for ob in list(bpy.context.selected_objects):
            ob.select_set(False)
    tree().set_expanded([('B', bpy.data.objects["skeleton1"].session_uid, "joint1"),
                         ('B', bpy.data.objects["skeleton1"].session_uid, "joint2")], True)
    park_mouse()
    redraw_all()


@step
def s_wait():
    redraw_all()


@step
def s_dblclick():
    shot("1_start")
    C["rows0"] = labels()
    x, y = row_point("pCube1")
    click(x, y)
    click(x, y)


@step
def s_wait_popup():
    redraw_all()


@step
def s_type():
    shot("2_rename_field")
    ev('A', 'PRESS', ctrl=True)
    ev('A', 'RELEASE', ctrl=True)
    for ch in "box1":
        ev('TEXTINPUT', 'PRESS', unicode=ch)


@step
def s_enter():
    tap('RET')


@step
def s_wait_enter():
    park_mouse()
    redraw_all()


@step
def s_renamed():
    ob = bpy.data.objects.get("box1")
    check(f"double-click + typing renames the row ({[o.name for o in bpy.data.objects if o.type == 'MESH']})",
          ob is not None)
    check(f"the shape follows ({ob.data.name if ob else None})", ob is not None and ob.data.name == "boxShape1")
    check(f"the row reads the new name ({labels()[:8]})", any(lab == "box1" for _k, lab, _d in labels()))
    va, vr = main_view()
    with bpy.context.temp_override(window=win(), area=va, region=vr):
        bpy.ops.ed.undo()
    names = sorted(o.name for o in bpy.data.objects if o.type == 'MESH')
    check(f"one undo takes the rename back ({names})", "pCube1" in names and "box1" not in names)
    with bpy.context.temp_override(window=win(), area=va, region=vr):
        bpy.ops.ed.redo()
    names = sorted(o.name for o in bpy.data.objects if o.type == 'MESH')
    check(f"redo renames it again ({names})", "box1" in names)
    redraw_all()


@step
def s_mmb_start():
    # middle-drag pCylinder1 onto joint3
    C["cyl_world"] = bpy.data.objects["pCylinder1"].matrix_world.translation.copy()
    drag(row_point("pCylinder1"), row_point("joint3"), 'MIDDLEMOUSE')


@step
def s_wait_mmb():
    park_mouse()
    redraw_all()


@step
def s_mmb():
    shot("3_mmb_onto_joint3")
    cyl = bpy.data.objects["pCylinder1"]
    check(f"MMB drop onto a joint row parents under that joint ({cyl.parent and cyl.parent.name}, "
          f"{cyl.parent_type}, {cyl.parent_bone})",
          cyl.parent is not None and cyl.parent.name == "skeleton1" and cyl.parent_type == 'BONE'
          and cyl.parent_bone == "joint3")
    moved = (cyl.matrix_world.translation - C["cyl_world"]).length
    check(f"it stays where it was ({moved:.4f})", moved < 1e-3)
    got = labels()
    i = next((n for n, r in enumerate(got) if r[1] == "joint3"), None)
    tree().set_expanded([('B', bpy.data.objects["skeleton1"].session_uid, "joint3")], True)
    got = labels()
    i = next((n for n, r in enumerate(got) if r[1] == "joint3"), None)
    check(f"pCylinder1 is a row under joint3 ({got})", i is not None and got[i + 1] == ('OBJECT', "pCylinder1", 3))
    # left-drag from box1 down over joint1: both picked (the skeleton = its root joint)
    redraw_all()
    drag(row_point("box1"), row_point("joint1"), 'LEFTMOUSE')


@step
def s_wait_drag():
    park_mouse()
    redraw_all()


@step
def s_dragged():
    shot("4_drag_select")
    sel = sorted(o.name for o in bpy.context.selected_objects)
    ops = [o.bl_idname for o in bpy.context.window_manager.operators][-1:]
    check(f"a left-drag over rows selects every row passed (joint rows = their skeleton), nothing is parented "
          f"({sel}, {ops})", sel == ["box1", "pCylinder1", "skeleton1"] and bpy.data.objects["box1"].parent is None)
    # right-click on empty space: the Maya Outliner menu
    area, region = outliner()
    x, y = region.x + region.width // 2, region.y + 30
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('RIGHTMOUSE', 'PRESS', x=x, y=y)
    ev('RIGHTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_menu():
    shot("5_rmb_menu")
    sel = sorted(o.name for o in bpy.context.selected_objects)
    check(f"a right-click keeps the selection ({sel})", sel == ["box1", "pCylinder1", "skeleton1"])
    tap('ESC')


@step
def s_eye():
    area, region = outliner()
    area.spaces.active.show_restrict_column_hide = True       # Display > Visibility Column
    redraw_all()


@step
def s_eye_click():
    area, region = outliner()
    rs = rows()
    t = tree()
    u = t.unit(bpy.context.preferences)
    k = next(i for i, r in enumerate(rs) if r.label == "box1")
    y0, y1 = t.row_rect(area, region, k, u, len(rs))
    ex = t.eye_x(region, u, len(rs), t.first_row(area, region, len(rs), u))
    shot("6_eye_column")
    click(region.x + int(ex), region.y + int((y0 + y1) / 2))


@step
def s_wait_eye():
    park_mouse()
    redraw_all()


@step
def s_eyed():
    ob = bpy.data.objects["box1"]
    check(f"the eye hides box1 (visibility off: {ob.hide_viewport})", ob.hide_viewport)
    area, region = outliner()
    area.spaces.active.show_restrict_column_hide = False
    ob.hide_viewport = False
    # pick joint3 by script with the skeleton closed: the joint1 row is dimly highlighted; F opens the rows
    tree().EXPANDED.clear()
    tree()._bump_expand()
    rig = bpy.data.objects["skeleton1"]
    va, vr = main_view()
    with bpy.context.temp_override(window=win(), area=va, region=vr):
        for o in list(bpy.context.selected_objects):
            o.select_set(False)
        rig.select_set(True)
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='POSE')
        for pb in rig.pose.bones:
            pb.select = pb.name == "joint3"
        rig.data.bones.active = rig.data.bones["joint3"]
    redraw_all()


@step
def s_wait_pose():
    redraw_all()


@step
def s_closed():
    shot("7_joint3_picked_closed")
    got = labels()
    above = tree().selected_ancestors(bpy.context)
    rig = bpy.data.objects["skeleton1"]
    check(f"no automatic opening (Maya): joint3 has no row yet ({got})", not any(r[1] == "joint3" for r in got))
    check(f"the joint1 row is marked as holding the selection ({above})", ('B', rig.session_uid, "joint1") in above)
    x, y = row_point("joint1")
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    key_over_outliner('F', "allset.outliner_tree_reveal")


@step
def s_wait_f():
    redraw_all()


@step
def s_revealed():
    shot("8_reveal_f")
    got = labels()
    check(f"F reveals joint3: joint1 > joint2 > joint3 ({got})",
          ('JOINT', "joint2", 1) in got and ('JOINT', "joint3", 2) in got)
    # Delete over the Outliner removes the selection (joint3 and below)
    x, y = row_point("joint1")
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    key_over_outliner('DEL', "allset.outliner_tree_delete")


@step
def s_wait_del():
    redraw_all()


@step
def s_deleted():
    rig = bpy.data.objects["skeleton1"]
    names = sorted(b.name for b in rig.data.bones)
    check(f"Delete in the Outliner removes the picked joint ({names})", names == ["joint1", "joint2"])
    check(f"pCylinder1 (on joint3) goes with it, like Maya ({[o.name for o in bpy.data.objects]})",
          "pCylinder1" not in bpy.data.objects)
    for km, k in TEMP:
        km.keymap_items.remove(k)
    TEMP.clear()


run()
