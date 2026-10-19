"""Step 53: Blender version compatibility and a safe install.

Runs on the target Blender 4.5 and on 5.x (BLENDER=... python tests/run.py): the keymap patches are strict
on 4.5 and only show the known Industry Compatible drift elsewhere, the Maya theme round trip gives the
user's theme back exactly, the manifest declares the tested range, the timeline shim matches the Blender."""

import hashlib
import tomllib
from importlib import import_module
from pathlib import Path

import bpy

import kit

ROOT = Path(__file__).resolve().parent.parent
patch = import_module(kit.MODULE + ".keymap.patch")
keymap = import_module(kit.MODULE + ".keymap")
theme = import_module(kit.MODULE + ".theme")
time_slider = import_module(kit.MODULE + ".ui.time_slider")

# Industry Compatible items the 4.5 patches expect that Blender 5.x doesn't have (checked on 5.2.2).
KNOWN_5X_DRIFT = {
    "Node Editor: no item node.viewer_border {'type': 'Z'}",
}


def _theme_hash():
    h = hashlib.sha256()

    def walk(obj, depth=0):
        if depth > 6:
            return
        for p in obj.bl_rna.properties:
            if p.identifier in ("rna_type", "filepath"):
                continue
            v = getattr(obj, p.identifier)
            if p.type == 'POINTER' and v is not None and hasattr(v, "bl_rna"):
                walk(v, depth + 1)
            elif p.type in ('FLOAT', 'INT', 'BOOLEAN', 'ENUM', 'STRING'):
                if hasattr(v, "__len__") and not isinstance(v, str):
                    v = [round(x, 4) if isinstance(x, float) else x for x in v]
                elif isinstance(v, float):
                    v = round(v, 4)
                h.update(f"{p.identifier}={v};".encode())
    walk(bpy.context.preferences.themes[0])
    return h.hexdigest()


def test_keymap_patches_strict_on_target_drift_known_elsewhere():
    keymap.generate_data()
    if tuple(bpy.app.version[:2]) == keymap.TARGET_VERSION:
        assert patch.STRICT and not patch.DRIFT, patch.DRIFT
    else:
        assert not patch.STRICT
        assert set(patch.DRIFT) <= KNOWN_5X_DRIFT, sorted(set(patch.DRIFT) - KNOWN_5X_DRIFT)
    assert bpy.context.window_manager.keyconfigs.get("Maya-style") is not None


def test_theme_round_trip_gives_the_user_theme_back():
    t = bpy.context.preferences.themes[0]
    t.view_3d.grid = (0.9, 0.1, 0.1, 1.0)          # the user's own tweak
    t.user_interface.wcol_regular.roundness = 0.3
    before = _theme_hash()
    assert bpy.ops.allset.theme_apply() == {'FINISHED'}
    assert _theme_hash() != before
    assert t.user_interface.wcol_regular.roundness == 0.0
    assert bpy.ops.allset.theme_restore() == {'FINISHED'}
    assert _theme_hash() == before, "every theme value comes back"
    bpy.ops.preferences.reset_default_theme()


def test_moved_theme_values_applied():
    t = bpy.context.preferences.themes[0]
    bpy.ops.allset.theme_apply()
    try:
        if hasattr(t, "common"):     # Blender 5.x
            assert tuple(round(c, 2) for c in t.common.anim.playhead[:3]) == (0.78, 0.78, 0.78)
            assert tuple(round(c, 2) for c in t.common.anim.keyframe[:3]) == (1.0, 0.0, 0.0)
        else:
            assert tuple(round(c, 2) for c in t.dopesheet_editor.frame_current[:3]) == (0.78, 0.78, 0.78)
        ui = t.user_interface
        assert all(getattr(ui, p.identifier).roundness == 0.0 for p in ui.bl_rna.properties
                   if p.identifier.startswith("wcol_") and p.identifier != "wcol_state")
    finally:
        bpy.ops.allset.theme_restore()


def test_manifest_declares_the_tested_range():
    data = tomllib.loads((ROOT / "src" / "allset" / "blender_manifest.toml").read_text(encoding="utf-8"))
    assert data["blender_version_min"] == "4.5.0", "4.2.23 fails 25 tests (step 117)"
    assert data["blender_version_max"] == "5.0.0", "4.5.x only: 5.0.1 fails 19 tests (step 117); re-measure before raising"
    v = tuple(bpy.app.version)
    assert (4, 5, 0) <= v < (5, 0, 0), v


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
