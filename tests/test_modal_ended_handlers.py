"""A window's list of modal operators can hold an entry with no operator: a modal operator that has just finished or
been cancelled keeps its handler in the window until Blender removes it, and ``Window.modal_operators`` shows that
handler as None. The kit's checks for a running transform, scrub, view navigation or 2D pan / zoom skip such an
entry instead of raising (the Time Slider draw and the Channel Box update call them on every redraw / update)."""

from contextlib import nullcontext
from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

joints = import_module(kit.MODULE + ".ui.maya_joints")
colors = import_module(kit.MODULE + ".ui.component_colors")
graph_keys = import_module(kit.MODULE + ".ui.graph_keys_draw")
selection = import_module(kit.MODULE + ".operators.joint_selection")


def _op(idname):
    return SimpleNamespace(bl_idname=idname)


def _wm(*ops):
    return SimpleNamespace(windows=[SimpleNamespace(modal_operators=list(ops))])


class _Bpy:
    """``bpy`` with a window manager made of the given modal operators."""

    def __init__(self, wm):
        self.context = SimpleNamespace(window_manager=wm)

    def __getattr__(self, name):
        return getattr(bpy, name)


def _with_bpy(module, wm, fn):
    saved = module.bpy
    module.bpy = _Bpy(wm)
    try:
        return fn()
    finally:
        module.bpy = saved


def test_transform_and_scrub_checks_skip_an_ended_handler():
    move = _op("TRANSFORM_OT_translate")
    assert _with_bpy(joints, _wm(None), joints.transform_op) is None
    assert _with_bpy(joints, _wm(None, move), joints.transform_op) is move
    assert _with_bpy(joints, _wm(None), joints.transforming) is False
    assert _with_bpy(joints, _wm(None), joints.scrubbing) is False
    assert _with_bpy(joints, _wm(None, _op("ANIM_OT_change_frame")), joints.scrubbing) is True


def test_navigation_checks_skip_an_ended_handler():
    assert _with_bpy(colors, _wm(None, _op("VIEW3D_OT_rotate")), colors._navigating) is True
    assert _with_bpy(colors, _wm(None), colors._navigating) is False
    pan = _op("VIEW2D_OT_pan")
    pan.as_pointer = lambda: 7
    assert graph_keys._navigation(SimpleNamespace(window=SimpleNamespace(modal_operators=[None, pan]))) == 7
    assert graph_keys._navigation(SimpleNamespace(window=SimpleNamespace(modal_operators=[None]))) is None


def test_joint_pick_mode_switch_check_skips_an_ended_handler():
    ob = bpy.context.view_layer.objects.active
    assert ob is not None and bpy.ops.object.mode_set.poll()
    context = SimpleNamespace(temp_override=lambda **_kw: nullcontext())
    context.window_manager = _wm(None)
    assert selection._switches(context, ob) is True
    context.window_manager = _wm(None, _op("TRANSFORM_OT_rotate"))
    assert selection._switches(context, ob) is False
