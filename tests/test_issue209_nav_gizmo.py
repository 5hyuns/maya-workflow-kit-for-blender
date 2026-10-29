"""Issue #209: add-on preference "Viewport Navigation" = Maya ViewCube (default) / Blender navigation gizmo.

With the Blender gizmo the kit's ViewCube is not drawn and Blender's navigation gizmo shows in the views where the
kit hid it (Maya views: ``show_gizmo_navigate`` off). Switching back, leaving Maya mode, disabling and saving a file
give those views their navigation flag back exactly; views the kit did not hide are never touched."""

import os
from importlib import import_module

import bpy

import kit


def _vf():
    return import_module(kit.MODULE + ".ui.view_furniture")


def _switch():
    return import_module(kit.MODULE + ".switch")


def _prefs():
    return bpy.context.preferences.addons[kit.MODULE].preferences


def _views():
    return [sp for sc in bpy.data.screens for a in sc.areas for sp in a.spaces if sp.type == 'VIEW_3D']


def _setup():
    """First 3D View = a Maya view (navigation gizmo off), the others stay Blender views (on)."""
    views = _views()
    assert len(views) >= 2, len(views)
    for sp in views:
        sp.show_gizmo_navigate = True
        sp.overlay.show_overlays = True
    views[0].show_gizmo_navigate = False
    return views[0], views[1:]


def _reset():
    p = _prefs()
    p.view_navigation = 'VIEWCUBE'
    p.maya_viewcube = True


def test_default_is_maya_viewcube():
    p = _prefs()
    assert p.view_navigation == 'VIEWCUBE'
    items = {i.identifier for i in p.bl_rna.properties["view_navigation"].enum_items}
    assert items == {'VIEWCUBE', 'BLENDER'}, items
    assert _vf().cube_wanted(p)


def test_blender_gizmo_shows_in_maya_views_only_and_comes_back():
    maya, others = _setup()
    vf = _vf()
    try:
        assert vf.maya_view(maya) and not any(vf.maya_view(sp) for sp in others)
        _prefs().view_navigation = 'BLENDER'
        assert maya.show_gizmo_navigate, "Blender navigation gizmo not shown in the Maya view"
        assert all(sp.show_gizmo_navigate for sp in others)
        assert not vf.cube_wanted(_prefs())
        # still a Maya view: camera name / view axis keep drawing there, not in the user's views
        assert vf.maya_view(maya) and not any(vf.maya_view(sp) for sp in others)
        _prefs().view_navigation = 'VIEWCUBE'
        assert not maya.show_gizmo_navigate, "navigation flag not given back"
        assert all(sp.show_gizmo_navigate for sp in others), "a user view was changed"
        assert vf.cube_wanted(_prefs()) and vf.maya_view(maya)
    finally:
        _reset()


def test_hud_viewcube_off_hides_the_blender_gizmo_too():
    maya, _others = _setup()
    try:
        _prefs().view_navigation = 'BLENDER'
        assert maya.show_gizmo_navigate
        _prefs().maya_viewcube = False       # Display > Heads Up Display > ViewCube: no navigation widget at all
        assert not maya.show_gizmo_navigate
        assert not _vf().cube_wanted(_prefs())
        _prefs().maya_viewcube = True
        assert maya.show_gizmo_navigate
    finally:
        _reset()
    assert not maya.show_gizmo_navigate


def test_maya_mode_off_restores_and_on_applies_again():
    maya, others = _setup()
    try:
        _prefs().view_navigation = 'BLENDER'
        assert maya.show_gizmo_navigate
        _switch().set_mode(False, layout=False)
        assert not maya.show_gizmo_navigate, "Maya mode off left Blender's gizmo on in the Maya view"
        assert all(sp.show_gizmo_navigate for sp in others)
        kit.maya_mode_on()
        assert maya.show_gizmo_navigate, "Maya mode on did not apply the preference"
    finally:
        _reset()
    assert not maya.show_gizmo_navigate


def test_disable_restores():
    maya, _others = _setup()
    _prefs().view_navigation = 'BLENDER'
    assert maya.show_gizmo_navigate
    kit.disable()
    try:
        assert not maya.show_gizmo_navigate, "disable left Blender's gizmo on in the Maya view"
    finally:
        kit.enable()
        _reset()


def test_saved_file_keeps_the_maya_flag():
    maya, _others = _setup()
    path = os.path.join(bpy.app.tempdir, "issue209_nav.blend")
    try:
        _prefs().view_navigation = 'BLENDER'
        bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
        assert maya.show_gizmo_navigate, "save turned the gizmo off in the open session"
        bpy.ops.wm.open_mainfile(filepath=path)
        # the file holds the Maya view (flag off); loading applies the preference again
        views = _views()
        assert any(sp.show_gizmo_navigate for sp in views)
        _prefs().view_navigation = 'VIEWCUBE'
        assert any(not sp.show_gizmo_navigate for sp in _views()), "the saved Maya view lost its flag"
    finally:
        _reset()
        bpy.ops.wm.read_homefile()
        if os.path.exists(path):
            os.remove(path)


def test_preference_rows():
    data = import_module(kit.MODULE + ".ui.maya_prefs_data")
    rows = [r for page in data.PAGES for _sec, rs in page[4] for r in rs]
    assert ("pref", "view_navigation") in {r[:2] for r in rows}
