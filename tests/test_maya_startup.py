"""Saved Maya mode must register inside Blender's restricted addon startup context."""
from importlib import import_module

import addon_utils
import bpy

import kit

AUTO_ENABLE = False


def test_reenable_with_saved_maya_mode_registers_all_operators():
    kit.enable()
    assert bpy.context.preferences.addons[kit.MODULE].preferences.maya_mode
    # Preserve the preference, as when Blender quits and starts again. Unlike
    # switch.set_mode(), addon_utils.enable() restricts access to bpy.data.
    addon_utils.disable(kit.MODULE, default_set=False)
    kit.enable(maya=False)
    try:
        assert import_module(kit.MODULE+'.switch')._registered[0]
        assert hasattr(bpy.types, 'ALLSET_OT_make_live')
        assert hasattr(bpy.types, 'ALLSET_OT_quad_draw_start')
        live = import_module(kit.MODULE+'.operators.live')
        assert live.reload in bpy.app.handlers.load_post
        # The normal load handler reconciles references when scene data exists.
        live.reload()
    finally:
        kit.disable()
