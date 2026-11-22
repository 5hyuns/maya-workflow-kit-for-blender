"""#477: the Channel Box name field, the Status Line rename and the Outliner rename make a name of what was typed,
like Maya: leading digits and symbols dropped, other characters a name can't hold -> "_", accents dropped, a
namespace prefix dropped, a trailing "#" = the next free number; only text with nothing usable is refused. A name
ending in a number with leading zeros gives the shape that number without them (Cube_01 -> Cube_Shape1)."""

from importlib import import_module

import bpy

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")
il = import_module(kit.MODULE + ".ui.input_line")

CASES = {
    "my cube": ("my_cube", "my_cubeShape"),
    "  lead": ("lead", "leadShape"),
    "x ": ("x", "xShape"),
    "_x": ("_x", "_xShape"),
    "a__b": ("a__b", "a__bShape"),
    "1box": ("box", "boxShape"),
    "123abc": ("abc", "abcShape"),
    "-x": ("x", "xShape"),
    "a-b": ("a_b", "a_bShape"),
    "x.y": ("x_y", "x_yShape"),
    "box|sub": ("box_sub", "box_subShape"),
    "box#": ("box1", "boxShape1"),
    "a#b#": ("a_b1", "a_bShape1"),
    "box##": ("box_1", "box_Shape1"),
    "élan": ("elan", "elanShape"),
    "naïve": ("naive", "naiveShape"),
    "box:sub": ("sub", "subShape"),
    "Cube_01": ("Cube_01", "Cube_Shape1"),
    "pSphere1_": ("pSphere1_", "pSphere1_Shape"),
}
REFUSED = ("", "1", "#", "큐브")


def _one_cube():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    ob.name, ob.data.name = "pCube1", "pCubeShape1"
    return ob


def test_channel_box_name_field_cleans_up():
    bad = []
    for text, (name, shape) in CASES.items():
        ob = _one_cube()
        got = cb.rename_lead(ob, text)
        if (got, ob.name, ob.data.name) != (name, name, shape):
            bad.append((text, got, ob.name, ob.data.name))
    assert not bad, bad


def test_nothing_usable_is_refused():
    for text in REFUSED:
        ob = _one_cube()
        assert cb.rename_lead(ob, text) is None and ob.name == "pCube1", text


def test_hash_takes_the_next_number():
    ob = _one_cube()
    bpy.ops.mesh.primitive_cube_add()
    bpy.context.active_object.name = "box1"
    assert cb.rename_lead(ob, "box#") == "box2"


def test_status_line_rename_hash_numbers_each():
    ob = _one_cube()
    bpy.ops.mesh.primitive_cube_add()
    other = bpy.context.active_object
    ob.select_set(True)
    other.select_set(True)
    bpy.context.view_layer.objects.active = ob
    assert il.rename(bpy.context, "crate#") == ["crate1", "crate2"]
    assert ob.name == "crate1" and other.name == "crate2"


def test_status_line_rename_cleans_up():
    ob = _one_cube()
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    assert il.rename(bpy.context, "9 big-box") == ["big_box"]
    assert ob.data.name == "big_boxShape"
