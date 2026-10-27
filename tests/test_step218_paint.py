"""Step 218 lane P: Paint Skin Weights in Maya 2026 terms (Issue #126 A1 A2 A5 A6). Flood = Maya's formulas with
redistribution / locks / selected-vertex limit, Influences RMB = Maya's 7 items, paint keys, Mode / Select Geometry.
Ground truth: tests/maya218_paint_data.py (Maya 2026, research/maya/re/maya2026_paint_skin_weights.md §3 §4 §7).

The scene is Maya's measurement scene rebuilt with Maya's vertex order (Blender index = Maya vertex id): polyCylinder
h 8 r 1 sx 20 sy 8 (caps are 20-gons, no centre vertex), rings at Maya y = 0..8 -> Blender z, joints at 0 / 4 / 8. The
bind is not redone: the measured "before" weights (the same on every vertex of a ring) are written into the groups."""

import math
from importlib import import_module

import bpy
from mathutils import Vector

import kit
import maya218_paint_data as data

joints = import_module(kit.MODULE + ".operators.joints")
skin = import_module(kit.MODULE + ".operators.skin")
wp = import_module(kit.MODULE + ".operators.weight_paint")
paint_weights = import_module(kit.MODULE + ".ui.paint_weights")
compat = import_module(kit.MODULE + ".compat")

SIDES, RINGS = 20, 9
NAMES = ("joint1", "joint2", "joint3")
FORMULA_TOL = 1e-6        # kit vs the formula on the exact (float32) inputs
MAYA_TOL = 5e-6           # kit vs Maya's printed numbers (6 decimals)
OPS = {"absolute": "REPLACE", "additive": "ADD", "scale": "SCALE", "smooth": "SMOOTH"}
REPORT = []


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def _cylinder():
    verts = [(math.cos(2 * math.pi * i / SIDES), math.sin(2 * math.pi * i / SIDES), float(j))
             for j in range(RINGS) for i in range(SIDES)]
    faces = [(j * SIDES + i, j * SIDES + (i + 1) % SIDES, (j + 1) * SIDES + (i + 1) % SIDES, (j + 1) * SIDES + i)
             for j in range(RINGS - 1) for i in range(SIDES)]
    faces.append(tuple(reversed(range(SIDES))))
    faces.append(tuple((RINGS - 1) * SIDES + i for i in range(SIDES)))
    me = bpy.data.meshes.new("pCylinderShape1")
    compat.mesh_from_pydata(me, verts, [], faces)       # Blender 5.0.1 mistypes .select_edge (step 229)
    me.update()
    ob = bpy.data.objects.new("pCylinder1", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _scene():
    """Maya's skinned cylinder in weight paint, painted influence joint2, nothing selected."""
    _clear()
    arm = joints.new_skeleton(bpy.context)
    parent = None
    for z in (0.0, 4.0, 8.0):
        parent = joints.add_joint(arm, Vector((0.0, 0.0, z)), parent, length=0.5)
    joints.finish(bpy.context, arm, list(NAMES))
    bpy.ops.object.mode_set(mode='OBJECT')
    cyl = _cylinder()
    mod = cyl.modifiers.new("skinCluster1", 'ARMATURE')
    mod.object = arm
    for name in NAMES:
        cyl.vertex_groups.new(name=name)
    _write_baseline(cyl)
    wp.set_vertex_selection(cyl, ())
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    cyl.select_set(True)
    bpy.context.view_layer.objects.active = cyl
    assert bpy.ops.allset.paint_skin_weights() == {'FINISHED'}
    assert bpy.context.mode == 'PAINT_WEIGHT'
    assert bpy.context.tool_settings.use_auto_normalize, "Maya's skin normalizes interactively"
    cyl.vertex_groups.active_index = cyl.vertex_groups["joint2"].index
    return arm, cyl


def _write_baseline(cyl):
    for name in NAMES:
        g = cyl.vertex_groups[name]
        for ring, w in enumerate(data.BASELINE[name]):
            g.add([ring * SIDES + i for i in range(SIDES)], w, 'REPLACE')
    for g in cyl.vertex_groups:
        g.lock_weight = False


def _weights(cyl, i):
    idx = {cyl.vertex_groups[n].index: k for k, n in enumerate(NAMES)}
    out = [0.0, 0.0, 0.0]
    for e in cyl.data.vertices[i].groups:
        if e.group in idx:
            out[idx[e.group]] = e.weight
    return out


def _brush(op, value, opacity):
    ts = bpy.context.tool_settings
    ups = compat.unified_paint_settings(ts)
    brush = ts.weight_paint.brush
    for owner in (ups, brush):
        if owner is not None:
            owner.weight = value
            owner.strength = opacity
    if brush is not None and op != "SMOOTH":
        brush.blend = {"REPLACE": 'MIX', "ADD": 'ADD', "SCALE": 'MUL'}[op]


def _neighbours(cyl):
    nb = [set() for _ in cyl.data.vertices]
    for e in cyl.data.edges:
        a, b = e.vertices
        nb[a].add(b)
        nb[b].add(a)
    return nb


def _formula(case, before, all_before, nb, i):
    """Spec §4 applied independently to the exact stored inputs (j2 painted)."""
    op, v, o = OPS[case["oper"]], case["value"], case["opacity"]
    w1, w2, w3 = before
    if op == "REPLACE":
        t = w2 + o * (v - w2)
    elif op == "ADD":
        t = w2 + o * v
    elif op == "SCALE":
        t = w2 * (1 - o * (1 - v))
    else:
        ring = [i, *nb[i]]
        t = w2 + o * (sum(all_before[k][1] for k in ring) / len(ring) - w2)
    lock = case["lock"] or {}
    locked = [k for k, n in enumerate(NAMES) if lock.get(n) and k != 1]
    room = 1 - sum(before[k] for k in locked)
    t = min(max(t, 0.0), room)
    free = [k for k in (0, 2) if k not in locked]
    total = sum(before[k] for k in free)
    out = list(before)
    out[1] = t
    for k in free:
        out[k] = (room - t) * before[k] / total
    return out


def _run(case):
    _arm, cyl = _scene()
    for name, on in (case["lock"] or {}).items():
        cyl.vertex_groups[name].lock_weight = bool(on)
    if case["select"]:
        wp.set_vertex_selection(cyl, range(60, 80))       # pCylinder1.vtx[60:79]
        cyl.data.use_paint_mask_vertex = False            # Maya floods the selection, mask shown or not
    op = OPS[case["oper"]]
    _brush(op, case["value"], case["opacity"])
    all_before = [_weights(cyl, i) for i in range(len(cyl.data.vertices))]
    nb = _neighbours(cyl)
    if op == "SMOOTH":
        assert wp.flood(bpy.context, 'SMOOTH') == {'FINISHED'}
    else:
        assert bpy.ops.allset.flood_weights() == {'FINISHED'}
    err_formula = err_maya = 0.0
    for vid, row in case["verts"].items():
        after = _weights(cyl, vid)
        for k in range(3):
            assert abs(all_before[vid][k] - row["before"][k]) < 1e-6, (case["case"], vid, all_before[vid], row)
        expected = (_formula(case, all_before[vid], all_before, nb, vid)
                    if not case["select"] or 60 <= vid < 80 else all_before[vid])
        err_formula = max(err_formula, *(abs(a - b) for a, b in zip(after, expected)))
        err_maya = max(err_maya, *(abs(a - b) for a, b in zip(after, row["after"])))
    changed = sum(1 for i in range(len(cyl.data.vertices)) if abs(_weights(cyl, i)[1] - all_before[i][1]) > 1e-9)
    REPORT.append((case["case"], err_formula, err_maya, changed))
    print(f"step218 flood {case['case']}: max |kit - formula| {err_formula:.2e}, max |kit - Maya| {err_maya:.2e}, "
          f"changed {changed} (Maya {case['n_changed_j2']})")
    assert err_formula < FORMULA_TOL, (case["case"], err_formula)
    assert err_maya < MAYA_TOL, (case["case"], err_maya)
    assert changed == case["n_changed_j2"], (case["case"], changed)
    sums = [sum(_weights(cyl, i)) for i in range(len(cyl.data.vertices))]
    assert max(abs(s - 1) for s in sums) < 1e-5, "Interactive normalization keeps every vertex at 1"
    return cyl


def _case(name):
    return next(c for c in data.FLOOD if c["case"] == name)


def test_flood_replace():
    _run(_case("absolute_v0.3_o1.0"))
    _run(_case("absolute_v0.3_o0.5"))
    _run(_case("absolute_v0_o1"))


def test_flood_add():
    _run(_case("additive_v0.3_o1.0"))
    _run(_case("additive_v0.3_o0.5"))


def test_flood_scale():
    _run(_case("scale_v0.5_o1.0"))
    _run(_case("scale_v0.5_o0.5"))


def test_flood_smooth():
    _run(_case("smooth_v1.0_o1.0"))
    _run(_case("smooth_v1.0_o0.5"))


def test_flood_smooth_ignores_value():
    results = []
    for value in (1.0, 0.5, 0.0):
        _arm, cyl = _scene()
        _brush("SMOOTH", value, 1.0)
        wp.flood(bpy.context, 'SMOOTH')
        results.append(_weights(cyl, 100))
    for r in results:
        for a, b in zip(r, data.SMOOTH_VALUE["1.0"]):
            assert abs(a - b) < MAYA_TOL, (r, data.SMOOTH_VALUE)


def test_flood_locks():
    _run(_case("absolute_with_joint3_locked"))
    _run(_case("additive_v1_o1_lock_j1"))


def test_flood_selected_vertices_only():
    cyl = _run(_case("absolute_selected_verts"))
    assert not cyl.data.use_paint_mask_vertex


def test_flood_blend_follows_brush_kind():
    # Blender's Blur brush = Maya Smooth (flood_settings), Average = Replace with the mean
    assert wp.maya_target('SMOOTH', 0.2, 0.9, 1.0, avg=0.4) == 0.4
    assert wp.redistribute({0: 0.5, 1: 0.5}, 1, 2.0, set(), {0, 1}) == {0: 0.0, 1: 1.0}
    # nothing unlocked to take the rest: the painted weight can't drop (delegated)
    assert wp.redistribute({1: 1.0}, 1, 0.3, set(), {0, 1}) == {1: 1.0}
    assert wp.redistribute({0: 0.4, 1: 0.6}, 1, 0.0, {0}, {0, 1}) == {0: 0.4, 1: 0.6}


def test_flood_is_one_undo_step():
    _arm, cyl = _scene()
    _brush("REPLACE", 0.3, 1.0)
    before = [_weights(cyl, i) for i in (0, 80, 160)]
    bpy.ops.ed.undo_push(message="before flood")
    assert bpy.ops.allset.flood_weights('EXEC_DEFAULT', True) == {'FINISHED'}
    assert abs(_weights(cyl, 0)[1] - 0.3) < 1e-6
    bpy.ops.ed.undo()
    cyl = bpy.data.objects["pCylinder1"]
    after = [_weights(cyl, i) for i in (0, 80, 160)]
    assert after == before, (before, after)


# --- A1: Influences RMB ------------------------------------------------------------------------------------

def test_influence_menu_labels_are_maya_2026():
    labels = [label for label, *_ in paint_weights.MAYA_RMB]
    assert labels == data.RMB_LABELS, labels
    for _label, op, prop, value in paint_weights.MAYA_RMB:
        mod, name = op.split(".")
        rna = getattr(getattr(bpy.ops, mod), name).get_rna_type()
        assert value in [e.identifier for e in rna.properties[prop].enum_items], (op, value)
    assert bpy.types.UI_MT_list_item_context_menu.draw._draw_funcs.count(paint_weights.draw_list_item_menu) == 1


def _selected(cyl):
    return {v.index for v in cyl.data.vertices if v.select}


def test_influence_menu_vertex_selection():
    arm, cyl = _scene()
    for b in arm.pose.bones:
        skin_bone_select(b, False)
    j3 = cyl.vertex_groups["joint3"]
    j3.remove([i for i in range(SIDES)])                    # ring 0 no longer touched by joint3
    cyl.data.use_paint_mask_vertex = False
    cyl.vertex_groups.active_index = cyl.vertex_groups["joint2"].index
    assert bpy.ops.allset.weight_influence_verts(mode='SET') == {'FINISHED'}
    assert len(_selected(cyl)) == data.RMB_COUNTS["select_verts_j2"] - 1 == 180   # Maya: 180 vertices + the mesh
    assert cyl.data.use_paint_mask_vertex, "the selection shows (vertex mask on)"
    cyl.vertex_groups.active_index = j3.index
    assert bpy.ops.allset.weight_influence_verts(mode='SET') == {'FINISHED'}
    assert _selected(cyl) == set(range(SIDES, SIDES * RINGS)), "> 0 rule: ring 0 has no joint3 weight"
    wp.set_vertex_selection(cyl, range(SIDES))
    cyl.vertex_groups.active_index = j3.index
    assert bpy.ops.allset.weight_influence_verts(mode='ADD') == {'FINISHED'}
    assert _selected(cyl) == set(range(SIDES * RINGS)), "union"
    cyl.vertex_groups.active_index = cyl.vertex_groups["joint1"].index
    assert bpy.ops.allset.weight_influence_verts(mode='REMOVE') == {'FINISHED'}
    assert _selected(cyl) == set(), "difference (Maya remove_verts_j1 leaves only the mesh)"
    # Lock Selected / Lock Inverse Selection / Unlock Inverse Selection (Maya rmb.lock_selected / lock_inverse)
    cyl.vertex_groups.active_index = cyl.vertex_groups["joint1"].index
    bpy.ops.allset.weight_influence(action='LOCK_SELECTED')
    assert [cyl.vertex_groups[n].lock_weight for n in NAMES] == [True, False, False]
    bpy.ops.allset.weight_influence(action='LOCK_OTHERS')
    assert [cyl.vertex_groups[n].lock_weight for n in NAMES] == [True, True, True]
    bpy.ops.allset.weight_influence(action='UNLOCK_OTHERS')
    assert [cyl.vertex_groups[n].lock_weight for n in NAMES] == [True, False, False]
    bpy.ops.allset.weight_influence(action='UNLOCK_SELECTED')
    assert [cyl.vertex_groups[n].lock_weight for n in NAMES] == [False, False, False]


def skin_bone_select(bone, value):
    from importlib import import_module as _im
    _im(kit.MODULE + ".ui.channel_box").set_bone_selected(bone, value)


def test_influence_menu_nothing_picked_is_maya_error():
    arm, cyl = _scene()
    for b in arm.pose.bones:
        skin_bone_select(b, False)
    cyl.vertex_groups.active_index = -1
    if cyl.vertex_groups.active is not None:
        return          # Blender keeps an active group: the error can't be reached from the UI either
    try:
        bpy.ops.allset.weight_influence_verts(mode='SET')
    except RuntimeError as ex:
        assert wp.NO_INFLUENCE in str(ex)
    else:
        raise AssertionError("expected Maya's error")


def test_sort_labels_and_natural_order():
    rna = wp.ALLSET_PG_weight_workspace.bl_rna.properties["sort"]
    assert [e.name for e in rna.enum_items] == ["Alphabetically", "By Hierarchy", "Flat"]
    assert rna.default == 'HIERARCHY'
    names = ["joint10", "joint2", "Joint1", "arm_b", "arm_a12", "arm_a3"]
    assert sorted(names, key=paint_weights.natural_key) == ["arm_a3", "arm_a12", "arm_b", "Joint1", "joint2",
                                                            "joint10"]


# --- A5 / A6: keys, Mode, Select Geometry, entry ------------------------------------------------------------

def _wp_items():
    return [k for k in kit.maya_kc().keymaps["Weight Paint"].keymap_items if k.active]


def _has(idname, type_, ctrl=False, alt=False, shift=False, **props):
    for k in _wp_items():
        if (k.idname == idname and k.type == type_ and k.value == 'PRESS' and bool(k.ctrl) == ctrl
                and bool(k.alt) == alt and bool(k.shift) == shift
                and all(getattr(k.properties, p) == v for p, v in props.items())):
            return True
    return False


def test_paint_keys():
    assert _has("allset.flood_weights", 'F', alt=True)
    assert not any(k.idname == "paint.weight_set" and k.type == 'F' and k.alt for k in _wp_items())
    assert _has("allset.paint_copy_vertex_weights", 'C', ctrl=True, alt=True)
    assert _has("allset.paint_paste_vertex_weights", 'V', ctrl=True, alt=True)
    assert _has("allset.skin_paint_mode", 'PERIOD', ctrl=True, step=1)
    assert _has("allset.skin_paint_mode", 'COMMA', ctrl=True, step=-1)
    assert _has("allset.paint_reflection", 'R', alt=True)


def test_mode_cycle_and_reflection():
    assert [wp.next_mode(m, 1) for m in wp.PAINT_MODES] == ['SELECT', 'PAINT_SELECT', 'PAINT']
    assert [wp.next_mode(m, -1) for m in wp.PAINT_MODES] == ['PAINT_SELECT', 'PAINT', 'SELECT']
    _arm, cyl = _scene()
    assert wp.paint_mode(bpy.context) == 'PAINT'
    mirror = cyl.data.use_mirror_x
    assert bpy.ops.allset.paint_reflection() == {'FINISHED'}
    assert cyl.data.use_mirror_x != mirror
    bpy.ops.allset.paint_reflection()
    assert cyl.data.use_mirror_x == mirror


def test_copy_paste_vertex_weights_while_painting():
    _arm, cyl = _scene()
    wp.set_vertex_selection(cyl, [80])
    assert bpy.ops.allset.paint_copy_vertex_weights() == {'FINISHED'}
    wp.set_vertex_selection(cyl, [0, 1, 2])
    assert bpy.ops.allset.paint_paste_vertex_weights() == {'FINISHED'}
    for i in (0, 1, 2):
        assert max(abs(a - b) for a, b in zip(_weights(cyl, i), _weights(cyl, 80))) < 1e-6
    assert max(abs(a - b) for a, b in zip(_weights(cyl, 3), data.FLOOD[0]["verts"][0]["before"])) < 1e-6


def test_select_geometry_and_entry_mask():
    _arm, cyl = _scene()
    bpy.ops.allset.paint_skin_weights()                  # leave
    assert bpy.context.mode == 'OBJECT'
    cyl.data.use_paint_mask_vertex = False
    wp.set_vertex_selection(cyl, [10])                   # Maya after_component_enter: vtx[10]
    assert bpy.ops.allset.paint_skin_weights() == {'FINISHED'}
    assert cyl.data.use_paint_mask_vertex and _selected(cyl) == {10}, "entry with a vertex selection shows it"
    assert bpy.ops.allset.select_geometry() == {'FINISHED'}
    assert _selected(cyl) == set() and not cyl.data.use_paint_mask_vertex
    assert bpy.context.mode == 'PAINT_WEIGHT' and cyl.select_get() and bpy.context.active_object == cyl
    bpy.ops.allset.paint_skin_weights()
    wp.set_vertex_selection(cyl, range(SIDES * RINGS))   # a full selection is the whole mesh: mask left alone
    bpy.ops.allset.paint_skin_weights()
    assert not cyl.data.use_paint_mask_vertex
