"""Hundreds of selected objects keep the selection wire light: the depth offset of every highlighted object is
computed for all of them at once, with the same result as one by one (boxes seen from the front and obliquely, thin
plates, flat cards, objects behind the eye or crossing a clip plane, empties and curves). The highlighted hierarchy
(every descendant of a selected object, in the colour of its nearest selected ancestor) is found with one look at the
file's parents, not one look through every object of the file for each highlighted object."""

import math
import random
import time
from importlib import import_module
from types import SimpleNamespace

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

import kit

wire = import_module(kit.MODULE + ".ui.selection_wire")


def _perspective(fov=0.9, aspect=1.6, near=0.1, far=200.0):
    f = 1.0 / math.tan(fov / 2)
    return Matrix(((f / aspect, 0, 0, 0), (0, f, 0, 0),
                   (0, 0, (far + near) / (near - far), 2 * far * near / (near - far)), (0, 0, -1, 0)))


def _view():
    eye = Vector((6.0, -14.0, 5.0))
    rot = (Vector((0, 0, 0)) - eye).to_track_quat('-Z', 'Y').to_matrix().to_4x4()
    return (Matrix.Translation(eye) @ rot).inverted()


def test_all_at_once_matches_one_by_one():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    rng = random.Random(4)
    objs = []
    mesh = bpy.data.meshes.new("box")
    mesh.from_pydata([(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], [],
                     [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    card = bpy.data.meshes.new("card")
    card.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
    curve = bpy.data.curves.new("crv", 'CURVE')
    spline = curve.splines.new('POLY')
    spline.points.add(2)
    for i, p in enumerate(spline.points):
        p.co = (i, 0.3 * i, 0, 1)
    for i in range(160):
        data = (mesh, card, curve, None)[i % 4]
        ob = bpy.data.objects.new(f"o{i}", data)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = (rng.uniform(-30, 30), rng.uniform(-30, 30), rng.uniform(-8, 8))
        ob.rotation_euler = Euler((rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(-3, 3)))
        s = rng.choice((1.0, 0.02, 3.0))
        ob.scale = (rng.uniform(0.2, 2.0), rng.uniform(0.2, 2.0), s)       # thin plates and big boxes
        objs.append(ob)
    near = bpy.data.objects.new("crossing", mesh)          # crosses the near plane
    bpy.context.scene.collection.objects.link(near)
    near.location = (6.0, -14.0, 5.0)
    objs.append(near)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pm = _perspective() @ _view()
    for viewport in ((1280, 800), (300, 900), (0, 800)):
        want = [wire.depth_bias(ob, dg, pm, viewport) for ob in objs]
        got = wire.depth_biases(objs, dg, pm, viewport)
        assert len(got) == len(want)
        for ob, g, w in zip(objs, got, want):
            # one by one projects the corners in single precision: a thin plate's depth separation (a few
            # millionths) differs by a few units in the last place of depths near 1
            assert (g == 0.0) == (w == 0.0), (ob.name, viewport, g, w)
            slack = wire.DEPTH_BIAS_THIN_SPAN * 4 * 2.0 ** -23
            assert abs(g - w) <= 0.02 * max(abs(w), abs(g)) + slack, (ob.name, viewport, g, w)
        if viewport[0] > 0:
            assert sum(w > 0 for w in want) > 20 and sum(w == 0 for w in want) > 5, "both kinds are covered"
    assert wire.depth_biases([], dg, pm, (100, 100)) == []
    few = objs[:wire.ARRAY_FROM - 1]        # a few objects: one by one
    assert wire.depth_biases(few, dg, pm, (1280, 800)) == [wire.depth_bias(o, dg, pm, (1280, 800)) for o in few]


def test_a_moved_rig_keeps_its_meshes_edges():
    """Moving a skeleton re-evaluates the mesh it deforms: the highlighted mesh's wire reads its points again but
    keeps its edges; an edit of the mesh itself, or a modifier that can change its edges, reads them again."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    arm = bpy.data.objects.new("rig", bpy.data.armatures.new("rig"))
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.data.edit_bones.new("b")
    eb.tail = (0, 0, 2)
    bpy.ops.object.mode_set(mode='OBJECT')
    me = bpy.data.meshes.new("skin")
    me.from_pydata([(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (0, 2)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    skin = bpy.data.objects.new("skin", me)
    bpy.context.scene.collection.objects.link(skin)
    group = skin.vertex_groups.new(name="b")
    group.add(list(range(8)), 1.0, 'REPLACE')
    skin.modifiers.new("Armature", 'ARMATURE').object = arm
    pb = arm.pose.bones["b"]
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (0.6, 0.0, 0.0)          # posed and not parented: moving the rig moves the points
    bpy.context.view_layer.update()
    assert wire.keeps_edges(skin)
    uid = skin.session_uid

    def read():
        co, ed = wire.edges_of(skin, bpy.context.evaluated_depsgraph_get())
        wire._batches[uid] = (None, len(ed))
        return co

    first = read()
    kept = wire._edges[uid]
    arm.location.y += 0.5
    bpy.context.view_layer.update()
    assert uid not in wire._batches, "the points moved: the batch is made again"
    assert wire._edges.get(uid) is kept, "the edges are kept"
    moved = read()
    assert not np.array_equal(first, moved) and wire._edges.get(uid) is kept
    me.vertices[0].co.x -= 0.25                                   # the mesh itself edited
    me.update()
    bpy.context.view_layer.update()
    assert uid not in wire._edges, "an edit of the mesh reads its edges again"
    read()
    skin.modifiers.new("Subdivision", 'SUBSURF')                  # can change the edges
    bpy.context.view_layer.update()
    assert uid not in wire._edges
    wire._batches.clear()
    wire._edges.clear()


def _view_space():
    return next(a.spaces.active for s in bpy.data.screens for a in s.areas if a.type == 'VIEW_3D')


def _ctx(space):
    c = bpy.context
    return SimpleNamespace(space_data=space, screen=None, view_layer=c.view_layer,
                           selected_objects=c.selected_objects, scene=c.scene)


def _rule(context):
    """The highlight rule written out plainly: each selected object in Object Mode and, under it, every descendant that
    isn't selected itself, in the colour of its nearest selected ancestor (lead = the active object); drawn when it is
    a wire type in Object Mode and shown in the view."""
    space, active = context.space_data, context.view_layer.objects.active
    out, seen = [], set()

    def visit(ob, lead):
        if ob.name in seen:
            return
        seen.add(ob.name)
        if ob.type in wire.WIRE_TYPES and ob.mode == 'OBJECT' and ob.visible_get(viewport=space):
            out.append((ob.name, lead))
        for child in ob.children:
            if not child.select_get():
                visit(child, lead)
    for ob in context.selected_objects:
        if ob.mode == 'OBJECT':
            visit(ob, ob == active)
    return out


class _ChildrenCalls:
    """Counts ``Object.children`` reads (each one looks through every object of the file)."""

    def __enter__(self):
        import _bpy_types
        self.owner, self.calls = _bpy_types.Object, 0
        self.real = self.owner.__dict__["children"]

        def counted(ob):
            self.calls += 1
            return self.real.fget(ob)
        self.owner.children = property(counted)
        return self

    def __exit__(self, *exc):
        self.owner.children = self.real


def _mesh_ob(name, parent=None, data=None, link=True):
    if data is None:
        data = bpy.data.meshes.new(name)
        data.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0)], [], [(0, 1, 2)])
    ob = bpy.data.objects.new(name, data)
    if link:
        bpy.context.scene.collection.objects.link(ob)
    ob.parent = parent
    return ob


def test_hierarchy_highlight_follows_the_nearest_selected_ancestor():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    group = bpy.data.objects.new("group1", None)                 # a selected empty: no wire of its own
    bpy.context.scene.collection.objects.link(group)
    c1 = _mesh_ob("pCube1", group)
    _mesh_ob("pCube1a", c1)
    crv = bpy.data.curves.new("curve1", 'CURVE')
    spline = crv.splines.new('POLY')
    spline.points.add(1)
    spline.points[1].co = (1, 0, 0, 1)
    curve = bpy.data.objects.new("curve1", crv)
    bpy.context.scene.collection.objects.link(curve)
    curve.parent = group
    off = _mesh_ob("offScene", group, link=False)                # in the file, not in the scene
    _mesh_ob("farKid", off)
    lead = _mesh_ob("pCube2")
    c3 = _mesh_ob("pCube3", lead)
    c4 = _mesh_ob("pCube4", c3)                                  # selected: keeps its own colour
    _mesh_ob("pCube5", c4)
    hid = _mesh_ob("hidden", lead)
    _mesh_ob("hidKid", hid)
    loose = _mesh_ob("pCube6")
    _mesh_ob("pCube7", loose)
    rig = bpy.data.objects.new("rig", bpy.data.armatures.new("rig"))
    bpy.context.scene.collection.objects.link(rig)
    _mesh_ob("skin", rig)
    bpy.context.view_layer.update()
    hid.hide_set(True)
    for ob in bpy.context.view_layer.objects:
        ob.select_set(ob in (group, lead, c4, rig))
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')                          # a picked control: no hierarchy highlight
    bpy.context.view_layer.objects.active = lead
    space = _view_space()
    try:
        ctx = _ctx(space)
        got = [(o.name, is_lead) for o, is_lead in wire.highlighted(ctx)]
        assert got == _rule(ctx), (got, _rule(ctx))
        assert dict(got) == {"pCube1": False, "pCube1a": False, "curve1": False, "farKid": False,
                             "pCube2": True, "pCube3": True, "pCube4": False, "pCube5": False, "hidKid": True}, got
        shown = space.show_object_viewport_curve
        space.show_object_viewport_curve = False                  # this view hides curves
        try:
            got = [(o.name, is_lead) for o, is_lead in wire.highlighted(_ctx(space))]
            assert got == _rule(_ctx(space)) and "curve1" not in dict(got), got
        finally:
            space.show_object_viewport_curve = shown
    finally:
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='OBJECT')


def test_highlight_looks_at_the_files_parents_once():
    """600 selected among 2,000 objects (chains of 5): asking each highlighted object for its children looked through
    all 2,000 objects every time (600 x 2,000); the hierarchy is now read once."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("shared")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0)], [], [(0, 1, 2)])
    obs, parent = [], None
    for i in range(2000):
        parent = _mesh_ob(f"o{i:04d}", parent if i % 5 else None, data=me)
        obs.append(parent)
    bpy.context.view_layer.update()
    for i, ob in enumerate(obs):
        ob.select_set(i % 10 < 3)                                 # chain heads and some links
    bpy.context.view_layer.objects.active = obs[0]
    ctx = _ctx(_view_space())
    want = _rule(ctx)
    with _ChildrenCalls() as children:
        t0 = time.perf_counter()
        got = [(o.name, is_lead) for o, is_lead in wire.highlighted(ctx)]
        dt = (time.perf_counter() - t0) * 1000
    print(f"highlighted {len(got)} of 2000 objects ({len(ctx.selected_objects)} selected): {dt:.2f} ms, "
          f"{children.calls} Object.children reads")
    assert got == want and len(got) == 1000
    assert children.calls == 0, f"{children.calls} looks through every object of the file"
    assert dt < 60.0, f"{dt:.1f} ms"


def test_posed_skeleton_reads_no_parents():
    """A skeleton picked in Pose Mode highlights no hierarchy (its child meshes aren't a selected hierarchy), so a
    redraw during a pose drag doesn't look through every object of the file for the parents; an object picked in
    Object Mode next to it still gets its hierarchy, read once."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("shared")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0)], [], [(0, 1, 2)])
    for i in range(1500):
        _mesh_ob(f"o{i:04d}", data=me)
    rig = bpy.data.objects.new("rig", bpy.data.armatures.new("rig"))
    bpy.context.scene.collection.objects.link(rig)
    _mesh_ob("skin", rig, data=me)
    box = _mesh_ob("box", data=me)
    _mesh_ob("boxKid", box, data=me)
    bpy.context.view_layer.update()
    for ob in bpy.context.view_layer.objects:
        ob.select_set(ob == rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')
    real, calls = wire.children_map, [0]

    def counted():
        calls[0] += 1
        return real()
    wire.children_map = counted
    try:
        ctx = _ctx(_view_space())
        assert wire.highlighted(ctx) == [] == _rule(ctx)
        assert calls[0] == 0, f"{calls[0]} looks through every object of the file for a posed skeleton"
        box.select_set(True)                                      # an Object Mode pick beside the posed skeleton
        ctx = _ctx(_view_space())
        got = [(o.name, is_lead) for o, is_lead in wire.highlighted(ctx)]
        assert got == _rule(ctx) == [("box", False), ("boxKid", False)], got
        assert calls[0] == 1
    finally:
        wire.children_map = real
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='OBJECT')


def test_world_matrices_and_kept_boxes_match_reading_each_object():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    rng = random.Random(7)
    objs, parent = [], None
    for i in range(40):
        ob = _mesh_ob(f"m{i}", parent if i % 3 else None)
        ob.location = (rng.uniform(-9, 9), rng.uniform(-9, 9), rng.uniform(-9, 9))
        ob.rotation_euler = Euler((rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(-3, 3)))
        ob.scale = (rng.uniform(0.1, 3), rng.uniform(0.1, 3), rng.uniform(0.1, 3))
        objs.append(ob)
        parent = ob
    bpy.context.view_layer.update()
    for some in (objs[::-1], objs[5:6]):                         # many of the file's objects, one of them
        worlds, ok = wire.world_matrices(some)
        assert ok.all()
        for ob, got in zip(some, worlds):
            assert got.ravel().tolist() == [v for row in ob.matrix_world for v in row], ob.name
    dg = bpy.context.evaluated_depsgraph_get()
    pm = _perspective() @ _view()
    boxes = [wire._bounds(ob, dg) for ob in objs]
    assert wire.depth_biases(objs, dg, pm, (1280, 800), boxes=boxes) == wire.depth_biases(objs, dg, pm, (1280, 800))
