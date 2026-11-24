"""#497: UV Editor > Modify > Unfold and Layout open their option windows; the saved settings drive the menu item,
Ctrl+U / Ctrl+L, the UV Toolkit buttons, the marking menu items and the 3D Cut and Sew tool's d key."""

from importlib import import_module

import bmesh
import bpy

import kit

uvt = import_module(kit.MODULE + ".operators.uv_tools")
uvl = import_module(kit.MODULE + ".operators.uv_layout")
ow = import_module(kit.MODULE + ".operators.option_windows")
box = import_module(kit.MODULE + ".ui.menu_option_box")

UNFOLD, LAYOUT = "UV Editor/Modify/Unfold", "UV Editor/Modify/Layout"


def _reset():
    ow.store("uv_unfold", None)
    ow.store("uv_layout", None)
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _edit(*obs):
    for o in bpy.context.view_layer.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_all(action='DESELECT')     # nothing picked = every shell


def _cube():
    """A cube with six shells (Automatic), in edit mode."""
    bpy.ops.mesh.primitive_cube_add(size=2)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_all(action='SELECT')
    assert bpy.ops.allset.uv_automatic() == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    _edit(ob)
    return ob


def _plane(name, x, sx=1.0, sy=1.0):
    """A one-face plane at ``x`` whose UVs fill 0-1 scaled by ``sx`` / ``sy``."""
    bpy.ops.object.mode_set(mode='OBJECT') if bpy.context.mode != 'OBJECT' else None
    bpy.ops.mesh.primitive_plane_add(size=2, location=(x, 0, 0))
    ob = bpy.context.active_object
    ob.name = name
    uv = ob.data.uv_layers.active.data
    for d in uv:
        d.uv = (d.uv[0] * sx, d.uv[1] * sy)
    return ob


def _uvs(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    return [l[uv].uv.copy() for f in bm.faces for l in f.loops]


def _box(points):
    xs, ys = [p.x for p in points], [p.y for p in points]
    return min(xs), max(xs), min(ys), max(ys)


def _close(a, b, tol=1e-3):
    return abs(a - b) <= tol


def test_windows_open_from_the_option_boxes():
    unfold, layout = ow.find_path(UNFOLD), ow.find_path(LAYOUT)
    assert unfold is not None and unfold.key == "uv_unfold" and unfold.action == "Unfold"
    assert layout is not None and layout.key == "uv_layout" and layout.action == "Layout"
    assert box.option_kind(UNFOLD) == box.option_kind(LAYOUT) == "window"
    assert hasattr(bpy.ops.allset, "opt_uv_unfold") and hasattr(bpy.ops.allset, "opt_uv_layout")
    d = unfold.defaults()
    assert d == {"iterations": 1, "layout_uvs": False, "prevent_flips": True}, d
    d = layout.defaults()
    assert d["pre_scale"] == "Preserve 3D Ratios" and d["pre_rotate"] == "Off" and d["rotate"] is False
    assert d["shell_padding"] == 0.0 and d["tile_padding"] == 0.0 and d["map_size"] == "1024"
    assert d["region"] == "Full square" and d["scale_mode"] == "Uniform" and d["multi"] == uvl.MULTI[0]
    region = next(f for f in layout.fields if f.name == "region")
    assert set(region.items) == set(uvl.REGIONS) | {"Custom"}, "every packing region can be picked"
    assert unfold.missing and layout.missing, "fields Blender has no counterpart for are listed greyed"
    # greyed until their switch is on (like Maya)
    assert not layout.enabled(d, "rotate_step") and layout.enabled({**d, "rotate": True}, "rotate_step")
    assert not layout.enabled(d, "region_min_u") and layout.enabled({**d, "region": "Custom"}, "region_min_u")


def test_layout_default_fills_0_1_without_turning():
    _reset()
    ob = _cube()
    assert bpy.ops.allset.menu_item(item=LAYOUT) == {'FINISHED'}
    lo_u, hi_u, lo_v, hi_v = _box(_uvs(ob))
    assert lo_u >= -1e-6 and lo_v >= -1e-6 and hi_u <= 1 + 1e-6 and hi_v <= 1 + 1e-6
    assert _close(max(hi_u, hi_v), 1.0, 0.02), "uniformly scaled to fill the square"


def test_layout_packing_region_and_tile_padding():
    _reset()
    ob = _cube()
    v = {**ow.current("uv_layout"), "region": "Top right"}
    assert bpy.ops.allset.opt_uv_layout('EXEC_DEFAULT', **v) == {'FINISHED'}
    lo_u, hi_u, lo_v, hi_v = _box(_uvs(ob))
    assert lo_u >= 0.5 - 1e-6 and lo_v >= 0.5 - 1e-6 and hi_u <= 1 + 1e-6 and hi_v <= 1 + 1e-6, (lo_u, lo_v)
    # 32 px tile padding on a 256 map = 32 / 256 of the region's width (0.5) kept free at its border
    v.update(region="Full square", map_size="256", tile_padding=32.0)
    assert bpy.ops.allset.opt_uv_layout('EXEC_DEFAULT', **v) == {'FINISHED'}
    lo_u, hi_u, lo_v, hi_v = _box(_uvs(ob))
    pad = 32 / 256
    assert min(lo_u, lo_v) >= pad - 1e-4 and max(hi_u, hi_v) <= 1 - pad + 1e-4, (lo_u, lo_v, hi_u, hi_v)
    assert _close(max(hi_u, hi_v), 1 - pad, 0.02) or _close(min(lo_u, lo_v), pad, 0.02)


def test_layout_custom_region_and_non_uniform_scale():
    _reset()
    ob = _cube()
    v = {**ow.current("uv_layout"), "region": "Custom", "region_min_u": 0.2, "region_max_u": 0.6,
         "region_min_v": 0.1, "region_max_v": 0.9, "scale_mode": "Non-Uniform"}
    assert bpy.ops.allset.opt_uv_layout('EXEC_DEFAULT', **v) == {'FINISHED'}
    lo_u, hi_u, lo_v, hi_v = _box(_uvs(ob))
    for got, want in ((lo_u, 0.2), (hi_u, 0.6), (lo_v, 0.1), (hi_v, 0.9)):
        assert _close(got, want), ("stretched to the whole region", lo_u, hi_u, lo_v, hi_v)


def test_layout_scale_mode_off_keeps_the_shell_size():
    _reset()
    a = _plane("small", 0.0, 0.25, 0.25)
    _edit(a)
    v = {**ow.current("uv_layout"), "scale_mode": "Off", "pre_scale": "Off"}
    assert bpy.ops.allset.opt_uv_layout('EXEC_DEFAULT', **v) == {'FINISHED'}
    lo_u, hi_u, lo_v, hi_v = _box(_uvs(a))
    assert _close(hi_u - lo_u, 0.25) and _close(hi_v - lo_v, 0.25), (lo_u, hi_u, lo_v, hi_v)


def test_layout_shell_padding_in_pixels():
    _reset()
    a, b = _plane("a", 0.0), _plane("b", 3.0)
    _edit(a, b)
    v = {**ow.current("uv_layout"), "shell_padding": 64.0, "map_size": "512"}
    assert bpy.ops.allset.opt_uv_layout('EXEC_DEFAULT', **v) == {'FINISHED'}
    ba, bb = _box(_uvs(a)), _box(_uvs(b))
    gap = max(bb[0] - ba[1], ba[0] - bb[1], bb[2] - ba[3], ba[2] - bb[3])
    assert gap >= 64 / 512 * 0.8, f"about 64 px between the shells on a 512 map, got {gap * 512:.1f} px"


def test_layout_multiple_objects_together_or_separately():
    _reset()
    a, b = _plane("a", 0.0), _plane("b", 3.0)
    _edit(a, b)
    assert bpy.ops.allset.uv_layout() == {'FINISHED'}
    ba, bb = _box(_uvs(a)), _box(_uvs(b))
    overlap = min(ba[1], bb[1]) - max(ba[0], bb[0]) > 1e-4 and min(ba[3], bb[3]) - max(ba[2], bb[2]) > 1e-4
    assert not overlap, ("Pack Together: one layout for both meshes", ba, bb)
    v = {**ow.current("uv_layout"), "multi": uvl.MULTI[1]}
    assert bpy.ops.allset.opt_uv_layout('EXEC_DEFAULT', **v) == {'FINISHED'}
    for ob in (a, b):
        lo_u, hi_u, lo_v, hi_v = _box(_uvs(ob))
        assert _close(hi_u - lo_u, 1.0, 0.01) and _close(hi_v - lo_v, 1.0, 0.01), ("each mesh fills 0-1", ob.name)


def test_layout_pre_rotation_horizontal_and_vertical():
    _reset()
    a = _plane("tall", 0.0, 0.2, 0.8)
    a.scale = (0.25, 1.0, 1.0)      # tall in 3D too: Preserve 3D Ratios keeps it tall
    _edit(a)
    v = {**ow.current("uv_layout"), "pre_rotate": "Horizontal"}
    assert bpy.ops.allset.opt_uv_layout('EXEC_DEFAULT', **v) == {'FINISHED'}
    lo_u, hi_u, lo_v, hi_v = _box(_uvs(a))
    assert hi_u - lo_u > hi_v - lo_v, ("long side along U", lo_u, hi_u, lo_v, hi_v)
    v["pre_rotate"] = "Vertical"
    assert bpy.ops.allset.opt_uv_layout('EXEC_DEFAULT', **v) == {'FINISHED'}
    lo_u, hi_u, lo_v, hi_v = _box(_uvs(a))
    assert hi_v - lo_v > hi_u - lo_u, ("long side along V", lo_u, hi_u, lo_v, hi_v)


def test_saved_layout_settings_drive_every_entry():
    _reset()
    ob = _cube()
    v = {**ow.current("uv_layout"), "region": "Bottom left"}
    assert bpy.ops.allset.opt_uv_layout('EXEC_DEFAULT', **v) == {'FINISHED'}
    assert ow.saved("uv_layout")["region"] == "Bottom left", "the command keeps its option values"

    def inside():
        lo_u, hi_u, lo_v, hi_v = _box(_uvs(ob))
        return lo_u >= -1e-6 and lo_v >= -1e-6 and hi_u <= 0.5 + 1e-6 and hi_v <= 0.5 + 1e-6

    for run in (lambda: bpy.ops.allset.menu_item(item=LAYOUT),      # menu item, UV Toolkit button, marking menu
                lambda: bpy.ops.allset.uv_layout('INVOKE_DEFAULT'),   # Ctrl+L
                lambda: bpy.ops.allset.uv_unfold_layout()):           # 3D Cut and Sew tool d
        bmesh.update_edit_mesh(ob.data)
        bm = bmesh.from_edit_mesh(ob.data)
        uv = bm.loops.layers.uv.active
        for f in bm.faces:                  # spread the shells over 0-2 first
            for loop in f.loops:
                loop[uv].uv = loop[uv].uv * 2.0
        bmesh.update_edit_mesh(ob.data)
        assert run() == {'FINISHED'}
        assert inside(), _box(_uvs(ob))


def test_unfold_window_runs_layout_after_it():
    _reset()
    ob = _cube()
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        for loop in f.loops:
            loop[uv].uv = loop[uv].uv * 3.0 + type(loop[uv].uv)((1.0, 1.0))
    bmesh.update_edit_mesh(ob.data)
    v = {**ow.current("uv_unfold"), "layout_uvs": True}
    assert bpy.ops.allset.opt_uv_unfold('EXEC_DEFAULT', **v) == {'FINISHED'}
    lo_u, hi_u, lo_v, hi_v = _box(_uvs(ob))
    assert lo_u >= -1e-6 and lo_v >= -1e-6 and hi_u <= 1 + 1e-6 and hi_v <= 1 + 1e-6, "Layout UVs ran"
    assert ow.saved("uv_unfold")["layout_uvs"] is True
    # Ctrl+U / the menu item use the saved values too
    for run in (lambda: bpy.ops.allset.uv_unfold('INVOKE_DEFAULT'), lambda: bpy.ops.allset.menu_item(item=UNFOLD)):
        bm = bmesh.from_edit_mesh(ob.data)
        uv = bm.loops.layers.uv.active
        for f in bm.faces:
            for loop in f.loops:
                loop[uv].uv = loop[uv].uv * 3.0
        bmesh.update_edit_mesh(ob.data)
        assert run() == {'FINISHED'}
        lo_u, hi_u, lo_v, hi_v = _box(_uvs(ob))
        assert hi_u <= 1 + 1e-6 and hi_v <= 1 + 1e-6, ("saved Layout UVs", lo_u, hi_u, lo_v, hi_v)


def test_unfold_iterations_zero_and_no_layout_keep_places():
    _reset()
    ob = _cube()
    before = _box(_uvs(ob))
    v = {**ow.current("uv_unfold"), "iterations": 0}
    assert bpy.ops.allset.opt_uv_unfold('EXEC_DEFAULT', **v) == {'FINISHED'}
    after = _box(_uvs(ob))
    assert all(_close(a, b, 0.05) for a, b in zip(before, after)), (before, after)


def test_hotkeys_and_toolkit_buttons():
    km = kit.maya_kc().keymaps.get("UV Editor")
    assert km is not None
    ids = {(k.idname, k.type, k.ctrl) for k in km.keymap_items}
    assert ("allset.uv_unfold", 'U', True) in ids and ("allset.uv_layout", 'L', True) in ids
    import inspect
    src = inspect.getsource(import_module(kit.MODULE + ".ui.uv_toolkit"))
    assert '_item(left, f"Modify/{name}"' in src and '_item(left, "Modify/Layout"' in src, \
        "the toolkit buttons are the menu items (Shift+click opens the same window)"


def test_layout_pre_rotation_aligns_a_scene_axis_to_v():
    _reset()
    a = _plane("wall", 0.0)
    a.rotation_euler = (1.5708, 0.0, 0.0)       # standing up: its faces span X and Z
    bpy.ops.object.transform_apply(rotation=True)
    uv = a.data.uv_layers.active.data
    for d in uv:                                 # UVs a quarter turn off: Z runs along U
        d.uv = (1.0 - d.uv[1], d.uv[0])
    _edit(a)
    v = {**ow.current("uv_layout"), "pre_rotate": "Align Z to V"}
    assert bpy.ops.allset.opt_uv_layout('EXEC_DEFAULT', **v) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(a.data)
    layer = bm.loops.layers.uv.active
    mw = a.matrix_world
    for f in bm.faces:
        for loop in f.loops:
            nxt = loop.link_loop_next
            d3 = mw @ nxt.vert.co - mw @ loop.vert.co
            if abs(d3.z) > 0.5 and abs(d3.x) < 1e-4:          # an edge straight up the object's Z
                duv = nxt[layer].uv - loop[layer].uv
                assert abs(duv.y) > 10 * abs(duv.x) and duv.y * d3.z > 0, ("Z points up V", duv)
                return
    raise AssertionError("no upright edge found")


def test_no_field_hides_an_operator_attribute():
    """A field named like an Operator attribute (``layout``, ``report`` ...) would break the window's drawing."""
    taken = set(dir(bpy.types.Operator))
    bad = [(w.key, f.name) for w in ow.WINDOWS for f in w.fields if f.name in taken]
    assert not bad, bad
