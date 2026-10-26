"""Step 224 (Issue #134, rest of #126: A3 A4 A7): Paint Skin Weights Tool Settings fields with Maya 2026's defaults,
the numeric weight display helpers (decision 7: 2,000 labels on screen, then brush-local), a second Bind Skin asks
Maya's question and binds nothing (decision 5), the Skin Clusters list shows every skin read-only and filters the
Influences list, export warns about several skins, Flood honours Min / Max value.
Spec: research/maya/re/maya2026_paint_skin_weights.md §2 (fields, ctx_defaults), §5 (numeric), §6 (skin clusters)."""

import math
from importlib import import_module

import bpy
import numpy as np
from mathutils import Vector

import kit
import test_step218_paint as p218

skin = import_module(kit.MODULE + ".operators.skin")
wp = import_module(kit.MODULE + ".operators.weight_paint")
file_io = import_module(kit.MODULE + ".operators.file_io")
units = import_module(kit.MODULE + ".operators.units")
paint_weights = import_module(kit.MODULE + ".ui.paint_weights")
numbers = import_module(kit.MODULE + ".ui.weight_numbers")
compat = import_module(kit.MODULE + ".compat")


def _approx(a, b, tol=1e-6):
    return all(abs(x - y) < tol for x, y in zip(a, b))


def test_tool_settings_defaults_equal_maya():
    arm, cyl = p218._scene()
    assert bpy.ops.allset.paint_skin_weights(settings=True) == {'FINISHED'}     # Reset to Maya's tool values
    s = wp.state(bpy.context)
    ts = bpy.context.tool_settings
    ups = compat.unified_paint_settings(ts)
    brush = ts.weight_paint.brush
    k = units.maya_unit(bpy.context.scene)
    got = {
        # frames (skinCtxClustersCollapsed 1; Stroke / Stylus Pressure / Display collapsed)
        "Skin Clusters open": s.show_skin_clusters, "Influences open": s.show_influences, "Brush open": s.show_brush,
        "Visualization open": s.show_visualization, "Stroke open": s.show_stroke,
        "Stylus Pressure open": s.show_pressure, "Display open": s.show_display,
        # Influences
        "Sort": s.sort,
        # Brush
        "Mode": wp.paint_mode(bpy.context), "Paint operation": brush.blend if brush else None,
        "Profile": paint_weights.current_profile(brush), "Weight Type": s.weight_type,
        "Normalize Weights": s.normalize_mode, "Opacity": round(ups.strength, 6), "Value": round(ups.weight, 6),
        "Min value": s.min_value, "Max value": s.max_value,
        # Visualization > Numeric
        "Show Numbers": s.show_numbers, "Decimal Places": s.number_places,
        "Number Color": tuple(round(c, 6) for c in s.number_color), "Color Ramp": s.number_color_ramp,
        "Numeric min color": tuple(s.number_min_color), "Numeric max color": tuple(s.number_max_color),
        # Stroke / Display
        "Radius(U)": round(compat_radius(ups) / k, 6) if ups.use_locked_size == 'SCENE' else None,
        "Reflection": cyl.use_mesh_mirror_x, "X-Ray Joints": arm.show_in_front,
    }
    want = {
        "Skin Clusters open": False, "Influences open": True, "Brush open": True, "Visualization open": True,
        "Stroke open": False, "Stylus Pressure open": False, "Display open": False,
        "Sort": 'HIERARCHY',
        "Mode": 'PAINT', "Paint operation": 'MIX', "Profile": 'SOFT', "Weight Type": 'SKIN',
        "Normalize Weights": 'INTERACTIVE', "Opacity": 1.0, "Value": 1.0, "Min value": 0.0, "Max value": 1.0,
        "Show Numbers": False, "Decimal Places": 2, "Number Color": (1.0, 1.0, 0.0), "Color Ramp": False,
        "Numeric min color": (1.0, 1.0, 1.0), "Numeric max color": (0.0, 0.0, 0.0),
        "Radius(U)": 1.0, "Reflection": False, "X-Ray Joints": True,
    }
    bad = {key: (got[key], want[key]) for key in want if got[key] != want[key]}
    assert not bad, bad


def compat_radius(ups):
    r = getattr(ups, "unprojected_radius", None)
    if r is None:                       # 5.x keeps a diameter (step 153)
        return ups.unprojected_size / 2.0
    return r


def test_normalize_weights_off_interactive_post():
    arm, cyl = p218._scene()
    s = wp.state(bpy.context)
    for key, auto in (('NONE', False), ('POST', False), ('INTERACTIVE', True)):
        s.normalize_mode = key
        assert s.normalize_mode == key and bpy.context.tool_settings.use_auto_normalize == auto
        assert cyl[skin.NORMALIZE_PROP] == key


def test_profile_buttons_set_the_falloff():
    arm, cyl = p218._scene()
    brush = bpy.context.tool_settings.weight_paint.brush
    for key in ('GAUSSIAN', 'SOLID', 'SOFT'):
        assert bpy.ops.allset.weight_profile(profile=key) == {'FINISHED'}
        assert paint_weights.current_profile(brush) == key
    assert bpy.ops.allset.weight_profile(profile='SQUARE') == {'CANCELLED'}      # no square Blender brush


def test_flood_honours_min_max_value():
    arm, cyl = p218._scene()
    s = wp.state(bpy.context)
    s.max_value = 0.6
    p218._brush('REPLACE', 1.0, 1.0)
    try:
        assert bpy.ops.allset.flood_weights() == {'FINISHED'}
    finally:
        s.max_value = 1.0
    w = [p218._weights(cyl, i)[1] for i in range(len(cyl.data.vertices))]
    assert max(w) <= 0.6 + 1e-6 and min(w) > 0.59, (min(w), max(w))


# --- numeric display (decision 7) --------------------------------------------------------------------------------

def test_number_format_and_ramp():
    assert numbers.format_weight(0.3456, 2) == "0.35"
    assert numbers.format_weight(0.3456, 4) == "0.3456"
    assert numbers.format_weight(1.0, 1) == "1.0"
    assert numbers.format_weight(0.5, 9) == "0.5000"          # Maya's 1-4 decimals
    assert numbers.ramp_color(0.0, (1, 1, 1), (0, 0, 0)) == (1, 1, 1)
    assert numbers.ramp_color(1.0, (1, 1, 1), (0, 0, 0)) == (0, 0, 0)
    assert _approx(numbers.ramp_color(0.25, (1, 1, 1), (0, 0, 0)), (0.75, 0.75, 0.75))


def test_labels_capped_at_2000_then_brush_local():
    rng = np.random.default_rng(1)
    x, y = rng.uniform(0, 1000, 5000), rng.uniform(0, 800, 5000)
    inside = np.ones(5000, bool)
    idx, n = numbers.pick(x[:1500], y[:1500], inside[:1500], None, 50)
    assert len(idx) == 1500 and n == 1500                          # under the cap: every vertex in view
    idx, n = numbers.pick(x, y, inside, (500, 400), 100)
    assert n == 5000 and 0 < len(idx) <= numbers.LIMIT
    assert np.all((x[idx] - 500) ** 2 + (y[idx] - 400) ** 2 <= 100 ** 2 + 1e-9)
    idx, n = numbers.pick(x, y, inside, None, 100)
    assert len(idx) == 0                                           # pointer outside the view: no labels


def test_projection_matches_blender():
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    from mathutils import Matrix
    persp = Matrix.Translation((0.1, -0.2, -5.0))
    persp = Matrix(((1.2, 0, 0, 0), (0, 1.6, 0, 0), (0, 0, -1.0, -0.2), (0, 0, -1.0, 0))) @ persp

    class R:
        width, height = 800, 600

    class RV:
        perspective_matrix = persp
    pts = np.array([[0.0, 0.0, 0.0], [0.5, 0.3, -1.0], [-1.0, 0.2, 0.5]])
    x, y, ok = numbers.project(pts, persp, 800, 600)
    for i, p in enumerate(pts):
        want = location_3d_to_region_2d(R, RV, Vector(p))
        assert want is not None and abs(want.x - x[i]) < 1e-3 and abs(want.y - y[i]) < 1e-3, (i, want, x[i], y[i])


# --- skin clusters (decision 5) ----------------------------------------------------------------------------------

def _second_skeleton(cyl):
    joints = import_module(kit.MODULE + ".operators.joints")
    bpy.ops.object.mode_set(mode='OBJECT')
    arm2 = joints.new_skeleton(bpy.context)
    parent, names = None, []
    for z in (2.0, 6.0):
        parent = joints.add_joint(arm2, Vector((0.5, 0.0, z)), parent, length=0.5)
        names.append(parent)
    joints.finish(bpy.context, arm2, names)
    bpy.ops.object.mode_set(mode='OBJECT')
    mod = cyl.modifiers.new("skinCluster2", 'ARMATURE')
    mod.object = arm2
    for name in names:
        cyl.vertex_groups.new(name=name).add([0, 1], 0.1, 'REPLACE')
    return arm2, set(names)


def test_second_bind_asks_maya_question_and_binds_nothing():
    arm, cyl = p218._scene()
    bpy.ops.object.mode_set(mode='OBJECT')
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    arm.select_set(True)
    cyl.select_set(True)
    bpy.context.view_layer.objects.active = cyl
    skin.QUESTION["mesh"] = None
    before = {g.name: [p218._weights(cyl, i) for i in (0, 80)] for g in cyl.vertex_groups[:1]}
    assert bpy.ops.allset.bind_skin() == {'CANCELLED'}
    assert skin.QUESTION["mesh"] == cyl.name
    assert skin.question_text(cyl.name) == ("There is already a skin cluster on pCylinder1.\n"
                                            "Do you want to create another?")
    assert len(skin.armature_modifiers(cyl)) == 1
    assert {g.name: [p218._weights(cyl, i) for i in (0, 80)] for g in cyl.vertex_groups[:1]} == before
    # a fresh mesh in the same selection still needs its own Bind Skin (Maya cancels the whole bind on No)
    assert "Add Influence" in skin.SECOND_SKIN_NOTE


def test_skin_clusters_list_filters_influences_and_export_warns():
    arm, cyl = p218._scene()
    arm2, second = _second_skeleton(cyl)
    mods = skin.armature_modifiers(cyl)
    assert [m.name for m in mods] == ["skinCluster1", "skinCluster2"]
    s = wp.state(bpy.context)

    def shown():
        flags, _order = paint_weights.influence_filter(cyl, 1, mod=paint_weights.chosen_cluster(bpy.context, cyl))
        return {g.name for g, f in zip(cyl.vertex_groups, flags) if f}
    s.skin_cluster = 0
    assert shown() == {"joint1", "joint2", "joint3"}              # Maya: the first bound one on entry
    assert bpy.ops.allset.weight_skin_cluster(index=1) == {'FINISHED'}
    assert shown() == second and not second & {"joint1", "joint2", "joint3"}
    s.skin_cluster = 0
    assert file_io.multi_skin_meshes([cyl, arm]) == [cyl.name]
