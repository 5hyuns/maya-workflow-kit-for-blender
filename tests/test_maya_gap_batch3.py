"""Maya items that were greyed: Modify > Convert > Displacement to Polygons (measured in Maya 2026: a new
``<name>_displacement1`` object, the source untouched, nothing selected = error) and Generate > Interactive
Grooming Tools brushes (Blender hair Curves sculpt brushes)."""

from importlib import import_module

import bpy

import kit

menu_map = import_module(kit.MODULE + ".ui.menu_map")


def _clear():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _run(path):
    kind, target, props = menu_map.spec(path)
    mod, _, name = target.partition(".")
    try:
        return getattr(getattr(bpy.ops, mod), name)(**props)
    except RuntimeError:                # an ERROR report (Maya's error): nothing done
        return {'CANCELLED'}


def _select(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = obs[-1] if obs else None


def test_displacement_to_polygons():
    _clear()
    _select()
    assert _run("Modify/Convert/Displacement to Polygons") == {'CANCELLED'}     # Maya: only surface shapes
    bpy.ops.mesh.primitive_plane_add()
    plane = bpy.context.active_object
    plane.name = "pPlane1"
    _select(plane)
    assert _run("Modify/Convert/Displacement to Polygons") == {'CANCELLED'}     # no Displace modifier
    bpy.ops.object.modifier_add(type='SUBSURF')
    mod = plane.modifiers.new("displace", 'DISPLACE')
    mod.strength = 2.0
    n_src = len(plane.data.vertices)
    assert _run("Modify/Convert/Displacement to Polygons") == {'FINISHED'}
    new = bpy.context.active_object
    assert new is not plane and new.name == "pPlane1_displacement1"
    assert not new.modifiers and len(new.data.vertices) > n_src                # stack baked in
    assert min(v.co.z for v in new.data.vertices) > 0.99        # displaced: strength 2 x (1 - midlevel 0.5)
    assert len(plane.modifiers) == 2 and len(plane.data.vertices) == n_src    # source untouched


def test_grooming_brushes():
    names = ("Density", "Place", "Length", "Cut", "Comb", "Grab", "Smooth", "Clump", "Select")
    for maya in names:
        assert menu_map.spec(f"Generate/Interactive Grooming Tools/{maya} Brush")[1] == "allset.groom_brush"
    for maya in ("Width", "Twist", "Noise", "Part", "Freeze"):
        assert f"Generate/Interactive Grooming Tools/{maya} Brush" not in menu_map.MAP
    _clear()
    bpy.ops.mesh.primitive_uv_sphere_add()
    _select(bpy.context.active_object)
    _run("Generate/Interactive Grooming Tools/Comb Brush")                     # mesh -> its new hair, Sculpt mode
    assert bpy.context.mode == 'SCULPT_CURVES'
    assert bpy.context.tool_settings.curves_sculpt.brush.curves_sculpt_brush_type == 'COMB'
    _run("Generate/Interactive Grooming Tools/Place Brush")
    assert bpy.context.tool_settings.curves_sculpt.brush.curves_sculpt_brush_type == 'ADD'
