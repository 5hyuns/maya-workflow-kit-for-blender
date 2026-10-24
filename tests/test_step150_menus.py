"""Step 150 lane A (#96): Maya Graph Editor View / Show items — Auto Frame, Auto Frame Time, Curve Name, Show >
Clear Below / Subdiv Objects mapped (ui/graph_view.py); the rest greyed with a one-line notice."""

import json
import os
from importlib import import_module
from pathlib import Path

import bpy

import kit

menu_map = import_module(kit.MODULE + ".ui.menu_map")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
notices = import_module(kit.MODULE + ".ui.notices")
graph_view = import_module(kit.MODULE + ".ui.graph_view")
preferences = import_module(kit.MODULE + ".preferences")

CAPTURE = Path(os.environ.get("ALLSET_ROOT", Path(__file__).resolve().parent.parent)) / \
    "research" / "maya" / "screens" / "editors104" / "_editors104.json"

GE = "Graph Editor"
MAPPED = {
    f"{GE}/View/Auto Frame": ("prop", "addon_prefs.graph_auto_frame", {}),
    f"{GE}/View/Auto Frame Time": ("prop", "addon_prefs.graph_auto_frame_time", {}),
    f"{GE}/View/Curve Name/Always": ("prop", "addon_prefs.graph_curve_names", {"value": 'ALWAYS'}),
    f"{GE}/View/Curve Name/Never": ("prop", "addon_prefs.graph_curve_names", {"value": 'NEVER'}),
    f"{GE}/View/Curve Name/Active Only": ("prop", "addon_prefs.graph_curve_names", {"value": 'ACTIVE'}),
}
GREYED_VIEW = ("Undo View Change", "Redo View Change", "Clip Time", "Show Results", "Show Buffer Curves",
               "Show Play Range Shades", "Lock Play Range Shades", "Highlight Affected Curves", "Keys/Never",
               "Key View/Detailed", "Key View/Simple", "Time Ruler Placement/Top", "Time Ruler Placement/Bottom",
               "Theme/Dark", "Theme/Light", "Theme/TRS Distinct", "Theme/Colorblind Compatible", "Theme/Classic",
               "Theme/Export Current Theme", "Simple Toolbar")
GREYED_SHOW = ("Objects/Asset", "Objects/IkHandles", "Objects/Characters", "Objects/Clips", "Objects/Sets",
               "Objects/MASH", "Attributes/Hidden", "Attributes/Driven by Anim Curve",
               "Attributes/Driven by Expression", "Attributes/Driven by Driven Key", "Attributes/User Defined",
               "Attributes/Published", "Show Selected Type(s)", "Select Attributes...", "Create Entry...",
               "Delete Entry...", "Show Auxiliary Nodes", "Auxiliary Nodes...")


def _prefs():
    return preferences.get(bpy.context)


def _scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 120
    sc.frame_preview_start, sc.frame_preview_end = 10, 30   # (setting the start turns the preview range on)
    sc.use_preview_range = False
    obs = []
    for name, frames, axis, values in (("pCube1", (1, 24), 0, (0.0, 5.0)), ("pCube2", (40, 200), 2, (0.0, 50.0))):
        bpy.ops.mesh.primitive_cube_add()
        ob = bpy.context.active_object
        ob.name = name
        for f, v in zip(frames, values):
            ob.location[axis] = v
            ob.keyframe_insert("location", index=axis, frame=f)
        obs.append(ob)
    sc.frame_set(1)
    return obs


def _graph():
    w = bpy.context.window_manager.windows[0]
    area = max(w.screen.areas, key=lambda a: a.width * a.height)
    area.ui_type = 'FCURVES'
    area.spaces.active.dopesheet.show_only_selected = True
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return w, area, region


def _select(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _view(region):
    v = region.view2d
    (x0, y0), (x1, y1) = v.region_to_view(0, 0), v.region_to_view(region.width, region.height)
    return x0, y0, x1, y1


# --- mappings ---------------------------------------------------------------------------------------------------

def test_view_items_mapped_to_kit_modes():
    for path, want in MAPPED.items():
        assert menu_map.spec(path) == want, (path, menu_map.spec(path))
        owner, attr = menu_sets.prop_owner(bpy.context, want[1])
        assert owner.as_pointer() == _prefs().as_pointer() and hasattr(owner, attr), path
    p = _prefs()
    assert p.graph_auto_frame is True and p.graph_auto_frame_time is False and p.graph_curve_names == 'NEVER'
    if CAPTURE.exists():     # Maya 2022 factory states (research/ is not tracked)
        view = next(m for m in json.loads(CAPTURE.read_text(encoding="utf-8"))["graph_editor"][0]["bars"][0]["menus"]
                    if m["title"] == "View")["items"]
        by = {it["text"]: it for it in view}
        assert by["Auto Frame"]["checked"] is True and by["Auto Frame Time"]["checked"] is False
        names = {it["text"]: it["checked"] for it in by["Curve Name"]["items"]}
        assert names == {"Always": False, "Never": True, "Active Only": False}, names
    # check / radio items toggle the add-on preference only
    menu_sets.set_prop(bpy.context, "addon_prefs.graph_auto_frame", {})
    assert p.graph_auto_frame is False
    menu_sets.set_prop(bpy.context, "addon_prefs.graph_auto_frame", {})
    menu_sets.set_prop(bpy.context, "addon_prefs.graph_curve_names", {"value": 'ACTIVE'})
    assert p.graph_curve_names == 'ACTIVE'
    p.graph_curve_names = 'NEVER'


def test_show_items_mapped():
    for ed in ("Graph Editor", "Dope Sheet"):
        assert menu_map.spec(f"{ed}/Show/Objects/Clear Below")[1] == "allset.graph_show_clear"
        assert menu_map.spec(f"{ed}/Show/Attributes/Clear Below") == (
            "op", "wm.context_set_string", {"data_path": "space_data.dopesheet.filter_text", "value": ""})
        assert menu_map.spec(f"{ed}/Show/Objects/Subdiv Objects") == (
            "prop", "space_data.dopesheet.show_meshes", {})


def test_show_clear_below_lists_every_object_type():
    w, area, region = _graph()
    ds = area.spaces.active.dopesheet
    for attr in graph_view.OBJECT_FILTERS:
        setattr(ds, attr, False)
    ds.filter_text = "Location"
    with bpy.context.temp_override(window=w, area=area, region=region):
        assert bpy.ops.allset.graph_show_clear() == {'FINISHED'}
        # (Blender's context_set_* report CANCELLED for space_data paths: no undo step, the value is set)
        bpy.ops.wm.context_set_string(data_path="space_data.dopesheet.filter_text", value="")
    assert all(getattr(ds, a) for a in graph_view.OBJECT_FILTERS)
    assert ds.filter_text == ""


# --- Auto Frame / Auto Frame Time -------------------------------------------------------------------------------

def test_auto_frame_frames_the_new_selection():
    a, b = _scene()
    w, area, region = _graph()
    p = _prefs()
    p.graph_auto_frame, p.graph_auto_frame_time = True, False
    graph_view._state["sig"] = None
    _select(a)
    assert graph_view.step(bpy.context, p) == 0, "first poll = baseline"
    assert graph_view.step(bpy.context, p) == 0, "no change, no frame"
    _select(b)
    assert graph_view.step(bpy.context, p) == 1
    x0, y0, x1, y1 = _view(region)
    assert x0 <= 40 and x1 >= 200 and x1 - x0 < 400, (x0, x1)
    assert y0 <= 0 and y1 >= 50 and y1 - y0 < 120, (y0, y1)
    _select(a)
    assert graph_view.step(bpy.context, p) == 1
    x0, _y0, x1, y1 = _view(region)
    assert x0 <= 1 and 24 <= x1 < 100 and 5 <= y1 < 20, (x0, x1, y1)
    # off: no framing
    p.graph_auto_frame = False
    _select(b)
    assert graph_view.step(bpy.context, p) == 0
    assert _view(region)[2] < 100
    p.graph_auto_frame = True


def test_auto_frame_time_keeps_the_value_axis_and_the_preview_range():
    a, b = _scene()
    w, area, region = _graph()
    p = _prefs()
    p.graph_auto_frame, p.graph_auto_frame_time = False, True
    graph_view._state["sig"] = None
    _select(a)
    graph_view.step(bpy.context, p)
    _x0, y0, _x1, y1 = _view(region)
    sc = bpy.context.scene
    for on in (False, True):
        sc.use_preview_range = on
        before = (sc.use_preview_range, sc.frame_preview_start, sc.frame_preview_end)
        _select(b if not on else a)
        assert graph_view.step(bpy.context, p) == 1
        got = (sc.use_preview_range, sc.frame_preview_start, sc.frame_preview_end)
        assert got == before, (got, before)
        if not on:
            x0, ny0, x1, ny1 = _view(region)
            lo, hi = graph_view.time_span([40, 200])
            assert abs(x0 - lo) < 0.5 and abs(x1 - hi) < 0.5, (x0, x1, lo, hi)
            assert abs(ny0 - y0) < 1e-3 and abs(ny1 - y1) < 1e-3, "value axis kept"
    x0, _y0, x1, _y1 = _view(region)
    lo, hi = graph_view.time_span([1, 24])
    assert abs(x0 - lo) < 0.5 and abs(x1 - hi) < 0.5, (x0, x1, lo, hi)
    p.graph_auto_frame, p.graph_auto_frame_time = True, False


def test_time_span():
    assert graph_view.time_span([]) is None
    assert graph_view.time_span([40, 200]) == (32, 208)
    lo, hi = graph_view.time_span([5])
    assert lo < 5 < hi


# --- Curve Name -------------------------------------------------------------------------------------------------

def test_plug_names():
    assert graph_view.maya_attr("Translate X") == "translateX"
    assert graph_view.maya_attr("Delta Rotate Z") == "deltaRotateZ"
    assert graph_view.maya_attr("myAttr") == "myAttr"
    assert graph_view.plug_name("pCube1", "location", "Translate X") == "pCube1.translateX"
    assert graph_view.plug_name("rig", 'pose.bones["joint2"].location', "Translate Y") == "joint2.translateY"
    assert graph_view.plug_name("Key", 'key_blocks["smile"].value', "Value") == "smile.value"


def test_curve_names_drawn_per_mode():
    a, b = _scene()
    w, area, region = _graph()
    _select(a, b)
    p = _prefs()
    with bpy.context.temp_override(window=w, area=area, region=region):
        bpy.ops.graph.view_all()
        p.graph_curve_names = 'NEVER'
        assert graph_view.name_items(bpy.context, region) == []
        p.graph_curve_names = 'ALWAYS'
        items = graph_view.name_items(bpy.context, region)
        texts = sorted(t for _x, _y, t, _c in items)
        assert texts == ["pCube1.translateX", "pCube2.translateZ"], texts
        # at the last key, in region pixels of the stored value
        x, y, _t, rgba = next(i for i in items if i[2] == "pCube2.translateZ")
        ex, ey = region.view2d.view_to_region(200, 50.0, clip=False)
        assert abs(x - ex) < 1 and abs(y - ey) < 1, (x, y, ex, ey)
        assert len(rgba) == 4
        p.graph_curve_names = 'ACTIVE'
        for ob, sel in ((a, True), (b, False)):
            for fc in kit.fcurves(ob):
                fc.select = sel
        assert [t for _x, _y, t, _c in graph_view.name_items(bpy.context, region)] == ["pCube1.translateX"]
        area.spaces.active.use_normalization = True
        assert graph_view.name_items(bpy.context, region) == [], "normalized view: no names"
        area.spaces.active.use_normalization = False
    p.graph_curve_names = 'NEVER'


# --- notices ----------------------------------------------------------------------------------------------------

def test_still_greyed_items_have_a_notice():
    paths = [f"{GE}/View/{i}" for i in GREYED_VIEW] + [f"{ed}/Show/{i}" for ed in (GE, "Dope Sheet")
                                                         for i in GREYED_SHOW]
    leaves = {p for p, _it in menu_sets.iter_items()}
    for path in paths:
        assert path in leaves, path
        assert path not in menu_map.MAP, path
        sub, line = notices.greyed_notice(path)
        assert sub and "Blender" in line, path
    # the View items now have their own line (no generic "no such display option")
    for item in GREYED_VIEW:
        if not item.startswith("Theme/"):
            assert f"{GE}/View/{item}" in notices.NOTICES, item
    assert "Snapshot" in notices.NOTICES[f"{GE}/View/Show Buffer Curves"][1]
