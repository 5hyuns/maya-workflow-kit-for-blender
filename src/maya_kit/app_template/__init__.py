# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya layout app template: install / remove / open.

An app template is not an extension type, so the template ("MayaKit": the
generated startup.blend + a thin __init__.py) ships inside this package and
is copied to the user's ``scripts/startup/bl_app_templates_user/``
(docs/user_decisions.md #3; research/blender/ui_architecture.md §2, §12).
Layout: docs/steps/step_5.md; generator: tools/make_startup.py.
"""

import importlib
import os
import shutil

import bpy

TEMPLATE_ID = "MayaKit"
SOURCE_DIR = os.path.join(os.path.dirname(__file__), TEMPLATE_ID)
MARKER = ".maya_kit"   # only folders carrying this file are ever removed


def user_templates_dir(create=False):
    return bpy.utils.user_resource(
        'SCRIPTS', path=os.path.join("startup", "bl_app_templates_user"), create=create)


def installed_dir():
    return os.path.join(user_templates_dir(), TEMPLATE_ID)


def is_installed():
    return os.path.isfile(os.path.join(installed_dir(), MARKER))


def install():
    dst = os.path.join(user_templates_dir(create=True), TEMPLATE_ID)
    if os.path.isdir(dst) and not os.path.isfile(os.path.join(dst, MARKER)):
        raise RuntimeError(f"{dst} exists and was not installed by Maya Kit")
    shutil.copytree(SOURCE_DIR, dst, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.blend1"))
    with open(os.path.join(dst, MARKER), "w", encoding="utf-8") as fh:
        fh.write("Installed by the Maya Kit extension. Removed by its 'Remove Maya Layout' button.\n")
    # A clean config has no scripts/startup at launch, so it is not on sys.path and the
    # template's __init__ (enables the add-on, re-activates the Maya keymap) would not
    # import until a restart (found by tools/release_check.py, docs/steps/step_13.md).
    bpy.utils.refresh_script_paths()
    importlib.invalidate_caches()
    return dst


def remove():
    dst = installed_dir()
    if not os.path.isdir(dst):
        return False
    if not os.path.isfile(os.path.join(dst, MARKER)):
        raise RuntimeError(f"{dst} was not installed by Maya Kit; not removing it")
    shutil.rmtree(dst)
    return True


class MAYAKIT_OT_layout_install(bpy.types.Operator):
    """Install the Maya layout as an application template (File > New > MayaKit)"""
    bl_idname = "maya_kit.layout_install"
    bl_label = "Install Maya Layout"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        try:
            dst = install()
        except (OSError, RuntimeError) as ex:
            self.report({'ERROR'}, str(ex))
            return {'CANCELLED'}
        self.report({'INFO'}, f"Maya layout installed: {dst}")
        return {'FINISHED'}


class MAYAKIT_OT_layout_remove(bpy.types.Operator):
    """Remove the Maya layout application template"""
    bl_idname = "maya_kit.layout_remove"
    bl_label = "Remove Maya Layout"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        try:
            removed = remove()
        except (OSError, RuntimeError) as ex:
            self.report({'ERROR'}, str(ex))
            return {'CANCELLED'}
        self.report({'INFO'}, "Maya layout removed" if removed else "Maya layout was not installed")
        return {'FINISHED'}


class MAYAKIT_OT_layout_open(bpy.types.Operator):
    """Start a new file with the Maya layout (unsaved changes are lost)"""
    bl_idname = "maya_kit.layout_open"
    bl_label = "New File with Maya Layout"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return is_installed()

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        # From a timer: switching templates re-registers the add-on, this operator included
        # (docs/steps/step_42.md).
        from .. import first_start
        first_start.open_layout_later()
        return {'FINISHED'}


classes = (MAYAKIT_OT_layout_install, MAYAKIT_OT_layout_remove, MAYAKIT_OT_layout_open)

register, unregister = bpy.utils.register_classes_factory(classes)
