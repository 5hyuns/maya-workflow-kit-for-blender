"""#516: the UV brush marking menu's east item names the brush tool it goes back to ("Last Tool: <tool>"), like Maya.

Only a change of brush tool counts (other tools in between keep it); before a second brush it reads "Last Tool:"."""

from importlib import import_module

import bpy

import kit

brush = import_module(kit.MODULE + ".operators.uv_brush")
menus = import_module(kit.MODULE + ".marking.menus")
marking = import_module(kit.MODULE + ".marking")


def _use(mode):
    brush.note_mode(mode)


def test_last_tool_follows_brush_changes():
    brush._modes.update(current=None, last=None)
    _use("PIN")
    assert brush._modes["last"] is None
    _use("PIN")                       # the same brush again: no change
    assert brush._modes["last"] is None
    _use("CUT")
    assert brush._modes == {"current": "CUT", "last": "PIN"}, brush._modes
    _use(None)                        # a non-brush tool in between keeps both
    _use("CUT")
    assert brush._modes["last"] == "PIN"
    _use("SMEAR")
    assert brush._modes == {"current": "SMEAR", "last": "CUT"}, brush._modes


def test_label_names_the_tool():
    brush._modes.update(current=None, last=None)
    assert brush._modes["last"] is None
    # no brush tool is active in the test window: last_mode keeps the noted ones
    _use("UNFOLD")
    assert brush.last_tool_label(bpy.context) == "Last Tool:", brush.last_tool_label(bpy.context)
    _use("PIN")
    assert brush.last_tool_label(bpy.context) == "Last Tool: Unfold"
    _use("OPTIMIZE")
    assert brush.last_tool_label(bpy.context) == "Last Tool: Pin"


def test_marking_menu_shows_the_live_label():
    brush._modes.update(current="SEW", last="CUT")
    m = menus.MENUS["UV_BRUSH"]
    assert m.radial["E"] == ("Last Tool", menus.UV_BRUSH_LAST), "the definition keeps its plain label"
    shown = menus.relabel(m, marking.live_label)
    assert shown is not m and shown.radial["E"] == ("Last Tool: Cut", menus.UV_BRUSH_LAST), shown.radial["E"]
    assert shown.radial["N"] == m.radial["N"] and shown.radial["W"] == m.radial["W"]
    other = menus.MENUS["UV_EDITOR_RMB"]
    assert menus.relabel(other, marking.live_label) is other, "menus without live labels stay the same object"


def test_last_tool_operator_switches_back():
    brush._modes.update(current="SEW", last="PIN")
    assert brush.last_mode(bpy.context) == "PIN"
