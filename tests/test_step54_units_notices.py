"""Step 54: create paths in Maya units (PLAN W5), light power x maya_unit^2, and the shared
notices (PLAN W3). ; GUI: tests/gui/gui_step54_units_notices.py."""

import types
from importlib import import_module

import bpy

import kit

create = import_module(kit.MODULE + ".operators.create")
units = import_module(kit.MODULE + ".operators.units")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
shelf_map = import_module(kit.MODULE + ".ui.shelf_map")
notices = import_module(kit.MODULE + ".ui.notices")
mm = import_module(kit.MODULE + ".marking.menus")

# The three unit setups of : MayaKit template (m, cm shown), Maya Units (1 BU = 1 cm), factory m.
SETUPS = {
    "template": dict(system='METRIC', length_unit='CENTIMETERS', scale_length=1.0),   # maya_unit 0.01
    "maya units": dict(system='METRIC', length_unit='CENTIMETERS', scale_length=0.01),  # 1
    "factory": dict(system='METRIC', length_unit='METERS', scale_length=1.0),          # 1
}
RAW_CREATE = {"object.armature_add", "object.text_add", "object.empty_image_add", "object.effector_add",
              "object.quick_smoke", "object.light_add"}


def _units(name):
    us = bpy.context.scene.unit_settings
    for key, value in SETUPS[name].items():
        setattr(us, key, value)
    return units.maya_unit()


def _fresh():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _make(kind):
    assert bpy.ops.maya_kit.create(kind=kind) == {'FINISHED'}, kind
    return bpy.context.view_layer.objects.active


def test_create_paths_in_maya_units():
    expect = {"template": 0.01, "maya units": 1.0, "factory": 1.0}
    for setup, want_k in expect.items():
        _fresh()
        k = _units(setup)
        assert abs(k - want_k) < 1e-6 * want_k, (setup, k)
        joint = _make('JOINT')
        bone = joint.data.bones[0]
        assert abs(bone.length - k) < 1e-5 * k and bone.name == "joint1" and joint.name == "skeleton1", setup
        assert joint.pose.bones[0].rotation_mode == 'XYZ'
        text = _make('TEXT')
        assert abs(text.data.size - k) < 1e-5 * k and text.name == "typeMesh1", (setup, text.data.size)
        plane = _make('IMAGE_PLANE')
        assert plane.empty_display_type == 'IMAGE' and abs(plane.empty_display_size - k) < 1e-5 * k
        assert plane.name == "imagePlane1"
        for kind, field, name in (('FIELD_AIR', 'WIND', "airField1"), ('FIELD_DRAG', 'DRAG', "dragField1"),
                                  ('FIELD_GRAVITY', 'WIND', "gravityField1"), ('FIELD_NEWTON', 'FORCE', "newtonField1"),
                                  ('FIELD_RADIAL', 'FORCE', "radialField1"),
                                  ('FIELD_TURBULENCE', 'TURBULENCE', "turbulenceField1"),
                                  ('FIELD_UNIFORM', 'WIND', "uniformField1"), ('FIELD_VORTEX', 'VORTEX', "vortexField1")):
            ob = _make(kind)
            assert ob.field.type == field and abs(ob.empty_display_size - k) < 1e-5 * k and ob.name == name, (setup, kind)
            assert tuple(ob.location) == (0.0, 0.0, 0.0), "Maya fields start at the origin"
        # gravity blows down (Maya -Y = Blender -Z): the wind's +Z axis points down
        g = bpy.data.objects["gravityField1"]
        assert (g.matrix_world.to_3x3().col[2]).z < -0.99
        u = bpy.data.objects["uniformField1"]
        assert (u.matrix_world.to_3x3().col[2]).x > 0.99, "Maya uniform field direction (1, 0, 0)"


def test_light_power_scaled_by_maya_unit_squared():
    for setup in SETUPS:
        _fresh()
        k = _units(setup)
        for kind, base in (('POINT_LIGHT', 10.0), ('SPOT_LIGHT', 10.0), ('AREA_LIGHT', 10.0)):
            ob = _make(kind)
            assert abs(ob.data.energy - base * k * k) < 1e-5 * base * k * k, (setup, kind, ob.data.energy)
        sun = _make('DIRECTIONAL_LIGHT')
        assert abs(sun.data.energy - 1.0) < 1e-9, "sun light: no distance falloff, not scaled"


def test_quick_smoke_domain_in_maya_units():
    for setup in ("template", "factory"):
        _fresh()
        k = _units(setup)
        cube = _make('CUBE')                         # 1 Maya unit cube at the origin
        cube.select_set(True)
        assert bpy.ops.maya_kit.quick_smoke() == {'FINISHED'}
        domain = next(o for o in bpy.data.objects if o is not cube)
        half = 0.5 * k
        want = (half + 1.0 * k, half + 1.0 * k, half + 2.0 * k)
        assert all(abs(a - b) < 1e-6 for a, b in zip(domain.scale, want)), (setup, tuple(domain.scale), want)
        assert abs(domain.location.z - 1.0 * k) < 1e-6


def _actions():
    for path, action in menu_map.MAP.items():
        yield path, action
    for key, (action, _icon) in shelf_map.BY_COMMAND.items():
        yield f"shelf {key}", action
    for name, menu in mm.MENUS.items():
        for path, _label, action in mm.walk(menu, name):
            yield path, action


def test_no_raw_create_operator_left():
    bad = []
    for path, action in _actions():
        s = menu_map.normalize(action) if not isinstance(action, mm.Sub) else None
        if s is not None and s[1] in RAW_CREATE:
            bad.append((path, s[1]))
    assert not bad, bad


def test_notices_are_real_menu_paths_with_a_line():
    paths = {path for path, _it in menu_sets.iter_items()}
    missing = sorted(set(notices.NOTICES) - paths)
    assert not missing, missing
    for path, (substitute, line) in notices.NOTICES.items():
        assert substitute and line.startswith("Blender") or "Blender" in line, (path, line)
    want = {"Windows/Relationship Editors/Animation Layers": "NLA", "Windows/Animation Editors/Trax Editor": "NLA",
            "Control/Create Character Set": "Keying Set", "Windows/Node Editor": "drivers",
            "Windows/General Editors/Hypergraph: Hierarchy": "Outliner", "Skeleton/HumanIK": "Rigify",
            "Windows/General Editors/Namespace Editor": "ns:", "File/Create Reference...": "Library Override",
            "File/Set Project...": "relative", "Modify/Evaluate Nodes/nucleuses": "nucleus",
            "Windows/Rendering Editors/Light Editor": "Light Editor", "Create/Lights/Point Light": "square"}
    for path, word in want.items():
        assert word in " ".join(notices.NOTICES[path]), (path, word)


class _Rec:
    def __init__(self):
        self.log = []

    def operator(self, idname, text=None, **kw):
        props = types.SimpleNamespace()
        self.log.append((idname, text, props))
        return props

    def menu(self, idname, text=None, **kw):
        self.log.append(("menu", idname, text))


def test_notice_in_tooltip_and_help_line():
    # an item with a substitute draws through maya_kit.menu_item (its tooltip carries the notice)
    rec = _Rec()
    menu_sets.draw_item(rec, "Windows/Animation Editors/Trax Editor", "Trax Editor")
    assert rec.log[0][0] == "maya_kit.menu_item" and rec.log[0][2].item == "Windows/Animation Editors/Trax Editor"
    props = types.SimpleNamespace(item="Windows/Animation Editors/Trax Editor")
    tip = menu_sets.MAYAKIT_OT_menu_item.description(bpy.context, props)
    assert "NLA" in tip and "Trax" in tip, tip
    assert "NLA" in notices.current(), "the Help Line shows the notice while the tooltip is up"
    # a greyed item keeps maya_kit.menu_unavailable, tooltip with the notice
    rec = _Rec()
    menu_sets.draw_item(rec, "Render/Batch Render", "Batch Render")     # step 67 (Light Editor is mapped now)
    assert rec.log[0][0] == "maya_kit.menu_unavailable"
    tip = menu_sets.MAYAKIT_OT_menu_unavailable.description(
        bpy.context, types.SimpleNamespace(item="Render/Batch Render"))
    assert "Batch Render" in tip and "blender -b" in tip, tip
    # items without a notice are unchanged
    rec = _Rec()
    menu_sets.draw_item(rec, "Create/Polygon Primitives/Cube", "Cube")
    assert rec.log[0][0] == "maya_kit.create"
    # every notice gets into its item's tooltip
    for path in notices.NOTICES:
        cls = menu_sets.MAYAKIT_OT_menu_item if path in menu_map.MAP else menu_sets.MAYAKIT_OT_menu_unavailable
        tip = cls.description(bpy.context, types.SimpleNamespace(item=path))
        assert notices.NOTICES[path][1] in tip, path
