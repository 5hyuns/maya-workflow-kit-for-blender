"""#330: the selection wire (lead green, other selected white) is drawn in Rendered shading too. The Maya layout
keeps Blender's own outline off, so a selection in a lit view (EEVEE / Cycles) had no highlight at all. The rule is
Blender's own for its outline: overlays on, in every shading mode; overlays off (the IPR picture) draws nothing."""

from importlib import import_module

import bpy

import kit

sw = import_module(kit.MODULE + ".ui.selection_wire")


def _view3d():
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                return area.spaces.active
    raise AssertionError("no 3D View space in the factory screens")


def test_every_shading_mode_draws_the_wire():
    space = _view3d()
    old = space.shading.type, space.overlay.show_overlays
    try:
        space.overlay.show_overlays = True
        for mode in ('WIREFRAME', 'SOLID', 'MATERIAL', 'RENDERED'):
            space.shading.type = mode
            assert sw.view_draws(space), mode
    finally:
        space.shading.type, space.overlay.show_overlays = old


def test_overlays_off_draws_nothing():
    """The IPR window's view: Rendered shading with overlays off = only the picture."""
    space = _view3d()
    old = space.shading.type, space.overlay.show_overlays
    try:
        space.shading.type = 'RENDERED'
        space.overlay.show_overlays = False
        assert not sw.view_draws(space)
        space.overlay.show_overlays = True
        assert sw.view_draws(space)
    finally:
        space.shading.type, space.overlay.show_overlays = old


def test_ipr_view_setup_turns_overlays_off():
    """ui/ipr_window.setup_view: the IPR picture is Rendered shading without overlays, so no wire is drawn over it."""
    ipr = import_module(kit.MODULE + ".ui.ipr_window")
    space = _view3d()
    old = (space.shading.type, space.overlay.show_overlays, space.show_gizmo,
           space.show_region_toolbar, space.show_region_ui, space.show_region_tool_header)
    try:
        space.overlay.show_overlays = True
        ipr.setup_view(space)
        assert space.shading.type == 'RENDERED' and not space.overlay.show_overlays
        assert not sw.view_draws(space)
    finally:
        (space.shading.type, space.overlay.show_overlays, space.show_gizmo,
         space.show_region_toolbar, space.show_region_ui, space.show_region_tool_header) = old
