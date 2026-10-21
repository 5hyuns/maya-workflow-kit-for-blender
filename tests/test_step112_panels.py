"""Step 112: the Tool Box column identity and framing beside the dock. The Solid Side Panels preset (Region Overlap
off) is gone since step 130 (docs/user_decisions.md #13): Maya mode leaves Blender's Region Overlap as the user set
it."""

from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

preferences = import_module(kit.MODULE + ".preferences")
toolbox = import_module(kit.MODULE + ".ui.toolbox")


def test_maya_mode_leaves_region_overlap_alone():
    p = bpy.context.preferences.system
    assert p.use_region_overlap, "factory value (on) kept in Maya mode"
    assert not hasattr(preferences.get(), "use_maya_panels")
    p.use_region_overlap = False          # the user's own choice survives disable / enable
    try:
        kit.disable()
        kit.enable()
        assert not p.use_region_overlap
    finally:
        p.use_region_overlap = True


def test_toolbox_identity_ignores_overlays():
    base = dict(type='VIEW_3D', show_region_toolbar=True, show_region_header=False, show_region_ui=False,
                show_object_viewport_mesh=False)
    for overlays in (False, True):
        sp = SimpleNamespace(**base, overlay=SimpleNamespace(show_overlays=overlays))
        assert toolbox.is_toolbox(sp)
    assert not toolbox.is_toolbox(SimpleNamespace(**dict(base, show_object_viewport_mesh=True)))


def test_fit_wide_box_in_narrow_perspective_view():
    """Ctrl+Shift+F / A with a far child in the view beside the solid dock (matrices from gui_step17_framing):
    the box ends inside the visible rect, centred, filling 0.95 on its tighter axis."""
    from mathutils import Matrix, Quaternion, Vector
    framing = import_module(kit.MODULE + ".operators.framing")
    rot = Quaternion((0.7123758792877197, 0.4410620927810669, 0.28735825419425964, 0.4641229212284088))
    win = Matrix(((1.3889, 0, 0, 0), (0, 1.765, 0, 0), (0, 0, -1.0, -0.02), (0, 0, -1, 0)))
    pts = [Vector((x, y, z)) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)] + [Vector((12, 0, 0))]
    size = rect = (901, 709)
    loc, d = framing.fit(pts, rot, win, 2.84, False, size, (0, 0) + rect)
    b = framing._bounds(win @ framing.view_matrix(loc, rot, d), framing.box_corners(pts), size)
    assert b[0] >= 0 and b[1] >= 0 and b[2] <= size[0] and b[3] <= size[1], b
    assert abs((b[0] + b[2]) / 2 - size[0] / 2) < 1 and abs((b[1] + b[3]) / 2 - size[1] / 2) < 1, b
    ratio = max((b[2] - b[0]) / size[0], (b[3] - b[1]) / size[1])
    assert abs(ratio - 0.95) < 0.01, ratio
