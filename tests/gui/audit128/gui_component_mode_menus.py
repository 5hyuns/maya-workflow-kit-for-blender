"""Audit 128 repro (menu sweep follow-up): Edit / Select / Modify menu items a Maya user clicks while in component
mode, run through the real menu button operator (allset.menu_item, as a click does). Maya 2022 runs all of these
in component mode (Select > All / Inverse / Deselect All act on components, Edit > Delete deletes the selected
components, Undo / Redo / Repeat always work, Group / Parent / Freeze act on the objects that own the components).
PASSes when each item changes something (or, for Undo, undoes)."""

import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import check, run, setup, step, view3d, win  # noqa: E402

C = {}


def ov(fn, *a, **kw):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return fn(*a, **kw)


def sel_faces():
    ob = bpy.context.edit_object
    return sum(1 for f in bmesh.from_edit_mesh(ob.data).faces if f.select) if ob else -1


def n_faces():
    ob = bpy.context.edit_object or bpy.context.active_object
    if ob.mode == 'EDIT':
        return len(bmesh.from_edit_mesh(ob.data).faces)
    return len(ob.data.polygons)


def edit_one_face():
    if bpy.context.mode != 'OBJECT':
        ov(bpy.ops.object.mode_set, mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    ov(bpy.ops.allset.create, kind='CUBE')
    ov(bpy.ops.object.mode_set, mode='EDIT')
    ov(bpy.ops.mesh.select_mode, type='FACE')
    ov(bpy.ops.mesh.select_all, action='DESELECT')
    ob = bpy.context.edit_object
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    bm.faces[0].select_set(True)
    bmesh.update_edit_mesh(ob.data)


def item(path):
    try:
        res = ov(bpy.ops.allset.menu_item, item=path)
    except Exception as ex:
        res = repr(ex)
    print("AUDIT", path, res)
    return res


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)


@step
def s_select():
    edit_one_face()
    item("Select/All")
    check(f"component mode: Select > All selects every face (1 -> {sel_faces()} of 6)", sel_faces() == 6)
    edit_one_face()
    item("Select/Inverse")
    check(f"component mode: Select > Inverse selects the other 5 faces ({sel_faces()})", sel_faces() == 5)
    edit_one_face()
    item("Select/Deselect All")
    check(f"component mode: Select > Deselect All ({sel_faces()} selected)", sel_faces() == 0)


@step
def s_delete():
    edit_one_face()
    item("Edit/Delete")
    check(f"component mode: Edit > Delete deletes the selected face (6 -> {n_faces()})", n_faces() == 5)


@step
def s_group():
    edit_one_face()
    before = set(bpy.data.objects.keys())
    item("Edit/Group")
    new = set(bpy.data.objects.keys()) - before
    check(f"component mode: Edit > Group groups the object (new {sorted(new)})", any(n.startswith("group") for n in new))
    edit_one_face()
    ob = bpy.context.edit_object
    ob.location.x = 0.05
    item("Modify/Freeze Transformations")
    check(f"component mode: Modify > Freeze Transformations zeroes Translate X ({ob.location.x:.3f})",
          abs(ob.location.x) < 1e-6)


run()
