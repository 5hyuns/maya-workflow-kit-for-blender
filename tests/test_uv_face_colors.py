"""UV Editor Shaded (#246): faces whose UVs wind clockwise (flipped) are told apart from front-facing ones; 5 / View >
Shaded turns the colours on, 4 / Wireframe off."""

from importlib import import_module

import bmesh
import bpy

import kit

uvd = import_module(kit.MODULE + ".ui.uv_display")
emm = import_module(kit.MODULE + ".ui.editor_menu_map")


def test_face_winding_splits_flipped_faces():
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    vs = [bm.verts.new(co) for co in ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (2, 0, 0), (2, 1, 0))]
    a = bm.faces.new((vs[0], vs[1], vs[2], vs[3]))
    b = bm.faces.new((vs[1], vs[4], vs[5], vs[2]))
    for f, corners in ((a, ((0, 0), (1, 0), (1, 1), (0, 1))),          # counter-clockwise
                       (b, ((1, 0), (1, 1), (2, 1), (2, 0)))):         # clockwise = flipped
        for loop, co in zip(f.loops, corners):
            loop[uv].uv = co
    front, flipped = uvd.face_winding(bm, uv, [a, b])
    assert len(front) == 2 and len(flipped) == 2, (front, flipped)     # each quad = 2 triangles
    assert all(abs(p[0]) <= 1.0 for t in front for p in t)
    assert all(p[0] >= 1.0 for t in flipped for p in t)
    bm.free()


def test_shaded_and_wireframe_turn_the_colours_on_and_off():
    assert emm.MAP["UV Editor/View/Shaded"] == ("prop", "window_manager.allset_uv_face_colors", {"value": True})
    assert emm.MAP["UV Editor/View/Wireframe"] == ("prop", "window_manager.allset_uv_face_colors", {"value": False})
    assert bpy.context.window_manager.allset_uv_face_colors is False      # off until Shaded is picked


def test_shaded_property_shows_or_hides_faces_in_uv_editors():
    wm = bpy.context.window_manager
    area = bpy.context.screen.areas[0] if bpy.context.screen else None
    if area is None:
        return
    old = area.ui_type
    area.ui_type = 'UV'
    space = area.spaces.active
    wm.allset_uv_face_colors = True
    assert space.uv_editor.show_faces and space.uv_editor.uv_face_opacity == 1.0
    wm.allset_uv_face_colors = False
    assert not space.uv_editor.show_faces
    area.ui_type = old
