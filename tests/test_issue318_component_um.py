"""Universal Manipulator on mesh components (#318, component mode): Ctrl+T in a component mode picks the same kit tool;
the box surrounds the selected vertices (World, or the object's axes in Local); a corner drag, an edge rotate and a
typed length run Blender's transforms on the selected components only; Rotate around Pivot turns them about the
selection's centre point. A drag's preview state is the selected vertices' positions."""

import math
from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit

um = import_module(kit.MODULE + ".operators.universal_manip")
ui_um = import_module(kit.MODULE + ".ui.universal_manip")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
TOL = 1e-4


def _close(a, b, eps=TOL):
    return all(abs(x - y) <= eps for x, y in zip(a, b))


def _cube(pick):
    """A 1-unit cube in edit mode with the vertices ``pick`` says selected (others deselected)."""
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.faces, *bm.edges, *bm.verts):
        el.select = False
    for v in bm.verts:
        v.select = bool(pick(v.co))
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    um.settings(bpy.context).property_unset("space")
    um.settings(bpy.context).property_unset("rotate_around")
    return ob


def _top(co):
    return co.z > 0.0


def _coords(ob, pick=None):
    bm = bmesh.from_edit_mesh(ob.data)
    return [v.co.copy() for v in bm.verts if pick is None or pick(v)]


def _box():
    frame, lo, hi = um.box_of(bpy.context)
    return tuple(round(v, 4) for v in lo), tuple(round(v, 4) for v in hi)


def _maya_items(keymap, key, **mods):
    kc = kit.maya_kc()
    km = kc.keymaps.get(keymap)
    out = []
    for kmi in km.keymap_items:
        if kmi.type == key and all(getattr(kmi, k) == v for k, v in mods.items()) and kmi.active:
            out.append((kmi.idname, getattr(kmi.properties, "name", None)))
    return out


def test_ctrl_t_in_component_mode_picks_the_same_tool():
    assert ("wm.tool_set_by_id", um.TOOL) in _maya_items("Mesh", 'T', ctrl=True)
    from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active
    ids = [item.idname for item, _i in ToolSelectPanelHelper._tools_flatten_with_tool_index(
        VIEW3D_PT_tools_active.tools_from_context(bpy.context, mode='EDIT_MESH')) if item is not None]
    assert um.TOOL in ids
    assert um.TOOL not in menu_sets.COMPONENT_TWIN
    assert ui_um.ALLSET_TL_universal_manip_mesh.bl_context_mode == 'EDIT_MESH'


def test_box_surrounds_the_selected_vertices():
    ob = _cube(_top)
    assert um.ready(bpy.context)
    assert _box() == ((-0.5, -0.5, 0.5), (0.5, 0.5, 0.5))
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.select = v.co.z > 0.0 or v.co.y > 0.0
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    assert _box() == ((-0.5, -0.5, -0.5), (0.5, 0.5, 0.5))
    for v in bm.verts:
        v.select = False
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    assert not um.ready(bpy.context) and um.box_of(bpy.context) is None


def test_corner_scale_moves_the_selected_vertices_only():
    ob = _cube(_top)
    frame, lo, hi = um.box_of(bpy.context)
    f, fixed = um.scale_plan(lo, hi, 7, 'FACE', 0, 0.5)          # corner +X +Y +Z dragged 0.5 out along X
    assert _close(f, (1.5, 1.0, 1.0)) and abs(fixed.x - -0.5) < TOL, (f, fixed)
    assert um.apply_scale(f, frame, frame @ fixed, final=True) == {'FINISHED'}
    top = _coords(ob, lambda v: v.co.z > 0.0)
    assert sorted(round(c.x, 4) for c in top) == [-0.5, -0.5, 1.0, 1.0], top     # the -X face stayed
    bottom = _coords(ob, lambda v: v.co.z < 0.0)
    assert all(abs(abs(c.x) - 0.5) < TOL and abs(abs(c.y) - 0.5) < TOL for c in bottom), bottom
    assert _close(ob.scale, (1, 1, 1)) and _close(ob.location, (0, 0, 0))


def test_typed_length_scales_the_components_about_the_box_centre():
    ob = _cube(_top)
    assert bpy.ops.allset.um_size(axis='Y', length=2.0) == {'FINISHED'}
    top = _coords(ob, lambda v: v.co.z > 0.0)
    assert sorted(round(c.y, 4) for c in top) == [-1.0, -1.0, 1.0, 1.0], top
    assert _box() == ((-0.5, -1.0, 0.5), (0.5, 1.0, 0.5))
    assert all(abs(abs(c.y) - 0.5) < TOL for c in _coords(ob, lambda v: v.co.z < 0.0))


def test_rotate_about_the_selection_centre_or_the_box_centre():
    ob = _cube(lambda co: co.z > 0.0 and not (co.x > 0.0 and co.y > 0.0))     # three top corners
    frame, lo, hi = um.box_of(bpy.context)
    pivot = um.rotate_pivot(bpy.context, frame, lo, hi)
    assert _close(pivot, (-1 / 6, -1 / 6, 0.5)), pivot                         # Pivot = the three points' centre
    um.settings(bpy.context).rotate_around = 'CENTER'
    assert _close(um.rotate_pivot(bpy.context, frame, lo, hi), (0, 0, 0.5))
    assert um.apply_rotate(2, math.radians(90), frame, Vector((0, 0, 0.5)), final=True) == {'FINISHED'}
    top = sorted((round(c.x, 4), round(c.y, 4)) for c in _coords(ob, lambda v: v.co.z > 0.0))
    # the three selected corners turned a quarter about the centre; the unselected one (+X +Y) stayed
    assert top == [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (0.5, 0.5)], top
    assert all(abs(c.z + 0.5) < TOL for c in _coords(ob, lambda v: v.co.z < 0.0))


def test_local_space_follows_the_object_axes():
    ob = _cube(_top)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.rotation_euler = (0, 0, math.radians(30))
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.view_layer.update()
    um.settings(bpy.context).space = 'LOCAL'
    frame, lo, hi = um.box_of(bpy.context)
    assert _close(hi - lo, (1, 1, 0)), (lo, hi)
    assert _close(frame.col[0], (math.cos(math.radians(30)), math.sin(math.radians(30)), 0))
    um.settings(bpy.context).space = 'WORLD'
    _f, lo, hi = um.box_of(bpy.context)
    assert (hi - lo).x > 1.0 + 1e-3                                           # the world box of a turned square is wider


def test_drag_state_is_the_selected_vertices():
    ob = _cube(_top)
    state = um.save_state(bpy.context)
    assert state and state[0][0] == "V" and state[0][1] == ob.name and len(state[0][2]) == 4
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        if v.select:
            v.co.z += 1.0
    bmesh.update_edit_mesh(ob.data)
    assert _box()[0][2] == 1.5
    um.restore(state)
    assert _box() == ((-0.5, -0.5, 0.5), (0.5, 0.5, 0.5))
    # the modal drag operators are ready in a component mode with a selection, and not without one
    assert bpy.ops.allset.um_size.poll()
    for v in bm.verts:
        v.select = False
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    assert not bpy.ops.allset.um_size.poll()
