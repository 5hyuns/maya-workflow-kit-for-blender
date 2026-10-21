"""Step 104: Maya editor chrome — Graph Editor / Dope Sheet / UV Editor menu bars from the Maya 2022 capture, every
leaf mapped or greyed with a notice, check items, icon rows, header draws swapped and restored, Curves > Infinity,
in / out tangents, Stats fields, the Graph Editor outliner rows. Plan: docs/steps/step_104.md."""

import json
import os
import types
from importlib import import_module
from pathlib import Path

import bpy

import kit

menu_map = import_module(kit.MODULE + ".ui.menu_map")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
notices = import_module(kit.MODULE + ".ui.notices")
data = import_module(kit.MODULE + ".ui.editor_menu_data")
chrome = import_module(kit.MODULE + ".ui.editor_chrome")
graph_keys = import_module(kit.MODULE + ".operators.graph_keys")

CAPTURE = Path(os.environ.get("ALLSET_ROOT", Path(__file__).resolve().parent.parent)) / \
    "research" / "maya" / "screens" / "editors104" / "_editors104.json"

# Maya 2022 GUI capture (research/maya/screens/editors104/_log.txt)
MAYA_BARS = {"Graph Editor": ["Edit", "View", "Select", "Curves", "Keys", "Tangents", "List", "Show", "Help"],
             "Dope Sheet": ["Edit", "View", "Curves", "Keys", "Tangents", "List", "Show", "Help"],
             "UV Editor": ["Edit", "Create", "Select", "Cut/Sew", "Modify", "Tools", "View", "Image", "Textures",
                           "UV Sets", "Help"],
             "UV Toolkit": ["Options", "Help"]}


def _leaves(editor=None):
    out = {}
    for path, it in menu_sets.iter_items():
        if path.split("/", 1)[0] not in MAYA_BARS or (editor and not path.startswith(editor + "/")):
            continue
        if not menu_sets.sub_items(path, it) or path in menu_map.MAP:
            out[path] = path in menu_map.MAP
    return out


def _count_capture(items):
    n = 0
    for e in items:
        if e.get("optionBox") or not e.get("visible", True) or e["sep"] or e.get("divider"):
            continue
        n += _count_capture(e["items"]) if e.get("items") else 1
    return n


def test_menu_bars_match_the_maya_capture():
    for editor, titles in MAYA_BARS.items():
        assert [t for t, _ in data.EDITORS[editor]] == titles, editor
    leaves = _leaves()
    print({ed: (len(_leaves(ed)), sum(_leaves(ed).values())) for ed in MAYA_BARS}, "total", len(leaves),
          "mapped", sum(leaves.values()))
    assert len(leaves) == 585, len(leaves)
    if CAPTURE.exists():   # research/ is not tracked: checked where the capture is
        cap = json.loads(CAPTURE.read_text(encoding="utf-8"))
        n = sum(_count_capture(m["items"]) for key in ("graph_editor", "dope_sheet", "uv_editor")
                for b in cap[key][0]["bars"] for m in b["menus"])
        assert n == len(leaves), (n, len(leaves))
    assert len([p for p in data.OPTION_BOXES if p.split("/", 1)[0] in MAYA_BARS]) == 120
    assert "Graph Editor/Edit/Cut" in data.OPTION_BOXES


def test_every_editor_leaf_mapped_or_noticed():
    leaves = _leaves()
    greyed = [p for p, m in leaves.items() if not m]
    assert not [p for p in greyed if notices.greyed_notice(p) is None]
    assert sum(leaves.values()) / len(leaves) >= 0.55, sum(leaves.values()) / len(leaves)
    # mapped operators exist
    for path, ok in leaves.items():
        s = menu_map.spec(path)
        if ok and s[0] in ("op", "v3d"):
            mod, name = s[1].split(".")
            assert getattr(getattr(bpy.ops, mod), name).get_rna_type() is not None, path


def test_menu_classes_and_submenus_registered():
    for editor, menus in data.EDITORS.items():
        for i, _m in enumerate(menus):
            assert hasattr(bpy.types, menu_sets.editor_menu_idname(editor, i)), (editor, i)
    sub = menu_sets.SUBMENU_IDS["Graph Editor/Tangents/Default In Tangent"]
    assert hasattr(bpy.types, sub)


def test_check_items_are_blender_properties():
    space = types.SimpleNamespace(show_extrapolation=True, use_normalization=False,
                                  dopesheet=types.SimpleNamespace(show_only_selected=True))
    ctx = types.SimpleNamespace(space_data=space, preferences=bpy.context.preferences)
    owner, attr = menu_sets.prop_owner(ctx, "space_data.dopesheet.show_only_selected")
    assert owner is space.dopesheet and attr == "show_only_selected"
    assert menu_sets.set_prop(ctx, "space_data.show_extrapolation", {}) == {'FINISHED'}
    assert space.show_extrapolation is False
    menu_sets.set_prop(ctx, "space_data.use_normalization", {"value": True})
    assert space.use_normalization is True
    edit = bpy.context.preferences.edit
    old = edit.keyframe_new_interpolation_type
    try:
        menu_sets.set_prop(bpy.context, "preferences.edit.keyframe_new_interpolation_type", {"value": 'LINEAR'})
        assert edit.keyframe_new_interpolation_type == 'LINEAR'
    finally:
        edit.keyframe_new_interpolation_type = old
    assert menu_map.spec("Graph Editor/View/Infinity") == ("prop", "space_data.show_extrapolation", {})


def test_icon_rows_follow_the_capture_and_use_real_icons():
    icons = set(bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.keys())
    for editor, row in chrome.ICONS.items():
        for it in row:
            if isinstance(it, tuple):
                assert it[1] in icons, (editor, it)
                if it[2] is None:
                    assert it[0] in chrome.NOTICES, it
    if CAPTURE.exists():
        cap = json.loads(CAPTURE.read_text(encoding="utf-8"))
        maya = [w["maya"] for w in cap["graph_editor"][0]["widgets"] if w["maya"]]
        kit_keys = [it[0] for it in chrome.GRAPH_ICONS if isinstance(it, tuple)]
        # Maya order kept (control names; the outliner load buttons carry the panel name as a prefix)
        idx = [next(i for i, m in enumerate(maya) if m.endswith(k)) for k in kit_keys]
        assert idx[:-2] == sorted(idx[:-2]), list(zip(kit_keys, idx))


def test_headers_swapped_while_enabled():
    assert chrome.own_draw(bpy.types.GRAPH_HT_header) is chrome._graph_header
    assert chrome.own_draw(bpy.types.DOPESHEET_HT_header) is chrome._dope_header


def test_header_draw_menus_and_icons():
    class Rec:
        def __init__(self):
            self.log = []

        def menu(self, idname, text="", icon='NONE'):
            self.log.append(("menu", idname, text))

        def operator(self, idname, text="", icon='NONE', **kw):
            self.log.append(("op", idname, icon))
            return types.SimpleNamespace()

        def row(self, **kw):
            return self

        def __getattr__(self, name):
            return lambda *a, **k: types.SimpleNamespace()

    rec = Rec()
    space = types.SimpleNamespace(type='GRAPH_EDITOR', mode='FCURVES', use_normalization=False,
                                  use_auto_normalization=False, dopesheet=types.SimpleNamespace(show_only_selected=True))
    ctx = types.SimpleNamespace(space_data=space, area=None, scene=bpy.context.scene,
                                tool_settings=bpy.context.scene.tool_settings, preferences=bpy.context.preferences)
    chrome.draw_menus(rec, ctx, "Graph Editor")
    chrome.draw_icons(rec, ctx, "Graph Editor")
    menus = [t for kind, _i, t in rec.log if kind == "menu"]
    assert menus[:9] == MAYA_BARS["Graph Editor"] and menus[9] == "Blender", menus
    ops = [i for kind, i, _ in rec.log if kind == "op"]
    assert ops.count("allset.editor_icon") >= 15 and "allset.editor_icon_unavailable" in ops


def _keyed_cube():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("pCubeShape1")
    ob = bpy.data.objects.new("pCube1", me)
    bpy.context.scene.collection.objects.link(ob)
    for f, x in ((1, 0.0), (12, 3.0), (24, 5.0)):
        ob.location.x = x
        ob.keyframe_insert("location", index=0, frame=f)
    ob.keyframe_insert("location", index=1, frame=12)
    return ob, chrome.object_curves(ob)


def test_curve_infinity_and_in_out_tangents():
    ob, fcs = _keyed_cube()
    fx = fcs[0]
    with bpy.context.temp_override(selected_editable_fcurves=[fx], editable_fcurves=[fx]):
        bpy.ops.allset.curve_infinity(side='POST', mode='CYCLE_OFFSET')
        bpy.ops.allset.curve_infinity(side='PRE', mode='OSCILLATE')
    cyc = [m for m in fx.modifiers if m.type == 'CYCLES']
    assert len(cyc) == 1 and cyc[0].mode_after == 'REPEAT_OFFSET' and cyc[0].mode_before == 'MIRROR'
    with bpy.context.temp_override(selected_editable_fcurves=[fx], editable_fcurves=[fx]):
        bpy.ops.allset.curve_infinity(side='POST', mode='LINEAR')
    assert fx.extrapolation == 'LINEAR' and cyc[0].mode_after == 'NONE' and cyc[0].mode_before == 'MIRROR'
    with bpy.context.temp_override(selected_editable_fcurves=[fx], editable_fcurves=[fx]):
        bpy.ops.allset.curve_infinity(side='PRE', mode='CONSTANT')
    assert not [m for m in fx.modifiers if m.type == 'CYCLES'] and fx.extrapolation == 'CONSTANT'
    # In / Out tangent on the middle key only
    for i, kp in enumerate(fx.keyframe_points):
        kp.select_control_point = i == 1
    graph_keys.apply_side(fx, 1, "LINEAR", "OUT")
    graph_keys.apply_side(fx, 1, "FLAT", "IN")
    kps = fx.keyframe_points
    assert kps[1].interpolation == 'LINEAR' and kps[0].interpolation == 'BEZIER'
    assert kps[1].handle_left_type == 'ALIGNED' and abs(kps[1].handle_left.y - kps[1].co.y) < 1e-6
    graph_keys.apply_side(fx, 1, "STEPPED", "IN")
    assert kps[0].interpolation == 'CONSTANT'


def test_stats_fields_read_and_move_the_selected_key():
    ob, fcs = _keyed_cube()
    fx = fcs[0]
    for i, kp in enumerate(fx.keyframe_points):
        kp.select_control_point = i == 2
    for kp in fcs[1].keyframe_points:
        kp.select_control_point = False
    sc = bpy.context.scene
    with bpy.context.temp_override(editable_fcurves=fcs):
        assert sc.allset_key_time == "24", sc.allset_key_time
        sc.allset_key_time = "+=6"
        assert abs(fx.keyframe_points[2].co.x - 30) < 1e-6
        sc.allset_key_value = "7"
        k = fx.keyframe_points[2]
        shown = sc.allset_key_value
    from importlib import import_module as im
    cb = im(kit.MODULE + ".ui.cb_entry")
    assert abs(k.co.y - cb.from_display(7.0, "LENGTH", sc)) < 1e-6, (k.co.y, shown)


def test_graph_outliner_rows_maya_names():
    ob, fcs = _keyed_cube()
    assert [chrome.attr_label(fc) for fc in fcs] == ["Translate X", "Translate Y"]
    assert chrome.attr_color(fcs[0]) == chrome.AXIS_COLOR[0] and chrome.attr_color(fcs[1]) == chrome.AXIS_COLOR[1]
    space = types.SimpleNamespace(dopesheet=types.SimpleNamespace(show_only_selected=False, show_hidden=False,
                                                                  filter_text=""))
    ctx = types.SimpleNamespace(scene=bpy.context.scene)
    rows = chrome.rows(ctx, space)
    assert [(k, fc and chrome.attr_label(fc)) for k, _o, fc in rows] == \
        [("OBJECT", None), ("ATTR", "Translate X"), ("ATTR", "Translate Y")]      # no Action / group rows
    chrome._expanded["pCube1"] = False
    try:
        assert len(chrome.rows(ctx, space)) == 1
    finally:
        chrome._expanded.clear()
    ctx2 = types.SimpleNamespace(scene=bpy.context.scene, space_data=space)
    chrome.show_rows(ctx2, {fcs[1]})
    assert fcs[1].select and not fcs[1].hide and fcs[0].hide and not fcs[0].select


def test_editor_click_item_passes_through_first():
    patches = import_module(kit.MODULE + ".keymap.maya_patches")
    assert "allset.graph_channel_click" in patches.PASS_THROUGH_FIRST
    assert any(a[0] == "Animation Channels" and a[1] == "allset.graph_channel_click" for a in patches.ADDED)
