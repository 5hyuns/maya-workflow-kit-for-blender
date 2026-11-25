"""The kit Hotkey Editor lists the UV Toolkit's Pivot, Snap and Measure buttons under Custom Scripts > UV Toolkit,
the Unfold and Layout option boxes, and the UV Editor's Select Overlapping / Non-Overlapping / Back-Facing /
Front-Facing UVs; a key given to one of them runs it."""

from importlib import import_module

import bmesh
import bpy

import kit
from rt60_dump import populate


def m(name):
    return import_module(f"{kit.MODULE}.{name}")


def test_rows_are_listed():
    populate()
    rows = {r["command"]: r for r in m("ui.hotkey_editor").rows()}
    for command, label, category in (
            ("UVToolkitPivotTopLeft", "UV Pivot Top Left", "Custom Scripts > UV Toolkit"),
            ("UVToolkitPivotCenter", "UV Pivot Center", "Custom Scripts > UV Toolkit"),
            ("UVToolkitEditPivot", "Edit UV Pivot", "Custom Scripts > UV Toolkit"),
            ("UVToolkitResetPivot", "Reset UV Pivot", "Custom Scripts > UV Toolkit"),
            ("UVToolkitSnapBottomRight", "Snap Shells Bottom Right", "Custom Scripts > UV Toolkit"),
            ("UVToolkitMeasure", "Measure UVs", "Custom Scripts > UV Toolkit"),
            ("UnfoldUVOptions", "Unfold (Option)", "Editors > UV Editor"),
            ("LayoutUVOptions", "Layout (Option)", "Editors > UV Editor"),
            ("SelectUVOverlappingComponents", "Select Overlapping UVs", "Other items > Polygon Select"),
            ("SelectUVBackFacingComponents", "Select Back-Facing UVs", "Other items > Polygon Select")):
        r = rows.get(command)
        assert r is not None, command
        assert (r["label"], r["category"]) == (label, category), r
        assert r["editable"] and r["status"] == "KIT", r


def _quad():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for old in list(bpy.data.objects):
        bpy.data.objects.remove(old)
    me = bpy.data.meshes.new("q")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(name="UVMap")
    ob = bpy.data.objects.new("q", me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(me)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    for lp, p in zip(bm.faces[0].loops, ((0.3, 0.3), (0.5, 0.3), (0.5, 0.6), (0.3, 0.6))):
        lp[uv].uv = p
    bm.faces[0].select_set(True)
    bmesh.update_edit_mesh(me)
    return ob


def _uv_area():
    scr = bpy.context.window.screen
    a = next(a for a in scr.areas if a.type in ('VIEW_3D', 'IMAGE_EDITOR'))
    a.ui_type = 'UV'
    return a, next(r for r in a.regions if r.type == 'WINDOW')


def _us(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    return [tuple(round(c, 6) for c in lp[uv].uv) for f in bm.faces for lp in f.loops]


def test_snap_key_does_what_the_button_does():
    a, r = _uv_area()
    ob = _quad()
    before = _us(ob)
    with bpy.context.temp_override(area=a, region=r, space_data=a.spaces.active):
        assert bpy.ops.allset.uv_snap_shells(position='BOTTOM_LEFT') == {'FINISHED'}
    button = _us(ob)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob = _quad()
    with bpy.context.temp_override(area=a, region=r, space_data=a.spaces.active):
        assert bpy.ops.allset.hotkey_command(item="UVToolkitSnapBottomLeft") == {'FINISHED'}
    assert _us(ob) == button != before, (before, button, _us(ob))
    bpy.ops.object.mode_set(mode='OBJECT')
