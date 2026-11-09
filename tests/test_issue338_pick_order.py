"""#338 follow-up: Modify > Match Transformations takes the last *picked* object as the source whatever way it was
picked. Blender's box / lasso / circle drags, the Outliner box and range, Select All and the select menus add objects
without making them active, so the active object alone isn't the last pick: a cube clicked first and a locator
added by a Shift+drag box must put the cube on the locator, not the locator on the cube.

A box adds objects the way ``_add`` does here: selected, the active object left alone, then the depsgraph update
the event loop runs after every selection change. Real box drags and Outliner clicks are in
tests/gui/gui_issue338_box_select.py."""

import math
import os
from importlib import import_module

import bpy
from mathutils import Euler, Matrix, Vector

import kit

snap = import_module(kit.MODULE + ".operators.snap_align")
joint_selection = import_module(kit.MODULE + ".operators.joint_selection")
input_line = import_module(kit.MODULE + ".ui.input_line")

TOL = 1e-4
HAND = "c_hand_ik"


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    bpy.context.view_layer.update()


def _cube(name, loc):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.select_set(False)
    bpy.context.view_layer.update()
    return ob


def _locator(name, loc, rot_deg=(0, 0, 0), scale=(1, 1, 1)):
    ob = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ob)
    ob.matrix_world = Matrix.LocRotScale(Vector(loc), Euler([math.radians(a) for a in rot_deg]), Vector(scale))
    ob.select_set(False)
    bpy.context.view_layer.update()
    return ob


def _rig():
    arm = bpy.data.armatures.new("rig")
    ob = bpy.data.objects.new("rig", arm)
    bpy.context.scene.collection.objects.link(ob)
    ob.matrix_world = Matrix.LocRotScale(Vector((0.3, -0.2, 0.1)), Euler((0, 0, math.radians(20))), None)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.edit_bones.new(HAND)
    eb.head = (1.0, 0.0, 2.0)
    eb.tail = (1.0, 0.5, 2.0)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.select_set(False)
    bpy.context.view_layer.objects.active = None
    bpy.context.view_layer.update()
    return ob


def _click(ob, keep=False):
    """A click on an object: it becomes selected and active (``keep``: Shift / Ctrl+Shift, the others stay)."""
    ctx = bpy.context
    if ctx.mode != 'OBJECT' and ctx.active_object is not None:
        joint_selection.leave(ctx, clear_selection=not keep)
    if not keep:
        for o in ctx.scene.objects:
            o.select_set(False)
    ob.select_set(True)
    ctx.view_layer.objects.active = ob
    ctx.view_layer.update()


def _add(*obs):
    """A box / lasso / Outliner box or range over ``obs``: selected in one go, the active object stays."""
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.update()


def _remove(*obs):
    """A Ctrl box (deselect) over ``obs``."""
    for ob in obs:
        ob.select_set(False)
    bpy.context.view_layer.update()


def _same(m1, m2, what):
    t1, r1, s1 = m1.decompose()
    t2, r2, s2 = m2.decompose()
    assert (t1 - t2).length < TOL, f"{what}: translation {tuple(t1)} != {tuple(t2)}"
    assert math.degrees(r1.rotation_difference(r2).angle) < 1e-3, f"{what}: rotation {r1} != {r2}"
    assert (s1 - s2).length < TOL, f"{what}: scale {tuple(s1)} != {tuple(s2)}"


def _match(kind='ALL'):
    r = bpy.ops.allset.match_transform(kind=kind)
    bpy.context.view_layer.update()
    return r


def _scene():
    _clear()
    cube = _cube("pCube1", (0, 0, 0))
    loc = _locator("locator1", (4, 1, 2), (10, 20, 30), (1, 2, 1))
    return cube, loc


def test_box_added_locator_is_the_source():
    # the report: click the cube, Shift+drag a box over the locator, Match -> the cube lands on the locator
    cube, loc = _scene()
    loc0 = loc.matrix_world.copy()
    _click(cube)
    _add(loc)
    assert bpy.context.view_layer.objects.active is cube, "a box leaves the active object alone"
    assert _match() == {'FINISHED'}
    _same(cube.matrix_world, loc0, "#338: the cube (picked first) must take the locator's transform")
    _same(loc.matrix_world, loc0, "#338: the locator (boxed last) must stay")


def test_box_added_cube_is_the_source():
    # the other order through a box: the locator clicked, the cube boxed -> the locator lands on the cube
    cube, loc = _scene()
    cube0 = cube.matrix_world.copy()
    _click(loc)
    _add(cube)
    assert _match() == {'FINISHED'}
    _same(loc.matrix_world, cube0, "the locator (picked first) must take the cube's transform")
    _same(cube.matrix_world, cube0, "the cube (boxed last) must stay")


def test_two_boxes_in_a_row():
    # nothing clicked: one box over the cube, then a Shift box over the locator -> the locator is the source
    cube, loc = _scene()
    bpy.context.view_layer.objects.active = None
    bpy.context.view_layer.update()
    loc0 = loc.matrix_world.copy()
    _add(cube)
    _add(loc)
    assert _match() == {'FINISHED'}
    _same(cube.matrix_world, loc0, "the cube (first box) must take the locator's transform")
    _same(loc.matrix_world, loc0, "the locator (second box) must stay")


def test_translate_rotate_scale_after_a_box():
    cube, loc = _scene()
    lt, lr, ls = loc.matrix_world.decompose()
    for kind in ('TRANSLATE', 'ROTATE', 'SCALE'):
        cube.matrix_world = Matrix.Identity(4)
        bpy.context.view_layer.update()
        _click(cube)
        _add(loc)
        assert _match(kind) == {'FINISHED'}
        t, r, s = cube.matrix_world.decompose()
        want = Matrix.LocRotScale(lt if kind == 'TRANSLATE' else Vector(),
                                  lr if kind == 'ROTATE' else Euler().to_quaternion(),
                                  ls if kind == 'SCALE' else Vector((1, 1, 1)))
        _same(Matrix.LocRotScale(t, r, s), want, f"Match {kind} after a box")
        _same(loc.matrix_world, Matrix.LocRotScale(lt, lr, ls), f"Match {kind}: the locator must stay")


def test_deselected_last_pick_hands_the_lead_back():
    # a, b clicked in turn, c boxed, then c taken off by a Ctrl box -> b is the source again
    _clear()
    a = _locator("a", (1, 0, 0))
    b = _locator("b", (0, 2, 0), (0, 30, 0))
    c = _locator("c", (0, 0, 3))
    b0, c0 = b.matrix_world.copy(), c.matrix_world.copy()
    _click(a)
    _click(b, keep=True)
    _add(c)
    _remove(c)
    assert _match() == {'FINISHED'}
    _same(a.matrix_world, b0, "a must take b's transform")
    _same(b.matrix_world, b0, "b (the last pick still selected) must stay")
    _same(c.matrix_world, c0, "c (deselected) must stay")


def test_click_on_a_selected_object_makes_it_the_last_pick():
    # Ctrl+Shift click on an object already selected (not the active one): it becomes the active one and the last pick
    _clear()
    a = _locator("a", (1, 0, 0))
    b = _locator("b", (0, 2, 0), (0, 30, 0))
    c = _locator("c", (0, 0, 3))
    b0 = b.matrix_world.copy()
    _click(a)
    _add(b, c)
    order = import_module(kit.MODULE + ".operators.pick_order").ordered(bpy.context)
    assert [o.name for o in order] == ["a", "b", "c"], [o.name for o in order]
    _click(b, keep=True)
    assert _match() == {'FINISHED'}
    for ob in (a, c):
        _same(ob.matrix_world, b0, f"{ob.name} must take b's transform")
    _same(b.matrix_world, b0, "b (clicked again, last) must stay")


def test_one_box_over_several_objects():
    # one box adds several objects at once: they follow in name order, after what was picked before
    _clear()
    first = _locator("first", (0, 0, 0))
    b = _locator("b", (1, 1, 1))
    c = _locator("c", (2, 0, 4), (0, 0, 45))
    c0 = c.matrix_world.copy()
    _click(first)
    _add(c, b)
    order = import_module(kit.MODULE + ".operators.pick_order").ordered(bpy.context)
    assert [o.name for o in order] == ["first", "b", "c"], [o.name for o in order]
    assert _match() == {'FINISHED'}
    for ob in (first, b):
        _same(ob.matrix_world, c0, f"{ob.name} must take c's transform")


def test_select_pattern_adds_the_last_pick():
    # Select > Select Pattern (extend) adds without making active: the matched object is the last pick
    cube, loc = _scene()
    loc0 = loc.matrix_world.copy()
    _click(cube)
    assert bpy.ops.object.select_pattern(pattern="locator*", extend=True) == {'FINISHED'}
    bpy.context.view_layer.update()
    assert loc.select_get() and bpy.context.view_layer.objects.active is cube
    assert _match() == {'FINISHED'}
    _same(cube.matrix_world, loc0, "the cube must take the locator's transform")


def test_select_by_name_field():
    # the Status Line select-by-name field: the matched object is selected and the last pick
    cube, loc = _scene()
    cube0 = cube.matrix_world.copy()
    _click(loc)
    assert input_line.select_by_name(bpy.context, "pCube*") == ["pCube1"]
    bpy.context.view_layer.update()
    _add(loc)                       # then the locator boxed back in: it is the newest pick
    loc0 = loc.matrix_world.copy()
    assert _match() == {'FINISHED'}
    _same(cube.matrix_world, loc0, "the cube must take the locator's transform")
    assert (Vector(cube0.translation) - Vector(loc0.translation)).length > 1


def test_select_all_keeps_the_picked_order():
    # Select All after a click: what was picked keeps its place, the newly selected follow (name order)
    _clear()
    a = _locator("a", (1, 0, 0))
    z = _locator("z", (0, 3, 0), (0, 0, 30))
    m = _locator("m", (0, 0, 2))
    m0 = m.matrix_world.copy()
    _click(z)
    assert bpy.ops.object.select_all(action='SELECT') == {'FINISHED'}
    bpy.context.view_layer.update()
    order = import_module(kit.MODULE + ".operators.pick_order").ordered(bpy.context)
    assert [o.name for o in order] == ["z", "a", "m"], [o.name for o in order]
    assert _match() == {'FINISHED'}
    for ob in (a, z):
        _same(ob.matrix_world, m0, f"{ob.name} must take m's transform")


def test_selection_made_in_one_go_puts_the_active_last():
    # a selection nothing saw being made (a file just loaded): the active object last, the others by name
    _clear()
    a = _locator("a", (1, 0, 0))
    b = _locator("b", (0, 2, 0), (0, 30, 0))
    a0 = a.matrix_world.copy()
    po = import_module(kit.MODULE + ".operators.pick_order")
    po._on_load()
    b.select_set(True)
    a.select_set(True)
    bpy.context.view_layer.objects.active = a
    assert [o.name for o in po.ordered(bpy.context)] == ["b", "a"]
    assert _match() == {'FINISHED'}
    _same(b.matrix_world, a0, "b must take the active object's transform")


def test_nothing_selected_cancels():
    cube, _loc = _scene()
    _click(cube)
    _remove(cube)
    assert bpy.context.view_layer.objects.active is cube and not cube.select_get()
    assert _match() == {'CANCELLED'}


def test_undo_and_redo_keep_the_box_order():
    cube, loc = _scene()
    cube0, loc0 = cube.matrix_world.copy(), loc.matrix_world.copy()
    bpy.ops.ed.undo_push(message="scene")
    _click(cube)
    bpy.ops.ed.undo_push(message="click cube")
    _add(loc)
    bpy.ops.ed.undo_push(message="box locator")
    assert bpy.ops.allset.match_transform('EXEC_DEFAULT', True, kind='ALL') == {'FINISHED'}
    cube, loc = bpy.data.objects["pCube1"], bpy.data.objects["locator1"]
    _same(cube.matrix_world, loc0, "the cube must take the locator's transform")
    bpy.ops.ed.undo()
    cube, loc = bpy.data.objects["pCube1"], bpy.data.objects["locator1"]
    _same(cube.matrix_world, cube0, "one undo puts the cube back")
    _same(loc.matrix_world, loc0, "the locator never moves")
    assert cube.select_get() and loc.select_get()
    # undo the box and redo it: the locator is the last pick again
    bpy.ops.ed.undo()
    cube, loc = bpy.data.objects["pCube1"], bpy.data.objects["locator1"]
    assert cube.select_get() and not loc.select_get()
    bpy.ops.ed.redo()
    cube, loc = bpy.data.objects["pCube1"], bpy.data.objects["locator1"]
    assert cube.select_get() and loc.select_get()
    assert _match() == {'FINISHED'}
    _same(cube.matrix_world, loc0, "after undo / redo of the box the cube still takes the locator's transform")
    _same(loc.matrix_world, loc0, "the locator never moves")


def test_file_reload_starts_from_the_selection():
    cube, loc = _scene()
    _click(cube)
    _add(loc)
    path = os.path.join(kit.ROOT, "tmp", "test_issue338_pick_order.blend")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path, check_existing=False)
    bpy.ops.wm.open_mainfile(filepath=path)
    cube, loc = bpy.data.objects["pCube1"], bpy.data.objects["locator1"]
    po = import_module(kit.MODULE + ".operators.pick_order")
    # the pick order isn't saved: after a load the active object is the last pick, like a selection made in one go
    assert [o.name for o in po.ordered(bpy.context)] == ["locator1", "pCube1"]
    _add(loc)
    _remove(loc)
    _add(loc)                       # boxed again after the load: the newest pick
    loc0 = loc.matrix_world.copy()
    assert _match() == {'FINISHED'}
    _same(cube.matrix_world, loc0, "after a reload a box still makes the boxed object the source")


def test_control_then_box_added_locator():
    # a rig control picked (Pose mode), Pose mode left (Ctrl+Tab), the locator boxed -> the control lands on it
    _clear()
    arm = _rig()
    loc = _locator("locator1", (3, 1, 0.5), (10, 20, 30))
    loc0, rig0 = loc.matrix_world.copy(), arm.matrix_world.copy()
    assert joint_selection.select(bpy.context, arm, HAND, False, False)
    bpy.context.view_layer.update()
    bpy.ops.object.mode_set(mode='OBJECT')
    assert arm.pose.bones[HAND].select and bpy.context.view_layer.objects.active is arm
    _add(loc)
    assert _match() == {'FINISHED'}
    bpy.context.view_layer.update()
    _same(snap._maya_frame(arm.pose.bones[HAND]), loc0, "the control must take the locator's transform")
    _same(loc.matrix_world, loc0, "the locator (boxed last) must stay")
    _same(arm.matrix_world, rig0, "the rig object must stay")


def test_locator_then_box_added_rig_with_a_picked_control():
    # the locator clicked, then the rig boxed in Object mode while its control is picked -> the locator follows the
    # control (a selected skeleton with picked controls stands for them)
    _clear()
    arm = _rig()
    loc = _locator("locator1", (3, 1, 0.5), (10, 20, 30))
    assert joint_selection.select(bpy.context, arm, HAND, False, False)
    bpy.context.view_layer.update()
    bpy.ops.object.mode_set(mode='OBJECT')
    hand0, rig0 = snap._maya_frame(arm.pose.bones[HAND]), arm.matrix_world.copy()
    _click(loc)
    assert not arm.select_get() and arm.pose.bones[HAND].select
    _add(arm)
    assert _match() == {'FINISHED'}
    bpy.context.view_layer.update()
    _same(loc.matrix_world, hand0, "the locator must take the control's transform")
    _same(snap._maya_frame(arm.pose.bones[HAND]), hand0, "the control (boxed last) must stay")
    _same(arm.matrix_world, rig0, "the rig object must stay")


def test_match_pivots_follows_the_box():
    cube, loc = _scene()
    loc_point = loc.matrix_world.translation.copy()
    _click(cube)
    _add(loc)
    assert bpy.ops.allset.match_pivots() == {'FINISHED'}
    bpy.context.view_layer.update()
    assert (loc.matrix_world.translation - loc_point).length < TOL, "the locator's pivot (boxed last) must stay"
    assert (cube.matrix_world.translation - loc_point).length < TOL, \
        "the cube's pivot must move onto the locator (boxed last)"
    assert (Vector(cube.location) - Vector((0, 0, 0))).length < TOL, "the cube itself must not move"
