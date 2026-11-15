# SPDX-License-Identifier: GPL-3.0-or-later
"""The kit's timers after File > Open and File > New. Blender drops every ``bpy.app.timers`` entry that is not
registered as persistent when it loads a file. The timers that run for as long as Maya mode is on (the Channel Box
value poll among them) are persistent: after a file is opened, a new file is made or a new Maya scene is started,
each one is still registered. The one-shot timers Maya mode starts with may go: a load_post handler of the same
module does their job for every file loaded later. Switching to Blender after a file load still stops every Maya
mode timer, so none was registered twice.

The watchers and updates the kit starts on demand (the pivot edit watch, the Edit Armature joint watch, the Euler
curve sync after a key change, the constraint group cleanup, the Component Editor auto update) start again after a
file load dropped them, instead of waiting for a timer that is gone."""

import os
import sys
import types
from importlib import import_module

import bpy

import kit

switch = import_module(kit.MODULE + ".switch")
first_start = import_module(kit.MODULE + ".first_start")
cb = import_module(kit.MODULE + ".ui.channel_box")
ce = import_module(kit.MODULE + ".ui.component_editor")
hold = import_module(kit.MODULE + ".operators.hold")
pivot = import_module(kit.MODULE + ".operators.pivot")
joint_edit = import_module(kit.MODULE + ".operators.joint_edit")
gc = import_module(kit.MODULE + ".operators.graph_curves_203")
cm = import_module(kit.MODULE + ".operators.constrain_multi")

OUT = os.path.join(kit.ROOT, "tmp", os.environ.get("ALLSET_SANDBOX", "test_env"), "persistent_timers")
POLL = "ui.channel_box._poll_transform_values"
CORE = ("i18n", "preferences", "translations", "settings_io", "switch", "welcome")

# Started once when Maya mode turns on, for the file that is open then; a load_post handler of the same module does
# the same for every file loaded later, so a load may drop them.
ONE_SHOT = {
    "ui.channel_box._first_rebuild",
    "ui.option_editor.restore_sessions",
    "ui.outliner_tree._first_hide",
    "ui.shelf._settle_later",
    "operators.driven_key._first_sync",
    "operators.soft_select._push_later",
    "operators.type_manip._on_load_later",
}


def _kit_functions():
    """'module:function' -> function for every function the kit's modules hold at module level (also inside lists
    and tuples): the callbacks they can register as timers."""
    out = {}
    for name, mod in list(sys.modules.items()):
        if mod is None or not (name == kit.MODULE or name.startswith(kit.MODULE + ".")):
            continue
        for value in list(vars(mod).values()):
            for v in (value if isinstance(value, (list, tuple)) else (value,)):
                if isinstance(v, types.FunctionType) and (v.__module__ or "").startswith(kit.MODULE + "."):
                    out[f"{v.__module__[len(kit.MODULE) + 1:]}.{v.__qualname__}"] = v
    return out


def _timers():
    return {label for label, fn in _kit_functions().items() if bpy.app.timers.is_registered(fn)}


def _maya_mode_only(labels):
    return sorted(k for k in labels if k.split(".")[0] not in CORE)


def _fresh():
    """Maya mode off and on again: every kit timer started anew, whatever an earlier load dropped."""
    switch.set_mode(False, layout=False)
    switch.set_mode(True, layout=False)
    return _timers()


def _save(name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    return path


def _kept(before, label):
    lost = sorted(set(before) - _timers() - ONE_SHOT)
    assert not lost, f"kit timers gone after {label}: {lost}"


def _object_mode():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _cube(name="pCube1"):
    _object_mode()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new(name)
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0)], [], [(0, 1, 2)])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob


def _nudge(ob):
    """A change and the depsgraph update after it."""
    ob.location.x += 0.1
    bpy.context.view_layer.update()


def test_maya_mode_starts_the_channel_box_poll():
    """Guard against a vacuous pass: the kit timers are found, the Channel Box value poll among them."""
    found = _fresh()
    assert POLL in found, sorted(found)
    assert set(found) - ONE_SHOT, sorted(found)
    unknown = sorted(ONE_SHOT - set(_kit_functions()))
    assert not unknown, f"one-shot timers listed here that the kit no longer has: {unknown}"


def test_timers_kept_after_open():
    before = _fresh()
    path = _save("kept_after_open.blend")
    for label in ("File > Open", "a second File > Open"):
        bpy.ops.wm.open_mainfile(filepath=path)
        _kept(before, label)


def test_timers_kept_after_new_file():
    before = _fresh()
    bpy.ops.wm.read_homefile()
    _kept(before, "File > New")
    bpy.ops.wm.read_homefile(use_empty=True)
    _kept(before, "File > New (empty)")


def test_timers_kept_after_new_maya_scene():
    before = _fresh()
    first_start.new_maya_scene()
    _kept(before, "a new scene in the Maya layout")


def test_switch_to_blender_after_a_load_stops_every_timer():
    before = _fresh()
    assert _maya_mode_only(before)
    path = _save("switch_after_load.blend")
    bpy.ops.wm.open_mainfile(filepath=path)
    switch.set_mode(False, layout=False)
    try:
        left = _maya_mode_only(_timers())
        assert not left, f"Maya mode timers left in Blender mode (registered twice?): {left}"
    finally:
        switch.set_mode(True, layout=False)
    _kept(before, "Blender mode, File > Open, Maya mode")
    bpy.ops.wm.open_mainfile(filepath=path)
    _kept(before, "Blender mode, File > Open, Maya mode, File > Open")


def test_pivot_edit_watches_again_after_open():
    _fresh()
    _cube()
    ts = bpy.context.scene.tool_settings
    hold.set_pivot_mode(ts, True)                     # Insert / a D tap: the pivot edit is on
    try:
        assert bpy.app.timers.is_registered(pivot._tick), "the pivot edit does not watch the moves"
        path = _save("pivot_edit.blend")
        bpy.ops.wm.open_mainfile(filepath=path)
        # the watch of the file before has ended: Reset / Bake / Match Pivots don't rewrite a move from its snapshots
        assert not pivot.watching() and not pivot._watch["snaps"], pivot._watch
        ts = bpy.context.scene.tool_settings
        hold.set_pivot_mode(ts, False)
        hold.set_pivot_mode(ts, True)                 # the pivot edit in the opened file
        assert bpy.app.timers.is_registered(pivot._tick), "after File > Open the pivot edit no longer watches the moves"
        assert set(pivot._watch["snaps"]) == {"pCube1"}, pivot._watch["snaps"]
    finally:
        hold.set_pivot_mode(bpy.context.scene.tool_settings, False)
        pivot.stop()


def _rig():
    _object_mode()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    arm = bpy.data.objects.new("rig", bpy.data.armatures.new("rig"))
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.data.edit_bones.new("joint1")
    eb.head, eb.tail = (0, 0, 0), (0, 0, 1)
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm


def test_joint_watch_runs_again_after_open():
    _fresh()
    arm = _rig()
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        joint_edit.watch()                            # Edit Armature mode: the joint frames are watched
        assert bpy.app.timers.is_registered(joint_edit._tick)
        bpy.ops.object.mode_set(mode='OBJECT')
        path = _save("joint_watch.blend")
        bpy.ops.wm.open_mainfile(filepath=path)
        arm = bpy.data.objects["rig"]
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')
        joint_edit.watch()
        assert bpy.app.timers.is_registered(joint_edit._tick), \
            "after File > Open the joint watch no longer runs in Edit Armature mode"
    finally:
        _object_mode()
        if bpy.app.timers.is_registered(joint_edit._tick):
            bpy.app.timers.unregister(joint_edit._tick)


def _key(ob, frame):
    ob.keyframe_insert("location", index=0, frame=frame)
    bpy.context.view_layer.update()


def test_curve_sync_scheduled_again_after_open():
    _fresh()
    ob = _cube()
    try:
        _key(ob, 1)
        assert bpy.app.timers.is_registered(gc._sync_tick), "a key change does not schedule the curve sync"
        path = _save("curve_sync.blend")
        bpy.ops.wm.open_mainfile(filepath=path)
        _key(bpy.data.objects["pCube1"], 5)
        assert bpy.app.timers.is_registered(gc._sync_tick), \
            "after File > Open a key change no longer schedules the curve sync"
    finally:
        if bpy.app.timers.is_registered(gc._sync_tick):
            bpy.app.timers.unregister(gc._sync_tick)
        gc._state["scheduled"] = False


def test_constraint_cleanup_scheduled_again_after_open():
    _fresh()
    ob = _cube()
    helpers = bpy.data.collections.new(cm.HELPERS)
    bpy.context.scene.collection.children.link(helpers)
    try:
        _nudge(ob)
        assert bpy.app.timers.is_registered(cm._tick), "a change does not schedule the constraint group cleanup"
        path = _save("constraint_cleanup.blend")
        bpy.ops.wm.open_mainfile(filepath=path)
        _nudge(bpy.data.objects["pCube1"])
        assert bpy.app.timers.is_registered(cm._tick), \
            "after File > Open a change no longer schedules the constraint group cleanup"
    finally:
        if bpy.app.timers.is_registered(cm._tick):
            bpy.app.timers.unregister(cm._tick)
        cm._state["pending"] = False
        for col in [c for c in bpy.data.collections if c.name == cm.HELPERS]:
            bpy.data.collections.remove(col)


def test_component_editor_update_scheduled_again_after_open():
    _fresh()
    ob = _cube()
    real = ce._is_open
    ce._is_open = lambda _context: True               # no window headless: the Component Editor stands open
    try:
        bpy.context.window_manager.allset_ce_auto_update = True
        _nudge(ob)
        assert bpy.app.timers.is_registered(ce._tick), "a change does not schedule the Component Editor update"
        path = _save("component_editor.blend")
        bpy.ops.wm.open_mainfile(filepath=path)
        bpy.context.window_manager.allset_ce_auto_update = True
        _nudge(bpy.data.objects["pCube1"])
        assert bpy.app.timers.is_registered(ce._tick), \
            "after File > Open a change no longer schedules the Component Editor update"
    finally:
        ce._is_open = real
        if bpy.app.timers.is_registered(ce._tick):
            bpy.app.timers.unregister(ce._tick)
        ce._pending["timer"] = False
