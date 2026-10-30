"""Joint Tool drag (#230): ``joints.move_joint`` moves the joint just placed the way ``add_joint`` would have placed
it there; the Help Line shows the Joint Tool's help while it runs; the preview handler comes and goes with the tool."""

from importlib import import_module

import bpy
from mathutils import Vector

import kit

joints = import_module(kit.MODULE + ".operators.joints")
preview = import_module(kit.MODULE + ".operators.joint_preview")
command_line = import_module(kit.MODULE + ".command_line")


def _clean():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _close(a, b):
    return (Vector(a) - Vector(b)).length < 1e-5


def test_move_joint_matches_add_joint():
    _clean()
    ob = joints.new_skeleton(bpy.context)
    a = joints.add_joint(ob, (0, 0, 0))
    b = joints.add_joint(ob, (1, 0, 0), a)
    assert joints.move_joint(ob, b, (2, 3, 0))
    ebs = ob.data.edit_bones
    assert _close(ebs[b].head, (2, 3, 0)), ebs[b].head
    assert _close(ebs[a].tail, (2, 3, 0)), "the bone from the parent follows"
    assert _close(ebs[b].tail, (3, 4.5, 0)), "the end joint keeps half the parent segment"
    ref = joints.add_joint(ob, (4, 3, 0), b)
    assert joints.move_joint(ob, ref, (4, 5, 0)) and _close(ebs[b].tail, (4, 5, 0))
    # a point on the parent joint itself is refused (no zero-length bone)
    assert not joints.move_joint(ob, ref, tuple(ebs[b].head))
    assert _close(ebs[ref].head, (4, 5, 0))


def test_move_root_joint():
    _clean()
    ob = joints.new_skeleton(bpy.context)
    a = joints.add_joint(ob, (0, 0, 0), length=0.5)
    assert joints.move_joint(ob, a, (1, 2, 3), length=0.5)
    eb = ob.data.edit_bones[a]
    assert _close(eb.head, (1, 2, 3)) and _close(eb.tail, (1, 2, 3.5))


def test_branch_joint_drag_keeps_parent():
    _clean()
    ob = joints.new_skeleton(bpy.context)
    a = joints.add_joint(ob, (0, 0, 0))
    b = joints.add_joint(ob, (0, 0, 2), a)
    joints.add_joint(ob, (0, 0, 4), b)
    tail = ob.data.edit_bones[b].tail.copy()
    c = joints.add_joint(ob, (2, 0, 2), b)       # a branch: b already has a child, not connected
    assert joints.move_joint(ob, c, (3, 0, 2))
    assert _close(ob.data.edit_bones[b].tail, tail), "a branch drag leaves the parent bone alone"


def test_modal_help_text():
    class _Op:
        bl_idname = "ALLSET_OT_test_modal"

    class _Win:
        modal_operators = [_Op()]

    class _Ctx:
        window = _Win()

    command_line.MODAL_HELP[_Op.bl_idname] = "Test help"
    try:
        assert command_line.modal_help(_Ctx()) == "Test help"
        _Win.modal_operators = []
        assert command_line.modal_help(_Ctx()) == ""
    finally:
        command_line.MODAL_HELP.pop(_Op.bl_idname, None)
    assert command_line.MODAL_HELP.get("ALLSET_OT_joint_tool", joints.STATUS) == joints.STATUS


def test_preview_handler_start_stop():
    preview.start()
    assert preview.running()
    preview.start()                     # a second start keeps one handler
    assert len(preview._handles) == 1
    preview.stop()
    assert not preview.running() and preview.STATE["ob"] is None
