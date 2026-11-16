"""#380: every kit edit that refills the edit-mode mesh (changing an extrusion, a primitive's creation values in
edit mode, the drag rebuilds of the mesh tools) leaves the mesh's select mode as it was. An emptied select mode makes
a click on a face / edge / vertex pick nothing in Blender 5.3 (only a marquee worked until the select mode changed)."""

import os
import re
from importlib import import_module

import bmesh
import bpy

import kit

compat = import_module(kit.MODULE + ".compat")
extrude = import_module(kit.MODULE + ".operators.extrude")
prim_history = import_module(kit.MODULE + ".operators.prim_history")
connect_tool = import_module(kit.MODULE + ".operators.connect_tool")
edge_loops = import_module(kit.MODULE + ".operators.edge_loops")
smart_extrude = import_module(kit.MODULE + ".operators.smart_extrude")

MODES = {'VERT': (True, False, False), 'EDGE': (False, True, False), 'FACE': (False, False, True)}


def _cube(mode):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.allset.create(kind='CUBE')
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = MODES[mode]
    bpy.ops.mesh.select_all(action='DESELECT')
    return ob


def _mode(ob):
    return set(bmesh.from_edit_mesh(ob.data).select_mode)


def _select_top(ob, mode):
    bm = bmesh.from_edit_mesh(ob.data)
    if mode == 'FACE':
        max(bm.faces, key=lambda f: f.calc_center_median().z).select_set(True)
    elif mode == 'EDGE':
        max(bm.edges, key=lambda e: sum(v.co.z - v.co.y for v in e.verts)).select_set(True)
    else:
        max(bm.verts, key=lambda v: v.co.z - v.co.y + v.co.x).select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def test_changing_an_extrusion_keeps_the_select_mode():
    for mode, change in (('FACE', {"local_translate_z": 1.0}), ('FACE', {"divisions": 3}),
                         ('EDGE', {"local_translate_z": 1.0}), ('VERT', {"length": 2.0})):
        ob = _cube(mode)
        _select_top(ob, mode)
        assert bpy.ops.allset.extrude() == {'FINISHED'}, mode
        assert _mode(ob) == {mode}, (mode, "after Ctrl+E", _mode(ob))
        assert extrude.set_params(bpy.context, **change) == {'FINISHED'}, (mode, change)
        assert _mode(ob) == {mode}, (mode, change, _mode(ob))
        # the extruded components are still the selection (the flush ran with the mode)
        bm = bmesh.from_edit_mesh(ob.data)
        assert any(f.select for f in bm.faces) or mode != 'FACE', (mode, change)


def test_primitive_values_in_edit_mode_keep_the_select_mode():
    ob = _cube('EDGE')
    assert prim_history.rebuild(bpy.context, ob, {"width": 3.0}) is not None
    assert _mode(ob) == {'EDGE'}, _mode(ob)


def test_mesh_tool_rebuilds_keep_the_select_mode():
    ob = _cube('VERT')
    bm = bmesh.from_edit_mesh(ob.data)
    pre = bm.copy()
    connect_tool._restore(bm, pre)
    pre.free()
    assert _mode(ob) == {'VERT'}, ("Connect Tool", _mode(ob))
    bm = bmesh.from_edit_mesh(ob.data)
    held = edge_loops._PreMesh(bm)
    try:
        held.restore(bm)
    finally:
        held.free()
    assert _mode(ob) == {'VERT'}, ("edge loop drag", _mode(ob))
    bm = bmesh.from_edit_mesh(ob.data)
    copy = bm.copy()
    smart_extrude.replace(ob, copy)
    copy.free()
    assert _mode(ob) == {'VERT'}, ("Smart Extrude", _mode(ob))


def test_an_emptied_mode_comes_back_from_the_tool_settings():
    ob = _cube('FACE')
    bm = bmesh.from_edit_mesh(ob.data)
    me = bpy.data.meshes.new("issue380")
    try:
        bm.to_mesh(me)
        bm.clear()                      # what Blender's own clear leaves: no select mode
        assert set(bm.select_mode) == set(), bm.select_mode
        compat.refill_bmesh(bm, me)
    finally:
        bpy.data.meshes.remove(me)
    assert _mode(ob) == {'FACE'}, _mode(ob)
    assert len(bmesh.from_edit_mesh(ob.data).faces) == 6


def test_no_bare_bmesh_clear_in_the_kit():
    """Refilling a BMesh goes through compat.clear_bmesh / refill_bmesh, which keep its select mode."""
    src = os.path.join(kit.ROOT, "src", "allset")
    bare = re.compile(r"\bbm\.clear\(\)|\.bm\.clear\(\)|\bbmesh_\w*\.clear\(\)")
    found = []
    for folder, _dirs, files in os.walk(src):
        for name in files:
            path = os.path.join(folder, name)
            if not name.endswith(".py") or path.endswith(os.path.join("allset", "compat.py")):
                continue
            with open(path, encoding="utf-8") as fh:
                for n, line in enumerate(fh, 1):
                    if bare.search(line):
                        found.append(f"{os.path.relpath(path, src)}:{n}")
    assert not found, found
