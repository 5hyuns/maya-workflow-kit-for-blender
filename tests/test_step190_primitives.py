"""Step 190 (audit 13 #9): Create > Polygon Primitives Pipe, Helix, Gear, Soccer Ball, Super Ellipse, Spherical
Harmonics, Ultra Shape built by the kit like Maya 2022 (mayapy ground truth: tests/maya190_prims_data.py, rules
research/maya/re/poly_prims_185.md).

Every case is made through ``prim_history.create_object`` (the Create menu path) in a 1 m scene (Maya unit 1) and
compared in Maya's order: vertex positions within 1e-4 (Maya (x, y, z) = Blender (x, z, -y)), identical face vertex
lists, UVs per face corner within 1e-4, hard edges. The node lands in Channel Box INPUTS and editing it rebuilds.
"""

from importlib import import_module

import bpy

import kit
from maya190_prims_data import CASES

prim_history = import_module(kit.MODULE + ".operators.prim_history")
prim_shapes = import_module(kit.MODULE + ".operators.prim_shapes")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
notices = import_module(kit.MODULE + ".ui.notices")

TOL = 1e-4
LABELS = {"Pipe": 'PIPE', "Helix": 'HELIX', "Gear": 'GEAR', "Soccer Ball": 'SOCCER_BALL',
          "Super Ellipse": 'SUPER_ELLIPSE', "Spherical Harmonics": 'SPHERICAL_HARMONICS', "Ultra Shape": 'ULTRA_SHAPE'}
NAMES = {'PIPE': ("pPipe1", "polyPipe"), 'HELIX': ("pHelix1", "polyHelix"), 'GEAR': ("pGear1", "polyGear"),
         'SOCCER_BALL': ("pSolid1", "polyPrimitiveMisc"), 'SUPER_ELLIPSE': ("pSuperShape1", "polySuperShape"),
         'SPHERICAL_HARMONICS': ("pSuperShape1", "polySuperShape"), 'ULTRA_SHAPE': ("pSuperShape1", "polySuperShape")}


def _fresh():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    us = bpy.context.scene.unit_settings
    us.system, us.length_unit, us.scale_length = 'METRIC', 'METERS', 1.0


def _maya(v):
    return (v.co.x, v.co.z, -v.co.y)


def _make(kind, values):
    ob = prim_history.create_object(bpy.context, kind, dict(values))
    bpy.context.view_layer.update()
    return ob


def _check(key, c):
    _fresh()
    ob = _make(c["kind"], c["set"])
    me, m = ob.data, c["mesh"]
    assert (len(me.vertices), len(me.polygons)) == (m["v"], m["f"]), (key, len(me.vertices), len(me.polygons))
    if "points" not in m:
        for i, p in enumerate(m["points_head"]):
            q = _maya(me.vertices[i])
            assert max(abs(a - b) for a, b in zip(q, p)) < TOL, (key, i, q, p)
        return
    for i, p in enumerate(m["points"]):
        q = _maya(me.vertices[i])
        assert max(abs(a - b) for a, b in zip(q, p)) < TOL, (key, i, q, p)
    for fi, (poly, f) in enumerate(zip(me.polygons, m["faces"])):
        assert list(poly.vertices) == list(f), (key, fi, list(poly.vertices), f)
    uv = me.uv_layers.get("map1")
    assert uv is not None, key
    for fi, (poly, row) in enumerate(zip(me.polygons, m["uvs"])):
        for li, want in zip(poly.loop_indices, row):
            got = tuple(uv.data[li].uv)
            assert want is not None and max(abs(a - b) for a, b in zip(got, want)) < TOL, (key, fi, got, want)
    hard = sorted(sorted(e.vertices) for e in me.edges if e.use_edge_sharp)
    flat = all(not p.use_smooth for p in me.polygons)
    if not flat:
        assert hard == sorted(sorted(h) for h in m["hard"]), (key, len(hard), len(m["hard"]))


def test_every_case_matches_maya():
    for key, c in sorted(CASES.items()):
        _check(key, c)


def test_menu_items_names_and_inputs():
    for label, kind in LABELS.items():
        path = f"Create/Polygon Primitives/{label}"
        s = menu_map.spec(path)
        assert s is not None and s[1] == "allset.create" and s[2] == {"kind": kind}, (path, s)
        _fresh()
        assert bpy.ops.allset.create(kind=kind) == {'FINISHED'}, kind
        ob = bpy.context.view_layer.objects.active
        name, node_type = NAMES[kind]
        assert ob.name == name, (kind, ob.name)
        owner, node = prim_history.node_of(ob)
        assert node is not None and node["type"] == node_type and node["name"] == node_type + "1", (kind, node)
    # the Spherical Harmonics / Ultra Shape items differ from Super Ellipse only by the node's shape
    _fresh()
    bpy.ops.allset.create(kind='ULTRA_SHAPE')
    _owner, node = prim_history.node_of(bpy.context.view_layer.objects.active)
    assert prim_history.attrs(_owner)["shape"] == 2, prim_history.attrs(_owner)
    # Interactive Creation / Exit On Completion stay greyed with a notice
    assert notices.greyed_notice("Create/Polygon Primitives/Interactive Creation")


def test_inputs_edit_rebuilds():
    _fresh()
    ob = _make('PIPE', {})
    assert len(ob.data.vertices) == 80
    prim_history.rebuild(bpy.context, ob, {"subdivisionsAxis": 6})
    assert len(ob.data.vertices) == 24, len(ob.data.vertices)
    _fresh()
    ob = _make('GEAR', {})
    prim_history.rebuild(bpy.context, ob, {"sides": 6, "heightDivisions": 1})
    assert (len(ob.data.vertices), len(ob.data.polygons)) == (96, 96)
