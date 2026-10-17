# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-behaviour operators (group, pick-walk, hold/tap snap, pivot, freeze, parent,
duplicate, delete history, create, visibility, ...).

Operator ids use the ``maya_kit.`` prefix. Each module lists its classes in
``classes``; they are registered in that order.
"""

import bpy

from . import (component, create, display, driven_key, duplicate, freeze, group, history, hold, joints, manip, marquee,
               material, menu_extras, mesh_maya, parenting, pickwalk, pivot, preselect, rig_tools, skin, snap_align, symmetry, taphold,
               time_keys, tool_keys, units, view, visibility)

classes = (*display.classes, *group.classes, *hold.classes, *taphold.classes,
           *pickwalk.classes, *view.classes, *freeze.classes, *parenting.classes,
           *duplicate.classes, *history.classes, *create.classes, *visibility.classes,
           *component.classes, *manip.classes, *material.classes,
           *marquee.classes, *preselect.classes, *menu_extras.classes,
           *tool_keys.classes, *symmetry.classes, *pivot.classes, *snap_align.classes, *time_keys.classes,
           *joints.classes, *skin.classes, *driven_key.classes, *rig_tools.classes, *mesh_maya.classes)

_register_classes, _unregister_classes = bpy.utils.register_classes_factory(classes)


def register():
    _register_classes()
    snap_align.register_props()
    driven_key.register_props()
    taphold.register_bindings()
    view.register_timer()
    units.register_handler()
    tool_keys.register_timer()
    symmetry.register_handler()
    pivot.register_handler()


def unregister():
    pivot.unregister_handler()
    symmetry.unregister_handler()
    tool_keys.unregister_timer()
    marquee.restore_all()
    preselect.clear()
    units.unregister_handler()
    duplicate.PAIRS.clear()
    view.unregister_timer()
    hold.unregister_cleanup()
    taphold.unregister_bindings()
    driven_key.unregister_props()
    snap_align.unregister_props()
    _unregister_classes()
