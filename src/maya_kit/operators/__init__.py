# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-behaviour operators (group, pick-walk, hold/tap snap, pivot, ...).

Operator ids use the ``maya_kit.`` prefix. Each module lists its classes in
``classes``; they are registered in that order.
"""

import bpy

from . import display, group, hold, pickwalk, taphold

classes = (*display.classes, *group.classes, *hold.classes, *taphold.classes,
           *pickwalk.classes)

_register_classes, _unregister_classes = bpy.utils.register_classes_factory(classes)


def register():
    _register_classes()
    taphold.register_bindings()


def unregister():
    hold.unregister_cleanup()
    taphold.unregister_bindings()
    _unregister_classes()
