# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-style UI: Channel Box, Attribute Editor, Status Line, shelf, menus.

See research/blender/api_limits.md for what is P/W/C in Blender's Python UI.
"""

import bpy

classes = ()

register, unregister = bpy.utils.register_classes_factory(classes)
