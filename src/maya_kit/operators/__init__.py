# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-behaviour operators (group, pick-walk, hold/tap snap, pivot, ...).

Operator ids use the ``maya_kit.`` prefix. Classes are listed in ``classes``.
"""

import bpy

classes = ()

register, unregister = bpy.utils.register_classes_factory(classes)
