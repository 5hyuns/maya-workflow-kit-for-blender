"""#357: Maya Blue Pencil on Blender's annotations — frames for the Time Slider marks, Alt+< / Alt+> jumps (wrapping
around like Maya), ghosts of the nearest frames (on, 3 frames each side, fading), the Tool Settings tools."""

from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

bp = import_module(kit.MODULE + ".ui.blue_pencil")
ts_mod = import_module(kit.MODULE + ".ui.time_slider")
prefs_mod = import_module(kit.MODULE + ".preferences")


def _annotation(frames=(5, 12, 20), hidden_frames=()):
    sc = bpy.context.scene
    for a in list(bpy.data.annotations):
        bpy.data.annotations.remove(a)
    gp = bpy.data.annotations.new("Annotations")
    sc.annotation = gp
    lay = gp.layers.new("Note")
    lay.color = (0.2, 0.6, 1.0)
    lay.thickness = 3
    for i, f in enumerate(frames):
        fr = lay.frames.new(f)
        st = fr.strokes.new()
        st.display_mode = '3DSPACE'
        st.points.add(2)
        st.points[0].co = (0.0, 0.0, float(i))
        st.points[1].co = (1.0, 0.0, float(i))
    if hidden_frames:
        other = gp.layers.new("Hidden")
        for f in hidden_frames:
            other.frames.new(f)
        other.annotation_hide = True
    return gp, lay


def test_jump_wraps_around_like_maya():
    frames = [5, 12, 20]
    assert bp.jump_target(frames, 8, True) == 12
    assert bp.jump_target(frames, 12, True) == 20
    assert bp.jump_target(frames, 20, True) == 5          # past the last: back to the first
    assert bp.jump_target(frames, 8, False) == 5
    assert bp.jump_target(frames, 5, False) == 20         # before the first: the last
    assert bp.jump_target([], 8, True) is None


def test_ghost_frames_and_fading():
    frames = [5, 12, 20, 30]
    assert bp.ghost_frames(frames, 12, 3, 3) == ([(5, 1)], [(20, 1), (30, 2)])
    assert bp.ghost_frames(frames, 15, 1, 1) == ([(5, 1)], [(20, 1)])      # frame 12 is the one shown at 15
    assert bp.ghost_frames(frames, 3, 3, 2) == ([], [(5, 1), (12, 2)])
    assert bp.ghost_frames(frames, 30, 0, 3) == ([], [])
    assert abs(bp.ghost_alpha(1, 3) - 0.4) < 1e-6
    assert abs(bp.ghost_alpha(2, 3) - 0.8 / 3) < 1e-6
    assert abs(bp.ghost_alpha(3, 3) - 0.4 / 3) < 1e-6


def test_frames_of_shown_layers():
    _annotation(hidden_frames=(7,))
    assert bp.frame_numbers(bpy.context.scene) == [5, 12, 20]


def test_operator_jumps():
    _annotation()
    sc = bpy.context.scene
    sc.frame_set(8)
    assert bpy.ops.allset.blue_pencil_frame(next=True) == {'FINISHED'}
    assert sc.frame_current == 12
    assert bpy.ops.allset.blue_pencil_frame(next=False) == {'FINISHED'}
    assert sc.frame_current == 5
    assert bpy.ops.allset.blue_pencil_frame(next=False) == {'FINISHED'}
    assert sc.frame_current == 20
    for a in list(bpy.data.annotations):
        bpy.data.annotations.remove(a)
    assert bpy.ops.allset.blue_pencil_frame(next=True) == {'CANCELLED'}


def test_alt_lt_gt_keys():
    items = [k for k in kit.maya_kc().keymaps["Frames"].keymap_items if k.idname == "allset.blue_pencil_frame"]
    got = {(k.type, k.shift, k.alt, k.ctrl, k.properties.next) for k in items}
    assert got == {('COMMA', True, True, False, False), ('GRLESS', False, True, False, False),
                   ('PERIOD', True, True, False, True), ('GRLESS', True, True, False, True)}, got


def test_ghost_settings_and_strokes():
    prefs = prefs_mod.get()
    assert (prefs.bp_ghost_previous, prefs.bp_ghost_previous_frames) == (True, 3)
    assert (prefs.bp_ghost_next, prefs.bp_ghost_next_frames) == (True, 3)
    _annotation()
    sc = bpy.context.scene
    sc.frame_set(12)
    strokes = bp.ghost_strokes(sc, False)
    assert len(strokes) == 2, strokes                    # frame 5 before, frame 20 after
    for pts, rgba, width, _front in strokes:
        assert abs(rgba[3] - 0.4) < 1e-6 and width == 3
        assert len(pts) == 2
    assert bp.ghost_strokes(sc, True) == []              # no view-space strokes
    try:
        prefs.bp_ghost_next = False
        assert len(bp.ghost_strokes(sc, False)) == 1
        prefs.bp_ghost_previous = False
        assert bp.ghost_strokes(sc, False) == []
    finally:
        prefs.bp_ghost_next = prefs.bp_ghost_previous = True
    # the kit draws the ghosts: the layers' own onion skin settings stay as they were
    lay = sc.annotation.layers[0]
    before = (lay.use_annotation_onion_skinning, lay.annotation_onion_before_range, lay.annotation_onion_after_range)
    bp.ghost_strokes(sc, False)
    assert before == (lay.use_annotation_onion_skinning, lay.annotation_onion_before_range,
                      lay.annotation_onion_after_range)


def test_time_slider_marks():
    view2d = SimpleNamespace(view_to_region=lambda x, y, clip=False: (x * 10.0, y))
    region = SimpleNamespace(width=400, view2d=view2d)
    tris = ts_mod.blue_pencil_marks(region, [5, 12], 4.0, 1.0)
    # frame 5's tick at x = 45: upright edge 2 px right of it, 8 px wide, 11 px tall, standing on y = 4
    assert tris[:3] == [(47.0, 4.0), (55.0, 4.0), (47.0, 15.0)], tris[:3]
    assert len(tris) == 6
    assert ts_mod.blue_pencil_marks(region, [100], 4.0, 1.0) == []    # off the slider
    scaled = ts_mod.blue_pencil_marks(region, [5], 0.0, 2.0)
    assert scaled == [(49.0, 0.0), (65.0, 0.0), (49.0, 22.0)], scaled


def test_tool_settings_tools():
    assert [t for _l, t in bp.TOOLS] == ["builtin.annotate", "builtin.annotate_line", "builtin.annotate_eraser"]
    assert set(t for _l, t in bp.TOOLS) <= bp.TOOL_IDS
