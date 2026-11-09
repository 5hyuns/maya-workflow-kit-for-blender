"""#342: Mesh Display > Soften Edge / Harden Edge / Soften/Harden Edges change what the mesh shows, also on a mesh with
history: a bevelled cube (polyBevel1 + Maya's smooth normals) that carries Blender's "Smooth by Angle" modifier, which
used to harden every edge over 30 degrees again after Soften Edge. Checked on the evaluated mesh (corner normals
after the whole modifier stack), in object mode and on selected edges, from the menu items, the Shift+RMB marking
menus and with undo."""

import math
from importlib import import_module

import bmesh
import bpy

import kit

display = import_module(kit.MODULE + ".operators.display")
extrude = import_module(kit.MODULE + ".operators.extrude")
menu_items = import_module(kit.MODULE + ".operators.menu_items")
mm = import_module(kit.MODULE + ".marking.menus")
modal = import_module(kit.MODULE + ".marking.modal")

SBA = "Smooth by Angle"


def _fresh():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    extrude.clear()


def _select(ob):
    for o in bpy.context.view_layer.objects:
        o.select_set(o is ob)
    bpy.context.view_layer.objects.active = ob


def _cube():
    assert bpy.ops.allset.create(kind='CUBE') == {'FINISHED'}
    return bpy.context.view_layer.objects.active


def _edit_edges(ob, pick):
    """Edit mode, edge select mode, only the edges ``pick(bm, e)`` selected."""
    _select(ob)
    if bpy.context.mode != 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    for e in bm.edges:
        if pick(bm, e):
            e.select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _vertical(bm, e):
    a, b = e.verts
    return abs(a.co.x - b.co.x) < 1e-6 and abs(a.co.y - b.co.y) < 1e-6


def _history_cube():
    """The issue's object: a kit cube, its four side edges bevelled in two segments (polyBevel1, Maya's smooth
    normals), then Blender's Shade Auto Smooth (a "Smooth by Angle" modifier, 30 degrees)."""
    _fresh()
    ob = _cube()
    _edit_edges(ob, _vertical)
    assert bpy.ops.allset.bevel(segments=2) == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    _select(ob)
    assert bpy.ops.object.shade_auto_smooth() == {'FINISHED'}
    assert ob.modifiers.get(display.NORMALS_MOD_NAME) is not None
    assert any(m.type == 'NODES' and m.node_group and m.node_group.name.startswith(SBA) for m in ob.modifiers)
    return ob


def _shown(ob):
    """{edge index: soft} for every edge between two faces that meet at an angle (more than 1 degree), read from the
    evaluated mesh: soft = both faces have the same corner normal at both ends of the edge."""
    dg = bpy.context.evaluated_depsgraph_get()
    eo = ob.evaluated_get(dg)
    me = eo.to_mesh()
    normal = {}
    faces = {}
    for p in me.polygons:
        for li in p.loop_indices:
            normal[(me.loops[li].vertex_index, p.index)] = me.corner_normals[li].vector.copy()
        for key in p.edge_keys:
            faces.setdefault(key, []).append(p.index)
    out = {}
    for e in me.edges:
        fs = faces.get(e.key, [])
        if len(fs) != 2:
            continue
        a, b = fs
        if me.polygons[a].normal.angle(me.polygons[b].normal, 0.0) < math.radians(1.0):
            continue
        out[e.index] = all((normal[(v, a)] - normal[(v, b)]).length < 1e-4 for v in e.vertices)
    eo.to_mesh_clear()
    return out


def _angles(ob):
    """{edge index: angle in degrees between its two faces} of the base mesh (edges with two faces)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    out = {e.index: math.degrees(e.calc_face_angle(0.0)) for e in bm.edges if len(e.link_faces) == 2}
    bm.free()
    return out


def _sba(ob):
    return [m.name for m in ob.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name.startswith(SBA)]


def _menu(item):
    return bpy.ops.allset.menu_item('EXEC_DEFAULT', True, item=item)


def test_soften_edge_on_history_object():
    """Object mode, Mesh Display > Soften Edge: every edge of the bevelled cube shades soft after the whole stack."""
    ob = _history_cube()
    _select(ob)
    before = _shown(ob)
    assert before and not all(before.values()), "the cube shows hard edges before"
    assert _menu("Mesh Display/Soften Edge") == {'FINISHED'}
    shown = _shown(ob)
    hard = [i for i, soft in shown.items() if not soft]
    assert not hard, f"{len(hard)} of {len(shown)} edges still shade hard after Soften Edge"
    assert not _sba(ob), "Soften Edge on the object takes the place of the Smooth by Angle modifier"
    assert ob.modifiers.get(display.NORMALS_MOD_NAME) is not None, "Maya's smooth normals stay"


def test_harden_edge_on_history_object():
    ob = _history_cube()
    _select(ob)
    assert _menu("Mesh Display/Soften Edge") == {'FINISHED'}
    assert _menu("Mesh Display/Harden Edge") == {'FINISHED'}
    shown = _shown(ob)
    soft = [i for i, s in shown.items() if s]
    assert shown and not soft, f"{len(soft)} of {len(shown)} edges still shade soft after Harden Edge"


def test_soften_harden_angle_on_history_object():
    """Soften/Harden Edges with the option box angle 60: the bevel strips (22.5 / 45 degrees) shade soft, the cube's
    90 degree edges hard, also where Smooth by Angle (30) would have hardened the 45 degree edges."""
    ob = _history_cube()
    _select(ob)
    assert bpy.ops.allset.soften_harden('EXEC_DEFAULT', True, angle=60.0) == {'FINISHED'}
    shown, angles = _shown(ob), _angles(ob)
    wrong = [(i, round(angles[i], 1), s) for i, s in shown.items() if s != (angles[i] <= 60.0)]
    assert not wrong, f"edges shaded against the 60 degree rule: {wrong[:8]}"
    assert any(40.0 < angles[i] < 50.0 for i in shown), "the cube has 45 degree bevel edges"


def test_soften_selected_edges_with_smooth_by_angle():
    """Edge mode on the history cube: Soften Edge on the top rim edges (90 degrees: the four sides and the bevel
    strips' eight) shades them soft; every other edge keeps what it showed before."""
    ob = _history_cube()
    before = _shown(ob)
    top = max(v.co.z for v in ob.data.vertices)

    def rim(bm, e):
        return all(abs(v.co.z - top) < 1e-6 for v in e.verts) and len(e.link_faces) == 2 and \
            e.calc_face_angle(0.0) > math.radians(80.0)
    _edit_edges(ob, rim)
    picked = {e.index for e in bmesh.from_edit_mesh(ob.data).edges if e.select}
    assert len(picked) == 12, picked
    assert _menu("Mesh Display/Soften Edge") == {'FINISHED'}
    assert bpy.context.mode == 'EDIT_MESH', "Soften Edge keeps component mode"
    bpy.ops.object.mode_set(mode='OBJECT')
    shown = _shown(ob)
    assert all(shown[i] for i in picked), [(i, shown[i]) for i in picked]
    changed = [i for i in shown if i not in picked and shown[i] != before[i]]
    assert not changed, f"edges that were not selected changed: {changed}"


def test_harden_selected_edges_keeps_smooth_by_angle():
    """Harden Edge on selected edges shows through the Smooth by Angle modifier (it keeps hard edges hard), so the
    modifier stays."""
    ob = _history_cube()
    names = _sba(ob)
    _edit_edges(ob, lambda bm, e: len(e.link_faces) == 2 and 10.0 < math.degrees(e.calc_face_angle(0.0)) < 30.0)
    picked = {e.index for e in bmesh.from_edit_mesh(ob.data).edges if e.select}
    assert picked
    assert _menu("Mesh Display/Harden Edge") == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    shown = _shown(ob)
    assert not any(shown[i] for i in picked)
    assert _sba(ob) == names


def test_plain_cube_object_and_edges():
    """No history: Soften Edge on the object shades every edge soft; on one selected edge only that edge."""
    _fresh()
    ob = _cube()
    _select(ob)
    assert not any(_shown(ob).values()), "a new cube shades hard"
    assert _menu("Mesh Display/Soften Edge") == {'FINISHED'}
    assert all(_shown(ob).values())
    assert _menu("Mesh Display/Harden Edge") == {'FINISHED'}
    assert not any(_shown(ob).values())
    _edit_edges(ob, lambda bm, e: e.index == 0)
    assert _menu("Mesh Display/Soften Edge") == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    shown = _shown(ob)
    assert shown[0] and not any(s for i, s in shown.items() if i != 0), shown


def test_undo_brings_back_the_modifier_and_edges():
    ob = _history_cube()
    _select(ob)
    before, names, name = _shown(ob), _sba(ob), ob.name
    bpy.ops.ed.undo_push(message="before")
    assert _menu("Mesh Display/Soften Edge") == {'FINISHED'}
    assert not _sba(ob) and all(_shown(ob).values())
    bpy.ops.ed.undo()
    ob = bpy.data.objects[name]
    assert _sba(ob) == names, _sba(ob)
    assert _shown(ob) == before


def _sub(menu, key):
    return menu.radial[key][1]


def test_marking_menus_run_the_mesh_display_items():
    """Shift+RMB object and edge marking menus: Harden Edge / Soften/Harden / Soften Edge are the Mesh Display
    items (Maya runs the same commands there)."""
    want = {"SE": "Mesh Display/Harden Edge", "E": "Mesh Display/Soften/Harden Edges",
            "NE": "Mesh Display/Soften Edge"}
    for menu, key in ((mm.SHIFT_OBJECT, "SE"), (mm.SHIFT_EDGE, "SE")):
        sub = _sub(menu, key)
        got = {k: sub.radial[k][1] for k in want}
        assert got == {k: ("item", p) for k, p in want.items()}, (menu.name, got)
        assert "Soften/Harden" in sub.options


def test_marking_menu_soften_edge_on_kit_cube():
    """Shift+RMB > Soften/Harden Edges > Soften Edge on a kit cube (its hard edges are marked sharp) and on the
    history cube: every edge shades soft."""
    _fresh()
    ob = _cube()
    _select(ob)
    action = _sub(mm.SHIFT_OBJECT, "SE").radial["NE"][1]
    assert modal.run_action(bpy.context, action) == {'FINISHED'}
    assert all(_shown(ob).values()), _shown(ob)
    ob = _history_cube()
    _select(ob)
    assert modal.run_action(bpy.context, action) == {'FINISHED'}
    assert all(_shown(ob).values())
    assert not _sba(ob)


def test_smooth_by_angle_rule():
    """The kit's copy of the Smooth by Angle rule (used to keep the look of edges that are not selected) gives what
    Blender's modifier shows on the history cube."""
    ob = _history_cube()
    shown = _shown(ob)
    md = ob.modifiers[_sba(ob)[0]]
    angle, ignore = menu_items.smooth_by_angle_inputs(md)
    assert abs(angle - math.radians(30.0)) < 1e-6 and ignore is False
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    menu_items.smooth_by_angle(bm, angle, ignore)
    got = {e.index: e.smooth for e in bm.edges if e.index in shown}
    bm.free()
    assert got == shown, [(i, got[i], shown[i]) for i in shown if got[i] != shown[i]]
