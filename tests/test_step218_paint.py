"""Step 218 lane P: Paint Skin Weights in Maya 2026 terms (Issue #126 A1 A2 A5 A6). Flood = Maya's formulas with
redistribution / locks / selected-vertex limit, Influences RMB = Maya's 7 items, paint keys, Mode / Select Geometry.
Maya 2026 Paint Skin Weights rules.

The scene is Maya's scene rebuilt with Maya's vertex order (Blender index = Maya vertex id): polyCylinder
h 8 r 1 sx 20 sy 8 (caps are 20-gons, no centre vertex), rings at Maya y = 0..8 -> Blender z, joints at 0 / 4 / 8. The
bind is not redone: Maya's "before" weights (the same on every vertex of a ring) are written into the groups."""

import math
from importlib import import_module

import bpy
from mathutils import Vector

import kit

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


def test_flood_blend_follows_brush_kind():
    # Blender's Blur brush = Maya Smooth (flood_settings), Average = Replace with the mean
    assert wp.maya_target('SMOOTH', 0.2, 0.9, 1.0, avg=0.4) == 0.4
    assert wp.redistribute({0: 0.5, 1: 0.5}, 1, 2.0, set(), {0, 1}) == {0: 0.0, 1: 1.0}
    # nothing unlocked to take the rest: the painted weight can't drop (delegated)
    assert wp.redistribute({1: 1.0}, 1, 0.3, set(), {0, 1}) == {1: 1.0}
    assert wp.redistribute({0: 0.4, 1: 0.6}, 1, 0.0, {0}, {0, 1}) == {0: 0.4, 1: 0.6}


# --- A1: Influences RMB ------------------------------------------------------------------------------------


def _selected(cyl):
    return {v.index for v in cyl.data.vertices if v.select}


def skin_bone_select(bone, value):
    from importlib import import_module as _im
    _im(kit.MODULE + ".ui.channel_box").set_bone_selected(bone, value)


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


