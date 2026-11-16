"""#363 in a real UI: key edits survive the Maya / Blender switch while Blender's event loop updates the keymaps
itself. A Maya key with a property (Smooth Mesh Preview 3, Numpad 3) moved to Ctrl+F7 in the user keymap (what
Preferences > Keymap does) is still there after Maya -> Blender -> Maya (with another add-on's operator registered and
gone in Blender mode); a Blender key changed in Blender mode (Object Mode Delete on F9) is still there after a Maya key
of the same keymap changed in Maya mode and Blender mode came back."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, setup, step  # noqa: E402

KM = "Object Mode"


def sw():
    return import_module(MODULE + ".switch")


def kcs():
    return bpy.context.window_manager.keyconfigs


def user_km():
    return kcs().user.keymaps[KM]


def kit_item(type):
    addon = kcs().addon.keymaps[KM]
    item = next(k for k in addon.keymap_items if k.idname == "allset.smooth_preview" and k.type == type)
    return user_km().keymap_items.find_match(addon, item)


def on(type, ctrl=False):
    out = []
    for k in user_km().keymap_items:
        if k.type == type and bool(k.ctrl) == ctrl and k.active:
            p = k.properties
            level = p.level if p is not None and "level" in p.bl_rna.properties and p.is_property_set("level") \
                else None
            out.append((k.idname, level))
    return out


class TMP_OT_issue363(bpy.types.Operator):
    bl_idname = "tmp.issue363"
    bl_label = "Issue 363"

    def execute(self, context):
        return {'FINISHED'}


@step
def s_setup():
    setup()


@step
def s_edit():
    item = kit_item('NUMPAD_3')
    item.type = 'F7'
    item.ctrl = 1


@step
def s_edited():
    check(f"the Maya key moved to Ctrl+F7 ({on('F7', True)})", on('F7', True) == [("allset.smooth_preview", 3)])
    sw().set_mode(False)


@step
def s_blender():
    check(f"Blender mode: no kit key on Ctrl+F7 ({on('F7', True)})", on('F7', True) == [])
    bpy.utils.register_class(TMP_OT_issue363)          # another add-on's operator comes ...


@step
def s_blender2():
    bpy.utils.unregister_class(TMP_OT_issue363)        # ... and goes


@step
def s_blender3():
    sw().set_mode(True)


@step
def s_maya_again():
    check(f"Maya mode again: Smooth Mesh Preview 3 still on Ctrl+F7 ({on('F7', True)}, Numpad 3: {on('NUMPAD_3')})",
          on('F7', True) == [("allset.smooth_preview", 3)] and on('NUMPAD_3') == [])
    sw().set_mode(False)


@step
def s_blender_edit():
    delete = next(k for k in user_km().keymap_items if k.idname == "object.delete" and k.type == 'X')
    delete.type = 'F9'


@step
def s_blender_edited():
    check(f"Blender mode: Delete on F9 ({on('F9')})", on('F9') == [("object.delete", None)])
    sw().set_mode(True)


@step
def s_maya_edit():
    kit_item('NUMPAD_1').type = 'F6'


@step
def s_maya_edited():
    check(f"Maya mode: Smooth Mesh Preview 1 on F6 ({on('F6')})", on('F6') == [("allset.smooth_preview", 1)])
    sw().set_mode(False)


@step
def s_blender_back():
    check(f"Blender mode again: Delete still on F9 ({on('F9')})", on('F9') == [("object.delete", None)])
    sw().set_mode(True)


@step
def s_maya_back():
    check(f"Maya mode again: both Maya key edits there ({on('F7', True)}, {on('F6')})",
          on('F7', True) == [("allset.smooth_preview", 3)] and on('F6') == [("allset.smooth_preview", 1)])
    user_km().restore_to_default()


run()
