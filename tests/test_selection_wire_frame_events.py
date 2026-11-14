"""A frame change keeps the selection wire of every object whose evaluated shape stays the same and drops the wire of
every object whose shape changed (skinned, wave, geometry nodes on the scene time, hooked, animated
modifier, cloth): with no handler writing during the frame change, the wires to drop come from the frame's own
update, and no object is asked about one by one. A frame change handler that writes (a script posing a skeleton
every frame) brings back the object-by-object look, so a mesh that skeleton deforms still gets its new wire. So do a
depsgraph update since the last frame change (its handlers may have written too), a window on another view layer
(its depsgraph evaluates the frame on its own) and a kit frame handler whose last look for its helpers is out of
date (it looks again, and may write)."""

import hashlib
import math
from importlib import import_module
from types import SimpleNamespace

import bpy
import numpy as np

import kit

wire = import_module(kit.MODULE + ".ui.selection_wire")


def _clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    wire._batches.clear()
    wire._edges.clear()
    wire._used.clear()
    wire._draws[0] = 0
    wire._updated[0] = False


def _link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _grid(name, loc, n=4):
    me = bpy.data.meshes.new(name)
    verts = [(i / n - 0.5, j / n - 0.5, 0.0) for j in range(n + 1) for i in range(n + 1)]
    faces = [(j * (n + 1) + i, j * (n + 1) + i + 1, (j + 1) * (n + 1) + i + 1, (j + 1) * (n + 1) + i)
             for j in range(n) for i in range(n)]
    me.from_pydata(verts, [], faces)
    ob = _link(bpy.data.objects.new(name, me))
    ob.location = loc
    return ob


def _rig(name, loc, keyed):
    rig = _link(bpy.data.objects.new(name, bpy.data.armatures.new(name)))
    rig.location = loc
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    b = rig.data.edit_bones.new("b")
    b.head, b.tail = (0, 0, -0.6), (0, 0, 0.6)
    bpy.ops.object.mode_set(mode='OBJECT')
    pb = rig.pose.bones["b"]
    pb.rotation_mode = 'XYZ'
    if keyed:
        pb.keyframe_insert("rotation_euler", frame=1)
        pb.rotation_euler = (0.8, 0.3, 0)
        pb.keyframe_insert("rotation_euler", frame=12)
    return rig


def _skinned(name, loc, rig):
    ob = _grid(name, loc)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.vertex_groups.new(name="b").add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
    ob.modifiers.new("Armature", 'ARMATURE').object = rig
    return ob


def _scene():
    _clear()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 30
    obs = [_skinned("skinned", (0, 0, 0), _rig("rig", (0, 0, 0), True))]
    ob = _grid("shape", (3, 0, 0))
    ob.shape_key_add(name="Basis")
    k = ob.shape_key_add(name="K")
    for i, v in enumerate(k.data):
        v.co.z += 0.3 * (i % 3)
    k.keyframe_insert("value", frame=1)
    k.value = 1.0
    k.keyframe_insert("value", frame=12)
    obs.append(ob)
    ob = _grid("wave", (6, 0, 0))
    ob.modifiers.new("Wave", 'WAVE')
    obs.append(ob)
    ob = _grid("time_nodes", (9, 0, 0))
    ng = bpy.data.node_groups.new("time_nodes", 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi, go = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
    sp, st, xyz = (ng.nodes.new(t) for t in ("GeometryNodeSetPosition", "GeometryNodeInputSceneTime",
                                             "ShaderNodeCombineXYZ"))
    ng.links.new(st.outputs["Seconds"], xyz.inputs["Z"])
    ng.links.new(xyz.outputs["Vector"], sp.inputs["Offset"])
    ng.links.new(gi.outputs[0], sp.inputs["Geometry"])
    ng.links.new(sp.outputs["Geometry"], go.inputs[0])
    ob.modifiers.new("GN", 'NODES').node_group = ng
    obs.append(ob)
    ob = _grid("hooked", (0, 3, 0))
    emp = _link(bpy.data.objects.new("hook_target", None))
    emp.keyframe_insert("location", frame=1)
    emp.location = (0, 0, 1)
    emp.keyframe_insert("location", frame=12)
    m = ob.modifiers.new("Hook", 'HOOK')
    m.object = emp
    m.vertex_indices_set([0, 1, 2])
    obs.append(ob)
    ob = _grid("keyed_modifier", (3, 3, 0))
    m = ob.modifiers.new("Displace", 'DISPLACE')
    m.strength = 0.0
    m.keyframe_insert("strength", frame=1)
    m.strength = 1.0
    m.keyframe_insert("strength", frame=12)
    obs.append(ob)
    ob = _grid("cloth", (6, 3, 1))
    ob.modifiers.new("Cloth", 'CLOTH')
    obs.append(ob)
    ob = _grid("still_subsurf", (9, 3, 0))
    ob.modifiers.new("Subsurf", 'SUBSURF')
    obs.append(ob)
    obs.append(_grid("still", (12, 3, 0)))
    obs.append(_skinned("posed_by_script", (0, 9, 0), _rig("script_rig", (0, 9, 0), False)))
    return obs


def _shape(ob, dg):
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    a = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", a)
    ev.to_mesh_clear()
    return hashlib.sha1(a.tobytes()).hexdigest()


def _frames(obs, frames):
    """[(objects whose wire went, objects whose shape changed)] of each frame change, every object holding a wire."""
    sc = bpy.context.scene
    sc.frame_set(1)
    dg = bpy.context.evaluated_depsgraph_get()
    before = {ob.name: _shape(ob, dg) for ob in obs}
    out = []
    for f in frames:
        for ob in obs:
            wire._batches[ob.session_uid] = (None, 0, None)
        wire._draws[0] = 0
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        now = {ob.name: _shape(ob, dg) for ob in obs}
        gone = {ob.name for ob in obs if ob.session_uid not in wire._batches}
        out.append((gone, {n for n in now if now[n] != before[n]}))
        before = now
    return out


def _asked_frames(obs, frames):
    """(``_frames``, the names of the objects asked about one by one)"""
    real, asked = wire.time_dependent, []

    def counted(ob, *args):
        asked.append(ob.name)
        return real(ob, *args)
    wire.time_dependent = counted
    try:
        rows = _frames(obs, frames)
    finally:
        wire.time_dependent = real
    return rows, asked


def test_a_frame_change_drops_the_changed_wires_from_its_update():
    obs = _scene()
    rows, asked = _asked_frames(obs, range(2, 14))
    for i, (gone, changed) in enumerate(rows):
        assert changed <= gone, f"frame {i + 2}: {sorted(changed - gone)} changed shape but kept their wire"
        assert not gone & {"still", "still_subsurf"}, f"frame {i + 2}: a still object lost its wire: {sorted(gone)}"
    moving = set().union(*(changed for _gone, changed in rows))
    assert {"skinned", "wave", "time_nodes", "hooked", "keyed_modifier", "cloth"} <= moving, moving
    assert not asked, f"{len(asked)} objects asked about one by one ({sorted(set(asked))[:6]})"
    _clear()


def test_a_frame_handler_that_writes_brings_back_the_object_by_object_look():
    obs = _scene()
    script_rig = bpy.data.objects["script_rig"]

    def pose_every_frame(scene, _dg=None):
        script_rig.pose.bones["b"].rotation_euler = (0.05 * scene.frame_current, 0, 0)

    bpy.app.handlers.frame_change_post.append(pose_every_frame)
    try:
        assert not wire._frame_writers_idle(bpy.context.scene)
        rows = _frames(obs, range(2, 8))
    finally:
        bpy.app.handlers.frame_change_post.remove(pose_every_frame)
    for i, (gone, changed) in enumerate(rows):
        assert "posed_by_script" in changed, f"frame {i + 2}: the script's pose didn't move the mesh"
        assert changed <= gone, f"frame {i + 2}: {sorted(changed - gone)} changed shape but kept their wire"
    _clear()


def test_a_depsgraph_update_since_the_last_frame_brings_back_the_object_by_object_look():
    """A ``depsgraph_update_post`` handler that writes has Blender evaluate a second time, unseen: a mesh posed that
    way may keep an old wire until the next frame change, which drops it as before."""
    obs = _scene()
    sc = bpy.context.scene
    sc.frame_set(1)
    posed, script_rig = bpy.data.objects["posed_by_script"], bpy.data.objects["script_rig"]
    before = _shape(posed, bpy.context.evaluated_depsgraph_get())
    for ob in obs:
        wire._batches[ob.session_uid] = (None, 0, None)

    def pose_on_update(_scene, _dg=None):
        pb = script_rig.pose.bones["b"]
        if abs(pb.rotation_euler.x - 0.7) > 1e-6:
            pb.rotation_euler.x = 0.7

    bpy.app.handlers.depsgraph_update_post.append(pose_on_update)
    try:
        bpy.data.objects["still"].location.x += 0.5
        dg = bpy.context.evaluated_depsgraph_get()
    finally:
        bpy.app.handlers.depsgraph_update_post.remove(pose_on_update)
    assert _shape(posed, dg) != before, "the handler's pose didn't move the mesh"
    sc.frame_set(2)
    assert posed.session_uid not in wire._batches, "the frame change kept the wire the update before it left behind"
    _clear()


def test_a_window_on_another_view_layer_brings_back_the_object_by_object_look():
    obs = _scene()
    sc = bpy.context.scene
    other = sc.view_layers.new("other")
    windows = [SimpleNamespace(scene=sc, view_layer=bpy.context.view_layer)]
    real = wire._windows
    wire._windows = lambda: windows
    try:
        assert wire._only_depsgraph(sc, bpy.context.evaluated_depsgraph_get())
        windows.append(SimpleNamespace(scene=sc, view_layer=other))
        assert not wire._only_depsgraph(sc, bpy.context.evaluated_depsgraph_get())
        rows, asked = _asked_frames(obs, range(2, 5))
    finally:
        wire._windows = real
        sc.view_layers.remove(other)
    assert asked, "the frame changes dropped wires from one depsgraph's update while a window draws another"
    for i, (gone, changed) in enumerate(rows):
        assert changed <= gone, f"frame {i + 2}: {sorted(changed - gone)} changed shape but kept their wire"
    _clear()


def test_a_kit_frame_handler_with_an_old_look_for_its_helpers_counts_as_writing():
    """The skeleton RP handles, normal / tangent constraints and pins look for their helpers again on a frame change
    when objects came or went since their last look, and may write then."""
    _scene()
    sc = bpy.context.scene
    sc.frame_set(1)           # each handler looks at the file as it is now
    assert wire._frame_writers_idle(sc)
    keys = ("operators.ik_rp:_on_frame", "operators.constrain_199:_on_frame", "operators.pins_205:_on_frame")
    for key in keys:
        assert wire._idle_writer(key, sc, []), key
    extra = bpy.data.objects.new("made_since", None)
    try:
        for key in keys:
            assert not wire._idle_writer(key, sc, []), f"{key}: an object made since its last look"
        assert not wire._frame_writers_idle(sc)
        sc.frame_set(2)
        assert wire._frame_writers_idle(sc), "the handlers looked again on the frame change"
    finally:
        bpy.data.objects.remove(extra)
    rp = import_module(kit.MODULE + ".operators.ik_rp")
    sc.frame_set(1)
    saved = rp._found[0]
    rp._found[0] = None       # a look that failed
    try:
        assert not wire._idle_writer("operators.ik_rp:_on_frame", sc, [])
    finally:
        rp._found[0] = saved
    _clear()
