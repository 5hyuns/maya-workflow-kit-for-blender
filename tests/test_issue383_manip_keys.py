"""#383 / #391 / #394: Ctrl on manipulator handles, Ctrl+Shift+drag slide on a Move handle, Ctrl+middle-drag along
normals with the Move tool.
GUI: tests/gui/gui_issue383_ctrl_handles.py, gui_issue383_extrude_ctrl.py, gui_issue391_394_slide_normal.py."""

import types
from importlib import import_module

import bpy

import kit

patches = import_module(kit.MODULE + ".keymap.maya_patches")
extrude_manip = import_module(kit.MODULE + ".ui.extrude_manipulator")
preferences = import_module(kit.MODULE + ".preferences")


def test_ctrl_snap_preference_off_by_default():
    prop = preferences.get(bpy.context).bl_rna.properties.get("manip_ctrl_snap")
    assert prop is not None, "manip_ctrl_snap preference"
    assert prop.default is False


def test_extrude_ctrl_handles():
    # Ctrl on an arrow = the plane of the other two axes, on a scale cube = the other two cubes
    assert extrude_manip.CTRL_OTHERS["TX"] == "PYZ"
    assert extrude_manip.CTRL_OTHERS["TY"] == "PXZ"
    assert extrude_manip.CTRL_OTHERS["TZ"] == "PXY"
    assert extrude_manip.CTRL_OTHERS["SX"] == ("SY", "SZ")
    assert extrude_manip.CTRL_OTHERS["SY"] == ("SX", "SZ")
    assert extrude_manip.CTRL_OTHERS["SZ"] == ("SX", "SY")
    for plane in ("PYZ", "PXZ", "PXY"):
        assert plane in extrude_manip.HANDLES


def test_slide_key_on_move_handles():
    kc = kit.maya_kc()
    for km in patches.GIZMO_KEYMAPS:
        items = [k for k in kc.keymaps[km].keymap_items if k.active and k.type == 'LEFTMOUSE' and k.value == 'PRESS'
                 and k.ctrl and k.shift and not k.alt]
        assert items and items[0].idname == "allset.manip_slide", (km, [k.idname for k in items])
    assert "allset.manip_slide" in patches.PASS_THROUGH_FIRST


def test_ctrl_mmb_moves_along_normals():
    kc = kit.maya_kc()
    km = kc.keymaps["3D View Tool: Move"]
    found = [k for k in km.keymap_items if k.active and k.type == 'MIDDLEMOUSE' and k.value == 'PRESS'
             and k.ctrl and not k.shift and not k.alt]
    assert found and found[0].idname == "allset.component_slide", [k.idname for k in found]
    assert found[0].properties.mode == 'NORMAL'
    # Ctrl+Shift+MMB stays the edge slide (#262)
    cs = [k for k in km.keymap_items if k.active and k.type == 'MIDDLEMOUSE' and k.ctrl and k.shift]
    assert cs and cs[0].idname == "allset.component_slide" and cs[0].properties.mode == 'EDGE'


class _Layout:
    """Records the property names drawn."""

    def __init__(self, log):
        self.log = log

    def prop(self, _data, name, **_kw):
        self.log.append(name)

    def operator(self, *_a, **_kw):
        return types.SimpleNamespace()

    def __getattr__(self, _name):
        return lambda *_a, **_kw: _Layout(self.log)


def test_ctrl_snap_preference_where_maya_users_look():
    """The preference shows in the Move Tool Settings and the Maya Preferences window (Manipulators); the Move
    tool's Reset Tool puts it back to off."""
    ts_ui = import_module(kit.MODULE + ".ui.tool_settings")
    prefs_data = import_module(kit.MODULE + ".ui.maya_prefs_data")
    log = []
    ts_ui.draw_settings(_Layout(log), bpy.context, 'TRANSLATE')
    assert "manip_ctrl_snap" in log, log
    log.clear()
    ts_ui.draw_settings(_Layout(log), bpy.context, 'RESIZE')
    assert "manip_ctrl_snap" not in log
    assert any(key == "MANIPULATORS" and row[:2] == ("pref", "manip_ctrl_snap")
               for key, _section, row in prefs_data.rows())
    p = preferences.get(bpy.context)
    p.manip_ctrl_snap = True
    ts_ui.reset_maya_options(bpy.context, 'TRANSLATE')
    assert p.manip_ctrl_snap is False
