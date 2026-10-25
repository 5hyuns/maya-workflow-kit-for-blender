"""Step 205 lane B (#112): Deform > Morph and Deform > Jiggle > Jiggle Deformer (operators/deformers_205b.py)
against Maya 2022 (tests/maya205_deform_data.py MORPH / JIGGLE, spec research/maya/re/deform_205.md §4 / §6).

Maya data is Y-up: the meshes are built in Blender's Z-up (Maya X, Y, Z -> Blender X, -Z, Y) so mirror axes are
checked through the kit's axis mapping. "O" cases must match within the case tolerance (1e-4); "U" cases have no
measured rule and are skipped with the reason."""

from importlib import import_module

import bpy
from mathutils import Vector

import kit
import maya205_deform_data as data

b205 = import_module(kit.MODULE + ".operators.deformers_205b")
deformers = import_module(kit.MODULE + ".operators.deformers")
history = import_module(kit.MODULE + ".operators.history")
cb = import_module(kit.MODULE + ".ui.channel_box")
ae = import_module(kit.MODULE + ".ui.attribute_editor")

# the target transform of the World-space cases (research/scripts/deform_205/morph_explore.py:102-103); their
# "target" points are world positions (morph_explore.py points())
TARGET_XFORM = {"abs_world_obj": (3.0, 1.0, 0.0), "abs_world_ws": (3.0, 1.0, 0.0)}
MODES = ("ABSOLUTE", "RELATIVE", "SURFACE", "RETARGET", "MIRROR")


def to_b(p):
    return Vector((p[0], -p[2], p[1]))


def to_m(v):
    return (v[0], v[2], -v[1])


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 30
    scene.frame_set(1)


def _mesh(name, pts, faces, keyed=None):
    """A mesh object from Maya points; ``keyed`` = points of a shape key at value 1 (an upstream deformation the
    Orig shape doesn't see)."""
    me = bpy.data.meshes.new(name + "Shape")
    me.from_pydata([to_b(p) for p in pts], [], [tuple(f) for f in faces])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if keyed is not None:
        ob.shape_key_add(name="Basis")
        kb = ob.shape_key_add(name="up")
        for i, p in enumerate(keyed):
            kb.data[i].co = to_b(p)
        kb.value = 1.0
    return ob


def _select(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _evaluated(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    e = ob.evaluated_get(dg)
    return [e.matrix_world @ v.co for v in e.data.vertices]


def _compare(got, expected, tol, what):
    assert len(got) == len(expected), f"{what}: {len(got)} points, Maya {len(expected)}"
    worst = max((Vector(to_m(g)) - Vector(e)).length for g, e in zip(got, expected))
    assert worst < tol, f"{what}: off by {worst:.2e} (tol {tol})"
    return worst


# --- Morph ----------------------------------------------------------------------------------------------------

def _morph_case(c):
    _clear()
    base = _mesh("pCube1", c["rest"], c["faces"], keyed=c["input"])
    mode = MODES[c["options"].get("morphMode", 0)]
    if c["target_orig"] is not None:
        tgt = _mesh("pCube2", c["target_orig"], c["faces"], keyed=c["target"])
    elif c["name"] in TARGET_XFORM:                # the data holds the moved target's world points
        t = TARGET_XFORM[c["name"]]
        tgt = _mesh("pCube2", [(p[0] - t[0], p[1] - t[1], p[2] - t[2]) for p in c["target"]], c["faces"])
        tgt.location = to_b(t)
    else:
        tgt = _mesh("pCube2", c["target"], c["faces"])
    bpy.context.view_layer.update()
    if mode == "MIRROR":
        _select(base)
    else:
        _select(base, tgt)
    space = "WORLD" if c["options"].get("morphSpace") else "OBJECT"
    res = bpy.ops.allset.morph('EXEC_DEFAULT', mode=mode, space=space,
                               use_original=bool(c["options"].get("useOriginalMorphTarget")))
    assert res == {'FINISHED'}, res
    md = base.modifiers["morph1"]
    for k, v in c["attrs"].items():
        a = deformers.attr(md, "maya:" + k)
        if a is None:                           # non-keyable (AE) attributes are node inputs (neighborLevel: none)
            socket = {"mirrorDirection": "Mirror Direction"}.get(k)
            if socket is not None:
                b205.set_(md, socket, int(v))
        else:
            a.set(md, v)
    if c["weights"] is not None:
        vg = base.vertex_groups["morph1"]
        for i, w in c["weights"].items():
            vg.add([int(i)], float(w), 'REPLACE')
    return base


def _run_morph(c):
    base = _morph_case(c)
    return _compare(_evaluated(base), c["expected"], c["tol"], c["name"])


def test_morph_o_cases_match_maya():
    done = []
    for c in data.MORPH:
        if c["rule"] != "O":
            continue
        done.append((c["name"], _run_morph(c)))
    assert len(done) == 23, done
    print("morph O cases:", ", ".join(f"{n} {w:.1e}" for n, w in done))


def test_morph_u_cases_skipped():
    # Retarget on a sphere (length off by up to 4 %), Retarget scaling attributes, Surface neighbour levels: no
    # measured rule (deform_205.md §4) — the kit runs them with the measured rule only
    skipped = [c["name"] for c in data.MORPH if c["rule"] == "U"]
    assert skipped == ["ret_sph", "ret_sph_ns05_ts2", "surf_sph_nb1"], skipped
    gaps = [f"{c['name']} {_run_morph({**c, 'tol': float('inf')}):.1e}" for c in data.MORPH if c["rule"] == "U"]
    print("SKIP morph U cases (no Maya rule, deform_205.md §4), kit gap:", ", ".join(gaps))


def test_morph_made_like_maya():
    c = data.MORPH[0]
    base = _morph_case(c)
    tgt = bpy.data.objects["pCube2"]
    md = base.modifiers["morph1"]
    assert {o.name for o in bpy.context.selected_objects} == {"pCube1", "pCube2"}
    assert bpy.context.active_object == base
    assert "morph1" in base.vertex_groups
    assert deformers.node_type(md) == "morph"
    assert ae.modifier_node(base, md) == ("morph1", "morph")
    assert cb._modifier_props(md)[:3] == ["maya:envelope", "maya:scaleEnvelope", "maya:uniformScaleWeight"]
    assert history.is_deformer(md)
    rest = b205.get(md, "Base Rest")
    assert rest is not None and rest.data == base.data and not rest.users_collection
    assert b205.get(md, "Target") == tgt
    # different point counts: Maya's error, nothing made
    other = _mesh("pCube3", [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)])
    _select(base, other)
    assert bpy.ops.allset.morph('EXEC_DEFAULT') == {'CANCELLED'}
    assert "morph2" not in base.modifiers


def test_morph_follows_upstream_and_paints():
    c = next(x for x in data.MORPH if x["name"] == "abs_env05")
    base = _morph_case(c)
    md = base.modifiers["morph1"]
    deformers.attr(md, "maya:envelope").set(md, 0.0)
    _compare(_evaluated(base), c["input"], 1e-5, "envelope 0 = input")
    _select(base)
    assert bpy.ops.allset.paint_deformer_weights('EXEC_DEFAULT', kind="morph") == {'FINISHED'}
    assert base.vertex_groups.active.name == "morph1"
    bpy.ops.object.mode_set(mode='OBJECT')


# --- Jiggle ---------------------------------------------------------------------------------------------------

def _jiggle_case(c):
    _clear()
    ob = _mesh("pCube1", c["rest"], c["faces"])
    if c["by"] == "transform":
        for f, t in enumerate(c["translate"], start=1):
            ob.location = to_b(t)
            ob.keyframe_insert("location", frame=f)
    else:                                         # a cluster on every point: an upstream shape key along Maya X
        ob.shape_key_add(name="Basis")
        kb = ob.shape_key_add(name="cluster1")
        kb.slider_max = 10.0
        for i, p in enumerate(c["rest"]):
            kb.data[i].co = to_b((p[0] + 1.0, p[1], p[2]))
        for f, t in enumerate(c["translate"], start=1):
            kb.value = t[0]
            kb.keyframe_insert("value", frame=f)
    bpy.context.scene.frame_set(1)
    _select(ob)
    assert bpy.ops.allset.jiggle('EXEC_DEFAULT') == {'FINISHED'}
    md = ob.modifiers["jiggle1"]
    for k, v in c["attrs"].items():
        deformers.attr(md, "maya:" + k).set(md, v)
    if c["weights"] is not None:
        vg = ob.vertex_groups["jiggle1"]
        for i, w in c["weights"].items():
            vg.add([int(i)], float(w), 'REPLACE')
    return ob


def _run_jiggle(c):
    ob = _jiggle_case(c)
    scene = bpy.context.scene
    worst = 0.0
    for f, expected in enumerate(c["expected_world"], start=1):
        scene.frame_set(f)
        worst = max(worst, _compare(_evaluated(ob), expected, c["tol"], f"{c['name']} frame {f}"))
    return worst


def test_jiggle_o_cases_match_maya():
    done = []
    for c in data.JIGGLE:
        if c["rule"] != "O":
            continue
        done.append((c["name"], _run_jiggle(c)))
    assert len(done) == 12, done
    print("jiggle O cases:", ", ".join(f"{n} {w:.1e}" for n, w in done))


def test_jiggle_u_cases_skipped():
    # Jiggle Weight / painted weight 0.5 change the dynamics, Enable Only After Object Stops (0.6875 x), Direction
    # Bias: no measured rule (deform_205.md §6)
    skipped = [c["name"] for c in data.JIGGLE if c["rule"] == "U"]
    assert skipped == ["jw05", "w_half", "stops", "db05", "dbm1"], skipped
    gaps = [f"{c['name']} {_run_jiggle({**c, 'tol': float('inf')}):.1e}" for c in data.JIGGLE if c["rule"] == "U"]
    print("SKIP jiggle U cases (no Maya rule, deform_205.md §6), kit gap:", ", ".join(gaps))


def test_jiggle_scrubs_back_from_the_cache():
    c = data.JIGGLE[0]
    ob = _jiggle_case(c)
    scene = bpy.context.scene
    for f in range(1, 11):
        scene.frame_set(f)
    scene.frame_set(4)
    _compare(_evaluated(ob), c["expected_world"][3], c["tol"], "frame 4 again")


def test_jiggle_made_like_maya():
    c = data.JIGGLE[0]
    ob = _jiggle_case(c)
    md = ob.modifiers["jiggle1"]
    assert ae.modifier_node(ob, md) == ("jiggle1", "jiggle")
    assert [r for r in cb._modifier_props(md)][:3] == ["maya:envelope", "maya:enable", "maya:ignoreTransform"]
    assert md.bake_directory == "//jiggle1Cache"
    assert {o.name for o in bpy.context.selected_objects} == {"pCube1"}
    _select(ob)
    assert bpy.ops.allset.paint_deformer_weights('EXEC_DEFAULT', kind="jiggle") == {'FINISHED'}
    assert ob.vertex_groups.active.name == "jiggle1"
    bpy.ops.object.mode_set(mode='OBJECT')
    # a second jiggle on vertices only: jiggle2 owns those points
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.data.vertices[0].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    assert bpy.ops.allset.jiggle('EXEC_DEFAULT') == {'FINISHED'}
    vg = ob.vertex_groups["jiggle2"]
    assert [v.index for v in ob.data.vertices if any(g.group == vg.index for g in v.groups)] == [0]


# --- history, menus, windows, undo, disable -----------------------------------------------------------------

def test_non_deformer_history_keeps_morph_and_jiggle():
    # no upstream deformation: Relative = rest + (target - rest) = the target
    c = next(x for x in data.MORPH if x["name"] == "rel_default")
    _clear()
    base = _mesh("pCube1", c["rest"], c["faces"])
    tgt = _mesh("pCube2", c["target"], c["faces"])
    weld = base.modifiers.new("Weld", 'WELD')                # a non-deformer node before the deformers
    weld.merge_threshold = 1e-6
    _select(base, tgt)
    assert bpy.ops.allset.morph('EXEC_DEFAULT', mode='RELATIVE') == {'FINISHED'}
    _select(base)
    assert bpy.ops.allset.jiggle('EXEC_DEFAULT') == {'FINISHED'}
    old = base.data
    assert bpy.ops.allset.delete_history(non_deformer=True) == {'FINISHED'}
    assert [m.name for m in base.modifiers] == ["morph1", "jiggle1"]
    assert base.data != old
    bpy.context.view_layer.update()
    assert b205.get(base.modifiers["morph1"], "Base Rest").data == base.data, "the rest follows the baked mesh"
    _compare(_evaluated(base), c["target"], 1e-4, "after Non-Deformer History")


def test_menu_and_windows():
    assert b205.MENU == {"Deform/Morph": "allset.morph", "Deform/Jiggle/Jiggle Deformer": "allset.jiggle",
                         "Deform/Paint Weights/Jiggle": ("allset.paint_deformer_weights", {"kind": "jiggle"})}
    ws = {w.key: w for w in b205.windows()}
    assert ws["deform_morph"].title == "Morph Options"
    assert ws["deform_morph"].defaults() == {"mode": "Absolute", "space": "Object", "use_original": False}
    assert ws["deform_jiggle"].title == "Jiggle Deformer Options"
    assert ws["deform_jiggle"].defaults() == {"stiffness": 0.5, "damping": 0.5, "weight": 1.0,
                                              "only_when_stops": False, "ignore_transform": False}
    assert ws["paint_weights_jiggle"].paths == ("Deform/Paint Weights/Jiggle",)
    # the windows' commands run
    _clear()
    c = data.JIGGLE[0]
    ob = _mesh("pCube1", c["rest"], c["faces"])
    _select(ob)
    assert ws["deform_jiggle"].run(bpy.context, {**ws["deform_jiggle"].defaults(), "stiffness": 0.2}) == {'FINISHED'}
    assert abs(b205.get(ob.modifiers["jiggle1"], "Stiffness") - 0.2) < 1e-6
    tgt = _mesh("pCube2", c["rest"], c["faces"])
    _select(ob, tgt)
    assert ws["deform_morph"].run(bpy.context, {**ws["deform_morph"].defaults(), "mode": "Surface"}) == {'FINISHED'}
    assert b205.get(ob.modifiers["morph1"], "Morph Mode") == 2


def test_one_undo_step_each():
    for op, two in ((bpy.ops.allset.jiggle, False), (bpy.ops.allset.morph, True)):
        _clear()
        c = data.JIGGLE[0]
        ob = _mesh("pCube1", c["rest"], c["faces"])
        obs = [ob, _mesh("pCube2", c["rest"], c["faces"])] if two else [ob]
        _select(*obs)
        bpy.ops.ed.undo_push(message="before")
        assert op('EXEC_DEFAULT', True) == {'FINISHED'}
        assert len(bpy.data.objects["pCube1"].modifiers) == 1
        bpy.ops.ed.undo()
        ob = bpy.data.objects["pCube1"]
        assert not ob.modifiers and not ob.vertex_groups, [m.name for m in ob.modifiers]


def test_disable_clean():
    assert b205._on_depsgraph in bpy.app.handlers.depsgraph_update_post
    kit.disable()
    try:
        assert b205._on_depsgraph not in bpy.app.handlers.depsgraph_update_post
        for name in ("ALLSET_OT_morph", "ALLSET_OT_jiggle", "ALLSET_OT_gn_deformer_enum"):
            assert not hasattr(bpy.types, name), name
    finally:
        kit.enable()
