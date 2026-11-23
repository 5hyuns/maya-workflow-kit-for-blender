"""#499: Ctrl+RMB in the UV Editor opens Maya's UV Editor selection conversion marking menu; its items convert the
selection and switch the UV Editor's component type. GUI: tests/gui/gui_issue499_uv_convert_menu.py."""

import types
from importlib import import_module

import bmesh
import bpy

import kit

marking = import_module(kit.MODULE + ".marking")
mm = import_module(kit.MODULE + ".marking.menus")
modal = import_module(kit.MODULE + ".marking.modal")
compat = import_module(kit.MODULE + ".compat")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
notices = import_module(kit.MODULE + ".ui.notices")
uv_shell_select = import_module(kit.MODULE + ".operators.uv_shell_select")


def _ring(sub):
    return {p: label for p, (label, _a) in sub.radial.items()}


def _list(sub):
    return [e[0] for e in sub.items if e != mm.DIVIDER]


def _ctx(space_mode='UV', mode='EDIT_MESH'):
    return types.SimpleNamespace(mode=mode, scene=bpy.context.scene, active_object=None,
                                 window_manager=types.SimpleNamespace(allset_uv_shell_mask=False),
                                 space_data=types.SimpleNamespace(type='IMAGE_EDITOR', mode=space_mode))


def test_ctrl_rmb_opens_the_convert_menu():
    assert marking.resolve("CTRL_RMB", _ctx()) == ("pie", marking.idname("UV_CONVERT"))
    assert marking.resolve("CTRL_RMB", _ctx(space_mode='VIEW')) is None, "image viewing: no UV menu"
    assert marking.resolve("CTRL_RMB", _ctx(mode='OBJECT')) is None
    km = kit.maya_kc().keymaps["UV Editor"]
    found = [(k.idname, k.properties.trigger) for k in km.keymap_items
             if k.active and k.type == 'RIGHTMOUSE' and k.value == 'PRESS' and k.ctrl and not k.shift and not k.alt]
    assert found == [("allset.marking_menu", 'CTRL_RMB')], found


def test_ring_and_list():
    m = mm.UV_CONVERT
    assert _ring(m) == {"S": "To Faces", "N": "To Edges", "E": "To UVs", "W": "To Vertices", "NE": "Grow Selection",
                        "NW": "Shrink Selection", "SE": "To UV Shell", "SW": "To UV Shell Border"}
    r = m.radial
    assert _ring(r["S"][1]) == {"S": "To Faces", "E": "To Connected Faces", "W": "To Contained Faces",
                                "SE": "To Face Perimeter", "N": "To Face Path"}
    assert _ring(r["N"][1]) == {"N": "To Edges", "NE": "To Edge Perimeter", "NW": "To Edge Loop", "W": "To Edge Ring",
                                "E": "To Contained Edges"}
    assert _ring(r["E"][1]) == {"E": "To UVs", "NE": "To UV Perimeter", "SE": "To UV Edge Loop"}
    assert _ring(r["W"][1]) == {"W": "To Vertices", "NW": "To Vertex Perimeter"}
    assert _ring(r["NE"][1]) == {"NE": "Grow", "N": "Grow Along Loop"}
    assert _ring(r["NW"][1]) == {"NW": "Shrink", "N": "Shrink Along Loop"}
    assert _list(m) == ["Select All", "Clear Selection", "Inverse Selection", "Selection Constraints",
                        "Transform Constraints", "Select Back-Facing", "Select Front-Facing", "Select Overlapping",
                        "Select Non-Overlapping", "Select Texture Borders", "Select Unmapped Faces",
                        "Shortest Edge Path Tool"]


def test_every_entry_runs_something():
    """Menu items run the UV Editor's Select menu entries (all mapped); only the two constraint submenus are greyed,
    with a notice."""
    greyed = []
    for path, _label, action in mm.label_walk(mm.UV_CONVERT, "UV_CONVERT"):
        if isinstance(action, mm.Sub) and not mm.is_unavailable(action):
            continue
        if mm.is_greyed(action):
            greyed.append(path)
            continue
        if action[0] == "item":
            assert action[1] in menu_map.MAP and menu_map.MAP[action[1]] is not None, path
        else:
            assert action[0] == "allset.uv_convert", path
    assert greyed == ["UV_CONVERT/Selection Constraints", "UV_CONVERT/Transform Constraints"], greyed
    assert all(p in notices.MARKING for p in greyed)


# --- the conversions -------------------------------------------------------------------------------

def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _grid():
    """A 4 x 4 quad grid in edit mode, one UV shell (UVs = x, y / 4), nothing selected."""
    _clear()
    n = 4
    verts = [(x, y, 0.0) for y in range(n + 1) for x in range(n + 1)]
    faces = [(y * (n + 1) + x, y * (n + 1) + x + 1, (y + 1) * (n + 1) + x + 1, (y + 1) * (n + 1) + x)
             for y in range(n) for x in range(n)]
    me = bpy.data.meshes.new("grid")
    me.from_pydata(verts, [], faces)
    me.uv_layers.new(name="UVMap")
    ob = bpy.data.objects.new("grid", me)
    bpy.context.collection.objects.link(ob)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        for loop in f.loops:
            loop[uv].uv = (loop.vert.co.x / n, loop.vert.co.y / n)
    bmesh.update_edit_mesh(me)
    return ob


def _uv_area():
    scr = bpy.context.window.screen
    a = next(a for a in scr.areas if a.type in ('VIEW_3D', 'IMAGE_EDITOR'))
    a.ui_type = 'UV'
    return a, next(r for r in a.regions if r.type == 'WINDOW')


def _at(x, y):
    return lambda v: round(v.co.x) == x and round(v.co.y) == y


def _select_uvs(ob, pick):
    """UV component (sync off, every face shown): select the UVs of the vertices ``pick`` accepts."""
    ts = bpy.context.scene.tool_settings
    a, r = _uv_area()
    with bpy.context.temp_override(area=a, region=r):
        assert bpy.ops.allset.uv_component(mode='UV') == {'FINISHED'}
    assert not ts.use_uv_select_sync
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        for lp in f.loops:
            on = pick(lp.vert)
            compat.set_uv_vert_selected(lp, uv, on)
    for f in bm.faces:
        for lp in f.loops:
            compat.set_uv_edge_selected(lp, uv, pick(lp.vert) and pick(lp.link_loop_next.vert))
    bmesh.update_edit_mesh(ob.data)


def _run(entry_path):
    action = next(a for p, _l, a in mm.label_walk(mm.UV_CONVERT, "UV_CONVERT") if p == entry_path)
    a, r = _uv_area()
    with bpy.context.temp_override(area=a, region=r):
        res = modal.run_action(bpy.context, action, path=entry_path)
    assert res == {'FINISHED'}, (entry_path, res)


def _selected(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return ({v.index for v in bm.verts if v.select}, {e.index for e in bm.edges if e.select},
            {f.index for f in bm.faces if f.select})


def test_uvs_to_faces_takes_the_faces_they_contain():
    ob = _grid()
    # the four UVs of the bottom-left face plus one more UV beside it
    _select_uvs(ob, lambda v: (round(v.co.x), round(v.co.y)) in {(0, 0), (1, 0), (0, 1), (1, 1), (2, 0)})
    _run("UV_CONVERT/To Faces/To Faces")
    ts = bpy.context.scene.tool_settings
    assert ts.use_uv_select_sync and tuple(ts.mesh_select_mode) == (False, False, True)
    _v, _e, faces = _selected(ob)
    assert faces == {0}, faces


def test_uvs_to_edges_and_vertices_take_what_they_touch():
    ob = _grid()
    _select_uvs(ob, _at(2, 2))          # one inner UV
    _run("UV_CONVERT/To Edges/To Edges")
    ts = bpy.context.scene.tool_settings
    assert ts.use_uv_select_sync and tuple(ts.mesh_select_mode) == (False, True, False)
    _v, edges, faces = _selected(ob)
    assert len(edges) == 4 and not faces, (edges, faces)
    _select_uvs(ob, _at(2, 2))
    _run("UV_CONVERT/To Vertices/To Vertices")
    assert tuple(ts.mesh_select_mode) == (True, False, False)
    verts, _e, _f = _selected(ob)
    assert verts == {12}, verts


def test_faces_to_uvs_then_to_vertices():
    ob = _grid()
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(f.index == 5)
    bmesh.update_edit_mesh(ob.data)
    _run("UV_CONVERT/To UVs/To UVs")
    assert not ts.use_uv_select_sync and ts.uv_select_mode == 'VERTEX'
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    picked = {lp.vert.index for f in bm.faces for lp in f.loops if compat.uv_vert_selected(lp, uv)}
    bm.faces.ensure_lookup_table()
    face_verts = {v.index for v in bm.faces[5].verts}
    assert picked == face_verts, (picked, face_verts)
    assert all(f.select for f in bm.faces), "UV component: every face's UVs shown"
    _run("UV_CONVERT/To Vertices/To Vertices")
    verts, _e, _f = _selected(ob)
    assert verts == face_verts and ts.use_uv_select_sync


def test_shell_border_and_grow_run():
    ob = _grid()
    _select_uvs(ob, _at(2, 2))
    _run("UV_CONVERT/Grow Selection/Grow")
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    grown = {lp.vert.index for f in bm.faces for lp in f.loops if compat.uv_vert_selected(lp, uv)}
    assert len(grown) > 1 and 12 in grown, grown
    _run("UV_CONVERT/To UV Shell")
    assert uv_shell_select.active(bpy.context) or not bpy.context.scene.tool_settings.use_uv_select_sync


# --- #507: the UV Editor menu bar's Select > Convert Selection converts like the Ctrl+RMB menu ----------------------

def test_menu_bar_convert_selection_converts():
    ob = _grid()
    _select_uvs(ob, lambda v: (round(v.co.x), round(v.co.y)) in {(0, 0), (1, 0), (0, 1), (1, 1), (2, 0)})
    a, r = _uv_area()
    with bpy.context.temp_override(area=a, region=r):
        assert bpy.ops.allset.menu_item(item="UV Editor/Select/Convert Selection/To Faces") == {'FINISHED'}
    ts = bpy.context.scene.tool_settings
    assert ts.use_uv_select_sync and tuple(ts.mesh_select_mode) == (False, False, True)
    _v, _e, faces = _selected(ob)
    assert faces == {0}, faces
