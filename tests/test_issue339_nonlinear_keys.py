"""Issue #339: the attributes of a nonlinear deformer (Bend, Twist, Squash, Flare, Sine, Wave) key and play back like
Maya. Deform > Nonlinear > Bend on a mesh, the bend1 node expanded in the Channel Box INPUTS of the handle (the
selection after the deformer is made) or of the mesh, a value typed at frame 1 and keyed, another typed at frame 10
and keyed, then a scrub: the node's value follows its keys and the deformed mesh follows the value. Keyed with S (S
keys the channels of the deformer node open in the Channel Box, with the selection's own channels) and with Channels >
Key Selected; the keyed row reads keyed. A closed node and Shift+W leave the deformer unkeyed; Auto Key keys a keyed
deformer channel when a new value is typed."""

import math
from importlib import import_module

import bmesh
import bpy
import numpy as np
from mathutils import Matrix

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")
deformers = import_module(kit.MODULE + ".operators.deformers")
compat = import_module(kit.MODULE + ".compat")
auto_key = import_module(kit.MODULE + ".operators.auto_key")

# Deform > Nonlinear kind, the Maya attribute typed and keyed, text at frame 1, text at frame 10, the attribute's value
# for those texts (Twist's End Angle is typed in degrees and read in radians)
CASES = (
    ('BEND', "curvature", "0", "1.5", (0.0, 1.5)),
    ('TWIST', "endAngle", "0", "90", (0.0, math.radians(90.0))),
    ('SQUASH', "factor", "0", "0.8", (0.0, 0.8)),
    ('FLARE', "endFlareX", "1", "2", (1.0, 2.0)),
    ('SINE', "amplitude", "0", "0.3", (0.0, 0.3)),
    ('WAVE', "amplitude", "0", "0.3", (0.0, 0.3)),
)
SCRUB = (10, 5, 1, 7, 10, 3, 1)


def _fresh():
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.actions):
        for d in list(coll):
            coll.remove(d)
    cb.reset_open()
    cb.set_selected_channels([])
    bpy.context.scene.allset_auto_key = False
    bpy.context.scene.frame_set(1)


def _select(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _column():
    """A 1 x 1 x 3 box with many points along its height (bend / twist / squash show on it)."""
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob = bpy.context.active_object
    ob.name, ob.data.name = "pCube1", "pCubeShape1"
    ob.data.transform(Matrix.Diagonal((1.0, 1.0, 3.0, 1.0)))
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=5, use_grid_fill=True)
    bm.to_mesh(ob.data)
    bm.free()
    bpy.context.view_layer.update()
    _select(ob)
    return ob


def _make(kind, lead_is_handle=True):
    """(mesh, handle, modifier, lead) after Deform > Nonlinear > ``kind`` on the column; the lead's deformer node is
    expanded in the Channel Box."""
    _fresh()
    mesh = _column()
    assert bpy.ops.allset.deformer(kind=kind) == {'FINISHED'}, kind
    handle = bpy.context.view_layer.objects.active
    assert handle is not mesh and handle.name.endswith("Handle"), handle.name
    md = next(m for m in mesh.modifiers if deformers.base_of(m) is not None)
    lead = handle if lead_is_handle else mesh
    _select(lead)
    cb.set_open(lead, cb.mod_node(md))      # the user clicked the node open in INPUTS
    cb.rebuild_rows()
    return mesh, handle, md, lead


def _row(attr):
    rows = [r for r in bpy.context.scene.allset_cb.rows if r.kind == "INPUT" and r.name == deformers.PREFIX + attr]
    assert rows, (attr, [(r.kind, r.name) for r in bpy.context.scene.allset_cb.rows])
    return rows[0]


def _points(mesh):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    return co.reshape(-1, 3)


def _type(attr, text):
    _row(attr).text = text
    bpy.context.view_layer.update()


def _key(how, frame, attr, text):
    bpy.context.scene.frame_set(frame)
    _type(attr, text)
    if how == "S":
        cb.set_selected_channels([])     # nothing picked in the Channel Box: S keys every keyable channel
        assert bpy.ops.allset.set_key() == {'FINISHED'}
    else:
        cb.set_selected_channels([cb.row_key(_row(attr))])
        assert bpy.ops.allset.cb_key_selected() == {'FINISHED'}
        cb.set_selected_channels([])


def _keys(fc):
    return [(round(k.co.x), round(k.co.y, 5)) for k in fc.keyframe_points]


def _value(md, attr):
    return deformers.attr(md, deformers.PREFIX + attr).get(md)


def _case(kind, attr, text1, text10, values, how, lead_is_handle):
    tag = f"{kind} {attr} {how} ({'handle' if lead_is_handle else 'mesh'})"
    mesh, handle, md, lead = _make(kind, lead_is_handle)
    key = cb.row_key(_row(attr))
    # what the deformation looks like at either value, before any key
    _type(attr, text10)
    want10 = _points(mesh)
    _type(attr, text1)
    want1 = _points(mesh)
    assert np.abs(want10 - want1).max() > 0.05, (tag, "the two values deform the column differently")
    _key(how, 1, attr, text1)
    _key(how, 10, attr, text10)
    fc = cb.fcurve(lead, key)
    assert fc is not None, (tag, "no curve", [f.data_path for f in compat.id_fcurves(mesh)])
    # the curve is the deformed mesh's (where the modifier is), also when the handle is the lead
    on_mesh = any(f.as_pointer() == fc.as_pointer() for f in compat.id_fcurves(mesh))
    assert on_mesh and fc.data_path.startswith(f'modifiers["{md.name}"].'), (tag, fc.data_path)
    assert [round(k.co.x) for k in fc.keyframe_points] == [1, 10], (tag, _keys(fc))
    assert fc.keyframe_points[0].co.y != fc.keyframe_points[1].co.y, (tag, _keys(fc))
    raw = [round(v, 5) for v in values]
    for frame in SCRUB:
        bpy.context.scene.frame_set(frame)
        want = fc.evaluate(frame)
        got = mesh.path_resolve(fc.data_path)
        got = got[fc.array_index] if hasattr(got, "__len__") else got
        assert abs(got - want) < 1e-5, (tag, frame, "the modifier follows its curve", got, want)
        state = cb.channel_state(lead, key)
        assert state == ('KEYED' if frame in (1, 10) else 'ANIMATED'), (tag, frame, state)
        pts = _points(mesh)
        if frame == 1:
            assert np.abs(pts - want1).max() < 1e-4, (tag, frame, "deformed like the frame 1 value")
            assert abs(_value(md, attr) - raw[0]) < 1e-4, (tag, frame, _value(md, attr), raw)
        elif frame == 10:
            assert np.abs(pts - want10).max() < 1e-4, (tag, frame, "deformed like the frame 10 value")
            assert abs(_value(md, attr) - raw[1]) < 1e-4, (tag, frame, _value(md, attr), raw)
        else:
            v = _value(md, attr)
            lo, hi = sorted(raw)
            assert lo + 1e-4 < v < hi - 1e-4, (tag, frame, "between the keys", v, raw)
            assert np.abs(pts - want1).max() > 1e-3 and np.abs(pts - want10).max() > 1e-3, (tag, frame)
    return mesh, handle, md, lead, key


def test_s_keys_the_open_nonlinear_node_from_its_handle():
    """The selection after Deform > Nonlinear is the handle; its INPUTS show the deformer node. S keys the node's
    channels while it is open, along with the handle's own."""
    for kind, attr, t1, t10, values in CASES:
        mesh, handle, md, lead, _key_ = _case(kind, attr, t1, t10, values, "S", True)
        assert cb.fcurve(handle, "tx") is not None, (kind, "S keys the handle's own channels too")
        # every channel of the open node is keyed (Low / High Bound too), on the deformed mesh
        for a in deformers.attrs(md):
            k = cb.input_key(md.type, 0, deformers.PREFIX + a.key)
            assert cb.fcurve(handle, k) is not None, (kind, a.key, "keyed with the node")


def test_s_keys_the_open_nonlinear_node_from_the_mesh():
    for kind, attr, t1, t10, values in CASES:
        mesh, _handle, _md, _lead, _key_ = _case(kind, attr, t1, t10, values, "S", False)
        assert cb.fcurve(mesh, "tx") is not None, kind


def test_key_selected_keys_a_nonlinear_channel():
    """Channels > Key Selected on the deformer's row keys that channel only."""
    for lead_is_handle in (True, False):
        for kind, attr, t1, t10, values in CASES:
            mesh, handle, md, lead, key = _case(kind, attr, t1, t10, values, "K", lead_is_handle)
            others = [cb.input_key(md.type, 0, deformers.PREFIX + a.key) for a in deformers.attrs(md)
                      if a.key != attr]
            # Flare's End Flare X / Z are one Blender value: keying one keys the other
            assert all(cb.fcurve(lead, k) is None for k in others if not k.endswith("endFlareZ")), (kind, others)
            assert cb.fcurve(lead, "tx") is None, (kind, "only the selected channel")


def test_closed_node_and_shift_w_leave_the_deformer_unkeyed():
    """Like the constraint weights: S keys a deformer node's channels only while it is open in the Channel Box;
    Shift+W / E / R key only Translate / Rotate / Scale."""
    mesh, handle, md, lead = _make('BEND')
    key = cb.input_key(md.type, 0, deformers.PREFIX + "curvature")
    assert bpy.ops.allset.set_key(channels='TRANSLATE') == {'FINISHED'}
    assert cb.fcurve(handle, "tx") is not None and cb.fcurve(handle, key) is None
    cb.reset_open()
    cb.rebuild_rows()
    bpy.context.scene.frame_set(5)
    assert bpy.ops.allset.set_key() == {'FINISHED'}
    assert cb.fcurve(handle, "rx") is not None, "S keys the handle"
    assert cb.fcurve(handle, key) is None, "a closed deformer node stays unkeyed"
    assert mesh.animation_data is None or not list(compat.id_fcurves(mesh)), "nothing keyed on the mesh"


def test_auto_key_keys_a_keyed_deformer_channel():
    """Maya Auto Key: a new value typed in a keyed deformer channel at another frame sets a key there."""
    for lead_is_handle in (True, False):
        mesh, handle, md, lead = _make('BEND', lead_is_handle)
        key = cb.row_key(_row("curvature"))
        _key("K", 1, "curvature", "0")
        bpy.context.scene.allset_auto_key = True
        bpy.context.scene.frame_set(8)
        _type("curvature", "1.2")
        if bpy.app.timers.is_registered(auto_key._flush):      # the Auto Key timer, run now (none in background)
            bpy.app.timers.unregister(auto_key._flush)
        auto_key._flush()
        fc = cb.fcurve(lead, key)
        assert fc is not None and _keys(fc) == [(1, 0.0), (8, 1.2)], (lead_is_handle, fc and _keys(fc))
        assert cb.fcurve(lead, "tx") is None, "Auto Key keys only the changed channel"
        bpy.context.scene.allset_auto_key = False


def test_break_connections_on_a_driven_deformer_channel_from_the_handle():
    """A driver on the deformer's value is found from the handle too, and Channels > Break Connections removes it
    from the deformed mesh."""
    mesh, handle, md, lead = _make('BEND')
    key = cb.row_key(_row("curvature"))
    d = md.driver_add("angle")
    d.driver.expression = "0.5"
    assert cb.driver(handle, key) is not None and cb.channel_state(handle, key) == 'DRIVEN'
    cb.set_selected_channels([key])
    assert bpy.ops.allset.cb_break_connections() == {'FINISHED'}
    assert cb.driver(handle, key) is None and not mesh.animation_data.drivers
