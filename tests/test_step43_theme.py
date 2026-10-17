"""Step 43: Maya theme v2 colours (measured in Maya 2022, research/maya/colors.json)."""

from importlib import import_module

import bpy

import kit

theme = import_module(kit.MODULE + ".theme")
preferences = import_module(kit.MODULE + ".preferences")


def _hex(c):
    return "#%02x%02x%02x" % tuple(round(v * 255) for v in tuple(c)[:3])


def test_maya_theme_v2_values():
    preferences.get().maya_theme = True
    t = bpy.context.preferences.themes[0]
    v, ui = t.view_3d, t.user_interface
    expect = {
        "flat background": (v.space.gradients.background_type, 'SINGLE_COLOR'),
        "background": (_hex(v.space.gradients.high_gradient), "#5c5c5c"),
        "grid": (_hex(v.grid), "#404040"),
        "lead (active)": (_hex(v.object_active), "#43ffa3"),
        "other selected": (_hex(v.object_selected), "#ffffff"),
        "component wire": (_hex(v.wire_edit), "#64dcff"),
        "vertex": (_hex(v.vertex), "#c800c8"),
        "selected vertex (as drawn)": (_hex(v.vertex_select), "#fdff88"),
        "selected edge": (_hex(v.edge_select), "#e4ac79"),
        "selected face": (_hex(v.face_select), "#e4ac79"),
        "manipulator X": (_hex(ui.axis_x), "#e60000"),
        "manipulator Y": (_hex(ui.axis_y), "#00e600"),
        "manipulator Z (as drawn)": (_hex(ui.axis_z), "#0000ff"),
        "active handle": (_hex(ui.gizmo_primary), "#ffff00"),
        "Outliner list": (_hex(t.outliner.space.back), "#373737"),
        "Outliner lead row": (_hex(t.outliner.active), "#5285a6"),
        "Outliner selected name": (_hex(t.outliner.selected_object), "#ffffff"),
        "tab inactive": (_hex(ui.wcol_tab.inner), "#373737"),
        "tab active": (_hex(ui.wcol_tab.inner_sel), "#444444"),
        "current frame": (_hex(t.dopesheet_editor.frame_current), "#c7c7c7"),
    }
    bad = {k: got for k, (got, want) in expect.items() if got != want}
    assert not bad, bad
    # face fill alphas measured against Maya's stipple (docs/steps/step_43.md)
    assert abs(v.face_select[3] - 0.25) < 0.01 and abs(v.face_mode_select[3] - 0.28) < 0.01  # re-measured in step 44
    # opaque 3D View header and regions (Maya panel bars / dock)
    assert v.space.header[3] == 1.0 and v.space.button[3] == 1.0
    preferences.get().maya_theme = False
