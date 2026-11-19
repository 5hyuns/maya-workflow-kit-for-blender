"""#392: UV > Camera-based maps from the view like Maya's camera-based projection. With an object selected in object
mode it maps every face of the object and comes back to object mode (the main UV menu, the UV Editor's Create menu and
the marking menu item all run the same item); in component mode it maps the selected faces.
GUI: tests/gui/gui_issue392_393_uv.py."""

from importlib import import_module

import bmesh
import bpy

import kit

menu_map = import_module(kit.MODULE + ".ui.menu_map")
mm = import_module(kit.MODULE + ".marking.menus")


def _window():
    """The main window: a Maya menu item runs its 3D View commands in that window's largest 3D View."""
    return bpy.context.temp_override(window=bpy.context.window_manager.windows[0])


def _cylinder():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.ops.allset.create(kind='CYLINDER')
    ob = bpy.context.active_object
    if ob.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.scene.objects:
        o.select_set(o is ob)
    bpy.context.view_layer.objects.active = ob
    return ob


def _uvs(ob):
    """UV per face corner, rounded, read from the mesh (object mode) or the edit mesh."""
    if ob.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(ob.data)
    else:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    out = [[(lp.vert.index, round(lp[uv].uv.x, 5), round(lp[uv].uv.y, 5)) for lp in f.loops] for f in bm.faces]
    if ob.mode != 'EDIT':
        bm.free()
    return out


def _one_uv_per_vertex(corners):
    """A projection from the view gives each vertex one UV: no seams, one shell."""
    return len({c for f in corners for c in f}) == len({c[0] for f in corners for c in f})


def test_every_camera_based_item_runs_the_main_menu_item():
    assert "UV/Camera-based" in menu_map.MAP
    assert menu_map.spec("UV Editor/Create/Camera-based") == menu_map.spec("UV/Camera-based")
    _label, sub = mm._mapping()          # the Shift+RMB Mapping submenu
    assert dict(sub.items)["Camera-Based Map"] == ("item", "UV/Camera-based")


def test_camera_based_from_object_mode_maps_the_whole_object():
    wrong = []
    for item in ("UV/Camera-based", "UV Editor/Create/Camera-based"):
        ob = _cylinder()
        before = _uvs(ob)
        assert not _one_uv_per_vertex(before), "the Maya cylinder has seams"
        with _window():
            res = bpy.ops.allset.menu_item(item=item)
        assert res == {'FINISHED'}, (item, res)
        after = _uvs(ob)
        if bpy.context.mode != 'OBJECT':
            wrong.append((item, "mode", bpy.context.mode))
        if after == before:
            wrong.append((item, "the UVs did not change"))
        elif not _one_uv_per_vertex(after):
            wrong.append((item, "not every face mapped from the view"))
    assert not wrong, wrong


def test_camera_based_in_component_mode_maps_the_selected_faces():
    ob = _cylinder()
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select_set(False)
    picked = [f.index for f in bm.faces if len(f.verts) == 4][:3]
    for i in picked:
        bm.faces[i].select_set(True)
    bmesh.update_edit_mesh(ob.data)
    before = _uvs(ob)
    with _window():
        res = bpy.ops.allset.menu_item(item="UV/Camera-based")
    assert res == {'FINISHED'}, res
    assert bpy.context.mode == 'EDIT_MESH'
    after = _uvs(ob)
    changed = {i for i, (a, b) in enumerate(zip(before, after)) if a != b}
    assert changed == set(picked), (changed, picked)
    bpy.ops.object.mode_set(mode='OBJECT')
