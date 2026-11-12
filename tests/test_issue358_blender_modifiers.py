"""#358: the Attribute Editor's bottom has Blender Modifiers... under Maya's Select / Load Attributes / Copy Tab: it
opens the object's whole Blender modifier stack (Add Modifier included) in a floating window. The modifiers stay
history nodes (Channel Box INPUTS, Attribute Editor tabs)."""

from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

ae = import_module(kit.MODULE + ".ui.attribute_editor")
rmb = import_module(kit.MODULE + ".marking.rmb_nodes")


class Recorder:
    """A stand-in UILayout that records (kind, text) of what a draw function adds."""

    def __init__(self, log=None):
        self.log = [] if log is None else log

    def __getattr__(self, name):
        if name in ("row", "column", "split", "box"):
            return lambda *a, **k: Recorder(self.log)
        if name in ("menu", "operator", "prop", "label"):
            def add(*args, **kw):
                self.log.append((name, kw.get("text", args[0] if args else ""), args[0] if args else ""))
                return SimpleNamespace()
            return add
        return lambda *a, **k: None


def _only(ob):
    for o in bpy.context.view_layer.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob


def _fresh():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)


def test_button_under_mayas_bottom_row():
    rec = Recorder()
    ae.draw_bottom(rec, None)
    ops = [(t, idname) for k, t, idname in rec.log if k == "operator"]
    assert ops == [("Select", "allset.ae_select"), ("Load Attributes", "allset.ae_load"),
                   ("Copy Tab", "allset.ae_copy_tab"), ("Blender Modifiers...", "allset.ae_blender_modifiers")], ops


def test_owner_and_poll():
    _fresh()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.modifiers.new("Bevel", 'BEVEL')
    assert ae.modifier_owner(cube) is cube
    bpy.ops.object.empty_add()
    empty = bpy.context.active_object
    assert ae.modifier_owner(empty) is None
    _only(empty)
    assert not bpy.ops.allset.ae_blender_modifiers.poll()
    # still a history node in INPUTS and an AE tab, like before
    names = [n for n, *_r in rmb.input_nodes(cube)]
    assert names == ["polyBevel1"], names
    assert any(t[0] == "M:Bevel" for t in ae.tabs(cube))


def test_target_is_the_modifier_tab_of_the_object():
    _fresh()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    assert ae.copy_tab_target(cube, "M:Bevel")[0] == 'MODIFIER'
