"""In a real UI (#373): a set of components made through the Maya menu in Edit Mode, then picked again from the
Outliner.

Two cubes; pCube1 in vertex mode with four vertices picked -> Create > Sets > Set (the Maya menu item) -> set1 holds
``pCube1.vtx[...]``, Edit Mode and the picks stay. Object Mode, nothing selected; set1 expanded in the kit's Outliner
-> its member row reads the Maya component name -> a click on the set row puts pCube1 in vertex mode with those four
vertices picked; in face mode on pCube2 a Quick Select Set of two faces, then Select > Quick Select Sets' item picks
them again from Object Mode."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, screenshot, view3d, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def outl():
    a = max((a for a in win().screen.areas if a.type == 'OUTLINER'), key=lambda a: a.height)
    return a, next(r for r in a.regions if r.type == 'WINDOW')


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def rows():
    """The kit set rows drawn: [(y0, y1, kind, label)]."""
    _a, r = outl()
    return [(y0, y1, row.kind, row.label) for y0, y1, row in mod("ui.outliner_tree").DRAWN.get(r.as_pointer(), [])
            if row.kind in ('SET', 'MEMBER')]


def point(row, x_units):
    _a, r = outl()
    u = mod("ui.outliner_tree").unit(bpy.context.preferences)
    return r.x + int(x_units * u), r.y + int((row[0] + row[1]) / 2)


def click(p):
    ev('MOUSEMOVE', 'NOTHING', x=p[0], y=p[1])
    ev('LEFTMOUSE', 'PRESS', x=p[0], y=p[1])
    ev('LEFTMOUSE', 'RELEASE', x=p[0], y=p[1])


def pick(ob, kind, ids):
    """Edit Mode on ``ob`` alone in component ``kind`` with ``ids`` picked."""
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for o in bpy.context.scene.objects:
            o.select_set(o == ob)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.allset.component_mode(type=kind)
    bm = bmesh.from_edit_mesh(ob.data)
    for seq in (bm.faces, bm.edges, bm.verts):
        for e in seq:
            e.select_set(False)
    seq = {'VERT': bm.verts, 'FACE': bm.faces}[kind]
    seq.ensure_lookup_table()
    for i in ids:
        seq[i].select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def picked(ob, kind):
    bm = bmesh.from_edit_mesh(ob.data)
    return {e.index for e in {'VERT': bm.verts, 'FACE': bm.faces}[kind] if e.select}


def object_mode_nothing_selected():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.scene.objects:
        o.select_set(False)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_cubes():
    bpy.ops.allset.keymap_activate()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        for _ in range(2):
            bpy.ops.allset.create(kind='CUBE')
    pick(bpy.data.objects["pCube1"], 'VERT', [0, 1, 2, 3])
    with bpy.context.temp_override(window=win(), area=area, region=region):
        check("Create > Sets > Set through the Maya menu item in Edit Mode",
              bpy.ops.allset.menu_item(item="Create/Sets/Set") == {'FINISHED'})
    sets = mod("operators.sets")
    s = sets.get("set1")
    a = bpy.data.objects["pCube1"]
    names = [n for o in sets.part_objects(s) for n in sets.component_names(s, o)] if s else None
    check(f"set1 holds pCube1's four vertices ({names})", names == ["pCube1.vtx[0:3]"] and not s.objects)
    check("Edit Mode and the picks stay", bpy.context.mode == 'EDIT_MESH' and picked(a, 'VERT') == {0, 1, 2, 3})
    object_mode_nothing_selected()
    s.allset_expanded = True
    redraw()


@step
def s_rows():
    r = rows()
    check(f"the Outliner shows set1 with its component row ({[(x[2], x[3]) for x in r]})",
          [(x[2], x[3]) for x in r] == [('SET', "set1"), ('MEMBER', "pCube1.vtx[0:3]")])
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue373_outliner_component_row.png"))
    C["set_row"] = r[0]
    click(point(r[0], 4.0))


@step
def s_set_clicked():
    a = bpy.data.objects["pCube1"]
    ts = bpy.context.scene.tool_settings
    check(f"a click on set1 picks its vertices in vertex mode (mode {bpy.context.mode}, "
          f"{tuple(ts.mesh_select_mode)})",
          bpy.context.mode == 'EDIT_MESH' and {o.name for o in bpy.context.objects_in_mode} == {"pCube1"}
          and tuple(ts.mesh_select_mode) == (True, False, False) and picked(a, 'VERT') == {0, 1, 2, 3})
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue373_set_picked.png"))
    pick(bpy.data.objects["pCube2"], 'FACE', [1, 3])
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create_quick_select_set('EXEC_DEFAULT', name="faces")
    object_mode_nothing_selected()


@step
def s_quick_menu():
    # Select > Quick Select Sets lists the set; its item runs select_set_members(name="faces")
    check("Select > Quick Select Sets lists the set", [c.name for c in mod("operators.sets").quick_sets()] == ["faces"])
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.select_set_members(name="faces")
    b = bpy.data.objects["pCube2"]
    check(f"the Quick Select Set picks pCube2's two faces in face mode ({bpy.context.mode})",
          bpy.context.mode == 'EDIT_MESH' and {o.name for o in bpy.context.objects_in_mode} == {"pCube2"}
          and tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, False, True)
          and picked(b, 'FACE') == {1, 3})


run()
