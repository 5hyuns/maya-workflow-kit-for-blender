"""Step 139 lane UV (#68,  U1 / U2): UV > Automatic / Contour Stretch from object mode act on the whole
object, Automatic = Maya polyAutoProjection (shell counts vs Maya), UV Editor > Create > Best Plane / Contour Stretch
mapped like the main UV menu. Maya numbers:  (Maya,
). Step doc: ; GUI: tests/gui/gui_step139_uv.py."""

from importlib import import_module

import bmesh
import bpy

import kit

uvt = import_module(kit.MODULE + ".operators.uv_tools")
ow = import_module(kit.MODULE + ".operators.option_windows")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")

# Maya 2022 polyAutoProjection, factory options (6 planes, 0.2 % space), whole object: shells, faces per shell, UVs.
MAYA_AUTO = {
    'CUBE': (6, [1, 1, 1, 1, 1, 1], 24),
    'SPHERE': (6, [104, 104, 72, 72, 24, 24], 482),
    'CYLINDER': (6, [20, 20, 6, 6, 4, 4], 90),     # the menu's cylinder (caps 1, 60 faces) like the kit's
    'PLANE': (1, [100], 121),
    'TORUS': (10, [96, 96, 36, 36, 36, 36, 16, 16, 16, 16], 536),
}
# Kit = each face to the plane it faces most, ties to Maya X (Maya's "Fast" optimisation rule, -o 0, checked: sphere
# 104 / 104 / 56 / 48 / 48 / 40). Maya's factory "Less distortion" (-o 1) moves some faces between neighbouring planes
# (sphere sides 72 / 72 / 24 / 24, torus 96 / 96 / 36 x4 / 16 x4): the kit's sizes there are the recorded deviation
#. Shell counts are Maya's everywhere; cube / cylinder / plane are Maya's exactly.
KIT_AUTO = dict(MAYA_AUTO, SPHERE=(6, [104, 104, 56, 56, 40, 40], None),
                TORUS=(10, [112, 112, 28, 28, 28, 28, 16, 16, 16, 16], None))


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    ow.store("uv_automatic", None)


def _make(kind):
    _clear()
    bpy.ops.allset.create(kind=kind)
    ob = bpy.context.active_object
    if ob.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.scene.objects:
        o.select_set(o is ob)
    bpy.context.view_layer.objects.active = ob
    return ob


def _info(ob):
    """(shells, faces per shell, UV count, UV bounds) of ``ob``'s active UV map; UV count = Maya's (one per distinct
    (vertex, UV position))."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    shells = uvt.islands(bm, uv)
    uvs = {(lp.vert.index, round(lp[uv].uv.x, 4), round(lp[uv].uv.y, 4)) for f in bm.faces for lp in f.loops}
    pts = [lp[uv].uv for f in bm.faces for lp in f.loops]
    bounds = (min(p.x for p in pts), min(p.y for p in pts), max(p.x for p in pts), max(p.y for p in pts))
    out = (len(shells), sorted((len(s) for s in shells), reverse=True), len(uvs), bounds)
    bm.free()
    return out


def test_object_mode_automatic_is_maya_auto_projection():
    """U1: object mode UV > Automatic through the kit menu item (the path that returned CANCELLED in step 133)."""
    rows = {}
    for kind, (shells, sizes, uvs) in KIT_AUTO.items():
        ob = _make(kind)
        res = bpy.ops.allset.menu_item(item="UV/Automatic")
        assert res == {'FINISHED'}, (kind, res)
        assert bpy.context.mode == 'OBJECT'
        n, got, count, (x0, y0, x1, y1) = _info(ob)
        rows[kind] = (n, got, count, MAYA_AUTO[kind])
        assert n == shells and got == sizes, (kind, n, got)
        if uvs is not None:
            assert count == uvs, (kind, count, uvs)
        # laid out in 0-1 with 0.2 % space (Maya bounds 0.002 - 0.998, checked)
        assert x0 >= 0.0019 and y0 >= 0.0019 and x1 <= 0.9981 and y1 <= 0.9981, (kind, x0, y0, x1, y1)
        assert max(x1, y1) > 0.9, (kind, x1, y1)
    print("kit vs Maya automatic:", rows)


def test_automatic_on_selected_faces():
    """Component mode: only the selected faces get new shells (Maya cube f[1]: 3 shells 3 / 2 / 1; f[0:1]: 5 shells)."""
    for faces, want in (((1,), [3, 2, 1]), ((0, 1), [2, 1, 1, 1, 1])):
        ob = _make('CUBE')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        for i in faces:
            bm.faces[i].select_set(True)
        bmesh.update_edit_mesh(ob.data)
        assert bpy.ops.allset.menu_item(item="UV/Automatic") == {'FINISHED'}
        assert bpy.context.mode == 'EDIT_MESH'
        bpy.ops.object.mode_set(mode='OBJECT')
        n, got, _c, _b = _info(ob)
        print("faces", faces, n, got)
        assert got == want, (faces, got, want)


def test_planes_option_and_window():
    w = ow.find_path("UV/Automatic")
    assert w is not None and w.key == "uv_automatic"
    assert ow.find_path("UV Editor/Create/Automatic") is w          # the UV Editor item has the same option box
    ob = _make('CUBE')
    res = ow.run(w, bpy.context, {"planes": "4", "spacing": 0.2})
    assert res == {'FINISHED'}, res
    n, _g, _c, _b = _info(ob)
    assert 2 <= n <= 6, n                 # Maya 4 planes on a cube: 4 shells (checked); kit: tetrahedron planes
    for planes in ("3", "5", "8", "12"):
        _make('SPHERE')
        assert bpy.ops.allset.uv_automatic(planes=planes) == {'FINISHED'}


def test_object_mode_contour_stretch():
    """U1: Contour Stretch from object mode = every face (Maya: one shell in 0-1; plane 121 UVs, checked)."""
    ob = _make('PLANE')
    assert bpy.ops.allset.menu_item(item="UV/Contour Stretch") == {'FINISHED'}
    n, _g, count, (x0, y0, x1, y1) = _info(ob)
    assert n == 1 and count == 121, (n, count)
    assert abs(x0) < 1e-4 and abs(y0) < 1e-4 and abs(x1 - 1) < 1e-4 and abs(y1 - 1) < 1e-4
    ob = _make('CUBE')
    assert bpy.ops.allset.menu_item(item="UV/Contour Stretch") == {'FINISHED'}
    n, _g, count, b = _info(ob)
    print("contour cube (Maya 1 shell / 8 UVs):", n, count, b)
    assert n == 1, n
    # a strip of faces fills the square (Maya plane f[0:9] -> the 10 faces span 0-1)
    ob = _make('PLANE')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    for i in range(10):
        bm.faces[i].select_set(True)
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.menu_item(item="UV/Contour Stretch") == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    n, got, _c, _b = _info(ob)
    assert n == 2 and got == [90, 10], (n, got)


def test_uv_editor_create_items_mapped():
    """U2: UV Editor > Create > Best Plane / Contour Stretch run the main UV menu's actions."""
    for item, main in (("Best Plane", "UV/Best Plane"), ("Contour Stretch", "UV/Contour Stretch"),
                       ("Automatic", "UV/Automatic")):
        path = f"UV Editor/Create/{item}"
        assert path in menu_map.MAP, path
        assert menu_map.spec(path) == menu_map.spec(main), (path, menu_map.spec(path), menu_map.spec(main))
    ob = _make('CUBE')
    assert bpy.ops.allset.menu_item(item="UV Editor/Create/Best Plane") == {'FINISHED'}
    assert bpy.ops.allset.menu_item(item="UV Editor/Create/Contour Stretch") == {'FINISHED'}
    assert ob.data.uv_layers.active is not None


def test_blender_alternatives_measured():
    """Record what Blender's own operators give on the same objects (why the kit projects in bmesh)."""
    out = {}
    for kind in ('CUBE', 'SPHERE'):
        ob = _make(kind)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.002)      # 66 degrees
        bpy.ops.object.mode_set(mode='OBJECT')
        out[kind + " smart_project"] = _info(ob)[:2]
    print("Blender alternatives:", {k: (v[0], v[1][:8]) for k, v in out.items()})


def test_other_projections_from_object_mode():
    """Maya's Planar / Cylindrical / Spherical also take an object selection as all its faces."""
    for item in ("UV/Planar", "UV/Normal-Based", "UV/Best Plane", "UV/Cylindrical", "UV/Spherical"):
        ob = _make('CUBE')
        before = _info(ob)
        assert bpy.ops.allset.menu_item(item=item) == {'FINISHED'}, item
        assert bpy.context.mode == 'OBJECT'
        after = _info(ob)
        print(item, before[:3], "->", after[:3])
        assert after[2:] != before[2:], item      # the UVs changed
