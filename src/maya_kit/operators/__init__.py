# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-behaviour operators (group, pick-walk, hold/tap snap, pivot, ...).

Operator ids use the ``maya_kit.`` prefix. Each module lists its classes in
``classes``; they are registered in that order.
"""

import bpy

from . import display, group

classes = (*display.classes, *group.classes)

register, unregister = bpy.utils.register_classes_factory(classes)
