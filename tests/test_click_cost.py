"""A click in a big scene stays light: picking a joint (and switching the lead skeleton between Object and Pose Mode)
does not make the kit walk every object of the scene — the parent rule (a hidden node hides what is below it) looks
only at the update's entries when nothing it reads changed, the Move-tool check comes before the look for skinning
meshes, and the priority test passes over meshes by their type. What a click selects and what the parent rule hides
stay the same: edits made only through Blender (no kit call) are still followed."""

from importlib import import_module
import types

import bpy
from mathutils import Matrix

import kit

dag = import_module(kit.MODULE + ".operators.dag")
js = import_module(kit.MODULE + ".operators.joint_selection")
sp = import_module(kit.MODULE + ".operators.select_priority")
layer_editor = import_module(kit.MODULE + ".ui.layer_editor")

EXTRA = 400                 # plain meshes around the rigs: the scene size a click must not scale with


class _Count:
    def __init__(self, owner, name):
        self.owner, self.name, self.calls = owner, name, 0
        self.real = getattr(owner, name)

    def __enter__(self):
        def counted(*a, **k):
            self.calls += 1
            return self.real(*a, **k)
        setattr(self.owner, self.name, counted)
        return self

    def __exit__(self, *exc):
        setattr(self.owner, self.name, self.real)


def _object_mode():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _clear():
    _object_mode()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for data in (bpy.data.armatures, bpy.data.meshes, bpy.data.curves):
        for d in list(data):
            data.remove(d)


def _rig(name, x, bones=6):
    data = bpy.data.armatures.new(name)
    rig = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    for i in range(bones):
        eb = data.edit_bones.new(f"{name}_j{i}")
        eb.head, eb.tail = (x, 0.0, 0.5 * i), (x, 0.0, 0.5 * i + 0.5)
        eb.parent = prev
        prev = eb
    bpy.ops.object.mode_set(mode='OBJECT')
    return rig


def _scene():
    """Two skeletons (the first skins a mesh), a group with children and many plain meshes."""
    _clear()
    sc = bpy.context.scene
    a, b = _rig("rigA", 0.0), _rig("rigB", 3.0)
    me = bpy.data.meshes.new("box")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
    body = bpy.data.objects.new("body", me)
    sc.collection.objects.link(body)
    body.modifiers.new("Armature", 'ARMATURE').object = a
    group = bpy.data.objects.new("group", None)
    sc.collection.objects.link(group)
    for i in range(EXTRA):
        o = bpy.data.objects.new(f"m{i}", me)
        o.location = (i % 20, 5 + i // 20, 0)
        sc.collection.objects.link(o)
        if i < 6:
            o.parent = group
    for o in sc.objects:
        o.select_set(False)
    bpy.context.view_layer.update()
    return a, b, group


def _walks():
    return _Count(dag, "sync"), _Count(dag, "_Walk"), _Count(js, "is_skinned")


def test_joint_clicks_walk_no_scene():
    a, b, _group = _scene()
    ctx = bpy.context
    bpy.context.view_layer.update()
    dag.sync()                                     # what a file load leaves: one walk of the scene
    counts = _walks()
    with counts[0] as sync, counts[1] as walk, counts[2] as skinned:
        for i in range(6):                         # like clicks alternating between the two skeletons
            ob = a if i % 2 == 0 else b
            assert js.select(ctx, ob, f"{ob.name}_j{i % 3}") is True
            bpy.context.view_layer.update()
    assert sync.calls == 0 and walk.calls == 0, ("the parent rule walked the scene", sync.calls, walk.calls)
    assert skinned.calls == 0, ("the skinning look ran without the Move tool", skinned.calls)
    # the same selection as before: the last skeleton alone, in Pose Mode, with the one picked joint
    assert ctx.mode == 'POSE' and ctx.active_object == b
    assert [o.name for o in ctx.selected_objects] == ["rigB"]
    assert [pb.name for pb in b.pose.bones if pb.select] == ["rigB_j2"]
    assert b.data.bones.active.name == "rigB_j2"
    assert not any(pb.select for pb in a.pose.bones) and a.mode == 'OBJECT'


def test_the_move_tool_still_decides_edit_or_pose():
    """With the Move tool an unskinned skeleton is picked in Edit Mode, a skinned one in Pose Mode (like before)."""
    a, b, _group = _scene()
    ctx = bpy.context
    real = js.move_tool_active
    js.move_tool_active = lambda _context: True
    try:
        js.select(ctx, b, "rigB_j1")
        assert ctx.mode == 'EDIT_ARMATURE' and b.mode == 'EDIT', ctx.mode
        assert b.data.edit_bones.active.name == "rigB_j1"
        js.select(ctx, a, "rigA_j1")
        assert ctx.mode == 'POSE' and a.mode == 'POSE', ctx.mode
    finally:
        js.move_tool_active = real
    _object_mode()
    b.pop(js.AUTO_EDIT, None)


def test_sync_reads_children_not_roots():
    """A walk of the scene asks for the hidden ancestors of objects that have a parent only."""
    a, b, group = _scene()
    with _Count(dag._Walk, "by_ancestor") as asked:
        dag.sync()
    children = sum(1 for o in bpy.context.scene.objects if o.parent is not None)
    assert asked.calls == children, (asked.calls, children)


def _upd():
    bpy.context.view_layer.update()         # looked up each time: undo replaces the view layer


def _hidden(*obs):
    return [o.hide_get() for o in obs]


def test_parent_rule_follows_blender_edits():
    """No kit call after these edits: the depsgraph update alone keeps a hidden node's descendants hidden."""
    a, b, group = _scene()
    _upd()
    kids = [o for o in bpy.context.scene.objects if o.parent == group]
    group.hide_viewport = True                     # its Visibility channel
    _upd()
    assert all(_hidden(*kids)) and all(dag.MARK in o for o in kids)
    assert not any(o.hide_viewport for o in kids), "the children's own Visibility stays on"
    kids[0].hide_set(False)                        # Blender's eye on a child of the hidden node
    _upd()
    assert kids[0].hide_get(), "a child of a hidden node came back"
    for o in kids:                                 # Alt+H: Blender shows every object again (more than a few)
        o.hide_set(False)
    _upd()
    assert all(_hidden(*kids)), _hidden(*kids)
    kids[1].name = "renamed_child"                 # a renamed child is still followed
    _upd()
    kids[1].hide_set(False)
    _upd()
    assert kids[1].hide_get()
    loose = bpy.context.scene.objects["m100"]
    loose.parent = group                           # parented from Python under the hidden node
    _upd()
    assert loose.hide_get() and dag.MARK in loose
    loose.parent = None
    _upd()
    assert not loose.hide_get() and dag.MARK not in loose
    new = bpy.data.objects.new("late_child", kids[0].data)
    new.parent = group
    bpy.context.scene.collection.objects.link(new)  # a new object under the hidden node
    _upd()
    assert new.hide_get()
    for i in range(4):                             # joint clicks in between change none of it
        ob = a if i % 2 == 0 else b
        js.select(bpy.context, ob, f"{ob.name}_j0")
        _upd()
    assert all(_hidden(*kids, new))
    _object_mode()
    group.hide_viewport = False
    _upd()
    assert not any(_hidden(*kids, new)) and not any(dag.MARK in o for o in (*kids, new))


def test_parent_rule_follows_ctrl_p_and_alt_p():
    """Blender's Ctrl+P under a node its display layer hides, then Alt+P."""
    a, b, group = _scene()
    coll = layer_editor.new_layer(bpy.context.scene, [group])
    coll.allset_layer.visible = False
    _upd()
    assert group.hide_get() and not group.hide_viewport
    loose = bpy.context.scene.objects["m200"]
    with bpy.context.temp_override(selected_editable_objects=[loose, group], active_object=group, object=group):
        bpy.ops.object.parent_set(type='OBJECT')   # Ctrl+P
    _upd()
    assert loose.parent == group and loose.hide_get() and dag.MARK in loose
    with bpy.context.temp_override(selected_editable_objects=[loose], active_object=loose, object=loose):
        bpy.ops.object.parent_clear(type='CLEAR')  # Alt+P
    _upd()
    assert loose.parent is None and not loose.hide_get() and dag.MARK not in loose


def test_few_hidden_children_come_back_hidden():
    """Blender's eye on one of a few children of a hidden node (each looked up by name, also after a rename)."""
    _scene()
    sc = bpy.context.scene
    top = bpy.data.objects.new("top", None)
    sc.collection.objects.link(top)
    kids = [sc.objects["m300"], sc.objects["m301"]]
    for o in kids:
        o.parent = top
    _upd()
    top.hide_viewport = True
    _upd()
    assert all(_hidden(*kids)) and all(dag.MARK in o for o in kids)
    kids[0].hide_set(False)
    _upd()
    assert kids[0].hide_get()
    kids[1].name = "kid_renamed"
    _upd()
    kids[1].hide_set(False)
    _upd()
    assert kids[1].hide_get()
    sc.objects["m302"].hide_set(True)              # Blender's own hide elsewhere stays the user's
    sc.objects["m302"].hide_set(False)
    _upd()
    assert not sc.objects["m302"].hide_get() and dag.MARK not in sc.objects["m302"]


def test_display_layer_and_undo_still_reach_the_children():
    a, b, group = _scene()
    kids = [o for o in bpy.context.scene.objects if o.parent == group]
    coll = layer_editor.new_layer(bpy.context.scene, [group])
    _upd()
    bpy.ops.ed.undo_push(message="layer")
    coll.allset_layer.visible = False              # the layer's V
    _upd()
    assert all(_hidden(*kids)) and all(dag.MARK in o for o in kids)
    bpy.ops.ed.undo_push(message="hidden")
    bpy.ops.ed.undo()
    _upd()
    kids = [o for o in bpy.context.scene.objects if o.parent and o.parent.name == "group"]
    assert not any(_hidden(*kids)) and not any(dag.MARK in o for o in kids)
    bpy.ops.ed.redo()
    _upd()
    kids = [o for o in bpy.context.scene.objects if o.parent and o.parent.name == "group"]
    assert all(_hidden(*kids)) and all(dag.MARK in o for o in kids)
    kids[0].hide_set(False)
    _upd()
    assert kids[0].hide_get()


def _view():
    # orthographic front view: x right, z up, 8 units across 400 px (50 px per unit)
    view = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, -10), (0, 0, 0, 1)))
    proj = Matrix(((0.25, 0, 0, 0), (0, 0.25, 0, 0), (0, 0, -0.01, 0), (0, 0, 0, 1)))
    rv3d = types.SimpleNamespace(perspective_matrix=proj @ view)
    region = types.SimpleNamespace(width=400, height=400)
    ctx = types.SimpleNamespace(space_data=None, view_layer=bpy.context.view_layer, scene=bpy.context.scene,
                                evaluated_depsgraph_get=bpy.context.evaluated_depsgraph_get)
    return ctx, region, rv3d


def test_priority_hits_pass_over_meshes_by_type():
    """The click's priority test only measures skeletons, curves and IK handles: meshes cost a type check, and the
    winners are the same with many meshes around."""
    a, b, group = _scene()
    sc = bpy.context.scene
    ik = bpy.data.objects.new("ikHandle1", None)
    sc.collection.objects.link(ik)
    ik.location = (-3, 0, 0)
    ik.empty_display_size = 0.5
    con = a.pose.bones["rigA_j3"].constraints.new('IK')
    con.target = ik
    con.influence = 0.0
    bpy.ops.curve.primitive_bezier_circle_add(radius=0.5, location=(1.5, -2, 0.5), rotation=(1.5708, 0, 0))
    circle = bpy.context.active_object
    _object_mode()
    bpy.context.view_layer.update()
    ctx, region, rv3d = _view()

    def best(x, z):
        got = sp.rank(sp.hits(ctx, region, rv3d, (200 + 50 * x, 200 + 50 * z)), sp.RADIUS_PX)
        return got and got[0]
    with _Count(sp, "kind_of") as kinds:
        assert best(0.0, 0.25) == "rigA"
        assert best(3.0, 0.75) == "rigB"
        assert best(-3.0, 0.0) == "ikHandle1"
        assert best(2.0, 0.5) == circle.name
        assert best(1.5, 0.5) is None              # inside the circle, away from its line
    ranked = 4                                     # two skeletons, the circle, the IK handle
    assert kinds.calls <= 5 * ranked, (kinds.calls, len(sc.objects))


def _reference_hits(ctx, region, rv3d, mouse):
    """Object by object, each line set projected on its own: what the priority test gives."""
    from_preselect = import_module(kit.MODULE + ".operators.preselect")
    dg = ctx.evaluated_depsgraph_get()
    targets = sp.ik_targets(ctx.scene)
    out = []
    for ob in ctx.scene.objects:
        kind = sp.kind_of(ob, targets)
        pri = sp.priority(kind)
        if pri <= sp.DEFAULT or not sp._selectable(ob, None, ctx.view_layer):
            continue
        a, b, reach = sp._segments(ob, kind, dg)
        if len(a) == 0:
            continue
        persp = rv3d.perspective_matrix
        xa, fa = from_preselect.project(a, persp, region.width, region.height)
        xb, fb = from_preselect.project(b, persp, region.width, region.height)
        import numpy as np
        width = reach * np.hypot(*(xb - xa).T) if np.any(reach) else None
        out.append((ob.name, pri, max(sp.segments_hit(mouse, xa, xb, fa & fb, width), 0.0)))
    return out


def test_curve_controls_are_read_in_one_pass():
    """Many curve controls (a Maya-style rig): one projection for all of them, the same distances and winner as
    measuring each on its own."""
    import math
    _scene()
    sc = bpy.context.scene
    for i in range(60):
        cu = bpy.data.curves.new(f"ctrl{i}", 'CURVE')
        spline = cu.splines.new('NURBS')
        spline.points.add(7)
        for k, p in enumerate(spline.points):
            ang = 2 * math.pi * k / 8
            p.co = (0.3 * math.cos(ang), 0.0, 0.3 * math.sin(ang), 1.0)
        spline.use_cyclic_u = True
        o = bpy.data.objects.new(f"ctrl{i}", cu)
        o.location = (0.7 * (i % 10) - 3.5, -1.0 + (i % 3), 0.7 * (i // 10) - 2.0)
        sc.collection.objects.link(o)
    sc.objects["ctrl7"].hide_set(True)
    sc.objects["ctrl8"].location.y = 30.0          # behind the view: no line in front
    bpy.context.view_layer.update()
    ctx, region, rv3d = _view()
    for mouse in ((200 + 50 * 0.5, 200), (163, 112), (5, 5), (200 - 50 * 3.2, 200 - 50 * 2.0)):
        want = _reference_hits(ctx, region, rv3d, mouse)
        with _Count(sp, "project") as projected:
            got = sp.hits(ctx, region, rv3d, mouse)
        assert [(n, p) for n, p, _d in got] == [(n, p) for n, p, _d in want], (got, want)
        assert all(abs(dg - dw) < 1e-9 or dg == dw for (_n, _p, dg), (_n2, _p2, dw) in zip(got, want))
        assert sp.rank(got, sp.RADIUS_PX) == sp.rank(want, sp.RADIUS_PX)
        assert projected.calls <= 2 + 2 * 2, projected.calls      # all curves once, each skeleton on its own
