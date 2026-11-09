"""#338: in Maya mode the last picked object is the lead everywhere the kit shows one, like Maya, whatever way it was
picked. Blender's box / lasso drags, the Outliner range / box, Select All and the select menus add objects without
making them active, and the kit's lead displays (Channel Box name and values, Attribute Editor, the lead-coloured
selection wire) and Blender's own tools read the active object. So after such a selection the kit makes the last
picked object the active one, in one undo with the selection: Undo takes back both, Redo brings back both.

A selecting operator the user runs pushes its own undo step and is registered, like ``op('EXEC_DEFAULT', True, ...)``
here; the kit's part runs from a timer in the UI (``pick_order.run_follow``, called directly here). Real box drags and
Outliner clicks are in tests/gui/gui_issue338_box_select.py."""

from importlib import import_module

import bpy

import kit

pick_order = import_module(kit.MODULE + ".operators.pick_order")
undo_pairs = import_module(kit.MODULE + ".operators.undo_pairs")
joint_marquee = import_module(kit.MODULE + ".operators.joint_marquee")
undo_steps = import_module(kit.MODULE + ".undo_steps")
channel_box = import_module(kit.MODULE + ".ui.channel_box")
cb_entry = import_module(kit.MODULE + ".ui.cb_entry")
selection_wire = import_module(kit.MODULE + ".ui.selection_wire")
switch = import_module(kit.MODULE + ".switch")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    bpy.context.view_layer.update()
    for fn in (pick_order.run_follow, undo_pairs.run_extra):
        if bpy.app.timers.is_registered(fn):
            bpy.app.timers.unregister(fn)
    undo_pairs.reset()
    joint_marquee._pending.clear()
    wm = bpy.context.window_manager
    pick_order._ops["last"] = wm.operators[-1].as_pointer() if len(wm.operators) else 0   # earlier tests' ops: seen


def _cube(name, x):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(a, b, c) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (x, 0.0, 0.0)
    return ob


def _locator(name, x):
    ob = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (x, 1.5, 2.5)
    return ob


def _scene(*extra):
    """pCube1 (x 0) and locator1 (x 4), the cube clicked (selected, active); ``extra`` cubes at those x."""
    _clear()
    cube, loc = _cube("pCube1", 0.0), _locator("locator1", 4.0)
    more = [_cube(f"pCube{i + 2}", x) for i, x in enumerate(extra)]
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube
    bpy.context.view_layer.update()
    bpy.ops.ed.undo_push(message="click pCube1")
    return (cube, loc, *more)


def _follow():
    """The kit's part after a selecting operator (a timer in the UI)."""
    if bpy.app.timers.is_registered(pick_order.run_follow):
        bpy.app.timers.unregister(pick_order.run_follow)
    return pick_order.run_follow()


def _extra():
    """The kit's extra undo / redo step of a paired step (a timer in the UI)."""
    if bpy.app.timers.is_registered(undo_pairs.run_extra):
        bpy.app.timers.unregister(undo_pairs.run_extra)
    wanted = undo_pairs.wanted()
    undo_pairs.run_extra()
    return wanted


def _undo():
    bpy.ops.ed.undo()
    return _extra()


def _redo():
    bpy.ops.ed.redo()
    return _extra()


def _obj(name):
    return bpy.data.objects[name]


def _selected():
    return sorted(o.name for o in bpy.context.view_layer.objects if o is not None and o.select_get())


def _active():
    ob = bpy.context.view_layer.objects.active
    return ob.name if ob is not None else None


def _shown_text(ob, key):
    """The Channel Box text of channel ``key`` for ``ob``."""
    return cb_entry.format_value(channel_box.get_value(ob, key), channel_box.entry_kind(ob, key), bpy.context.scene)


def _add_by_menu(pattern):
    """A select menu / box that adds objects: a registered operator with its own undo step; the active one stays."""
    r = bpy.ops.object.select_pattern('EXEC_DEFAULT', True, pattern=pattern, extend=True)
    bpy.context.view_layer.update()
    return r


def _lead_shown(name):
    cb = bpy.context.scene.allset_cb
    lead = channel_box.lead(bpy.context)
    assert lead is not None and lead.name == name, f"Channel Box lead {lead and lead.name} != {name}"
    assert cb.lead_name == name, f"Channel Box name line {cb.lead_name!r} != {name!r}"
    ob = _obj(name)
    assert cb.tx_text == _shown_text(ob, "tx") and cb.tz_text == _shown_text(ob, "tz"), \
        f"Channel Box values ({cb.tx_text}, {cb.tz_text}) are not {name}'s"


# --- a selection that adds objects: the last pick becomes the active one ---------------------------------------------

def test_added_locator_becomes_the_lead():
    # the report: click the cube, Shift+drag a box over the locator -> the locator is the lead (Channel Box, AE)
    cube, loc = _scene()
    assert _add_by_menu("locator1") == {'FINISHED'}
    assert _selected() == ["locator1", "pCube1"] and _active() == "pCube1"     # Blender: the active one stays
    _follow()
    assert _active() == "locator1", f"the locator (picked last) must be the active object, not {_active()}"
    _lead_shown("locator1")
    lead, others = import_module(kit.MODULE + ".operators.snap_align").match_lead(bpy.context)
    assert lead == _obj("locator1") and others == [_obj("pCube1")], "Match keeps the same lead"


def test_wire_draws_the_last_pick_in_the_lead_colour():
    cube, loc, cube2 = _scene(-4.0)
    _add_by_menu("pCube2")
    _follow()
    drawn = {ob.name: is_lead for ob, is_lead in selection_wire.highlighted(bpy.context)}
    assert drawn == {"pCube1": False, "pCube2": True}, f"lead colour on the cube picked last: {drawn}"


def test_one_undo_and_one_redo_take_the_lead_along():
    _scene()
    _add_by_menu("locator1")
    _follow()
    assert _active() == "locator1"
    # Undo: the selection and the lead before the box come back with one Ctrl+Z
    assert _undo() == 'UNDO', "the kit's step and the selection step are taken back together"
    assert _selected() == ["pCube1"] and _active() == "pCube1", (_selected(), _active())
    _lead_shown("pCube1")
    # Redo: both come back with one Shift+Z
    assert _redo() == 'REDO'
    assert _selected() == ["locator1", "pCube1"] and _active() == "locator1", (_selected(), _active())
    _lead_shown("locator1")


def test_undo_from_a_later_step_lands_on_the_lead():
    _scene()
    _add_by_menu("locator1")
    _follow()
    x0 = _obj("pCube1").location.x
    assert bpy.ops.allset.match_transform('EXEC_DEFAULT', True, kind='ALL') == {'FINISHED'}
    assert abs(_obj("pCube1").location.x - 4.0) < 1e-4, "Match moves the cube onto the locator"
    assert _undo() is None, "the Match step stands alone"
    assert abs(_obj("pCube1").location.x - x0) < 1e-4
    assert _selected() == ["locator1", "pCube1"] and _active() == "locator1", (_selected(), _active())
    _follow()
    assert _active() == "locator1"


def test_several_objects_at_once_last_by_name():
    _scene(-4.0)
    _add_by_menu("*")             # locator1 and pCube2 join pCube1 in one go (name order)
    _follow()
    assert _active() == "pCube2", _active()
    assert [o.name for o in pick_order.ordered(bpy.context)] == ["pCube1", "locator1", "pCube2"]


def test_a_deselected_lead_hands_over():
    # the lead deselected (Ctrl+click / Shift+click on it, a Ctrl box): the last pick still selected is the lead
    _scene(-4.0)
    _add_by_menu("locator1")
    _follow()
    assert _active() == "locator1"
    bpy.ops.ed.undo_push(message="lead locator")
    r = bpy.ops.object.select_all('EXEC_DEFAULT', True, action='INVERT')       # locator1 off, pCube2 on
    bpy.context.view_layer.update()
    assert r == {'FINISHED'} and _selected() == ["pCube2"] and _active() == "locator1"
    _follow()
    assert _active() == "pCube2", _active()
    _lead_shown("pCube2")


def test_nothing_selected_leaves_the_active_object():
    _scene()
    bpy.ops.object.select_all('EXEC_DEFAULT', True, action='DESELECT')
    bpy.context.view_layer.update()
    _follow()
    assert _selected() == [] and _active() == "pCube1"


def test_select_all_from_a_menu_is_one_undo_step():
    _scene(-4.0)
    r = undo_steps.command("Select All", lambda: bpy.ops.object.select_all(action='SELECT'))
    assert r == {'FINISHED'}
    assert _active() == "pCube2", f"Select All: the last of the new picks is the lead, not {_active()}"
    assert not bpy.app.timers.is_registered(pick_order.run_follow), "a menu command does it in its own step"
    assert _undo() is None, "one plain undo step"
    assert _selected() == ["pCube1"] and _active() == "pCube1", (_selected(), _active())


def test_operators_that_select_nothing_leave_it():
    # a transform is no selection: nothing to follow
    _scene()
    _obj("locator1").select_set(True)            # a script's selection: no operator, the kit keeps out of it
    bpy.context.view_layer.update()
    r = bpy.ops.transform.translate('EXEC_DEFAULT', True, value=(1.0, 0.0, 0.0))
    bpy.context.view_layer.update()
    assert r == {'FINISHED'}
    assert not bpy.app.timers.is_registered(pick_order.run_follow)
    assert _active() == "pCube1"


def test_pose_mode_keeps_the_active_rig():
    _clear()
    loc = _locator("locator1", 4.0)
    arm = bpy.data.armatures.new("rig")
    rig = bpy.data.objects.new("rig", arm)
    bpy.context.scene.collection.objects.link(rig)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.edit_bones.new("joint1")
    eb.head, eb.tail = (0, 0, 0), (0, 0.5, 0)
    bpy.ops.object.mode_set(mode='POSE')
    loc.select_set(True)
    bpy.context.view_layer.update()
    assert pick_order.follow(bpy.context) is False
    assert _active() == "rig" and bpy.context.mode == 'POSE'
    bpy.ops.object.mode_set(mode='OBJECT')


def test_blender_rule_without_maya_mode():
    _scene()
    switch.set_mode(False, layout=False)
    try:
        _add_by_menu("locator1")
        _follow()
        assert _active() == "pCube1", "Maya mode off: Blender's active object stays"
        assert pick_order.follow(bpy.context) is False
    finally:
        switch.set_mode(True, layout=False)


def test_waits_for_the_joint_marquee():
    # a marquee the kit finishes after Blender's box (joints) makes the lead in its own step; this one waits for it
    _scene()
    _add_by_menu("locator1")
    joint_marquee._pending.append({"stub": True})
    try:
        again = _follow()
        assert again and _active() == "pCube1", "waits while the kit's marquee step is still to come"
    finally:
        joint_marquee._pending.clear()
    assert _follow() is None and _active() == "locator1"

