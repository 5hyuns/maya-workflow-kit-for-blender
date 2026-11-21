"""#436: an image plane's Attribute Editor tab (imagePlane) has Display Mode, Image Name and Alpha Gain. Alpha Gain
below 1 draws the image see-through (Blender: the image empty's Opacity = object colour alpha with alpha blending);
a wireframe colour set on the plane keeps its Alpha Gain."""

from importlib import import_module

import bpy

import kit

ae_nodes = import_module(kit.MODULE + ".ui.ae_nodes")
image_plane = import_module(kit.MODULE + ".operators.image_plane")
wire_color = import_module(kit.MODULE + ".operators.wire_color")


def _plane():
    ob = bpy.data.objects.new("imagePlane1", None)
    ob.empty_display_type = 'IMAGE'
    ob.data = bpy.data.images.new("reference", 8, 8)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _rows(ob):
    sections, layout_id = ae_nodes.sections_for(ob, "S")
    return layout_id, [(sec.name, row[2], row[3]) for sec in sections for row in sec.rows if row[0] == "prop"]


def test_image_plane_tab():
    ob = _plane()
    tab = next(t for t in ae_nodes.tabs(ob) if t[0] == "S")
    assert tab[2] == "imagePlane", tab
    layout_id, rows = _rows(ob)
    assert layout_id == "image_plane", layout_id
    assert ("Image Plane Attributes", "allset_alpha_gain", "Alpha Gain") in rows, rows
    assert ("Image Plane Attributes", "allset_image_plane_display", "Display Mode") in rows, rows
    assert ("Image Plane Attributes", "filepath", "Image Name") in rows, rows
    loc = bpy.data.objects.new("locator1", None)
    assert ae_nodes.node_type(loc) == "locator"       # a plain empty stays a locator


def test_alpha_gain():
    ob = _plane()
    assert abs(ob.allset_alpha_gain - 1.0) < 1e-6 and not ob.use_empty_image_alpha
    ob.allset_alpha_gain = 0.4
    assert abs(ob.color[3] - 0.4) < 1e-6 and ob.use_empty_image_alpha, (tuple(ob.color), ob.use_empty_image_alpha)
    assert abs(ob.allset_alpha_gain - 0.4) < 1e-6
    ob.allset_alpha_gain = 1.0
    assert not ob.use_empty_image_alpha and abs(ob.color[3] - 1.0) < 1e-6
    # Blender's own Opacity (checkbox + slider) shows up as the same Alpha Gain
    ob.use_empty_image_alpha = True
    ob.color[3] = 0.25
    assert abs(ob.allset_alpha_gain - 0.25) < 1e-6


def test_wire_colour_keeps_alpha_gain():
    ob = _plane()
    ob.allset_alpha_gain = 0.5
    ob.allset_override_enabled = True
    ob.allset_override_mode = 'RGB'
    ob.allset_override_color = (1.0, 0.0, 0.0)
    wire_color.apply(ob)
    assert abs(ob.color[3] - 0.5) < 1e-6 and ob.color[0] > 0.9, tuple(ob.color)
    ob.allset_override_enabled = False
    wire_color.apply(ob)
    assert abs(ob.color[3] - 0.5) < 1e-6, tuple(ob.color)


def test_display_mode():
    ob = _plane()
    assert ob.allset_image_plane_display == 'RGBA'
    ob.allset_image_plane_display = 'NONE'
    assert ob.get(image_plane.NONE_MARK) and not image_plane.shown(ob)
    ob.allset_image_plane_display = 'RGBA'
    assert image_plane.shown(ob) and ob.allset_image_plane_display == 'RGBA'
