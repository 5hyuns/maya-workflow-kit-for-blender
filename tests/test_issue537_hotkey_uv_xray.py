"""#537 #538 #539 #542: the kit Hotkey Editor lists the UV Editor's menu commands (Align, Distribute UVs, Straighten
UVs ...), the UV Toolkit's buttons (Align Min U ... Max V, Unfold Along U / V, Straighten U / V, the Move / Rotate /
Scale steps, Flip U / V, Distribute, Layout Along) under Custom Scripts, X-Ray (Toggle) and X-Ray Joints, and Edit
Mesh > Duplicate; a key given to one of them runs it."""

from importlib import import_module

import bmesh
import bpy

import kit
from rt60_dump import populate


def m(name):
    return import_module(f"{kit.MODULE}.{name}")


def _he():
    return m("ui.hotkey_editor")


def _row(command):
    return next(r for r in _he().rows() if r["command"] == command)


def _setup():
    populate()
    keymap = m("keymap")
    keymap.deactivate()
    keymap.activate()
    bpy.context.window_manager.keyconfigs.update()


def _window_items(idname):
    km = bpy.context.window_manager.keyconfigs.user.keymaps["Window"]
    return [k for k in km.keymap_items if k.idname == idname and k.is_user_defined]


def test_rows_are_listed_and_found():
    hr = m("keymap.hotkey_rows")
    rows = _he().rows()
    for command, label, category in (
            ("AlignUV", "Align", "Editors > UV Editor"),
            ("AlignUVOptions", "Align (Option)", "Editors > UV Editor"),
            ("UVStraighten", "Straighten UVs", "Editors > UV Editor"),
            ("DistributeUVs", "Distribute UVs", "Editors > UV Editor"),
            ("UVToolkitAlignMinU", "Align Min U", "Custom Scripts > UV Toolkit"),
            ("UVToolkitAlignMaxV", "Align Max V", "Custom Scripts > UV Toolkit"),
            ("UVToolkitUnfoldAlongU", "Unfold Along U", "Custom Scripts > UV Toolkit"),
            ("UVToolkitUnfoldAlongV", "Unfold Along V", "Custom Scripts > UV Toolkit"),
            ("UVToolkitRotateClockwise", "Rotate UVs Clockwise", "Custom Scripts > UV Toolkit"),
            ("ViewportXRayToggle", "X-Ray (Toggle)", "Other items > Modeling Toolkit"),
            ("ViewportXRayJointsToggle", "X-Ray Joints (Toggle)", "Custom Scripts > Viewport"),
            ("DuplicateFace", "Duplicate", "Menu items > Modeling > Edit Mesh")):
        r = next((r for r in rows if r["command"] == command), None)
        assert r is not None, command
        assert (r["label"], r["category"]) == (label, category), r
        assert r["editable"] and r["status"] == "KIT", r
    found = lambda text: {r["command"] for r in hr.search(rows, text)}     # noqa: E731
    assert {"UVToolkitUnfoldAlongU", "UVToolkitUnfoldAlongV"} <= found("unfold along"), found("unfold along")
    assert {"UVToolkitAlignMinU", "UVToolkitAlignAvgU", "UVToolkitAlignMaxU"} <= found("align")
    assert {"ViewportXRayToggle", "ViewportXRayJointsToggle"} <= found("xray") | found("x-ray")
    custom = {r["command"] for r in hr.search(rows, category="Custom Scripts")}
    assert len(custom) >= 30 and "UVToolkitLayoutAlongV" in custom, sorted(custom)
    commands = [r["command"] for r in rows if r.get("path")]
    assert len(commands) == len(set(commands)), "every command is listed once"


def _quad():
    """A quad in edit mode, UV Sync Selection on, every vertex selected; UVs (0.1,0.1) (0.4,0.2) (0.5,0.6) (0.2,0.5)."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    me = bpy.data.meshes.new("q537")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(name="UVMap")
    ob = bpy.data.objects.new("q537", me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (True, False, False)
    bm = bmesh.from_edit_mesh(me)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    for lp, p in zip(bm.faces[0].loops, ((0.1, 0.1), (0.4, 0.2), (0.5, 0.6), (0.2, 0.5))):
        lp[uv].uv = p
    for v in bm.verts:
        v.select = True
    bm.select_flush(True)
    bmesh.update_edit_mesh(me)
    return ob


def _us(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    return [round(lp[uv].uv.x, 5) for lp in bm.faces[0].loops]


def test_toolkit_key_runs_the_button():
    _setup()
    he = _he()
    ctx = bpy.context
    row = _row("UVToolkitAlignMinU")
    ok, _taken = he.assign(ctx, row, {"type": "F7", "ctrl": True, "alt": True})
    assert ok
    items = _window_items("allset.hotkey_command")
    assert [(k.type, k.properties.item) for k in items] == [('F7', "UVToolkitAlignMinU")], items
    assert he.kit_text(ctx, row) == "Ctrl+Alt+F7 *", he.kit_text(ctx, row)
    ob = _quad()
    assert bpy.ops.allset.hotkey_command(item=items[0].properties.item) == {'FINISHED'}
    assert _us(ob) == [0.1] * 4, _us(ob)
    bpy.ops.object.mode_set(mode='OBJECT')
    assert he.restore_all(ctx) >= 1
    assert not _window_items("allset.hotkey_command")


def test_toolkit_values_come_from_the_toolkit():
    """Straighten UVs reads the toolkit's angle tolerance like the button does."""
    ob = _quad()
    tk = bpy.context.scene.allset_uv_toolkit
    tk.straighten_tolerance = 0.0          # no edge is within 0 degrees of U: nothing moves
    before = _us(ob)
    bpy.ops.allset.hotkey_command(item="UVToolkitStraightenU")
    assert _us(ob) == before, (before, _us(ob))
    bpy.ops.object.mode_set(mode='OBJECT')


def test_xray_toggle():
    scr = bpy.context.window.screen
    area = next(a for a in scr.areas if a.type == 'VIEW_3D')
    shading = area.spaces.active.shading
    was = shading.show_xray
    with bpy.context.temp_override(area=area, space_data=area.spaces.active):
        res = bpy.ops.allset.hotkey_command(item="ViewportXRayToggle")
    assert res == {'FINISHED'}, res
    assert shading.show_xray != was, (was, shading.show_xray)
    with bpy.context.temp_override(area=area, space_data=area.spaces.active):
        bpy.ops.allset.hotkey_command(item="ViewportXRayToggle")
    assert shading.show_xray == was


def test_unknown_command_is_refused():
    assert bpy.ops.allset.hotkey_command(item="NoSuchCommand") == {'CANCELLED'}


def test_every_kit_command_names_a_real_operator_and_settings():
    kit_cmds = m("keymap.hotkey_kit")
    tk = bpy.context.scene.allset_uv_toolkit
    bad = []
    for command, _label, _cat, idname, props in kit_cmds.COMMANDS:
        if idname == "toggle":
            continue
        mod, name = idname.split(".")
        try:
            rna = getattr(getattr(bpy.ops, mod), name).get_rna_type()
        except (AttributeError, KeyError):
            bad.append((command, idname))
            continue
        for k, v in props.items():
            if k not in rna.properties:
                bad.append((command, k))
            if isinstance(v, str) and v.startswith("@") and not hasattr(tk, v[1:]):
                bad.append((command, v))
            elif isinstance(v, str) and not v.startswith("@") and rna.properties[k].type == 'ENUM':
                if v not in {i.identifier for i in rna.properties[k].enum_items}:
                    bad.append((command, k, v))
    assert not bad, bad
