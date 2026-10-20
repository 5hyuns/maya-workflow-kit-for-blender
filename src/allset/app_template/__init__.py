# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya layout app template: install / remove / open.

An app template is not an extension type, so the template ("Maya_Workflow_Kit", shown as "Maya Workflow Kit": the
generated startup.blend and splash images) ships inside this package and
is copied to the user's ``scripts/startup/bl_app_templates_user/``
(docs/user_decisions.md #3; research/blender/ui_architecture.md §2, §12).
Layout: docs/steps/step_5.md; generator: tools/make_startup.py.

Data only (step 115): no ``__init__.py``, so no code runs outside the extension
(Blender imports a template with ``ignore_not_found``, $S/modules/bl_app_template_utils.py:162).
The Maya keymap is re-activated after a template switch by the keymap module.
Only the user installs it (Make Blender Maya / Install Maya Layout); a user disable
or Remove of the extension deletes it again (``remove_on_disable``).
"""

import os
import shutil

import bpy

from ..names import PRODUCT

TEMPLATE_ID = "Maya_Workflow_Kit"   # Blender shows "Maya Workflow Kit" (underscores -> spaces)
SOURCE_DIR = os.path.join(os.path.dirname(__file__), TEMPLATE_ID)
MARKER = ".allset"   # only folders carrying this file are ever removed
# Earlier names of the template folder (decision 12): "MayaKit" before step 111, "Allset" before step 125. Installing
# or removing the layout also removes those old copies, again only when they carry the marker of their time.
LEGACY = (("MayaKit", ".maya_kit"), ("Allset", MARKER))


def user_templates_dir(create=False):
    return bpy.utils.user_resource(
        'SCRIPTS', path=os.path.join("startup", "bl_app_templates_user"), create=create)


def installed_dir():
    return os.path.join(user_templates_dir(), TEMPLATE_ID)


def is_installed():
    return os.path.isfile(os.path.join(installed_dir(), MARKER))


def remove_legacy():
    """Remove templates installed under the kit's earlier name (marker-checked); returns the removed folders."""
    out = []
    for name, marker in LEGACY:
        old = os.path.join(user_templates_dir(), name)
        if os.path.isfile(os.path.join(old, marker)):
            shutil.rmtree(old, ignore_errors=True)
            out.append(old)
    return out


def install():
    remove_legacy()
    dst = os.path.join(user_templates_dir(create=True), TEMPLATE_ID)
    if os.path.isdir(dst) and not os.path.isfile(os.path.join(dst, MARKER)):
        raise RuntimeError(f"{dst} exists and was not installed by {PRODUCT}")
    shutil.copytree(SOURCE_DIR, dst, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.blend1"))
    stale = os.path.join(dst, "__init__.py")   # copies made before step 115 carried code
    if os.path.isfile(stale):
        os.remove(stale)
        shutil.rmtree(os.path.join(dst, "__pycache__"), ignore_errors=True)
    with open(os.path.join(dst, MARKER), "w", encoding="utf-8") as fh:
        fh.write(f"Installed by the {PRODUCT} extension. Removed by its 'Remove Maya Layout' button and when the "
                 "extension is disabled or removed.\n")
    _set_wanted(True)
    return dst


def _set_wanted(value):
    try:
        from .. import preferences
        preferences.get().layout_installed = value
    except (KeyError, AttributeError):
        pass


def remove(keep_wanted=False):
    removed_old = bool(remove_legacy())
    if not keep_wanted:
        _set_wanted(False)
    dst = installed_dir()
    if not os.path.isdir(dst):
        return removed_old
    if not os.path.isfile(os.path.join(dst, MARKER)):
        raise RuntimeError(f"{dst} was not installed by {PRODUCT}; not removing it")
    shutil.rmtree(dst)
    return True


def remove_on_disable():
    """The extension is being disabled or removed by the user: take the template (ours only, marker-checked)
    with it. Quitting keeps it (``switch.user_disabling``)."""
    try:
        return remove(keep_wanted=True)
    except (OSError, RuntimeError) as ex:
        print(f"{PRODUCT}: Maya layout template not removed:", ex)
        return False


def reinstall_if_wanted():
    """Register: the user installed the template and it is gone although the add-on preferences still say so
    (removed while they were kept, e.g. by an older version's disable): put it back."""
    try:
        from .. import preferences
        wanted = preferences.get().layout_installed
    except (KeyError, AttributeError):
        return False
    if not wanted or is_installed() or os.path.isdir(installed_dir()):
        return False
    try:
        install()
    except (OSError, RuntimeError) as ex:
        print(f"{PRODUCT}: Maya layout template not reinstalled:", ex)
        return False
    return True


class ALLSET_OT_layout_install(bpy.types.Operator):
    """Install the Maya layout as an application template (File > New > Maya Workflow Kit)"""
    bl_idname = "allset.layout_install"
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


class ALLSET_OT_layout_remove(bpy.types.Operator):
    """Remove the Maya layout application template"""
    bl_idname = "allset.layout_remove"
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


class ALLSET_OT_layout_open(bpy.types.Operator):
    """Start a new file with the Maya layout (unsaved changes are lost)"""
    bl_idname = "allset.layout_open"
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


classes = (ALLSET_OT_layout_install, ALLSET_OT_layout_remove, ALLSET_OT_layout_open)

register, unregister = bpy.utils.register_classes_factory(classes)
