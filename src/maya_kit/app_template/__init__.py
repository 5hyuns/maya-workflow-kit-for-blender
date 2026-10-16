# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya layout app template.

An app template is not an extension type, so the template files will live in
this folder and an install/remove button in preferences will copy them to the
user's ``scripts/startup/bl_app_templates_user/`` (;
,).
"""

import bpy

classes = ()

register, unregister = bpy.utils.register_classes_factory(classes)
