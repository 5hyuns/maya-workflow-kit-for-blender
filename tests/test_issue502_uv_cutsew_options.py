"""#502: UV Editor > Cut/Sew > Auto Seams, Move and Sew, Merge and Stitch Together open their option windows; the
saved settings drive the menu item."""

from importlib import import_module

import bmesh
import bpy

import kit

uvt = import_module(kit.MODULE + ".operators.uv_tools")
ow = import_module(kit.MODULE + ".operators.option_windows")
box = import_module(kit.MODULE + ".ui.menu_option_box")

CS = "UV Editor/Cut/Sew/"
KEYS = ("uv_auto_seams", "uv_move_sew", "uv_merge", "uv_stitch_together")


def _cube(automatic=False):
    for key in KEYS:
        ow.store(key, None)
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add(size=2)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_all(action='SELECT')
    if automatic:
        assert bpy.ops.allset.uv_automatic() == {'FINISHED'}
    bpy.ops.mesh.select_all(action='DESELECT')
    return ob


def _bm(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.ensure_lookup_table()
    return bm, bm.loops.layers.uv.active


def _shells(ob):
    bm, uv = _bm(ob)
    return len(uvt.islands(bm, uv))


def _pick_edge(ob, index):
    bm, _uv = _bm(ob)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    bm.edges[index].select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def test_windows_open_from_the_option_boxes():
    for item, key, action in (("Auto Seams", "uv_auto_seams", "Auto Seams"),
                              ("Move and Sew", "uv_move_sew", "Move and Sew"), ("Merge", "uv_merge", "Merge UVs"),
                              ("Stitch Together", "uv_stitch_together", "Stitch Together")):
        w = ow.find_path(CS + item)
        assert w is not None and w.key == key and w.action == action, (item, w and w.key)
        assert box.option_kind(CS + item) == "window", item
        assert hasattr(bpy.ops.allset, "opt_" + key)
    assert ow.find_path(CS + "Auto Seams").defaults() == {"seams": "Cut", "method": "Automatic"}
    ms = ow.find_path(CS + "Move and Sew")
    assert ms.defaults() == {"limit": False, "faces": 10}
    assert not ms.enabled(ms.defaults(), "faces") and ms.enabled({"limit": True, "faces": 10}, "faces")
    assert ow.find_path(CS + "Merge").defaults() == {"distance": 0.01}


def test_auto_seams_cut_along_hard_edges_and_select():
    ob = _cube()
    assert _shells(ob) == 1
    seams = sum(e.seam for e in _bm(ob)[0].edges)
    v = {"seams": "Select", "method": "Cut along hard edges"}
    assert bpy.ops.allset.opt_uv_auto_seams('EXEC_DEFAULT', **v) == {'FINISHED'}
    bm, _uv = _bm(ob)
    assert _shells(ob) == 1 and sum(e.seam for e in bm.edges) == seams, "Select: nothing is cut"
    picked = [e for e in bm.edges if e.select]
    assert picked, "Select: the seam edges are selected"
    assert tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, True, False)
    v["seams"] = "Cut"
    bpy.ops.mesh.select_all(action='DESELECT')      # nothing picked: the whole mesh
    assert bpy.ops.allset.opt_uv_auto_seams('EXEC_DEFAULT', **v) == {'FINISHED'}
    assert _shells(ob) == 6, "a flat-shaded cube: every edge is hard, each face its own shell"


def test_auto_seams_saved_settings_drive_the_menu_item():
    ob = _cube()
    assert bpy.ops.allset.opt_uv_auto_seams('EXEC_DEFAULT', seams="Select", method="Cut along hard edges") == \
        {'FINISHED'}
    bm, _uv = _bm(ob)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.menu_item(item=CS + "Auto Seams") == {'FINISHED'}
    assert _shells(ob) == 1 and any(e.select for e in _bm(ob)[0].edges), "the saved Select is used"


def test_move_and_sew_limit_shell_size():
    ob = _cube(automatic=True)
    assert _shells(ob) == 6
    bm, _uv = _bm(ob)
    edge = next(e for e in bm.edges if len(e.link_faces) == 2).index
    _pick_edge(ob, edge)
    bpy.ops.allset.opt_uv_move_sew('EXEC_DEFAULT', limit=True, faces=0)
    assert _shells(ob) == 6, "a moving shell over the face limit stays apart"
    _pick_edge(ob, edge)
    assert bpy.ops.allset.opt_uv_move_sew('EXEC_DEFAULT', limit=True, faces=1) == {'FINISHED'}
    assert _shells(ob) == 5, "within the limit the shells are sewn"


def test_merge_threshold():
    ob = _cube(automatic=True)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.allset.opt_uv_merge('EXEC_DEFAULT', distance=0.0)
    assert _shells(ob) == 6, "threshold 0: shells apart stay apart"
    bpy.ops.mesh.select_all(action='SELECT')
    assert bpy.ops.allset.opt_uv_merge('EXEC_DEFAULT', distance=10.0) == {'FINISHED'}
    assert _shells(ob) < 6, "a large threshold merges the UVs of each vertex"
    assert ow.saved("uv_merge") == {"distance": 10.0}
