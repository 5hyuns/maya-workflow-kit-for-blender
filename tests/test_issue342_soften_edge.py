"""#342: Mesh Display > Soften Edge / Harden Edge / Soften/Harden Edges change what the mesh shows, also on a mesh with
history: a bevelled cube (polyBevel1 + Maya's smooth normals) that carries Blender's "Smooth by Angle" modifier, which
used to harden every edge over 30 degrees again after Soften Edge. Checked on the evaluated mesh (corner normals
after the whole modifier stack), in object mode and on selected edges, from the menu items, the Shift+RMB marking
menus and with undo: in component mode one Ctrl+Z brings back the edges and the modifier together (and the
selection, still in component mode), one Shift+Z the result."""

import ctypes
import math
import os
import sys
import tempfile
from importlib import import_module

import bmesh
import bpy

import kit

compat = import_module(kit.MODULE + ".compat")
display = import_module(kit.MODULE + ".operators.display")
extrude = import_module(kit.MODULE + ".operators.extrude")
menu_items = import_module(kit.MODULE + ".operators.menu_items")
undo_pairs = import_module(kit.MODULE + ".operators.undo_pairs")
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


# --- undo in component mode -----------------------------------------------------------------------------------------

def _extra():
    """The kit's extra undo / redo steps now (a timer in the UI); returns what was waiting."""
    if bpy.app.timers.is_registered(undo_pairs.run_extra):
        bpy.app.timers.unregister(undo_pairs.run_extra)
    wanted = undo_pairs.wanted()
    undo_pairs.run_extra()
    return wanted


def _undo():
    bpy.ops.ed.undo()
    return _extra()


def _redo():
    bpy.ops.ed.redo()
    return _extra()


def _plain(v):
    if hasattr(v, "to_dict"):
        return v.to_dict()
    if isinstance(v, (str, bool, int, float)) or v is None:
        return v
    if isinstance(v, set):
        return tuple(sorted(v))
    try:
        return tuple(_plain(x) for x in v)
    except TypeError:
        return getattr(v, "name", repr(v))


def _modifier(md):
    """Every setting of a modifier (and a Geometry Nodes modifier's inputs)."""
    out = {"name": md.name, "type": md.type}
    for p in md.bl_rna.properties:
        if p.identifier in ("rna_type", "execution_time") or p.type == 'COLLECTION':
            continue
        v = getattr(md, p.identifier, None)
        out[p.identifier] = getattr(v, "name", None) if p.type == 'POINTER' else _plain(v)
    if md.type == 'NODES' and md.node_group is not None:
        out["inputs"] = {it.identifier: _plain(compat.gn_input_get(md, it.identifier))
                         for it in md.node_group.interface.items_tree
                         if getattr(it, "in_out", None) == 'INPUT'
                         and getattr(it, "socket_type", "") != 'NodeSocketGeometry'}
    return out


def _state(name):
    """What Ctrl+Z must bring back: mode, selection, edge / face shading flags, the modifier stack with every setting,
    a change made in component mode outside the mesh (the object's custom property) and what the evaluated mesh
    shows."""
    ob = bpy.data.objects[name]
    if ob.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(ob.data)
    else:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
    out = {
        "mode": bpy.context.mode,
        "select_mode": tuple(bpy.context.scene.tool_settings.mesh_select_mode),
        "verts": tuple(v.select for v in bm.verts),
        "edges": tuple(e.select for e in bm.edges),
        "faces": tuple(f.select for f in bm.faces),
        "soft": tuple(e.smooth for e in bm.edges),
        "face_smooth": tuple(f.smooth for f in bm.faces),
        "modifiers": [_modifier(md) for md in ob.modifiers],
        "session": ob.get("session"),
        "shown": _shown(ob),
    }
    if ob.mode != 'EDIT':
        bm.free()
    return out


def _diff(a, b):
    return {k: (a[k], b[k]) for k in a if a[k] != b[k]}


def _top_rim(bm, e):
    top = max(v.co.z for v in bm.verts)
    return all(abs(v.co.z - top) < 1e-6 for v in e.verts) and len(e.link_faces) == 2 and \
        e.calc_face_angle(0.0) > math.radians(80.0)


def _pick(ob, pick):
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    for e in bm.edges:
        if pick(bm, e):
            e.select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _component_mode(tab=True):
    """The history cube in edge mode with its top rim selected, like a user gets there: Tab (Blender's undo step,
    ``tab``) and a selection (its own step). In component mode the object also gets a custom property — a change
    outside the mesh that only object-mode undo steps hold."""
    ob = _history_cube()
    _select(ob)
    name = ob.name
    bpy.ops.ed.undo_push(message="history cube")
    if tab:
        assert bpy.ops.object.editmode_toggle('EXEC_DEFAULT', True) == {'FINISHED'}
    else:
        bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    entered = _state(name)
    _pick(ob, _top_rim)
    if tab:
        bpy.ops.ed.undo_push(message="Select")
    ob["session"] = 1
    ob.update_tag()
    return name, entered


def test_component_mode_undo_takes_back_edges_and_modifier_together():
    """Edge mode, Soften Edge on the rim makes the Smooth by Angle modifier give way. One Ctrl+Z: the state before,
    exactly (component mode, selection, edge flags, the modifier with its settings and place in the stack, the custom
    property) - Blender's own step, nothing after it. One Shift+Z: the result, back in component mode. The next
    Ctrl+Z takes back the selection: no press is lost on the command's object-mode steps."""
    undo_pairs.reset()
    name, entered = _component_mode()
    before = _state(name)
    assert len(_sba(bpy.data.objects[name])) == 1 and sum(before["edges"]) == 12
    assert _menu("Mesh Display/Soften Edge") == {'FINISHED'}
    after = _state(name)
    assert after["mode"] == 'EDIT_MESH' and after["edges"] == before["edges"], "component mode, same selection"
    assert not _sba(bpy.data.objects[name]), "the modifier gave way"
    picked = [i for i, s in enumerate(before["edges"]) if s]
    assert all(after["shown"][i] for i in picked), "the rim shades soft"
    assert after["session"] == 1

    assert _undo() is None, "one Blender undo step lands on the state before"
    assert _state(name) == before, _diff(_state(name), before)
    assert _redo() == undo_pairs.EDIT, "Shift+Z lands on the result and goes back to component mode"
    assert _state(name) == after, _diff(_state(name), after)
    assert _undo() is None
    assert _state(name) == before, _diff(_state(name), before)

    assert _undo() == 'UNDO'                  # the selection
    st = _state(name)
    assert st["mode"] == 'EDIT_MESH' and st["edges"] == entered["edges"], "the next Ctrl+Z took back the selection"
    assert len(_sba(bpy.data.objects[name])) == 1
    _undo()                                   # Tab
    assert bpy.context.mode == 'OBJECT'
    assert _redo() is None and bpy.context.mode == 'EDIT_MESH'
    assert _redo() is None and _state(name)["edges"] == before["edges"]
    assert _redo() == 'REDO', "Shift+Z from the selection goes on to the result"
    assert _state(name) == after, _diff(_state(name), after)


def test_component_mode_entered_without_an_undo_step():
    """Component mode entered by a script (no Tab step, no selection step): one Ctrl+Z still lands on the state
    before in component mode, the next one on the object-mode step before it; Shift+Z comes back the same way."""
    undo_pairs.reset()
    name, _entered = _component_mode(tab=False)
    before = _state(name)
    assert _menu("Mesh Display/Soften Edge") == {'FINISHED'}
    after = _state(name)
    _undo()
    assert _state(name) == before, _diff(_state(name), before)
    _undo()
    assert bpy.context.mode == 'OBJECT' and len(_sba(bpy.data.objects[name])) == 1
    _redo()
    assert _state(name) == before, _diff(_state(name), before)
    _redo()
    assert _state(name) == after, _diff(_state(name), after)


def test_undo_after_more_component_work():
    """After Soften Edge the user selects other edges: Ctrl+Z takes back that selection and stays in component mode
    on the result; the next Ctrl+Z is the state before Soften Edge."""
    undo_pairs.reset()
    name, _entered = _component_mode()
    before = _state(name)
    assert _menu("Mesh Display/Soften Edge") == {'FINISHED'}
    after = _state(name)
    _pick(bpy.data.objects[name], lambda bm, e: e.index < 3)
    bpy.ops.ed.undo_push(message="Select")
    assert _state(name)["edges"] != after["edges"]
    assert _undo() == undo_pairs.EDIT
    assert _state(name) == after, _diff(_state(name), after)
    assert _undo() is None
    assert _state(name) == before, _diff(_state(name), before)
    assert _redo() == undo_pairs.EDIT
    assert _state(name) == after, _diff(_state(name), after)


def test_tab_out_and_back_in_after_soften_edge():
    """Soften Edge, Tab to object mode and back: Ctrl+Z takes back the Tab into component mode (object mode), the
    next one the Tab out (component mode, the result), the next one Soften Edge."""
    undo_pairs.reset()
    name, _entered = _component_mode()
    before = _state(name)
    assert _menu("Mesh Display/Soften Edge") == {'FINISHED'}
    after = _state(name)
    assert bpy.ops.object.editmode_toggle('EXEC_DEFAULT', True) == {'FINISHED'}
    bpy.context.view_layer.update()            # the UI draws (and evaluates) after every step
    assert bpy.ops.object.editmode_toggle('EXEC_DEFAULT', True) == {'FINISHED'}
    bpy.context.view_layer.update()
    assert bpy.context.mode == 'EDIT_MESH'
    assert _undo() is None
    assert bpy.context.mode == 'OBJECT'
    assert _undo() == undo_pairs.EDIT
    assert _state(name) == after, _diff(_state(name), after)
    assert _undo() is None
    assert _state(name) == before, _diff(_state(name), before)


def test_component_mode_without_giving_way_is_one_edit_mode_step():
    """Harden Edge on selected edges shows through the modifier: no trip through object mode, a plain edit-mode undo
    step (Ctrl+Z needs no extra step)."""
    undo_pairs.reset()
    ob = _history_cube()
    _select(ob)
    name = ob.name
    bpy.ops.ed.undo_push(message="history cube")
    assert bpy.ops.object.editmode_toggle('EXEC_DEFAULT', True) == {'FINISHED'}
    bpy.ops.mesh.select_mode(type='EDGE')
    _pick(ob, lambda bm, e: len(e.link_faces) == 2 and 10.0 < math.degrees(e.calc_face_angle(0.0)) < 30.0)
    bpy.ops.ed.undo_push(message="Select")
    before = _state(name)
    assert _menu("Mesh Display/Harden Edge") == {'FINISHED'}
    assert len(_sba(bpy.data.objects[name])) == 1
    assert _state(name) != before
    assert _undo() is None, "a plain edit-mode step"
    assert _state(name) == before, _diff(_state(name), before)
    assert _redo() is None
    assert len(_sba(bpy.data.objects[name])) == 1


def test_option_box_run_is_one_undo_step_and_opens_no_redo_panel():
    """The Soften/Harden Edges option window runs the command from the UI (undo depth 0): the same one Ctrl+Z /
    one Shift+Z, and no Adjust Last Operation (it would undo only part of the command)."""
    cls = bpy.types.ALLSET_OT_soften_harden
    assert 'UNDO' not in cls.bl_options, "Blender's redo panel needs UNDO"
    undo_pairs.reset()
    name, _entered = _component_mode()
    before = _state(name)
    assert bpy.ops.allset.soften_harden('EXEC_DEFAULT', True, angle=180.0) == {'FINISHED'}
    after = _state(name)
    assert not _sba(bpy.data.objects[name])
    assert _undo() is None
    assert _state(name) == before, _diff(_state(name), before)
    assert _redo() == undo_pairs.EDIT
    assert _state(name) == after, _diff(_state(name), after)


def test_plain_commands_still_one_undo_step_from_the_ui():
    """Without the trip (object mode here) a run from the UI (undo depth 0) is one undo step, like before."""
    undo_pairs.reset()
    ob = _history_cube()
    _select(ob)
    name = ob.name
    bpy.ops.ed.undo_push(message="history cube")
    shown = _shown(ob)
    assert bpy.ops.allset.soften_harden('EXEC_DEFAULT', True, angle=180.0) == {'FINISHED'}
    assert not _sba(ob)
    bpy.ops.ed.undo()
    ob = bpy.data.objects[name]
    assert len(_sba(ob)) == 1 and _shown(ob) == shown


# --- Edit > Undo History ----------------------------------------------------------------------------------------

def _undo_steps():
    """(name, type, active) of every undo step, oldest first, as Blender prints them (to the C stdout only)."""
    crt = ctypes.cdll.ucrtbase
    crt.fflush(None)
    sys.stdout.flush()
    fd, path = tempfile.mkstemp(suffix=".txt")
    saved = os.dup(1)
    try:
        os.dup2(fd, 1)
        bpy.context.window_manager.print_undo_steps()
        crt.fflush(None)
    finally:
        os.dup2(saved, 1)
        os.close(saved)
        os.close(fd)
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = [ln for ln in f.read().splitlines() if "name=" in ln]
    os.remove(path)
    return [(ln.split("name='", 1)[1].rstrip("'"), ln.split("type='", 1)[1].split("'", 1)[0], "*" in ln[:6])
            for ln in lines]


def _jump(index):
    """Click line ``index`` of Edit > Undo History; returns the kit's extra step that followed."""
    assert bpy.ops.ed.undo_history(item=index) == {'FINISHED'}
    return _extra()


def test_undo_history_lines_and_where_each_one_lands():
    """After Soften Edge in component mode Undo History lists Select, Object Mode, Edit Mode, Soften Edge (like Tab's
    steps around the command). Each line lands on what it names: Edit Mode = the state before in component mode,
    Soften Edge = the result in component mode, Object Mode (a jump back from the result) = the state before in object
    mode, without going past it. Shift+Z from there: Edit Mode, then the result. Ctrl+Z keeps working one command at
    a time. A jump forward onto Object Mode goes on to the result, like Shift+Z."""
    undo_pairs.reset()
    name, entered = _component_mode()
    before = _state(name)
    assert _menu("Mesh Display/Soften Edge") == {'FINISHED'}
    after = _state(name)
    steps = _undo_steps()
    active = next(i for i, s in enumerate(steps) if s[2])
    assert active == len(steps) - 1
    # Blender 5.3 prints the step type's identifier (EDIT_MESH), earlier versions its name (Edit Mesh)
    tail = [(n, t.replace("_", " ").title()) for n, t, _a in steps[active - 3:active + 1]]
    assert tail == [("Select", "Edit Mesh"), ("Object Mode", "Global Undo"), ("Edit Mode", "Edit Mesh"),
                    ("Soften Edge", "Global Undo")], tail
    select_line, object_line, edit_line, result_line = active - 3, active - 2, active - 1, active
    before_object = {**before, "mode": 'OBJECT'}

    assert _jump(edit_line) is None
    assert _state(name) == before, _diff(_state(name), before)
    assert _jump(result_line) == undo_pairs.EDIT
    assert _state(name) == after, _diff(_state(name), after)

    assert _jump(object_line) is None, "a jump back onto Object Mode stays there"
    assert _state(name) == before_object, _diff(_state(name), before_object)
    assert len(_sba(bpy.data.objects[name])) == 1
    assert _redo() is None, "Shift+Z: the Edit Mode line"
    assert _state(name) == before, _diff(_state(name), before)
    assert _redo() == undo_pairs.EDIT, "Shift+Z: the result"
    assert _state(name) == after, _diff(_state(name), after)

    assert _undo() is None and _state(name) == before, "Ctrl+Z: the state before"
    assert _undo() == 'UNDO', "the next Ctrl+Z takes back the selection"
    st = _state(name)
    assert st["mode"] == 'EDIT_MESH' and st["edges"] == entered["edges"]

    assert _jump(result_line) == undo_pairs.EDIT
    assert _state(name) == after, _diff(_state(name), after)
    assert _jump(select_line) is None
    st = _state(name)
    assert st["mode"] == 'EDIT_MESH' and st["edges"] == before["edges"] and len(_sba(bpy.data.objects[name])) == 1
    assert _jump(object_line) == 'REDO', "forward onto Object Mode: on to the result, like Shift+Z"
    assert _state(name) == after, _diff(_state(name), after)
