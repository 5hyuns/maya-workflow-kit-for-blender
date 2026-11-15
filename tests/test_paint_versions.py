"""Paint Skin Weights and the shelf on every supported Blender: the Blender paint panels drawn inside the kit's Tool
Settings, the Replace brush after Smooth, Value / Opacity landing where Blender's strokes read them, how the tool
starts on a new skin, the shelf tab text colour from the user's theme, and the Range Slider's Keying popover."""

import os
from importlib import import_module
from types import SimpleNamespace

import bpy
from mathutils import Vector

import kit


def _mod(name):
    return import_module(f"{kit.MODULE}.{name}")


class Recorder:
    """A stand-in UILayout: every call is recorded and returns another Recorder."""

    def __init__(self, log=None):
        object.__setattr__(self, "log", [] if log is None else log)

    def __setattr__(self, name, value):
        pass

    def __getattr__(self, name):
        def call(*args, **kwargs):
            self.log.append((name, args, kwargs))
            return Recorder(self.log)
        return call

    def props(self):
        """(owner, property) of every ``prop`` call."""
        return [(a[0], a[1]) for n, a, _k in self.log if n in ("prop", "prop_enum") and len(a) >= 2]


class _DockContext:
    """``bpy.context`` as Blender's paint panels see it in a docked Properties editor's main region."""

    def __init__(self, space='PROPERTIES'):
        object.__setattr__(self, "_over", {"region": SimpleNamespace(type='WINDOW'),
                                           "space_data": SimpleNamespace(type=space)})

    def __getattr__(self, name):
        over = object.__getattribute__(self, "_over")
        return over[name] if name in over else getattr(bpy.context, name)


def _clear():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)


def _bound_cylinder():
    """A three-joint skeleton bound to a cylinder (Skin > Bind Skin), the cylinder selected."""
    _clear()
    joints = _mod("operators.joints")
    arm = joints.new_skeleton(bpy.context)
    parent = None
    for p in ((0, 0, 0), (0, 0, 1), (0, 0, 2)):
        parent = joints.add_joint(arm, Vector(p), parent, length=0.5)
    joints.finish(bpy.context, arm, ["joint1", "joint2", "joint3"])
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=2.6, location=(0, 0, 1.3), vertices=12)
    cyl = bpy.context.active_object
    arm.select_set(True)
    cyl.select_set(True)
    bpy.context.view_layer.objects.active = cyl
    assert bpy.ops.allset.bind_skin() == {'FINISHED'}
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    cyl.select_set(True)
    bpy.context.view_layer.objects.active = cyl
    return arm, cyl


def _blender_value_owner(brush, name):
    """The struct Blender's own paint UI shows (and its strokes read) ``name`` from, asked through Blender's
    ``UnifiedPaintPanel.prop_unified``; plus the struct of its "use unified" toggle."""
    from bl_ui import properties_paint_common as paint_common
    rec = Recorder()
    paint_common.UnifiedPaintPanel.prop_unified(rec, _DockContext('VIEW_3D'), brush, name,
                                                unified_name="use_unified_" + name)
    owners = rec.props()
    value = next(o for o, p in owners if p == name)
    toggle = next(o for o, p in owners if p == "use_unified_" + name)
    return value, toggle


# --- How Paint Skin Weights starts on a new skin (first: Blender's own start state) ---------------------------------

def test_flood_replaces_with_full_opacity_on_a_new_skin():
    _arm, cyl = _bound_cylinder()
    assert bpy.ops.allset.paint_skin_weights() == {'FINISHED'}
    cyl.vertex_groups.active_index = cyl.vertex_groups["joint3"].index
    assert bpy.ops.allset.flood_weights() == {'FINISHED'}
    bpy.ops.allset.paint_skin_weights()                      # leave
    j3 = cyl.vertex_groups["joint3"].index
    w3 = [next((g.weight for g in v.groups if g.group == j3), 0.0) for v in cyl.data.vertices]
    sums = [sum(g.weight for g in v.groups) for v in cyl.data.vertices]
    assert min(w3) > 0.999 and max(sums) < 1.001, (min(w3), max(sums))


def test_new_skin_starts_with_replace_and_one_influence():
    _arm, cyl = _bound_cylinder()
    ts = bpy.context.scene.tool_settings
    assert bpy.ops.allset.paint_skin_weights() == {'FINISHED'}
    brush = ts.weight_paint.brush
    value, _t = _blender_value_owner(brush, "weight")
    opacity, _t = _blender_value_owner(brush, "strength")
    # Maya Paint Skin Weights: Replace, Value 1, Opacity 1, the painted influence alone (no Multi-Paint)
    assert brush.blend == 'MIX' and _mod("operators.weight_paint").brush_kind(brush) == 'DRAW', \
        (brush.name, brush.blend)
    assert abs(value.weight - 1.0) < 1e-5 and abs(opacity.strength - 1.0) < 1e-5, (value.weight, opacity.strength)
    assert not ts.use_multipaint and ts.use_auto_normalize
    # the next time on this skin: the brush and Multi-Paint stay as the user left them
    bpy.ops.allset.weight_tool(kind='DRAW', blend='ADD')
    ts.use_multipaint = True
    bpy.ops.allset.paint_skin_weights()                      # leave
    assert bpy.ops.allset.paint_skin_weights() == {'FINISHED'} and bpy.context.mode == 'PAINT_WEIGHT'
    assert ts.use_multipaint and ts.weight_paint.brush.blend == 'ADD', ts.weight_paint.brush.name
    ts.use_multipaint = False
    bpy.ops.allset.weight_tool(kind='DRAW', blend='MIX')
    bpy.ops.object.mode_set(mode='OBJECT')


# --- Blender paint panels inside the Tool Settings -------------------------------------------------------------------

def test_tool_settings_draw_blender_brush_panels():
    _arm, cyl = _bound_cylinder()
    assert bpy.ops.allset.paint_skin_weights() == {'FINISHED'} and bpy.context.mode == 'PAINT_WEIGHT'
    pw = _mod("ui.paint_weights")
    s = _mod("operators.weight_paint").state(bpy.context)
    for flag in ("show_brush", "show_stroke", "show_display"):
        setattr(s, flag, True)
    drawn = []
    native = pw._native

    def record(layout, context, cls):
        drawn.append(cls.__name__)
        native(layout, context, cls)
    pw._native = record
    try:
        ctx = _DockContext()
        for section in (pw._brush, pw._stroke, pw._display):
            rec = Recorder()
            section(rec, ctx)            # raises when a Blender panel asks the kit's stand-in for something it lacks
            props = {p for _o, p in rec.props()}
            if section is pw._brush:
                assert {"curve_distance_falloff_preset", "falloff_shape"} <= props, sorted(props)
    finally:
        pw._native = native
    # Blender's own weight paint Tool Settings show the falloff in the Shape panel where there is one (5.3)
    from bl_ui import properties_paint_common as paint_common
    falloff = "ShapePanel" if hasattr(paint_common, "ShapePanel") else "FalloffPanel"
    assert drawn == [falloff, "StrokePanel", "DisplayPanel"], drawn
    bpy.ops.object.mode_set(mode='OBJECT')


# --- Replace after Smooth --------------------------------------------------------------------------------------------

def test_replace_after_smooth_gets_a_draw_brush():
    _arm, _cyl = _bound_cylinder()
    assert bpy.ops.allset.paint_skin_weights() == {'FINISHED'}
    model = _mod("operators.weight_paint")
    wp = bpy.context.tool_settings.weight_paint
    assert bpy.ops.allset.weight_tool(kind='BLUR') == {'FINISHED'}
    assert model.brush_kind(wp.brush) == 'BLUR', wp.brush.name
    # Maya Replace (the dock's Replace button) after Smooth: a draw brush mixing the Value in
    assert bpy.ops.allset.weight_tool(kind='DRAW', blend='MIX') == {'FINISHED'}
    assert model.brush_kind(wp.brush) == 'DRAW' and wp.brush.blend == 'MIX', (wp.brush.name, wp.brush.blend)
    for kind in ('AVERAGE', 'SMEAR', 'DRAW'):
        assert bpy.ops.allset.weight_tool(kind=kind) == {'FINISHED'}, kind
        assert model.brush_kind(wp.brush) == kind, (kind, wp.brush.name)
    bpy.ops.object.mode_set(mode='OBJECT')


# --- Value / Opacity / Radius are tool settings --------------------------------------------------------------------

def test_option_window_values_reach_the_strokes_for_every_operation():
    _arm, _cyl = _bound_cylinder()
    assert bpy.ops.allset.paint_skin_weights() == {'FINISHED'}
    ts = bpy.context.tool_settings
    wp = ts.weight_paint
    # the Paint Skin Weights option window: Replace, Value 0.3, Opacity 0.4
    assert bpy.ops.allset.paint_skin_weights(settings=True, operation='REPLACE', value=0.3, opacity=0.4,
                                             radius=1.0) == {'FINISHED'}
    for kind, blend in ((None, None), ('BLUR', ''), ('DRAW', 'ADD'), ('SMEAR', ''), ('DRAW', 'MIX')):
        if kind is not None:
            assert bpy.ops.allset.weight_tool(kind=kind, blend=blend) == {'FINISHED'}, kind
        brush = wp.brush
        value, _t = _blender_value_owner(brush, "weight")
        opacity, _t = _blender_value_owner(brush, "strength")
        assert abs(value.weight - 0.3) < 1e-5 and abs(opacity.strength - 0.4) < 1e-5, \
            (brush.name, value, value.weight, opacity, opacity.strength)
    # the dock's Value presets write what the strokes read
    assert bpy.ops.allset.weight_value(value=0.75) == {'FINISHED'}
    value, _t = _blender_value_owner(wp.brush, "weight")
    assert abs(value.weight - 0.75) < 1e-5, (value, value.weight)
    bpy.ops.object.mode_set(mode='OBJECT')


def test_dock_value_rows_use_blenders_owner_and_toggle():
    _arm, _cyl = _bound_cylinder()
    assert bpy.ops.allset.paint_skin_weights() == {'FINISHED'}
    pw = _mod("ui.paint_weights")
    brush = bpy.context.tool_settings.weight_paint.brush
    for name, label in (('strength', 'Opacity'), ('weight', 'Value'), ('size', 'Radius')):
        rec = Recorder()
        pw._unified(rec, bpy.context, name, label)
        owners = rec.props()
        value, toggle = _blender_value_owner(brush, name)
        prop = 'unprojected_size' if name == 'size' and getattr(value, 'use_locked_size', '') == 'SCENE' else name
        assert (value, prop) in owners and (toggle, 'use_unified_' + name) in owners, (name, owners, value, toggle)
    bpy.ops.object.mode_set(mode='OBJECT')


# --- Shelf tab text from the theme --------------------------------------------------------------------------------

def _theme_preset(word):
    for d in bpy.utils.preset_paths("interface_theme"):
        for f in sorted(os.listdir(d)):
            if word in f.lower() and f.endswith(".xml"):
                return os.path.join(d, f)
    raise kit.Skip(f"no {word} theme preset")


def _luma(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def test_shelf_tab_text_reads_on_light_and_dark_themes():
    sp = _mod("ui.shelf_paint")
    try:
        for word, dark_text in (("light", True), ("dark", False)):
            bpy.ops.script.execute_preset(filepath=_theme_preset(word),
                                          menu_idname="USERPREF_MT_interface_theme_presets")
            base = sp._theme_colour(bpy.context)
            current, other, glyph = sp._text_colours(bpy.context)
            # the theme's own Image Editor text: black on the Light theme's grey header, light grey on the Dark one
            assert (_luma(glyph) < 0.2) == dark_text and (_luma(other) < _luma(base)) == dark_text, \
                (word, base, current, other, glyph)
            assert abs(_luma(other) - _luma(base)) > 0.3, (word, base, other)
            assert _luma(other) != _luma(current), (word, current, other)    # other tabs dimmer than the current one
    finally:
        bpy.ops.preferences.reset_default_theme()


# --- Range Slider: Animation Preferences > Keying -------------------------------------------------------------------

def test_keying_entry_pops_a_whole_blender_popover():
    ts = _mod("ui.time_slider")
    rec = Recorder()
    ts.ALLSET_MT_anim_preferences.draw(SimpleNamespace(layout=rec), bpy.context)
    panel = next(k["panel"] for n, _a, k in rec.log if n == "popover" and k.get("text") == "Keying")
    cls = getattr(bpy.types, panel)
    # a popover of its own (a child panel popped alone loses its parent's width), holding the keying set rows
    assert not getattr(cls, "bl_parent_id", ""), (panel, cls.bl_parent_id)
    settings = bpy.types.TIME_PT_keyframing_settings
    assert panel == settings.__name__ or getattr(settings, "bl_parent_id", "") == panel, panel
