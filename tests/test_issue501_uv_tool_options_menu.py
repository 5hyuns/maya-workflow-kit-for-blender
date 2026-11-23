"""#501: Ctrl+Shift+RMB in the UV Editor opens the option marking menu of the UV Editor's active tool, like Maya
(Move / Rotate / Scale: Symmetry, Step Snap, Select and the tool's options; the select tools: Symmetry, Pick/Marquee,
Drag/Marquee, Soft Select). GUI: tests/gui/gui_issue501_uv_tool_options_menu.py."""

import types
from importlib import import_module

import bpy

import kit

marking = import_module(kit.MODULE + ".marking")
mm = import_module(kit.MODULE + ".marking.menus")
modal = import_module(kit.MODULE + ".marking.modal")
draw = import_module(kit.MODULE + ".marking.draw")
notices = import_module(kit.MODULE + ".ui.notices")
snap_align = import_module(kit.MODULE + ".operators.snap_align")


def _ring(sub):
    return {p: label for p, (label, _a) in sub.radial.items()}


def _list(sub):
    return [e[0] for e in sub.items if e != mm.DIVIDER]


class _Tools:
    def __init__(self, tid):
        self.tid = tid

    def from_space_image_mode(self, mode, create=False):
        assert mode == 'UV'
        return types.SimpleNamespace(idname=self.tid) if self.tid else None

    def from_space_view3d_mode(self, mode, create=False):
        raise AssertionError("the UV Editor reads its own tool")


def _ctx(tid, space_mode='UV', mode='EDIT_MESH'):
    return types.SimpleNamespace(mode=mode, scene=bpy.context.scene, active_object=None,
                                 workspace=types.SimpleNamespace(tools=_Tools(tid)),
                                 window_manager=types.SimpleNamespace(allset_uv_shell_mask=False),
                                 space_data=types.SimpleNamespace(type='IMAGE_EDITOR', mode=space_mode))


def test_menu_follows_the_uv_editor_tool():
    def pick(tid, **kw):
        found = marking.resolve("TOOL_OPTIONS", _ctx(tid, **kw))
        return found and found[1]
    assert pick("builtin.move") == marking.idname("UV_OPT_MOVE")
    assert pick("builtin.transform") == marking.idname("UV_OPT_MOVE")
    assert pick("builtin.rotate") == marking.idname("UV_OPT_ROTATE")
    assert pick("builtin.scale") == marking.idname("UV_OPT_SCALE")
    for tid in ("builtin.select", "builtin.select_box", "builtin.select_circle", "builtin.select_lasso"):
        assert pick(tid) == marking.idname("UV_OPT_SELECT"), tid
    assert not pick("builtin.cursor") and not pick("")
    assert not pick("builtin.move", space_mode='VIEW') and not pick("builtin.move", mode='OBJECT')
    km = kit.maya_kc().keymaps["UV Editor"]
    found = [(k.idname, k.properties.trigger) for k in km.keymap_items
             if k.active and k.type == 'RIGHTMOUSE' and k.value == 'PRESS' and k.ctrl and k.shift and not k.alt]
    assert found == [("allset.marking_menu", 'TOOL_OPTIONS')], found


def test_rings_and_lists():
    assert _ring(mm.UV_OPT_MOVE) == {"N": "Symmetry", "E": "Step Snap", "SE": "Keep Spacing", "S": "Select"}
    assert _ring(mm.UV_OPT_ROTATE) == {"N": "Symmetry", "E": "Step Snap", "S": "Select"}
    assert _ring(mm.UV_OPT_SCALE) == {"N": "Symmetry", "E": "Step Snap", "S": "Select",
                                      "W": "Prevent Negative Scale"}
    assert _ring(mm.UV_OPT_SELECT) == {"N": "Symmetry", "NE": "Drag/Marquee", "E": "Highlight Backfaces",
                                       "S": "Soft Select", "NW": "Pick/Marquee"}
    for menu, last in ((mm.UV_OPT_MOVE, "Move Options"), (mm.UV_OPT_ROTATE, "Rotate Options"),
                       (mm.UV_OPT_SCALE, "Scale Options"), (mm.UV_OPT_SELECT, "Select Options")):
        assert _list(menu) == ["Selection Constraints", "Transform Constraints", last], menu.name
        assert menu.items[-1][1] == "allset.uv_tool_settings", "the UV Editor sidebar's Tool tab"
    sel = mm.UV_OPT_MOVE.radial["S"][1]
    assert _ring(sel) == {"NE": "Drag/Marquee", "E": "Highlight Backfaces", "NW": "Pick/Marquee", "S": "Soft Select"}
    assert _list(sel) == ["Selection Constraints", "Transform Constraints", "Select Options"]
    soft = sel.radial["S"][1]
    assert _ring(soft) == {"N": "Object", "S": "Soft Select", "SW": "Volume", "W": "Surface", "NW": "Global",
                           "E": "Color Feedback"}
    assert _ring(mm.UV_OPT_MOVE.radial["N"][1]) == _ring(mm.OPT_MOVE.radial["N"][1]), "the same Symmetry menu"
    # the UV Editor's select tools, like the UV Toolkit's Pick/Marquee and Drag
    assert mm.UV_OPT_SELECT.radial["NW"][1] == ("tool", "builtin.select_box", {"space_type": 'IMAGE_EDITOR'})
    assert mm.UV_OPT_SELECT.radial["NE"][1] == ("tool", "builtin.select_circle", {"space_type": 'IMAGE_EDITOR'})


def test_greyed_entries_have_notices():
    for name in ("UV_OPT_MOVE", "UV_OPT_ROTATE", "UV_OPT_SCALE", "UV_OPT_SELECT"):
        greyed = [p for p, _l, a in mm.label_walk(mm.MENUS[name], name) if mm.is_greyed(a)]
        assert greyed and all(p in notices.MARKING for p in greyed), [p for p in greyed if p not in notices.MARKING]


def _uv_area():
    scr = bpy.context.window.screen
    a = next(a for a in scr.areas if a.type in ('VIEW_3D', 'IMAGE_EDITOR'))
    a.ui_type = 'UV'
    return a, next(r for r in a.regions if r.type == 'WINDOW')


def test_step_snap_is_the_uv_increment_snap():
    ts = bpy.context.scene.tool_settings
    ts.use_snap_uv = False
    ts.use_snap = False
    _label, action = mm.UV_OPT_MOVE.radial["E"]
    assert draw.checked(action) is False
    a, r = _uv_area()
    with bpy.context.temp_override(area=a, region=r):
        assert modal.run_action(bpy.context, action) == {'FINISHED'}
    assert ts.use_snap_uv and 'INCREMENT' in ts.snap_uv_element and ts.use_snap_translate
    assert draw.checked(action) is True
    assert not ts.use_snap, "the 3D View's snapping stays as it was"
    with bpy.context.temp_override(area=a, region=r):
        assert modal.run_action(bpy.context, action) == {'FINISHED'}
    assert not ts.use_snap_uv and draw.checked(action) is False
    # with UV vertex snapping on, Step Snap Off keeps that
    ts.use_snap_uv = True
    ts.snap_uv_element = {'VERTEX', 'INCREMENT'}
    snap_align.set_uv_step_snap(ts, 'ROTATE', False)
    assert ts.use_snap_uv and set(ts.snap_uv_element) == {'VERTEX'}

