"""Step 27: = / - manipulator size (restored on disable), PgUp/PgDn smoothing level, 0,
Home default view, Alt+5 wireframe on shaded. """

from importlib import import_module
from types import SimpleNamespace

import bpy
from mathutils import Quaternion, Vector

import kit

display = import_module(kit.MODULE + ".operators.display")
view = import_module(kit.MODULE + ".operators.view")
preferences = import_module(kit.MODULE + ".preferences")


def _items(km, type, **mods):
    km = kit.maya_kc().keymaps[km]
    want = {"shift": False, "ctrl": False, "alt": False, **mods}
    return [k for k in km.keymap_items if k.active and k.type == type and k.value == 'PRESS'
            and all(getattr(k, m) == v for m, v in want.items())]


def test_keys_bound():
    assert [(k.idname, round(k.properties.factor, 2)) for k in _items("3D View", 'EQUAL')] == \
        [("allset.manip_size", 1.25)]
    assert [(k.idname, round(k.properties.factor, 2)) for k in _items("3D View", 'EQUAL', shift=True)] == \
        [("allset.manip_size", 1.25)]
    assert [(k.idname, round(k.properties.factor, 2)) for k in _items("3D View", 'MINUS')] == \
        [("allset.manip_size", 0.8)]
    assert [k.idname for k in _items("3D View", 'HOME')] == ["allset.view_home"]
    alt5 = _items("3D View", 'FIVE', alt=True)
    assert [k.properties.data_path for k in alt5] == ["space_data.overlay.show_wireframes"]
    for km in ("Object Mode", "Mesh"):
        assert [k.properties.delta for k in _items(km, 'PAGE_UP')] == [1], km
        assert [k.properties.delta for k in _items(km, 'PAGE_DOWN')] == [-1], km
        assert [(k.idname, k.properties.level) for k in _items(km, 'ZERO')] == \
            [("allset.smooth_preview", 1)], km


def test_manip_size_steps_and_restores_on_disable():
    view_prefs = bpy.context.preferences.view
    original = view_prefs.gizmo_size
    bpy.ops.allset.manip_size(factor=1.25)
    bigger = view_prefs.gizmo_size
    assert bigger == round(original * 1.25), (original, bigger)
    bpy.ops.allset.manip_size(factor=0.8)
    bpy.ops.allset.manip_size(factor=0.8)
    assert view_prefs.gizmo_size < original
    for _ in range(30):
        bpy.ops.allset.manip_size(factor=1.25)
    assert view_prefs.gizmo_size == 200, "clamped to Blender's range"
    assert str(original) in preferences.get().runtime_backup
    kit.disable()
    try:
        assert view_prefs.gizmo_size == original, "disable restores the user's size"
    finally:
        kit.enable()
    assert preferences.get().runtime_backup == ""


def _mesh():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add()
    return bpy.context.active_object


def test_smoothing_level_up_down_and_clamp():
    ob = _mesh()
    bpy.ops.allset.smooth_level(delta=1)
    mod = display.preview_modifier(ob, create=False)
    assert mod is not None and mod.levels == 3 and not mod.show_viewport, "hidden until 3"
    bpy.ops.allset.smooth_preview(level=3)
    assert mod.show_viewport and mod.levels == 3
    for _ in range(5):
        bpy.ops.allset.smooth_level(delta=1)
    assert mod.levels == display.SMOOTH_LEVELS[1]
    for _ in range(9):
        bpy.ops.allset.smooth_level(delta=-1)
    assert mod.levels == display.SMOOTH_LEVELS[0]
    bpy.ops.allset.smooth_preview(level=1)        # = Maya 0 key
    assert not mod.show_viewport


def test_home_view_is_maya_persp():
    rv3d = SimpleNamespace(view_perspective='PERSP', view_location=Vector((5, 5, 5)),
                           view_distance=99.0, view_rotation=Quaternion())
    view.home_view(rv3d, 0.01)
    assert abs(rv3d.view_distance - 0.4482) < 1e-3 and Vector(rv3d.view_location).length == 0
    forward = rv3d.view_rotation @ Vector((0, 0, 1))     # view looks down -Z: +Z = towards the eye
    assert (forward - Vector((28, -28, 21)).normalized()).length < 1e-4, forward
    ortho = SimpleNamespace(view_perspective='ORTHO', view_location=Vector((1, 2, 3)),
                            view_distance=5.0, view_rotation=Quaternion((0.5, 0.5, 0.5, 0.5)))
    view.home_view(ortho, 1.0)
    assert ortho.view_rotation == Quaternion((0.5, 0.5, 0.5, 0.5)), "ortho keeps its direction"
    assert Vector(ortho.view_location).length == 0 and abs(ortho.view_distance - 44.82) < 0.01
