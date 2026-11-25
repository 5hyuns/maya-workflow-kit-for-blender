"""UV projections in the kit's UV component mode (UV Sync Selection off) work on faces, like Maya: picked UV faces
are projected, only those; with only UVs or UV edges picked nothing is projected (a warning, CANCELLED). The mesh
selection is the same afterwards (#553)."""

import os
import sys

import bmesh
import bpy

import kit
from importlib import import_module

sys.path.insert(0, os.path.dirname(__file__))
import test_uv_selection_scope as S  # noqa: E402

compat = import_module(kit.MODULE + ".compat")

OPS = (("uv_planar", {}), ("uv_planar", {"axis": 'Z'}), ("uv_cylindrical", {}), ("uv_spherical", {}),
       ("uv_automatic", {}), ("uv_contour", {}))


def _uv_scene(uv_mode):
    obs = S._scene(2)
    assert bpy.ops.allset.uv_component(mode=uv_mode) == {'FINISHED'}
    return obs


def _pick(ob, faces=(), verts=()):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        compat.set_uv_face_selected(f, uv, f.index in faces)
        for lp in f.loops:
            if lp.vert.index in verts:
                compat.set_uv_vert_selected(lp, uv, True)
    bmesh.update_edit_mesh(ob.data)


def _mesh_sel(obs):
    return [[f.select for f in bmesh.from_edit_mesh(o.data).faces] for o in obs]


def _run(op, props):
    scr = bpy.context.window.screen
    a = next(a for a in scr.areas if a.type in ('VIEW_3D', 'IMAGE_EDITOR'))
    a.ui_type = 'UV'
    r = next(r for r in a.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(area=a, region=r, space_data=a.spaces.active):
        return getattr(bpy.ops.allset, op)(**props)


def test_uv_face_pick_projects_only_those_faces():
    for op, props in OPS:
        obs = _uv_scene('UV_FACE')
        _pick(obs[0], faces=(1, 4))
        _pick(obs[1])
        sel = _mesh_sel(obs)
        before = S._uvs(obs)
        assert _run(op, props) == {'FINISHED'}, op
        after = S._uvs(obs)
        changed = {k for k in before if before[k] != after[k]}
        assert changed and changed <= {("c0", 1), ("c0", 4)}, (op, props, changed)
        assert _mesh_sel(obs) == sel, op


def test_uv_point_pick_projects_nothing():
    for mode in ('UV', 'UV_EDGE'):
        for op, props in OPS:
            obs = _uv_scene(mode)
            _pick(obs[0], verts=(0,))
            _pick(obs[1])
            sel = _mesh_sel(obs)
            before = S._uvs(obs)
            assert _run(op, props) == {'CANCELLED'}, (mode, op)
            assert S._uvs(obs) == before, (mode, op)
            assert _mesh_sel(obs) == sel, (mode, op)


def test_uv_sync_face_selection_still_projects_it():
    obs = S._scene(2)
    S._select_mesh(obs[1], 'FACE')
    S._select_mesh(obs[0], 'FACE', faces=(2,))
    before = S._uvs(obs)
    assert _run("uv_planar", {}) == {'FINISHED'}
    changed = {k for k in before if before[k] != S._uvs(obs)[k]}
    assert changed == {("c0", 2)}, changed
