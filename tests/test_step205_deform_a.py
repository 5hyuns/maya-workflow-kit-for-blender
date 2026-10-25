"""Step 205 lane A (#112): Maya Deform > Tension / Solidify / Sculpt as kit Geometry Nodes deformers
(operators/deformers_205a.py). Ground truth: tests/maya205_deform_data.py (Maya 2022 mayapy, research/maya/re/
deform_205.md); every "O" case must match within its tol (1e-4); "U" cases only print their residual."""

from importlib import import_module

import bpy
from mathutils import Matrix, Vector

import kit
import maya205_deform_data as data

dfa = import_module(kit.MODULE + ".operators.deformers_205a")
deformers = import_module(kit.MODULE + ".operators.deformers")
wire = import_module(kit.MODULE + ".operators.wire_deformer")
history = import_module(kit.MODULE + ".operators.history")
cb = import_module(kit.MODULE + ".ui.channel_box")
ae = import_module(kit.MODULE + ".ui.attribute_editor")

TENSION_INPUT = {"smoothingIterations": "Smoothing Iterations", "smoothingStep": "Smoothing Step",
                 "squashConstraint": "Squash Constraint", "stretchConstraint": "Stretch Constraint",
                 "pinBorderVertices": "Pin Border Vertices", "envelope": "Envelope", "relative": "Relative",
                 "inwardConstraint": "Inward Constraint", "outwardConstraint": "Outward Constraint",
                 "shearStrength": "Shear Strength", "bendStrength": "Bend Strength"}
SCULPT_INPUT = {"mode": "Mode", "insideMode": "Inside Mode", "maximumDisplacement": "Maximum Displacement",
                "dropoffDistance": "Dropoff Distance", "dropoffType": "Dropoff Type", "envelope": "Envelope"}
SOLIDIFY_INPUT = {"attachmentMode": "Attachment Mode", "stabilizationLevel": "Stabilization Level",
                  "useBorderFalloff": "Use Border Falloff", "borderFalloffBlur": "Border Falloff Blur",
                  "scaleMode": "Scale Mode", "envelope": "Envelope", "normalScale": "Normal Scale",
                  "tangentPlaneScale": "Tangent Plane Scale", "scaleEnvelope": "Scale Envelope"}


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def _select(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _mesh(rest, faces, inp=None, name="pCube1"):
    """Mesh at the origin with Maya's points / face-corner order; ``inp`` = upstream input (a shape key, like Maya's
    upstream blendShape)."""
    me = bpy.data.meshes.new(name.replace("pCube", "pCubeShape"))
    me.from_pydata([tuple(p) for p in rest], [], [tuple(f) for f in faces])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if inp is not None and any((Vector(a) - Vector(b)).length > 1e-12 for a, b in zip(rest, inp)):
        ob.shape_key_add(name="Basis")
        k = ob.shape_key_add(name="input")
        for i, p in enumerate(inp):
            k.data[i].co = p
        k.value = 1.0
    _select(ob)
    return ob


def _eval(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    eob = ob.evaluated_get(dg)
    me = eob.to_mesh()
    pts = [v.co.copy() for v in me.vertices]
    eob.to_mesh_clear()
    return pts


def _err(pts, expected):
    assert len(pts) == len(expected), (len(pts), len(expected))
    return max((p - Vector(e)).length for p, e in zip(pts, expected))


def _node(ob, base):
    return next(md for md in ob.modifiers if md.name.startswith(base))


BOOLS = {"pinBorderVertices", "useBorderFalloff"}
INTS = {"smoothingIterations", "mode", "insideMode", "dropoffType", "attachmentMode", "stabilizationLevel",
        "borderFalloffBlur", "scaleMode"}


def _set(md, table, attrs):
    for k, v in attrs.items():
        wire.set_(md, table[k], bool(v) if k in BOOLS else int(v) if k in INTS else float(v))


def _weights(ob, name, weights):
    vg = ob.vertex_groups[name]
    for i, w in (weights or {}).items():
        vg.add([int(i)], float(w), 'REPLACE')


# --- Tension: every "O" case -------------------------------------------------------------------------------------

def _tension_case(c):
    _clear()
    ob = _mesh(c["rest"], c["faces"], c["input"])
    dfa.create(bpy.context, 'TENSION')
    md = _node(ob, "tension")
    _set(md, TENSION_INPUT, c["attrs"])
    _weights(ob, md.name, c["weights"])
    return _err(_eval(ob), c["expected"])


def test_tension_matches_maya():
    bad, seen = [], 0
    for c in data.TENSION:
        e = _tension_case(c)
        print(f"tension {c['name']:26s} {c['rule']} {e:.2e}")
        if c["rule"] == "O":
            seen += 1
            if e > c["tol"]:
                bad.append((c["name"], e))
    assert seen >= 30, seen
    assert not bad, bad


# --- Sculpt: every "O" case ----------------------------------------------------------------------------------------

def _sculpt_case(c):
    _clear()
    ob = _mesh(c["rest"], c["faces"])
    v = c["values"]
    dfa.create(bpy.context, 'SCULPT')
    md = _node(ob, "sculpt")
    _set(md, SCULPT_INPUT, v)
    m = c["sculptor_world"]                    # Maya: row-major, row vectors
    M = Matrix([m[0:4], m[4:8], m[8:12], m[12:16]]).transposed()
    wire.get(md, "Sculptor").matrix_world = M
    wire.get(md, "Stretch Origin").location = c["origin_world"]
    return _err(_eval(ob), c["expected"])


def test_sculpt_matches_maya():
    bad, seen = [], 0
    for c in data.SCULPT:
        e = _sculpt_case(c)
        print(f"sculpt {c['name']:18s} {c['rule']} {e:.2e}")
        if c["rule"] == "O":
            seen += 1
            if e > c["tol"]:
                bad.append((c["name"], e))
    assert seen == 7, seen
    assert not bad, bad


# --- Solidify: [U] rule; the measured facts ------------------------------------------------------------------------

def _solidify_case(c):
    import re
    _clear()
    ob = _mesh(c["rest"], c["faces"], c["input"])
    if c["membership_faces"]:
        faces = []
        for s in c["membership_faces"]:
            a, b_ = map(int, re.match(r"f\[(\d+):(\d+)\]", s).groups())
            faces += range(a, b_ + 1)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        for f in faces:
            ob.data.polygons[f].select = True
            for vi in ob.data.polygons[f].vertices:
                ob.data.vertices[vi].select = True
        bpy.ops.object.mode_set(mode='EDIT')
    dfa.create(bpy.context, 'SOLIDIFY')
    md = _node(ob, "solidify")
    _set(md, SOLIDIFY_INPUT, c["attrs"])
    return ob, md, _eval(ob)


def test_solidify_measured_facts():
    cases = {c["name"]: c for c in data.SOLIDIFY}
    # Borders on the whole mesh: nothing moves [O]
    c = cases["wave_default"]
    _ob, _md, out = _solidify_case(c)
    assert _err(out, c["input"]) < 1e-5 and _err(out, c["expected"]) < 1e-4
    # Full on a rigidly moved mesh: the input itself [O]
    c = cases["full_rigid"]
    _ob, _md, out = _solidify_case(c)
    assert _err(out, c["expected"]) < 1e-4, _err(out, c["expected"])
    # Full on the whole mesh: a rigid copy of the rest shape, translation = the input centroid [O]
    c = cases["wave6_default_full"]
    ob, md, out = _solidify_case(c)
    rest = [Vector(p) for p in c["rest"]]
    n = len(out)
    cen = sum(out, Vector()) / n
    want = sum((Vector(p) for p in c["input"]), Vector()) / n
    assert (cen - want).length < 1e-5, (cen, want)
    for i, j in ((0, 48), (3, 45), (10, 30)):
        assert abs((out[i] - out[j]).length - (rest[i] - rest[j]).length) < 1e-4
    # envelope blends linearly [O]
    full = out
    wire.set_(md, "Envelope", 0.5)
    half = _eval(ob)
    mid = [(Vector(a) + b) / 2 for a, b in zip(c["input"], full)]
    assert _err(half, mid) < 1e-5
    # a region's border ring stays, points outside the membership too [O]
    c = cases["sel16_borders"]
    ob, md, out = _solidify_case(c)
    moved = {i for i, (p, q) in enumerate(zip(out, c["input"])) if (p - Vector(q)).length > 1e-6}
    maya = {i for i, (p, q) in enumerate(zip(c["expected"], c["input"])) if (Vector(p) - Vector(q)).length > 1e-6}
    assert moved == maya, (sorted(moved), sorted(maya))
    # residuals of the [U] cases (Kabsch rotation, falloff) — recorded, not asserted
    for c in data.SOLIDIFY:
        _ob, _md, out = _solidify_case(c)
        print(f"solidify {c['name']:22s} U {_err(out, c['expected']):.2e}")


# --- names, selection, Channel Box, AE, Paint Weights ---------------------------------------------------------------

def _cube():
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob = bpy.context.active_object
    ob.name, ob.data.name = "pCube1", "pCubeShape1"
    return ob


def test_names_selection_rows():
    _clear()
    ob = _cube()
    dfa.create(bpy.context, 'TENSION')
    assert [m.name for m in ob.modifiers] == ["tension1"] and "tension1" in ob.vertex_groups
    assert bpy.context.active_object == ob and ob.select_get()            # Maya: pCube1, tension1
    _select(ob)
    dfa.create(bpy.context, 'TENSION')
    dfa.create(bpy.context, 'SOLIDIFY')
    assert [m.name for m in ob.modifiers] == ["tension1", "tension2", "solidify1"]
    _select(ob)
    dfa.create(bpy.context, 'SCULPT')
    assert "sculpt1" in ob.modifiers
    sculptor, origin = bpy.data.objects["sculptor1"], bpy.data.objects["sculpt1StretchOrigin"]
    assert bpy.context.active_object == sculptor and list(bpy.context.selected_objects) == [sculptor]
    assert sculptor.empty_display_type == 'SPHERE' and tuple(sculptor.scale) == (1.0, 1.0, 1.0)
    assert (sculptor.location - Vector()).length < 1e-6 and (origin.location - Vector()).length < 1e-6
    for md, base in ((ob.modifiers["tension1"], "tension"), (ob.modifiers["solidify1"], "solidify"),
                     (ob.modifiers["sculpt1"], "sculpt")):
        assert deformers.base_of(md) == base and deformers.node_type(md) == base
        assert history.is_deformer(md)
        assert ae.modifier_node(ob, md) == (md.name, base)
        rows = cb._modifier_props(md)
        assert rows[0] == "maya:envelope", rows
    t = ob.modifiers["tension1"]
    assert cb._modifier_props(t) == ["maya:" + k for k in ("envelope", "smoothingIterations", "smoothingStep",
                                                           "inwardConstraint", "outwardConstraint", "squashConstraint",
                                                           "stretchConstraint", "relative")]
    a = deformers.attr(t, "maya:smoothingIterations")
    assert a.get(t) == 10
    a.set(t, 4)
    assert wire.get(t, "Smoothing Iterations") == 4
    assert deformers.paint_group(ob, "tension") == "tension2"
    # the sculpt node's lengths are Maya numbers (× Unit inside the node)
    s = ob.modifiers["sculpt1"]
    assert abs(deformers.attr(s, "maya:maximumDisplacement").get(s) - 0.1) < 1e-6
    assert abs(wire.get(s, "Unit") - 1.0) < 1e-9
    # AE tab draws the node's attributes
    assert dfa.draw_ae is not None and dfa.kind_of(s) == "sculpt"


def test_paint_weights_tension():
    _clear()
    ob = _cube()
    dfa.create(bpy.context, 'TENSION')
    assert bpy.ops.allset.paint_deformer_weights(kind="tension") == {'FINISHED'}
    assert bpy.context.mode == 'PAINT_WEIGHT'
    assert ob.vertex_groups.active.name == "tension1"
    bpy.ops.object.mode_set(mode='OBJECT')


def test_components_make_the_membership():
    _clear()
    ob = _cube()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for i in (0, 1, 2):
        ob.data.vertices[i].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    dfa.create(bpy.context, 'TENSION')
    vg = ob.vertex_groups["tension1"]
    assert sorted(v.index for v in ob.data.vertices if any(g.group == vg.index for g in v.groups)) == [0, 1, 2]


# --- Delete Non-Deformer History keeps them ------------------------------------------------------------------------

def test_non_deformer_history_keeps_them():
    _clear()
    c = next(c for c in data.TENSION if c["name"] == "grid_multi_default")
    ob = _mesh(c["rest"], c["faces"])
    bev = ob.modifiers.new("polyBevel1", 'BEVEL')
    bev.width = 0.1
    _select(ob)
    dfa.create(bpy.context, 'TENSION')
    _select(ob)
    dfa.create(bpy.context, 'SOLIDIFY')
    _select(ob)
    dfa.create(bpy.context, 'SCULPT')
    _select(ob)
    n_before = len(_eval(ob))
    assert bpy.ops.allset.delete_history(non_deformer=True) == {'FINISHED'}
    assert [m.name for m in ob.modifiers] == ["tension1", "solidify1", "sculpt1"]
    assert len(ob.data.vertices) == n_before                     # the bevel is baked into the mesh
    pts = _eval(ob)
    assert all(p.length == p.length and p.length < 1e3 for p in pts)
    assert len(ob.data.attributes[dfa.SLOT_COUNT].data) == n_before   # partner table re-taken for the new topology
    assert list(ob.data[dfa.TOPO_PROP]) == [len(ob.data.vertices), len(ob.data.edges), len(ob.data.loops)]
    # Delete History bakes them
    assert bpy.ops.allset.delete_history() == {'FINISHED'}
    assert not ob.modifiers
    _eval(ob)                                                      # the handler drops the hidden tables
    assert dfa.SLOT_COUNT not in ob.data.attributes
    assert not [a.name for a in ob.data.attributes if a.name.startswith(dfa.REST)]


def test_tension_pulls_an_upstream_stretch_back():
    """Live: a deformer above (a Hook moving a vertex) is the tension's input."""
    _clear()
    c = next(c for c in data.TENSION if c["name"] == "grid_side_default")
    ob = _mesh(c["rest"], c["faces"])
    loc = bpy.data.objects.new("locator1", None)
    bpy.context.scene.collection.objects.link(loc)
    hk = ob.modifiers.new("cluster1", 'HOOK')
    hk.object = loc
    hk.vertex_indices_set([12])
    loc.location = (0.3, 0.0, 0.1)
    _select(ob)
    dfa.create(bpy.context, 'TENSION')
    assert _err(_eval(ob), c["expected"]) < 1e-4


# --- Prune Membership > Sculpt -------------------------------------------------------------------------------------

def test_prune_sculpt():
    _clear()
    c = next(c for c in data.SCULPT if c["name"] == "grid_default")
    ob = _mesh(c["rest"], c["faces"])
    dfa.create(bpy.context, 'SCULPT')
    sculptor = bpy.context.active_object
    before = _eval(ob)
    vg = ob.vertex_groups["sculpt1"]
    assert bpy.ops.allset.prune_sculpt() == {'FINISHED'}
    kept = {v.index for v in ob.data.vertices if any(g.group == vg.index for g in v.groups)}
    moved = {i for i, (p, r) in enumerate(zip(before, c["rest"])) if (p - Vector(r)).length > 1e-7}
    assert moved <= kept and len(kept) < len(ob.data.vertices), (len(kept), len(moved))
    assert _err(_eval(ob), [tuple(p) for p in before]) < 1e-6           # pruning changes nothing visible
    _select(sculptor)
    assert bpy.ops.allset.prune_sculpt() == {'CANCELLED'}              # nothing left to prune


# --- option windows, menu, undo, disable ---------------------------------------------------------------------------

def test_option_windows_have_maya_factory_values():
    ws = {w.key: w for w in dfa.windows()}
    assert ws["deform_tension"].defaults() == {"iterations": 10, "step": 0.5, "pin_border": True, "relative": 0.0,
                                               "inward": 0.0, "outward": 0.0, "squash": 1.0, "stretch": 1.0,
                                               "shear": 0.0, "bend": 0.0}
    assert ws["deform_solidify"].defaults() == {"attachment": "Borders", "stabilization": 0, "border_falloff": True,
                                                "falloff_iterations": 2}
    assert ws["deform_sculpt"].defaults() == {"mode": "Stretch", "inside_mode": "Even", "max_displacement": 0.1,
                                              "dropoff_type": "Linear", "dropoff_distance": 1.0, "centered": True}
    assert ws["paint_weights_tension"].paths == ("Deform/Paint Weights/Tension",)
    for w in ws.values():
        if w.key.startswith("paint_weights"):
            continue           # Maya's Paint Attributes Tool, shared with the other Paint Weights boxes
        assert w.match[0] == "allset.deformer_tss"
        assert set(w.defaults()) <= set(dfa.DEFAULTS[w.match[1]["kind"]])
    # a window's values reach the node
    _clear()
    ob = _cube()
    ws["deform_tension"].run(bpy.context, {**ws["deform_tension"].defaults(), "iterations": 3, "shear": 0.25})
    md = ob.modifiers["tension1"]
    assert wire.get(md, "Smoothing Iterations") == 3 and abs(wire.get(md, "Shear Strength") - 0.25) < 1e-6


def test_menu_actions_exist():
    for path, action in dfa.MENU.items():
        op = action[0] if isinstance(action, tuple) else action
        mod, name = op.split(".")
        assert hasattr(getattr(bpy.ops, mod), name), path
    assert set(dfa.MENU) == {"Deform/Tension", "Deform/Solidify", "Deform/Sculpt", "Deform/Paint Weights/Tension",
                             "Deform/Prune Membership/Sculpt"}


def test_one_undo_step_each():
    for kind in ('TENSION', 'SOLIDIFY', 'SCULPT'):
        _clear()
        ob = _cube()
        bpy.ops.ed.undo_push(message="before")
        assert bpy.ops.allset.deformer_tss('EXEC_DEFAULT', True, kind=kind) == {'FINISHED'}
        assert len(bpy.data.objects["pCube1"].modifiers) == 1
        bpy.ops.ed.undo()
        ob = bpy.data.objects["pCube1"]
        assert not ob.modifiers and not ob.vertex_groups, kind
        assert "sculptor1" not in bpy.data.objects


def test_disable_is_clean():
    assert dfa._on_depsgraph in bpy.app.handlers.depsgraph_update_post
    kit.disable()
    try:
        assert dfa._on_depsgraph not in bpy.app.handlers.depsgraph_update_post
        assert not hasattr(bpy.types, "ALLSET_OT_deformer_tss") and not hasattr(bpy.types, "ALLSET_OT_prune_sculpt")
        assert not {"tension", "solidify", "sculpt"} & set(deformers.BASES)
        assert not {"tension", "solidify", "sculpt"} & set(deformers.ATTRS)
    finally:
        kit.enable()
    assert "tension" in import_module(kit.MODULE + ".operators.deformers").BASES
