"""Polygon Cube / Sphere / Cone / Plane / Torus creation nodes have Height Baseline and Create UVs like the
Cylinder (#480): the rows, their choices and starting values, the baseline shift along the build axis and no UVs
for Create UVs None / off."""
from importlib import import_module

import bpy

import kit

ps = import_module(kit.MODULE + ".operators.prim_shapes")
ph = import_module(kit.MODULE + ".operators.prim_history")
ci = import_module(kit.MODULE + ".ui.creation_inputs")

KINDS = {'CUBE': "polyCube", 'SPHERE': "polySphere", 'CONE': "polyCone", 'PLANE': "polyPlane",
         'TORUS': "polyTorus"}


def _bbox(node_type, **kw):
    verts = ps.build(node_type, {**ps.defaults(node_type), **kw}).verts
    return tuple(tuple(round(f(v[i] for v in verts), 5) for i in range(3)) for f in (min, max))


def test_rows_choices_and_starting_values():
    for node_type in KINDS.values():
        rows = ci.node_rows(node_type)
        assert rows[0] == "heightBaseline" and "createUVs" in rows, (node_type, rows)
        assert ps.defaults(node_type)["heightBaseline"] == 0.0
        assert ps.clamp(node_type, "heightBaseline", 3.0) == 1.0
        assert ps.clamp(node_type, "heightBaseline", -3.0) == -1.0
    assert ci.node_rows("polyCone")[-5:-3] == ["createUVs", "roundCap"]
    expect = {"polyCube": (5, "Normalize Collectively and Preserve Aspect Ratio"),
              "polySphere": (3, "Sawtooth at pole"),
              "polyCone": (4, "Normalize and Preserve Aspect Ratio"),
              "polyPlane": (3, "Normalize and Preserve Aspect Ratio")}
    for node_type, (count, label) in expect.items():
        labels, values = ph.enum_labels(node_type, "createUVs")
        assert len(labels) == count and labels[0] == "None", (node_type, labels)
        assert labels[values.index(ps.defaults(node_type)["createUVs"])] == label, node_type
    assert ps.defaults("polyTorus")["createUVs"] is True
    assert ph.entry_kind("polyTorus", "createUVs") != "ENUM"


def test_height_baseline_moves_the_shape_along_its_axis():
    assert _bbox("polyCube", heightBaseline=-1.0) == ((-0.5, 0.0, -0.5), (0.5, 1.0, 0.5))
    assert _bbox("polyCube", heightBaseline=0.5) == ((-0.5, -0.75, -0.5), (0.5, 0.25, 0.5))
    assert _bbox("polySphere", heightBaseline=1.0) == ((-1.0, -2.0, -1.0), (1.0, 0.0, 1.0))
    assert _bbox("polyCone", heightBaseline=-1.0) == ((-1.0, 0.0, -1.0), (1.0, 2.0, 1.0))
    assert _bbox("polyTorus", heightBaseline=-1.0)[0][1] == 0.0
    assert _bbox("polyTorus", heightBaseline=-1.0)[1][1] == 1.0
    assert _bbox("polyPlane", heightBaseline=1.0) == ((-0.5, 0.0, 0.0), (0.5, 0.0, 1.0))
    assert _bbox("polyPlane", heightBaseline=-0.5) == ((-0.5, 0.0, -0.75), (0.5, 0.0, 0.25))
    # turned with the axis: Axis Z puts the cube along +Z, the plane's height along Y
    assert _bbox("polyCube", heightBaseline=1.0, axisY=0.0, axisZ=1.0) == ((-0.5, -0.5, -1.0), (0.5, 0.5, 0.0))
    assert _bbox("polyPlane", heightBaseline=1.0, axisY=0.0, axisZ=1.0) == ((-0.5, -1.0, 0.0), (0.5, 0.0, 0.0))


def _fresh(kind):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    return ph.create_object(bpy.context, kind)


def test_create_uvs_off_and_baseline_rebuild_each_object():
    for kind in KINDS:
        ob = _fresh(kind)
        assert len(ob.data.uv_layers) == 1, kind
        ph.rebuild(bpy.context, ob, {"createUVs": False if kind == 'TORUS' else 0})
        assert len(ob.data.uv_layers) == 0, kind
        ph.rebuild(bpy.context, ob, {"createUVs": True if kind == 'TORUS' else 1, "heightBaseline": -1.0})
        assert len(ob.data.uv_layers) == 1, kind
        if kind != 'PLANE':
            zs = [v.co.z for v in ob.data.vertices]
            assert abs(min(zs)) < 1e-6 < max(zs), (kind, min(zs), max(zs))


def test_create_without_uvs_keeps_them_off():
    for kind in KINDS:
        ob = _fresh(kind)
        bpy.data.objects.remove(ob, do_unlink=True)
        ob = ph.create_object(bpy.context, kind, create_uvs=False)
        assert not ph.attrs(ph.owner_of(ob))["createUVs"], kind
        assert len(ob.data.uv_layers) == 0, kind
        ph.rebuild(bpy.context, ob, {"heightBaseline": 0.5})
        assert len(ob.data.uv_layers) == 0, kind
