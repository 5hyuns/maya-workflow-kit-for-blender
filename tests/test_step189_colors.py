"""Step 189 (audit 13 #6): Maya Mesh Display colour commands against mayapy.

Ground truth: tests/maya189_colors_data.py (research/maya/re/mesh_display_184_colors*.json). The Maya mesh g21 (two
quads, corner k of face f = faces[f][k]) gets a CORNER float colour set; Maya's uncoloured corners are white in the kit
(delegated, color_sets_maya.UNSET).
"""

import re
from importlib import import_module

import bmesh
import bpy

import kit
from maya189_colors_data import APPLY, MESHES, MOD, RENAME, SAMPLE

cs = import_module(kit.MODULE + ".operators.color_sets_maya")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
option_windows = import_module(kit.MODULE + ".operators.option_windows")

TOL = 1e-4
_OP = {1: 'REPLACE', 2: 'ADD', 3: 'SUBTRACT', 4: 'REMOVE'}


def _fresh():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    bpy.context.scene.pop(cs.BAKE_SETS, None)


def _build(name="g21", colors=None, extra_set=None):
    m = MESHES[name]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in m["verts"]], [], [tuple(f) for f in m["faces"]])
    me.update()
    if colors is not None:
        attr = me.color_attributes.new("colorSet1", 'FLOAT_COLOR', 'CORNER')
        for li, loop in enumerate(me.loops):
            attr.data[li].color = colors[loop.vertex_index]
        me.color_attributes.active_color = attr
    if extra_set:
        attr = me.color_attributes.new(extra_set, 'FLOAT_COLOR', 'CORNER')
        for d in attr.data:
            d.color = cs.UNSET
        me.color_attributes.active_color = attr
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    return ob


def _select(ob, sel):
    comps = [s for s in sel if "." in s]
    if not comps:
        return
    bpy.ops.object.mode_set(mode='EDIT')
    faces = any(".f[" in s for s in comps)
    edges = any(".e[" in s for s in comps)
    bpy.context.tool_settings.mesh_select_mode = (not faces and not edges, edges, faces)
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.ensure_lookup_table()
    for s in comps:
        i = int(re.search(r"\[(\d+)\]", s).group(1))
        (bm.faces if ".f[" in s else bm.edges if ".e[" in s else bm.verts)[i].select_set(True)
    bmesh.update_edit_mesh(ob.data)


def _corners(ob, name=None):
    me = ob.data
    attr = me.color_attributes[name] if name else me.color_attributes.active_color
    return [tuple(d.color) for d in attr.data]


def _near(a, b):
    return max(abs(x - y) for x, y in zip(a, b)) < TOL


def test_apply_color_matches_maya():
    skip = {"apply_vtxface",              # Blender has no vertex-face selection
            "apply_indiv_red", "apply_indiv_red_new", "apply_indiv_none"}   # individual channels: not in the kit
    for key, c in sorted(APPLY.items()):
        if key in skip:
            continue
        _fresh()
        pre = c["cmd"] != "" and key in ("apply_face_on_vertex_colors", "apply_vertex_on_vertex_colors", "apply_add",
                                          "apply_subtract", "apply_remove_object", "apply_remove_face",
                                          "apply_add_over_one", "apply_second_set", "apply_color_values")
        ob = _build(colors=SAMPLE if pre else None, extra_set="mySet" if key == "apply_second_set" else None)
        _select(ob, c["sel"]) if c["sel"] else ob.select_set(False)
        ovs = c["ovs"]
        color = (ovs.get("polyApplyColorRedValue", 0.5), ovs.get("polyApplyColorGreenValue", 0.5),
                 ovs.get("polyApplyColorBlueValue", 0.5))
        res = bpy.ops.allset.apply_color(operation=_OP[ovs.get("polyApplyColorOperation", 1)], color=color,
                                         alpha=ovs.get("polyApplyColorAlphaValue", 1.0))
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        if not c["ok"]:
            assert res == {'CANCELLED'}, key
            continue
        assert res == {'FINISHED'}, key
        assert ob.data.color_attributes.active_color.name == c["current"], (key, c["current"])
        got = _corners(ob)
        want = [x for row in c["faces"] for x in row]
        for i, (g, w) in enumerate(zip(got, want)):
            assert _near(g, w if w is not None else cs.UNSET), (key, i, g, w)


def test_modify_current_set_matches_maya():
    for key, c in sorted(MOD.items()):
        a = c["attrs"]
        ramps = {name: [(p, v, k) for p, v, k in c["ramp"][f"{name}Scale"]]
                 for name in ("red", "green", "blue", "alpha", "intensity") if f"{name}Scale" in c["ramp"]}
        cols = c["before"]
        want = [x for row in c["faces"] for x in row]
        corners = [v for f in MESHES["g21"]["faces"] for v in f]
        for i, v in enumerate(corners):
            got = cs.color_mod(cols[v], a.get("huev", 0.0), a.get("satv", 1.0), a.get("value", 1.0), **ramps)
            assert _near(got, want[i]), (key, i, cols[v], got, want[i])


def test_modify_operator_runs_on_the_current_set():
    _fresh()
    ob = _build(colors=SAMPLE)
    assert bpy.ops.allset.color_set_modify(value=2.0, intensity_0=0.5, intensity_1=0.5) == {'FINISHED'}
    want = [x for row in MOD["m2_value2_ihalf"]["faces"] for x in row]
    for i, (g, w) in enumerate(zip(_corners(ob), want)):
        assert _near(g, w), (i, g, w)


def test_rename_rules():
    for key, c in sorted(RENAME.items()):
        names = set(c["sets"]) if not c["ok"] else {"colorSet1"}
        if key == "rename_clash":
            names = {"colorSet1", "other"}
        err = cs.rename_error(names, c["new"])
        assert (err is None) == c["ok"], (key, err)
    _fresh()
    ob = _build(colors=SAMPLE)
    assert bpy.ops.allset.color_set_rename(new_name="paint") == {'FINISHED'}
    assert ob.data.color_attributes.active_color.name == "paint"
    try:
        bpy.ops.allset.color_set_rename(new_name="position")     # an attribute name Blender uses
        raise AssertionError("renamed onto an existing attribute")
    except RuntimeError:
        pass


def test_keyframe_vertex_colors():
    _fresh()
    ob = _build(colors=SAMPLE)
    _select(ob, ["g21.vtx[1]"])
    assert bpy.ops.allset.color_keyframe() == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    fcs = kit.fcurves(ob.data)
    paths = {fc.data_path for fc in fcs}
    want = {f'attributes["colorSet1"].data[{li}].color' for li, loop in enumerate(ob.data.loops) if loop.vertex_index == 1}
    assert paths == want, (paths, want)


def test_bake_sets_and_prelight():
    _fresh()
    ob = _build()
    assert bpy.ops.allset.bake_set_assign_new() == {'FINISHED'}
    assert ob[cs.BAKE_SET] == "vertexBakeSet1"
    assert bpy.ops.allset.bake_set_assign_new() == {'FINISHED'}
    assert ob[cs.BAKE_SET] == "vertexBakeSet2" and set(cs.bake_sets(bpy.context.scene)) == {"vertexBakeSet1",
                                                                                            "vertexBakeSet2"}
    assert bpy.ops.allset.bake_set_assign(name="vertexBakeSet1") == {'FINISHED'}
    assert ob[cs.BAKE_SET] == "vertexBakeSet1"
    assert bpy.ops.allset.bake_set_edit(scale_rgba=2.0, bake_color=True, color_blending='OVERWRITE',
                                        alpha_blending='OVERWRITE') == {'FINISHED'}
    assert cs.bake_settings(bpy.context.scene, ob)["scaleRgba"] == 2.0
    # a sun lights the quads from +Z: Prelight writes lit colours into colorSet1, the render engine comes back
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN'))
    bpy.context.scene.collection.objects.link(sun)
    engine = bpy.context.scene.render.engine
    assert bpy.ops.allset.prelight() == {'FINISHED'}
    assert bpy.context.scene.render.engine == engine
    cols = _corners(ob, "colorSet1")
    assert all(c[0] > 0.05 for c in cols), cols[:2]


def test_select_shared_instances():
    _fresh()
    a = _build()
    b = bpy.data.objects.new("inst", a.data)
    bpy.context.scene.collection.objects.link(b)
    lone = _build("g22")
    for o in (b, lone):
        o.select_set(False)
    a.select_set(True)
    bpy.context.view_layer.objects.active = a
    assert bpy.ops.allset.select_shared_instances() == {'FINISHED'}
    assert set(bpy.context.selected_objects) == {b}            # Maya: the other instance (share_instance_perinst)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    lone.select_set(True)
    assert bpy.ops.allset.select_shared_instances() == {'CANCELLED'}       # no other instance: a warning


def test_menu_items_and_windows():
    for path, op in (("Mesh Display/Apply Color", "allset.apply_color"),
                     ("Mesh Display/Rename Current Set...", "allset.color_set_rename"),
                     ("Mesh Display/Modify Current Set", "allset.color_set_modify"),
                     ("Mesh Display/Set Keyframe for Vertex Color", "allset.color_keyframe"),
                     ("Mesh Display/Prelight (Maya)", "allset.prelight"),
                     ("Mesh Display/Assign New Set", "allset.bake_set_assign_new"),
                     ("Mesh Display/Assign Existing Set", "allset.bake_set_assign"),
                     ("Mesh Display/Edit Assigned Set", "allset.bake_set_edit"),
                     ("Mesh Display/Per Instance Sharing/Select Shared Instances",
                      "allset.select_shared_instances")):
        assert menu_map.spec(path)[1] == op, path
    w = option_windows.find_path("Mesh Display/Apply Color")
    assert w is not None and w.title == "Apply Color Options"
    w = option_windows.find_path("Mesh Display/Prelight (Maya)")
    assert w is not None and w.title == "Prelight (Maya) Options"
