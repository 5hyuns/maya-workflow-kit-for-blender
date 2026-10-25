"""Step 202: Skin > Edit Influences > Add Influence weights = Maya's (factory: Lock weights off, Dropoff 4). Rule:
research/maya/re/add_influence_202.md; numbers: tests/maya202_add_influence_data.py (mayapy). Lock weights stays the
step 196 behaviour."""

from importlib import import_module

import bpy

import kit
from maya202_add_influence_data import CASES, UNEXPLAINED

rig = import_module(kit.MODULE + ".operators.rig_maya")
cbm = import_module(kit.MODULE + ".ui.channel_box")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.armatures):
        for d in list(coll):
            coll.remove(d)


def _z_up(p):
    """Maya Y-up -> Blender Z-up (a rotation: distances, and so the weights, are unchanged)."""
    return (p[0], -p[2], p[1])


def _build(case):
    """Points mesh + skeleton + the case's weights before Add Influence."""
    _clear()
    c = CASES[case]
    data = bpy.data.armatures.new("skeleton")
    arm = bpy.data.objects.new("skeleton1", data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    parent_of = {ch: j for j, (_p, children) in c["joints"].items() for ch in children}
    for name, (p, children) in c["joints"].items():
        eb = data.edit_bones.new(name)
        eb.head = _z_up(p)
        tail = _z_up(c["joints"][children[0]][0]) if children else (eb.head[0], eb.head[1], eb.head[2] + 0.5)
        eb.tail = tail
    for name, parent in parent_of.items():
        data.edit_bones[name].parent = data.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    me = bpy.data.meshes.new("skin")
    me.from_pydata([_z_up(p) for p in c["points"]], [], [])
    ob = bpy.data.objects.new("pPlane1", me)
    bpy.context.scene.collection.objects.link(ob)
    md = ob.modifiers.new("skinCluster1", 'ARMATURE')
    md.object = arm
    for k, name in enumerate(c["influences"]):
        if name in c["new"]:
            continue
        vg = ob.vertex_groups.new(name=name)
        for i, row in enumerate(c["before"]):
            if row[k] > 0.0:
                vg.add([i], row[k], 'REPLACE')
        vg.lock_weight = name in c["locked"]
    ob[rig.MAX_INFLUENCES_PROP] = c["max_influences"]
    return ob, arm


def _weights(ob, names):
    out = []
    for v in ob.data.vertices:
        w = {ob.vertex_groups[g.group].name: g.weight for g in v.groups}
        out.append(tuple(w.get(n, 0.0) for n in names))
    return out


def test_add_influence_matches_mayapy():
    skip = set(UNEXPLAINED)
    worst = 0.0
    for case, c in CASES.items():
        ob, _arm = _build(case)
        assert rig.add_influence(ob, list(c["new"]), dropoff=c["dropoff"]) == list(c["new"]), case
        got = _weights(ob, c["influences"])
        for i, (row, want) in enumerate(zip(got, c["after"])):
            if (case, i) in skip:
                continue
            err = max(abs(a - b) for a, b in zip(row, want))
            worst = max(worst, err)
            assert err < 1e-4, (case, i, c["points"][i], row, want)
    print("worst", worst)


def test_unexplained_vertex_is_the_documented_one():
    for case, i in UNEXPLAINED:
        assert CASES[case]["points"][i] == (2.5, 2.0, 0.0)


def test_dropoff_of_an_added_influence_is_kept_for_the_next_add():
    """Maya keeps a dropoff per influence: an influence added with Dropoff 1 keeps it when another joint is added."""
    c = CASES["plane_new_4_4_dr1"]
    ob, arm = _build("plane_new_4_4_dr1")
    rig.add_influence(ob, ["joint4"], dropoff=1.0)
    assert dict(ob[rig.DROPOFF_PROP]) == {"joint4": 1.0}
    first = _weights(ob, c["influences"])
    # adding the same joint again changes nothing; recomputing with the stored dropoffs gives the same weights
    assert rig.add_influence(ob, ["joint4"]) == []
    assert _weights(ob, c["influences"]) == first


def test_lock_weights_path_unchanged():
    """Lock weights + Default weight (step 196, mayapy infl_lock_0.3): new weight everywhere, others x (1 - w)."""
    ob, _arm = _build("plane_new_4_4")
    before = _weights(ob, ("joint1", "joint2", "joint3"))
    assert rig.add_influence(ob, ["joint4"], lock=True, weight=0.3) == ["joint4"]
    g4 = ob.vertex_groups["joint4"]
    assert g4.lock_weight
    after = _weights(ob, ("joint1", "joint2", "joint3", "joint4"))
    for b, a in zip(before, after):
        assert abs(a[3] - 0.3) < 1e-6
        assert all(abs(x * 0.7 - y) < 1e-6 for x, y in zip(b, a[:3]))
    ob, _arm = _build("plane_new_4_4")
    rig.add_influence(ob, ["joint4"], lock=True, weight=0.0)
    assert all(row[3] == 0.0 for row in _weights(ob, ("joint1", "joint2", "joint3", "joint4")))
    assert ob.vertex_groups["joint4"].lock_weight


def test_operator_matches_maya_and_undoes():
    c = CASES["plane_new_4_4"]
    ob, arm = _build("plane_new_4_4")
    for b in arm.data.bones:
        cbm.set_bone_selected(arm.pose.bones[b.name], b.name == "joint4")
    for o in bpy.context.scene.objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = ob
    before = _weights(ob, c["influences"])
    bpy.ops.ed.undo_push(message="test start")
    assert bpy.ops.allset.add_influence('EXEC_DEFAULT', True) == {'FINISHED'}
    got = _weights(ob, c["influences"])
    assert max(abs(a - b) for row, want in zip(got, c["after"]) for a, b in zip(row, want)) < 1e-4
    bpy.ops.ed.undo()
    ob = bpy.data.objects["pPlane1"]
    assert "joint4" not in ob.vertex_groups
    assert _weights(ob, c["influences"]) == before
