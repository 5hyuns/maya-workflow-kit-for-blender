"""Step 8: Maya marking menus as pies (definitions, classes, dispatch, keymap, Q/W/E/R)."""

import json
import os
import types
from importlib import import_module

import bpy

import kit

mm = import_module(kit.MODULE + ".marking.menus")
marking = import_module(kit.MODULE + ".marking")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
taphold = import_module(kit.MODULE + ".operators.taphold")
maya_patches = import_module(kit.MODULE + ".keymap.maya_patches")

RESEARCH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "research", "maya", "marking_menus.json")
# Menus resolved by hand (radials set from variables in Maya, hotkeys_and_menus.md:248-252).
HAND_RESOLVED = {"dagMenuProc", "dagMenuProc_curve", "buildObjectMenuItemsNow"}
LABEL_ALIASES = {"To Edges": "<$toEdges>", "To Faces": "<$toFaces>"}


class FakeLayout:
    def __init__(self, log=None):
        self.log = [] if log is None else log

    def _sub(self, *_a, **_k):
        return FakeLayout(self.log)

    row = column = box = menu_pie = _sub

    def operator(self, idname, text=None, **kw):
        props = types.SimpleNamespace()
        self.log.append(("op", idname, text, props))
        return props

    def menu(self, idname, text=None, **kw):
        self.log.append(("menu", idname, text))

    def separator(self, *a, **kw):
        self.log.append(("sep",))

    def label(self, text="", **kw):
        self.log.append(("label", text))


def _tool_ids():
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as T
    ids = set()

    def walk(items):
        for it in items:
            if isinstance(getattr(it, "idname", None), str):
                ids.add(it.idname)
            elif isinstance(it, (tuple, list)):
                walk(it)
    for _mode, items in T.tools_all():
        walk(items)
    return ids


def _override():
    win = bpy.context.window_manager.windows[0]
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return bpy.context.temp_override(window=win, area=area, region=region)


def _fresh():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


# --- definitions ------------------------------------------------------------------

def test_definitions_well_formed():
    assert len(mm.MENUS) == 13, sorted(mm.MENUS)
    for name, menu in mm.MENUS.items():
        for path, label, action in mm.walk(menu, name):
            assert label and isinstance(label, str), path
        stack = [menu]
        while stack:
            sub = stack.pop()
            assert set(sub.radial) <= set(mm.RADIALS), (name, sub.radial.keys())
            for _label, action in list(sub.radial.values()) + [e for e in sub.items if e != mm.DIVIDER]:
                if isinstance(action, mm.Sub):
                    stack.append(action)


def test_radial_positions_match_research():
    if not os.path.exists(RESEARCH):
        print("research/maya/marking_menus.json missing: skipped")
        return
    data = json.load(open(RESEARCH, encoding="utf-8"))["menus"]
    checked = 0
    bad = []

    def compare(sub, items, where):
        nonlocal checked
        by_label = {}
        for it in items:
            if it.get("label"):
                by_label.setdefault(it["label"], it)
        for pos, (label, action) in sub.radial.items():
            src = by_label.get(LABEL_ALIASES.get(label, label))
            if src is None:
                bad.append((where, label, "not in research"))
                continue
            checked += 1
            if src.get("radial") != pos:
                bad.append((where, label, pos, src.get("radial")))
            if isinstance(action, mm.Sub) and src.get("submenu"):
                compare(action, src["submenu"], f"{where}/{label}")

    for name, menu in mm.MENUS.items():
        if name in HAND_RESOLVED:
            continue
        compare(menu, data[name]["items"], name)
    print("radial items checked against research:", checked)
    assert not bad, bad
    assert checked >= 80, checked


def test_actions_exist():
    tools = _tool_ids()
    bad = []
    for name, menu in mm.MENUS.items():
        for path, _label, action in mm.walk(menu, name):
            if action is None or isinstance(action, mm.Sub):
                continue
            kind, target, props = menu_map.normalize(action)
            if kind in ("op", "v3d"):
                mod, op = target.split(".")
                try:
                    rna = getattr(getattr(bpy.ops, mod), op).get_rna_type()
                except (AttributeError, KeyError):
                    bad.append((path, target))
                    continue
                bad.extend((path, target, k) for k in props if k not in rna.properties)
            elif kind == "tool" and target not in tools:
                bad.append((path, target))
            elif kind == "menu" and not hasattr(bpy.types, target):
                bad.append((path, target))
    assert not bad, bad


def test_pie_classes_and_slot_order():
    for name in mm.MENUS:
        assert hasattr(bpy.types, marking.idname(name)), name
    # RMB mesh pie: Blender order W, E, S, N, NW, NE, SW, SE.
    fake = types.SimpleNamespace(layout=FakeLayout())
    getattr(bpy.types, marking.idname("dagMenuProc")).draw(fake, bpy.context)
    texts = [e[2] for e in fake.layout.log if e[0] in ("op", "menu")]
    assert texts[:2] == ["Vertex", "Edge"][:0] + ["Vertex", "UV"], texts  # W, E
    assert texts[2] == "Face" and texts[3] == "Select", texts  # S, then the list under S
    assert "Edge" in texts and "Object Mode" in texts and texts.index("Edge") > texts.index("Face")
    # Radial submenu = another pie; empty slots = separators.
    fake = types.SimpleNamespace(layout=FakeLayout())
    getattr(bpy.types, marking.idname("contextPolyToolsEdgeMM")).draw(fake, bpy.context)
    pies = [e for e in fake.layout.log if e[0] == "op" and e[1] == "wm.call_menu_pie"]
    assert {p[3].name for p in pies} >= {marking.idname("contextPolyToolsEdgeMM", "N"),
                                          marking.idname("contextPolyToolsEdgeMM", "NE")}, pies
    fake = types.SimpleNamespace(layout=FakeLayout())
    getattr(bpy.types, marking.idname("rotateMarkingMenuImpl")).draw(fake, bpy.context)
    seps = [e for e in fake.layout.log if e[0] == "sep"]
    assert seps, "N is empty in Maya's rotate options: a separator keeps the slot"
    grey = [e for e in fake.layout.log if e[0] == "op" and e[1] == "maya_kit.menu_unavailable"]
    assert any(g[2] == "Discrete Rotate" for g in grey)


def test_dispatch_by_context():
    _fresh()
    R = marking.resolve
    with _override():
        assert R("RMB", bpy.context) == ("pie", marking.idname("buildObjectMenuItemsNow"))
        assert R("SHIFT_RMB", bpy.context) == ("pie", marking.idname("contextPolyToolsDefaultMM"))
        bpy.ops.mesh.primitive_cube_add()
        assert R("RMB", bpy.context) == ("pie", marking.idname("dagMenuProc"))
        assert R("SHIFT_RMB", bpy.context) == ("pie", marking.idname("contextPolyToolsObjectMM"))
        assert R("CTRL_RMB", bpy.context) == ("pie", marking.idname("dagMenuProc")), "object: RMB menu"
        bpy.ops.object.mode_set(mode='EDIT')
        ts = bpy.context.scene.tool_settings
        for sel, want in (((True, False, False), "contextPolyToolsVertexMM"),
                          ((False, True, False), "contextPolyToolsEdgeMM"),
                          ((False, False, True), "contextPolyToolsFaceMM")):
            ts.mesh_select_mode = sel
            assert R("SHIFT_RMB", bpy.context) == ("pie", marking.idname(want)), sel
        assert R("CTRL_RMB", bpy.context) == ("pie", marking.idname("polyConvertMM"))
        assert R("RMB", bpy.context) == ("pie", marking.idname("dagMenuProc"))
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.camera_add()
        assert R("RMB", bpy.context) == ("menu", "VIEW3D_MT_object_context_menu")
        bpy.ops.curve.primitive_bezier_curve_add()
        assert R("RMB", bpy.context) == ("pie", marking.idname("dagMenuProc_curve"))


def test_tool_options_dispatch():
    ws = bpy.context.workspace
    tool = ws.tools.from_space_view3d_mode('OBJECT', create=True)
    for tid, want in (("builtin.move", "translateMarkingMenuImpl"), ("builtin.rotate", "rotateMarkingMenuImpl"),
                      ("builtin.scale", "scaleMarkingMenuImpl"), ("builtin.select_box", "selectMarkingMenuImpl")):
        tool.idname = tid
        with _override():
            assert marking.resolve("TOOL_OPTIONS", bpy.context) == ("pie", marking.idname(want)), tid


def test_component_item_targets_picked_object():
    _fresh()
    with _override():
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        a = bpy.context.active_object
        bpy.ops.mesh.primitive_cube_add(location=(5, 0, 0))
        b = bpy.context.active_object
        bpy.context.window_manager.maya_kit_mm_target = a.name  # RMB was over cube a
        bpy.ops.maya_kit.mm_component(type='EDGE')
        assert bpy.context.mode == 'EDIT_MESH' and bpy.context.active_object == a
        assert tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, True, False)
        assert not b.select_get()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.window_manager.maya_kit_mm_target = b.name
        bpy.ops.maya_kit.mm_component(type='NONE')
        assert bpy.context.mode == 'OBJECT' and b.select_get() and not a.select_get()
        bpy.ops.maya_kit.mm_clear_selection()
        assert not bpy.context.selected_objects
        bpy.context.window_manager.maya_kit_mm_target = ""


def test_pick_object_ray_cast():
    _fresh()
    with _override():
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        r3d = bpy.context.region_data
        r3d.view_location = (0, 0, 0)
        r3d.view_distance = 10
        region = bpy.context.region
        if region.width < 10:  # -b: region sizes may be 0, ray cast needs a real view
            print("region has no size in -b: skipped")
            return
        ev = types.SimpleNamespace(mouse_region_x=region.width // 2, mouse_region_y=region.height // 2)
        assert marking.pick_object(bpy.context, ev) == cube
        ev = types.SimpleNamespace(mouse_region_x=2, mouse_region_y=2)
        assert marking.pick_object(bpy.context, ev) is None


# --- keymap and Q/W/E/R ------------------------------------------------------------

def _items(km_name):
    kc = bpy.context.window_manager.keyconfigs["Maya"]
    return kc.keymaps[km_name].keymap_items


def test_keymap_marking_menus():
    for km, _menu in maya_patches.MM_KEYMAPS:
        items = _items(km)
        found = {}
        for kmi in items:
            if kmi.type == 'RIGHTMOUSE' and kmi.idname == "maya_kit.marking_menu" and kmi.value == 'PRESS':
                found[(kmi.shift, kmi.ctrl)] = kmi.properties.trigger
        assert found == {(False, False): "RMB", (True, False): "SHIFT_RMB",
                         (False, True): "CTRL_RMB", (True, True): "TOOL_OPTIONS"}, (km, found)
        assert not [k for k in items if k.idname == "wm.call_menu" and k.type == 'RIGHTMOUSE'], km
    v3d = _items("3D View")
    assert not [k for k in v3d if k.type == 'RIGHTMOUSE' and k.shift and not k.ctrl], "Shift+RMB cursor removed"


def test_keymap_qwer_tap_hold():
    for km in maya_patches.TOOL_KEY_KEYMAPS:
        items = _items(km)
        for key, binding in maya_patches.TOOL_KEYS:
            hits = [k for k in items if k.type == key and not (k.shift or k.ctrl or k.alt)]
            assert [(k.idname, k.properties.binding) for k in hits] == [("maya_kit.tap_hold", binding)], \
                (km, key, [(k.idname) for k in hits])
    for _key, binding in maya_patches.TOOL_KEYS:
        b = taphold.get_binding(binding)
        assert b.tool.startswith("builtin.") and hasattr(bpy.types, marking.idname(b.menu)), binding


def test_bindings_removed_on_disable():
    kit.disable()
    try:
        names = taphold.binding_names()
        assert not any(n.startswith("tool_") for n in names), names
        assert not hasattr(bpy.types, marking.idname("dagMenuProc"))
        assert "maya_kit_mm_target" not in bpy.types.WindowManager.bl_rna.properties
    finally:
        kit.enable()
