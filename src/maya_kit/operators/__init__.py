# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-behaviour operators (group, pick-walk, hold/tap snap, pivot, freeze, parent,
duplicate, delete history, create, visibility, ...).

Operator ids use the ``maya_kit.`` prefix. Each module lists its classes in
``classes``; they are registered in that order.
"""

import bpy

from . import (bookmarks, component, create, cut_sew, display, driven_key, duplicate, extrude, file_io, freeze, option_windows, fx, global_keys4, graph_keys, group, history, hold, joints, pivot_menu, key_batch, key_batch3, key_insert, manip, marquee,
               material, menu_extras, menu_items, mesh_maya, mesh_tools, outliner_drag, parenting, pickwalk, pivot, playblast, preselect, project, rig_tools, select_priority, sets, shading_maps, skin, snap_align, symmetry, taphold,
               time_keys, tool_keys, units, uv_tools, view, view_keys3, visibility)

classes = (*display.classes, *group.classes, *hold.classes, *taphold.classes,
           *pickwalk.classes, *view.classes, *freeze.classes, *parenting.classes,
           *duplicate.classes, *history.classes, *create.classes, *visibility.classes,
           *component.classes, *manip.classes, *material.classes,
           *marquee.classes, *preselect.classes, *select_priority.classes, *menu_extras.classes,
           *tool_keys.classes, *symmetry.classes, *pivot.classes, *snap_align.classes, *time_keys.classes,
           *joints.classes, *skin.classes, *driven_key.classes, *rig_tools.classes, *mesh_maya.classes,
           *mesh_tools.classes, *extrude.classes, *uv_tools.classes, *shading_maps.classes, *fx.classes, *project.classes, *graph_keys.classes, *playblast.classes, *key_batch.classes, *cut_sew.classes,
           *outliner_drag.classes, *key_insert.classes, *view_keys3.classes, *global_keys4.classes,
           *pivot_menu.classes, *sets.classes, *menu_items.classes, *file_io.classes, *option_windows.classes,
           *key_batch3.classes, *bookmarks.classes)

_register_classes, _unregister_classes = bpy.utils.register_classes_factory(classes)


def register():
    _register_classes()
    snap_align.register_props()
    driven_key.register_props()
    mesh_tools.register_props()
    extrude.register_handlers()
    uv_tools.register_props()
    fx.register_props()
    taphold.register_bindings()
    graph_keys.register_bindings()
    pivot_menu.register_props()
    sets.register_props()
    view.register_timer()
    units.register_handler()
    tool_keys.register_timer()
    symmetry.register_handler()
    pivot.register_handler()
    project.register_handlers()
    preselect.register_handlers()
    cut_sew.register_handlers()
    outliner_drag.register_handlers()
    material.register_handlers()


def unregister():
    material.unregister_handlers()
    outliner_drag.unregister_handlers()
    cut_sew.unregister_handlers()
    project.unregister_handlers()
    pivot.unregister_handler()
    symmetry.unregister_handler()
    tool_keys.unregister_timer()
    marquee.restore_all()
    preselect.clear()
    units.unregister_handler()
    duplicate.PAIRS.clear()
    view.unregister_timer()
    hold.unregister_cleanup()
    graph_keys.unregister_bindings()
    sets.unregister_props()
    pivot_menu.unregister_props()
    taphold.unregister_bindings()
    fx.unregister_props()
    uv_tools.unregister_props()
    extrude.unregister_handlers()
    mesh_tools.clear()
    mesh_tools.unregister_props()
    driven_key.unregister_props()
    snap_align.unregister_props()
    _unregister_classes()
