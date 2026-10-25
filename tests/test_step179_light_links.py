"""Step 179: Maya light / shadow linking (operators/light_links.py) against mayapy (research/maya/re/light_links_179.json:
the same scene, the same commands, lightlink queries and select results), a Cycles render probe and the editor."""

import json
import os
from importlib import import_module

import bpy

import kit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "research", "maya", "re", "light_links_179.json")
ll = import_module(kit.MODULE + ".operators.light_links")
editor = import_module(kit.MODULE + ".ui.light_link_editor")
OBJECTS = ("pCube1", "pCube2", "pCube3", "group1")


def scene():
    """The mayapy scene: pointLight1, spotLight1, pCube1..3 (pCube3 under group1)."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    sc = bpy.context.scene
    out = {}
    for name, kind in (("pointLight1", 'POINT'), ("spotLight1", 'SPOT')):
        ob = bpy.data.objects.new(name, bpy.data.lights.new(name, kind))
        sc.collection.objects.link(ob)
        out[name] = ob
    for i in (1, 2, 3):
        ob = bpy.data.objects.new(f"pCube{i}", bpy.data.meshes.new(f"pCubeShape{i}"))
        sc.collection.objects.link(ob)
        out[ob.name] = ob
    g = bpy.data.objects.new("group1", None)
    sc.collection.objects.link(g)
    out["pCube3"].parent = g
    out["group1"] = g
    return out


def links(nodes, lights):
    """The JSON 'links' block for our state (transforms only, as the Maya lists filtered below)."""
    d = {"light": {}, "shadow": {}, "object_lights": {}, "object_shadow_lights": {}}
    for l in lights:
        d["light"][l] = sorted(o for o in nodes if o in OBJECTS and ll.linked(nodes[l], nodes[o], "LIGHT"))
        d["shadow"][l] = sorted(o for o in nodes if o in OBJECTS and ll.linked(nodes[l], nodes[o], "SHADOW"))
    for o in OBJECTS:
        d["object_lights"][o] = sorted(l for l in lights if ll.linked(nodes[l], nodes[o], "LIGHT"))
        d["object_shadow_lights"][o] = sorted(l for l in lights if ll.linked(nodes[l], nodes[o], "SHADOW"))
    return d


def maya_links(block, lights):
    keep = set(OBJECTS) | set(lights)
    return {k: {n: sorted(x for x in v if x in keep) for n, v in sub.items() if n in keep} for k, sub in block.items()}


def run(nodes, names, kind, make):
    ll.link_selection([nodes[n] for n in names], kind, make)


CASES = {
    "default": lambda n: None,
    "break": lambda n: run(n, ["pointLight1", "pCube2"], "LIGHT", False),
    "break_make": lambda n: (run(n, ["pointLight1", "pCube2"], "LIGHT", False),
                             run(n, ["pointLight1", "pCube2"], "LIGHT", True)),
    "break_group": lambda n: run(n, ["pointLight1", "group1"], "LIGHT", False),
    "break_two_lights": lambda n: run(n, ["pointLight1", "spotLight1", "pCube1"], "LIGHT", False),
    "shadow_break": lambda n: run(n, ["spotLight1", "pCube1"], "SHADOW", False),
    "shadow_break_make": lambda n: (run(n, ["spotLight1", "pCube1"], "SHADOW", False),
                                    run(n, ["spotLight1", "pCube1"], "SHADOW", True)),
}


def test_link_queries_match_maya():
    if not os.path.exists(DATA):
        print("research/ missing: skipped")
        return
    data = json.load(open(DATA, encoding="utf-8"))["cases"]
    lights = ["pointLight1", "spotLight1"]
    for name, fn in CASES.items():
        nodes = scene()
        fn(nodes)
        got, want = links(nodes, lights), maya_links(data[name]["links"], lights)
        assert got == want, (name, got, want)
    # Illuminates by Default off: lights nothing until a link is made (shadow list: Maya [] too)
    nodes = scene()
    d = bpy.data.objects.new("directionalLight1", bpy.data.lights.new("directionalLight1", 'SUN'))
    bpy.context.scene.collection.objects.link(d)
    nodes["directionalLight1"] = d
    d.allset_illuminates_by_default = False
    case = data["not_default"]
    assert [o for o in OBJECTS if ll.linked(d, nodes[o])] == case["before_make"]
    run(nodes, ["directionalLight1", "pCube1"], "LIGHT", True)
    want = maya_links(case["links"], lights + ["directionalLight1"])
    assert links(nodes, lights + ["directionalLight1"])["light"] == want["light"]
    # a new object is lit by default lights even after a break
    nodes = scene()
    run(nodes, ["pointLight1", "pCube2"], "LIGHT", False)
    c4 = bpy.data.objects.new("pCube4", bpy.data.meshes.new("pCubeShape4"))
    bpy.context.scene.collection.objects.link(c4)
    assert sorted(l for l in lights if ll.linked(nodes[l], c4)) == \
        sorted(x for x in data["new_object_after_break"]["new_cube_lights"] if x in lights)


def test_select_commands_match_maya():
    if not os.path.exists(DATA):
        print("research/ missing: skipped")
        return
    want = json.load(open(DATA, encoding="utf-8"))["cases"]["selects"]["selects"]
    nodes = scene()
    run(nodes, ["pointLight1", "pCube2"], "LIGHT", False)
    run(nodes, ["spotLight1", "pCube1"], "SHADOW", False)
    vl = bpy.context.view_layer
    for label, names, kind, lights in (
            ("objects_by_light0", ["pointLight1"], "LIGHT", False),
            ("objects_by_light0_two_selected", ["pointLight1", "spotLight1"], "LIGHT", False),
            ("lights_on_cube1", ["pCube2"], "LIGHT", True),
            ("lights_on_cube0", ["pCube1"], "LIGHT", True),
            ("shadowed_by_light1", ["spotLight1"], "SHADOW", False),
            ("shadow_lights_on_cube0", ["pCube1"], "SHADOW", True),
            ("shadow_lights_on_cube1", ["pCube2"], "SHADOW", True),
            ("objects_by_cube_selected", ["pCube1"], "LIGHT", False),
            ("lights_by_light_selected", ["pointLight1"], "LIGHT", True)):
        for o in bpy.context.scene.objects:
            o.select_set(o.name in names)
        vl.objects.active = nodes[names[0]]          # Maya's first selected node
        bpy.ops.allset.light_link_select(kind=kind, lights=lights)
        got = sorted(o.name for o in bpy.context.scene.objects if o.select_get())
        assert got == want[label], (label, got, want[label])


def test_operators_and_editor():
    nodes = scene()
    for o in bpy.context.scene.objects:
        o.select_set(o.name in ("spotLight1", "group1"))
    assert bpy.ops.allset.light_link(kind="LIGHT", make=False) == {'FINISHED'}
    assert not ll.linked(nodes["spotLight1"], nodes["pCube3"]) and ll.linked(nodes["spotLight1"], nodes["pCube1"])
    coll = nodes["spotLight1"].light_linking.receiver_collection
    assert coll.name == "spotLight1_lightLinks" and coll.use_fake_user
    assert coll not in list(bpy.context.scene.collection.children_recursive)      # linked to no scene
    for o in bpy.context.scene.objects:
        o.select_set(o.name == "pCube1")
    assert bpy.ops.allset.light_link(kind="LIGHT", make=False) == {'CANCELLED'}     # no light selected
    # editor toggle = make / break the link of one pair (with the hierarchy)
    bpy.ops.allset.light_link_toggle(light="spotLight1", target="group1", kind="LIGHT")
    assert ll.linked(nodes["spotLight1"], nodes["pCube3"]) and ll.linked(nodes["spotLight1"], nodes["group1"])
    bpy.ops.allset.light_link_toggle(light="pointLight1", target="pCube2", kind="SHADOW")
    assert not ll.linked(nodes["pointLight1"], nodes["pCube2"], "SHADOW")
    wm = bpy.context.window_manager
    wm.allset_ll_mode = "LIGHT_CENTRIC"
    left, right = editor.lists(bpy.context)
    assert [o.name for o in left] == ["pointLight1", "spotLight1"] and "pCube1" in [o.name for o in right]
    wm.allset_ll_mode = "OBJECT_CENTRIC"
    left, right = editor.lists(bpy.context)
    assert "pCube1" in [o.name for o in left] and [o.name for o in right] == ["pointLight1", "spotLight1"]


def test_cycles_render_probe():
    """One light, two cubes: the cube whose light link is broken renders dark (Cycles)."""
    import bmesh
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 4
    sc.render.resolution_x, sc.render.resolution_y = 64, 32
    sc.world = bpy.data.worlds.new("black")
    sc.world.color = (0, 0, 0)
    for node in (sc.world.node_tree.nodes if sc.world.node_tree else ()):    # 5.0+: worlds always have nodes
        if node.type == 'BACKGROUND':                                          # whose Background lights the scene
            node.inputs["Strength"].default_value = 0.0
    cubes = []
    for i, x in enumerate((-1.5, 1.5)):
        me = bpy.data.meshes.new(f"probe{i}")
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2.0)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(f"probe{i}", me)
        ob.location = (x, 0, 0)
        sc.collection.objects.link(ob)
        cubes.append(ob)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type, cam.data.ortho_scale, cam.location = 'ORTHO', 8, (0, 0, 10)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN'))
    sun.data.energy = 3
    sc.collection.objects.link(sun)
    ll.link_selection([sun, cubes[1]], "LIGHT", False)

    path = os.path.join(bpy.app.tempdir, "step179_probe.png")
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path)
    w, h = img.size
    px = list(img.pixels)

    def value(u):
        i = (int(0.5 * h) * w + int(u * w)) * 4
        return sum(px[i:i + 3]) / 3
    lit, dark = value(0.3125), value(0.6875)
    print("probe lit / unlinked", lit, dark)
    assert lit > 0.3 and dark < 0.05, (lit, dark)
