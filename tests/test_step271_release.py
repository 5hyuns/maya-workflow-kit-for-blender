"""Step 271 (0.6.0 release QA): fixes found by the gate.

- Start-up in Maya mode registers with Blender's restricted data: the constraint helper lookup must not touch
  ``bpy.data.collections`` then (the start-up itself is checked by test_step130_lifecycle).
- Menu / marking-menu items whose Blender operator can't run warn or do nothing instead of raising."""

from importlib import import_module

import bpy

import kit

constrain_multi = import_module(kit.MODULE + ".operators.constrain_multi")


class _Restricted:
    """Stands for Blender's restricted ``bpy.data`` during add-on registration (no ID collections)."""


def test_helpers_with_restricted_data_finds_nothing():
    real = constrain_multi.bpy
    fake = type("FakeBpy", (), {"data": _Restricted()})()
    constrain_multi.bpy = fake
    try:
        assert constrain_multi.helpers() == []
    finally:
        constrain_multi.bpy = real
    assert constrain_multi.helpers() == []          # a real file without helpers


def test_smoke_in_edit_mode_warns_instead_of_raising():
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        assert bpy.ops.allset.quick_smoke() == {'CANCELLED'}
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
    assert not any(ob.name.startswith("Smoke Domain") for ob in bpy.data.objects)


def test_pivot_reset_without_selection_does_nothing():
    bpy.ops.object.select_all(action='DESELECT')
    assert bpy.ops.allset.pivot_reset() == {'CANCELLED'}
