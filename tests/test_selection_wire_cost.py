"""Hundreds of selected objects keep the selection wire light: the depth offset of every highlighted object is
computed for all of them at once, with the same result as one by one (boxes seen from the front and obliquely, thin
plates, flat cards, objects behind the eye or crossing a clip plane, empties and curves)."""

import math
import random
from importlib import import_module

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
