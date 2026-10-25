"""Step 205 (#112): UV Pin / Proximity Pin against Maya 2022 (tests/maya205_deform_data.py PINS, mayapy; spec
research/maya/re/deform_205.md §7). Every case is rebuilt — mesh, UVs, the upstream blendShape as a shape key (weight
0 = rest, 1 = deformed, 0.5 = half), the pinned transform's world matrix, the option window values and pin attributes
— and the pinned object's world matrix (position + axes) is compared with Maya's within the case's tolerance.

Maya Y-up is converted to Blender Z-up (x, y, z) -> (x, -z, y); the target's local axes are unchanged (the pin writes
its X / Y / Z axes), so a Maya world matrix M (column form) becomes C · M."""

from importlib import import_module

import bpy
from mathutils import Matrix, Vector

import kit
from maya205_deform_data import PINS

pins = import_module(kit.MODULE + ".operators.pins_205")

C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
ATTRS = {"offsetTranslation": pins.OFFSET_T, "offsetOrientation": pins.OFFSET_O, "envelope": pins.ENVELOPE}
REPORT = []


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for d in list(bpy.data.meshes):
        bpy.data.meshes.remove(d)
    pins._rescan()


def _p(v):
    return (v[0], -v[2], v[1])


def _maya_matrix(flat):
    """Maya row-vector 4x4 (rows = X, Y, Z axes, translation) -> Blender world matrix (Z-up)."""
    m = Matrix([flat[0:4], flat[4:8], flat[8:12], flat[12:16]]).transposed()
    return C @ m


def _mesh(case):
    me = bpy.data.meshes.new("pPlaneShape1")
    me.from_pydata([_p(v) for v in case["rest"]], [], [tuple(f) for f in case["faces"]])
    uvl = me.uv_layers.new(name="map1")
    for lp in me.loops:
        uvl.uv[lp.index].vector = case["uvs"][lp.vertex_index]      # polyPlane: UV index = vertex index
    me.update()
    ob = bpy.data.objects.new("pPlane1", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.shape_key_add(name="Basis")
    key = ob.shape_key_add(name="blendShape1", from_mix=False)
    for i, v in enumerate(case["deformed"]):
        key.data[i].co = _p(v)
    key.value = 0.0
    return ob, key


def _select(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _settle():
    for _i in range(3):
        bpy.context.view_layer.update()
        pins.update()
    bpy.context.view_layer.update()


def _residual(ob, flat):
    got = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world
    want = _maya_matrix(flat)
    return max(abs(got[i][j] - want[i][j]) for i in range(3) for j in range(4))


def _pin(case):
    _clear()
    plane, key = _mesh(case)
    loc = bpy.data.objects.new("locator1", None)
    bpy.context.scene.collection.objects.link(loc)
    loc.matrix_world = _maya_matrix(case["input_matrix"])
    bpy.context.view_layer.update()
    _select(plane, loc)
    cmd, opt = case["cmd"], case["options"]
    na = pins.AXIS_ITEMS[opt.get(cmd + "normalAxis", 0)]
    ta = pins.AXIS_ITEMS[opt.get(cmd + "tangentAxis", 1)]
    inputs = []
    if cmd == "UVPin":
        node, pinned, inherit = pins.uv_pin(bpy.context, normal_axis=na, tangent_axis=ta)
    else:
        node, pinned, inputs, inherit = pins.proximity_pin(
            bpy.context, maintain_offset=bool(opt.get("ProximityPinmaintainOffset", 1)),
            mode='UV' if opt.get("ProximityPincoordMode", 0) == 1 else 'EDGE', normal_axis=na, tangent_axis=ta)
    assert pinned == [loc] and inherit == ["locator1"], (pinned, inherit)    # Maya warns for every pinned transform
    assert tuple(loc.location) == (0, 0, 0) and tuple(loc.rotation_euler) == (0, 0, 0)   # translate / rotate zeroed
    h = loc.constraints[node].target
    for a, v in case["attrs"].items():
        h[ATTRS[a]] = v
    return plane, key, loc, inputs


def _check(case):
    plane, key, loc, inputs = _pin(case)
    res = {}
    _settle()
    res["rest"] = _residual(loc, case["rest_matrix"])
    key.value = 1.0
    _settle()
    res["deformed"] = _residual(loc, case["deformed_matrix"])
    key.value = 0.5
    _settle()
    res["half"] = _residual(loc, case["half_matrix"])
    if case["after"]:
        key.value = 1.0
        inputs[0].location = _p((0.5, 0.6, 0.1))          # Maya: xform pinInput -ws -t 0.5 0.6 0.1
        _settle()
        res["moved input"] = _residual(loc, case["after"]["world"])
    worst = max(res.values())
    REPORT.append(f"{case['name']} ({case['rule']}): {worst:.2e} " + ", ".join(f"{k} {v:.1e}" for k, v in res.items()))
    print("PIN205", REPORT[-1])
    return worst


def test_pins_match_maya():
    bad = []
    for case in PINS:
        tol = case["tol"]
        if tol is None:
            continue
        worst = _check(case)
        if worst > tol:
            bad.append(f"{case['name']}: {worst:.2e} > {tol}")
    assert not bad, "; ".join(bad) + "\n" + "\n".join(REPORT)
    assert sum(1 for c in PINS if c["rule"] == "O") == 16


def test_proximity_pin_undo_is_one_step():
    case = next(c for c in PINS if c["name"] == "prox_default")
    _clear()
    plane, key = _mesh(case)
    loc = bpy.data.objects.new("locator1", None)
    bpy.context.scene.collection.objects.link(loc)
    loc.matrix_world = _maya_matrix(case["input_matrix"])
    bpy.context.view_layer.update()
    before = loc.matrix_world.copy()
    _select(plane, loc)
    bpy.ops.ed.undo_push(message="before")
    assert bpy.ops.allset.proximity_pin('EXEC_DEFAULT', True) == {'FINISHED'}
    assert "pinInput" in bpy.data.objects and loc.constraints
    bpy.ops.ed.undo()
    loc = bpy.data.objects["locator1"]
    assert not loc.constraints and "pinInput" not in bpy.data.objects
    assert not any(o.get(pins.KIND) for o in bpy.data.objects)
    assert max(abs(loc.matrix_world[i][j] - before[i][j]) for i in range(4) for j in range(4)) < 1e-6
    pins.update()
