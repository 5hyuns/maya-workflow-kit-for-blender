"""Maya surface shaders that are a node set-up in Blender (Ramp Shader, Layered Shader, Surface Shader, Use
Background) are greyed wherever Maya offers them (Hypershade Create, Favorites, the shelf): the tooltip and the Help
Line say how Blender builds them in the Shader Editor, and the command line's shadingNode gives the same sentence."""

from importlib import import_module

import bpy

import kit

menu_map = import_module(kit.MODULE + ".ui.menu_map")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
notices = import_module(kit.MODULE + ".ui.notices")
shelf = import_module(kit.MODULE + ".ui.shelf")
hs = import_module(kit.MODULE + ".ui.hypershade")
cmds = import_module(kit.MODULE + ".command_line.cmds_shim")

HS = "Hypershade/Create/Materials/"
SETUPS = {"Ramp Shader": ("rampShader", "Ramp Material", ("Layer Weight", "Color Ramp", "Base Color")),
          "Layered Shader": ("layeredShader", "Layered Material", ("Mix Shader",)),
          "Surface Shader": ("surfaceShader", "Surface Material", ("Emission",)),
          "Use Background": ("useBackground", "Use Background", ("Holdout", "Shadow Catcher"))}


def test_hypershade_items_greyed_with_the_blender_way():
    paths = {p for p, _it in menu_sets.iter_items()}
    for label, (_t, _b, words) in SETUPS.items():
        path = HS + label
        assert path in paths, path
        assert menu_map.spec(path) is None, f"{path} is greyed"
        sub, line = notices.greyed_notice(path)
        assert sub.startswith("Shader Editor"), (path, sub)
        assert all(w in line for w in words), (path, line)
        tip = notices.tooltip(path, False)
        assert "(greyed)" in tip and line in tip, tip
    # the Create pane lists them in their place, after New Material
    labels = [label for label, _p in hs.create_items('SURFACE')]
    assert labels[0] == "New Material" and all(lab in labels for lab in SETUPS), labels


def test_shelf_buttons_greyed_with_the_same_notice():
    buttons = {label: action for _i, label, action, _icon in shelf.all_buttons("Rendering")}
    for label, (_t, button, _w) in SETUPS.items():
        assert buttons[button] is None, f"{button} is greyed"
        assert shelf.button_notice("Rendering", button) == notices.NOTICES[HS + label], button
    assert buttons["Standard Surface Material"] is not None
    for kind in ("Lambert", "Blinn", "Phong", "Phong E", "Anisotropic"):
        assert buttons[f"{kind} Material"] is None
        assert "Standard Surface Material" in shelf.button_notice("Rendering", f"{kind} Material")[1]


def test_shading_node_gives_the_notice():
    before = len(bpy.data.materials)
    for label, (maya_type, _b, _w) in SETUPS.items():
        try:
            cmds.shadingNode(maya_type, asShader=True)
        except RuntimeError as ex:
            assert notices.NOTICES[HS + label][1] in str(ex), ex
        else:
            raise AssertionError(f"shadingNode {maya_type} makes nothing")
    assert len(bpy.data.materials) == before
