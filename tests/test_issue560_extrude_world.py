"""#560: the face extrusion manipulator has the world / local switch and the light-blue rotate ring, like Maya. On
world axes its handles drive polyExtrudeFace's Translate / Rotate / Scale (world space, about the centre of the
extruded faces' bounding box); the ring drives Local Rotate (each face's local frame about its centre). The local
values and the world values each move a vertex and it takes both; a level of a divided extrusion takes its share."""

import math
from importlib import import_module

import bmesh
import bpy
from mathutils import Matrix

import kit

extrude = import_module(kit.MODULE + ".operators.extrude")
units = import_module(kit.MODULE + ".operators.units")
in_view = import_module(kit.MODULE + ".ui.in_view")

R2 = math.sqrt(2.0)


def _cube(location=(0.0, 0.0, 0.0)):
    """A 2 x 2 x 2 cube in edit mode with its top face extruded (a polyExtrudeFace record)."""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    extrude.clear()
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z > 0.9:
            f.select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    bpy.ops.ed.undo_push(message="test start")
    assert bpy.ops.allset.extrude('EXEC_DEFAULT', True) == {'FINISHED'}
    return ob


def _cap(ob):
    """World points of the cap (the selected face), sorted."""
    bm = bmesh.from_edit_mesh(ob.data)
    pts = {v.index: ob.matrix_world @ v.co for f in bm.faces if f.select for v in f.verts}
    return sorted(tuple(round(c, 4) + 0.0 for c in p) for p in pts.values())


def _same(got, want, tol=1e-3):
    want = sorted(tuple(round(c, 4) + 0.0 for c in p) for p in want)
    return len(got) == len(want) and all(max(abs(a - b) for a, b in zip(g, w)) <= tol for g, w in zip(got, want))


def _unit():
    return units.maya_unit(bpy.context.scene)


def test_world_translate_rotate_scale():
    u = _unit()
    ob = _cube()
    assert extrude.set_params(bpy.context, translate_x=0.5) == {'FINISHED'}
    assert _same(_cap(ob), [(x + 0.5 * u, y, 1) for x in (-1, 1) for y in (-1, 1)]), _cap(ob)
    # about the centre of the extruded face (0, 0, 1), in world space
    assert extrude.set_params(bpy.context, translate_x=0.0, scale_x=2.0, scale_y=3.0) == {'FINISHED'}
    assert _same(_cap(ob), [(2 * x, 3 * y, 1) for x in (-1, 1) for y in (-1, 1)]), _cap(ob)
    assert extrude.set_params(bpy.context, scale_x=1.0, scale_y=1.0, rotate_x=90.0) == {'FINISHED'}
    assert _same(_cap(ob), [(x, 0, 1 + y) for x in (-1, 1) for y in (-1, 1)]), _cap(ob)
    # the object's place counts: the pivot is in world space
    ob = _cube(location=(3.0, 0.0, 0.0))
    assert extrude.set_params(bpy.context, scale_x=2.0) == {'FINISHED'}
    assert _same(_cap(ob), [(3 + 2 * x, y, 1) for x in (-1, 1) for y in (-1, 1)]), _cap(ob)


def test_local_rotate_and_both_kinds_add():
    ob = _cube()
    assert extrude.set_params(bpy.context, local_rotate_z=45.0) == {'FINISHED'}
    assert _same(_cap(ob), [(R2, 0, 1), (-R2, 0, 1), (0, R2, 1), (0, -R2, 1)]), _cap(ob)
    # Local Scale and Scale along the same axis: each adds its own move (1 + 1 + 1 = 3 times as wide)
    assert extrude.set_params(bpy.context, local_rotate_z=0.0, local_scale_x=2.0, scale_x=2.0) == {'FINISHED'}
    assert _same(_cap(ob), [(3 * x, y, 1) for x in (-1, 1) for y in (-1, 1)]), _cap(ob)


def test_divisions_take_their_share():
    ob = _cube()
    u = _unit()
    assert extrude.set_params(bpy.context, divisions=2, local_translate_z=1.0, rotate_z=90.0) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    mid = sorted(tuple(round(c, 4) + 0.0 for c in v.co) for v in bm.verts if abs(v.co.z - (1 + 0.5 * u)) < 1e-4)
    want = [(R2 * math.cos(math.radians(a)), R2 * math.sin(math.radians(a)), 1 + 0.5 * u) for a in (0, 90, 180, 270)]
    assert _same(mid, want), mid       # the middle ring is turned by half the angle (45 of 90)


def test_drag_preview_matches_the_rebuild():
    ob = _cube()
    _o, rec = extrude.active(bpy.context)
    params = dict(rec.params, rotate_y=30.0, scale_z=1.5, translate_y=0.2, local_rotate_x=20.0, local_scale_y=0.7,
                  local_translate_z=0.4)
    unit = _unit()
    extrude.preview(ob, rec, params, unit)
    assert rec.fast_preview, "a value change keeps the topology: vertices only"
    dragged = _cap(ob)
    assert extrude.set_params(bpy.context, **{k: params[k] for k in params if params[k] != rec.params.get(k)}) \
        == {'FINISHED'}
    assert _cap(ob) == dragged


def test_manipulator_switch_and_ring():
    ob = _cube()
    rec = extrude.current(ob)
    hf = in_view.handle_fields
    assert in_view.turnable(rec)
    assert hf(rec, "VR") == in_view.LOCAL_ROT and hf(rec, "RZ", rings=True) == ("local_rotate_z",)
    assert hf(rec, "TX") == ("local_translate_x",)
    assert bpy.ops.allset.tc_space() == {'FINISHED'}
    assert in_view.flags(extrude.current(ob)) == (True, False)
    world = {h: hf(rec, h, world=True, rings=True) for h in ("TX", "TZ", "SY", "VR", "RZ")}
    assert world == {"TX": ("translate_x",), "TZ": ("translate_z",), "SY": ("scale_y",),
                     "VR": ("rotate_x", "rotate_y", "rotate_z"), "RZ": ("rotate_z",)}, world
    frame = in_view.manip_frame(ob, rec, world=True)
    assert frame is not None and frame[1] == Matrix.Identity(3)
    assert bpy.ops.allset.tc_space() == {'FINISHED'}
    assert in_view.flags(extrude.current(ob)) == (False, False)


def test_rest_values_change_nothing():
    """Every new value at rest leaves the extrusion as before (old records and saved histories have none)."""
    ob = _cube()
    assert extrude.set_params(bpy.context, local_translate_z=0.5) == {'FINISHED'}
    before = _cap(ob)
    _o, rec = extrude.active(bpy.context)
    for f in extrude.MANIP_FIELDS[5:]:
        assert rec.params[f] == (1.0 if "scale" in f else 0.0), f
    assert _same(before, [(x, y, 1 + 0.5 * _unit()) for x in (-1, 1) for y in (-1, 1)]), before
