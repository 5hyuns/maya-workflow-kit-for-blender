"""UV Editor: B is the soft select key like in the 3D View (#571): tap toggles the one soft select state, hold +
LMB / MMB drag sets the radius; the header shows the radius in UV space."""

from importlib import import_module

import bpy

import kit

taphold = import_module(kit.MODULE + ".operators.taphold")
soft = import_module(kit.MODULE + ".operators.soft_select")


def test_b_in_the_uv_editor_is_the_kit_key():
    km = kit.maya_kc().keymaps["UV Editor"]
    b = [k for k in km.keymap_items if k.type == 'B' and k.value == 'PRESS' and not (k.ctrl or k.shift or k.alt)
         and k.active]
    assert [k.idname for k in b] == ["allset.tap_hold"], [(k.idname, k.properties.items()) for k in b]
    assert b[0].properties.binding == "soft_select"


class _Area:
    type = 'IMAGE_EDITOR'

    def __init__(self):
        self.header = "unset"

    def header_text_set(self, text):
        self.header = text

    def tag_redraw(self):
        pass


class _Ctx:
    def __init__(self, area):
        self.scene = bpy.context.scene
        self.area = area
        self.region = None
        self.mode = 'EDIT_MESH'


class _Ev:
    def __init__(self, x):
        self.mouse_x, self.mouse_y = x, 0
        self.mouse_region_x, self.mouse_region_y = x, 0


def test_b_drag_in_the_uv_editor_sets_the_radius_in_uv_space():
    soft.set_on(False)
    ts = bpy.context.scene.tool_settings
    ts.proportional_size = 0.1
    area = _Area()
    ctx = _Ctx(area)
    b = taphold.get_binding("soft_select")
    assert b.click(ctx, _Ev(500)) == 'DRAG'
    assert soft.is_on() and ts.use_proportional_edit
    b.drag(ctx, _Ev(600), (500, 0))
    assert abs(ts.proportional_size - 0.2) < 1e-6
    assert area.header == "Falloff Radius: 0.200", area.header
    b.drag_end(ctx)
    assert area.header is None
    b.tap(ctx)                      # a tap toggles the same state off
    assert not soft.is_on() and not ts.use_proportional_edit
