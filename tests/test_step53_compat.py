"""Step 53: Blender version compatibility and a safe install (docs/steps/step_53.md).

Runs on the main target Blender 5.2 and on 4.5 / 5.0 / 5.1 (BLENDER=... python tests/run.py): the keymap patches are
strict on 5.2 and 4.5 (step 272) and only show the known Industry Compatible drift elsewhere, the manifest declares the tested range, the
timeline shim matches the Blender. (The theme round trip tests went with the theme, step 130.)"""

import tomllib
from importlib import import_module
from pathlib import Path

import bpy

import kit

ROOT = Path(__file__).resolve().parent.parent
patch = import_module(kit.MODULE + ".keymap.patch")
keymap = import_module(kit.MODULE + ".keymap")
compat = import_module(kit.MODULE + ".compat")
time_slider = import_module(kit.MODULE + ".ui.time_slider")

# Industry Compatible items the patches expect that Blender 5.0 / 5.1 don't have (none since the Node Editor Z
# removal became optional, step 272).
KNOWN_5X_DRIFT = set()


def test_keymap_patches_strict_on_target_drift_known_elsewhere():
    keymap.generate_data()
    if tuple(bpy.app.version[:2]) in compat.STRICT_VERSIONS:
        assert patch.STRICT and not patch.DRIFT, patch.DRIFT
    else:
        assert not patch.STRICT
        assert set(patch.DRIFT) <= KNOWN_5X_DRIFT, sorted(set(patch.DRIFT) - KNOWN_5X_DRIFT)
    assert keymap.is_applied() and len(kit.maya_kc().keymaps) >= 240


def test_manifest_declares_the_tested_range():
    data = tomllib.loads((ROOT / "src" / "allset" / "blender_manifest.toml").read_text(encoding="utf-8"))
    assert data["blender_version_min"] == "4.5.0", "4.2.23 fails 25 tests (step 117)"
    assert data["blender_version_max"] == "5.3.0", "4.5.x-5.2.x: measured in step 118 (docs/compat_5x.md); re-measure before raising"
    v = tuple(bpy.app.version)
    assert (4, 5, 0) <= v < (5, 3, 0), v


def test_timeline_shim_matches_this_blender():
    from bl_ui import space_time
    assert time_slider.LEGACY_TIMELINE == hasattr(space_time, "TIME_HT_editor_buttons")
    buttons, menus = time_slider.header_classes()
    assert "draw_header" in buttons.__dict__ and "draw_collapsible" in menus.__dict__
    kit.disable()
    try:
        assert "draw_collapsible" not in menus.__dict__
    finally:
        kit.enable()


def test_select_loops_wrapper():
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='DESELECT')
        import bmesh
        bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
        bm.edges.ensure_lookup_table()
        bm.edges[0].select = True
        bmesh.update_edit_mesh(bpy.context.active_object.data)
        assert bpy.ops.allset.select_loops(ring=True) == {'FINISHED'}
        bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
        assert sum(e.select for e in bm.edges) == 4, "a cube edge ring has 4 edges"
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')


def test_sources_compile_without_warnings():
    """Python in Blender 5.x warns about invalid escapes (later Pythons reject them)."""
    import warnings
    src = Path(__file__).resolve().parent.parent / "src" / "allset"
    bad = []
    for path in src.rglob("*.py"):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        bad += [f"{path.name}:{w.lineno} {w.message}" for w in caught]
    assert not bad, bad
