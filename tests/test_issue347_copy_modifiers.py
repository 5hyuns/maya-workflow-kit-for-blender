"""#347: what a plain copy (Edit > Duplicate, Ctrl+D) does with Blender modifiers.

- Modelling modifiers shown in the viewport and deformers are baked into the copy, like Maya's modelling history and
  deformers (Mirror, Array, a Boolean with its cutter, a Subdivision at its viewport level).
- A modifier switched off in the viewport stays on the copy as it is, not applied; one that reads another object
  (an Armature's skeleton, a Hook's handle) is removed, since a plain copy has no connections.
- Multires stays live on the copy with its levels and sculpt detail. The shape-key mix and the deformers above it go
  into the base mesh; the modifiers after it stay live, except the ones that read another object.
- Subdiv Proxy (Mesh > Smooth Proxy, Ctrl+Shift+~): the copy is the cage only, like copying a Maya proxy cage.
"""

import math
from importlib import import_module

import bpy

import kit

duplicate = import_module(kit.MODULE + ".operators.duplicate")
display = import_module(kit.MODULE + ".operators.display")
gk = import_module(kit.MODULE + ".operators.global_keys4")
menu_map = import_module(kit.MODULE + ".ui.menu_map")


def _fresh():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.armatures, bpy.data.curves, bpy.data.actions):
        for idb in list(coll):
            coll.remove(idb)
    duplicate.PAIRS.clear()
    bpy.context.scene.frame_set(1)


def _only(*obs):
    for o in bpy.context.view_layer.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = obs[-1]


def _cube(name="pCube1", location=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    ob = bpy.context.active_object
    ob.name = name
    return ob


def _points(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [ev.matrix_world @ v.co for v in ev.data.vertices]


def _same(a, b, eps=1e-4):
    return len(a) == len(b) and all((p - q).length < eps for p, q in zip(a, b))


def _copy(ob):
    _only(ob)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    copy = bpy.context.active_object
    assert copy is not ob and copy.data is not ob.data
    return copy


def _names(ob):
    return [m.name for m in ob.modifiers if not display.is_preview(m)]


def _skeleton(name="joint1"):
    """Two bones up Z (joint1 at the origin, joint2 at z 1)."""
    arm = bpy.data.objects.new(name, bpy.data.armatures.new(name))
    bpy.context.collection.objects.link(arm)
    _only(arm)
    bpy.ops.object.mode_set(mode='EDIT')
    b1 = arm.data.edit_bones.new("joint1")
    b1.head, b1.tail = (0, 0, -1), (0, 0, 0)
    b2 = arm.data.edit_bones.new("joint2")
    b2.head, b2.tail, b2.parent = (0, 0, 0), (0, 0, 1), b1
    bpy.ops.object.mode_set(mode='OBJECT')
    arm.pose.bones["joint2"].rotation_mode = 'XYZ'
    return arm


def _skin(mesh, arm, name="skinCluster1"):
    g1, g2 = mesh.vertex_groups.new(name="joint1"), mesh.vertex_groups.new(name="joint2")
    for v in mesh.data.vertices:
        (g2 if v.co.z > 0 else g1).add([v.index], 1.0, 'REPLACE')
    md = mesh.modifiers.new(name, 'ARMATURE')
    md.object = arm
    return md


def _sculpted(name="pSculpt1"):
    """A cube with a two-level Multires and sculpted detail on the top level; viewport level 1."""
    ob = _cube(name)
    md = ob.modifiers.new("Multires", 'MULTIRES')
    with bpy.context.temp_override(object=ob, active_object=ob):
        for _ in range(2):
            assert bpy.ops.object.multires_subdivide(modifier=md.name, mode='CATMULL_CLARK') == {'FINISHED'}
    ref_me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    for v in ref_me.vertices:
        v.co += v.co.normalized() * 0.15 * math.sin(v.co.x * 4.0) * math.cos(v.co.y * 3.0)
    ref = bpy.data.objects.new("sculptRef", ref_me)
    bpy.context.collection.objects.link(ref)
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob, ref],
                                   selected_editable_objects=[ob, ref]):
        assert bpy.ops.object.multires_reshape(modifier=md.name) == {'FINISHED'}
    bpy.data.objects.remove(ref)
    bpy.data.meshes.remove(ref_me)
    md.levels = 1
    return ob, md


def _top_level(ob):
    """Points at the top Multires level (the full sculpt detail)."""
    md = next(m for m in ob.modifiers if m.type == 'MULTIRES')
    keep = md.levels
    md.levels = md.total_levels
    try:
        return _points(ob)
    finally:
        md.levels = keep


# --- modifiers switched off in the viewport ------------------------------------------------------------------

def test_switched_off_subdivision_stays_on_the_copy_unapplied():
    _fresh()
    ob = _cube()
    sub = ob.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels, sub.render_levels = 2, 3
    sub.show_viewport = False
    shown = _points(ob)
    copy = _copy(ob)
    assert _names(copy) == ["Subdivision"], _names(copy)
    kept = copy.modifiers["Subdivision"]
    assert kept.type == 'SUBSURF' and not kept.show_viewport and kept.show_render
    assert (kept.levels, kept.render_levels) == (2, 3), (kept.levels, kept.render_levels)
    assert len(copy.data.vertices) == 8, "not applied: the copy keeps the cube's 8 points"
    assert _same(_points(copy), shown)
    kept.show_viewport = True                     # switching it on smooths the copy like the original
    sub.show_viewport = True
    assert _same(_points(copy), _points(ob))


def test_switched_off_modifiers_that_read_another_object_are_removed():
    """A switched-off Armature and Hook read other objects: a plain copy has no connections, so they go."""
    _fresh()
    arm = _skeleton()
    ob = _cube()
    skin = _skin(ob, arm)
    skin.show_viewport = False
    handle = bpy.data.objects.new("cluster1Handle", None)
    bpy.context.collection.objects.link(handle)
    hook = ob.modifiers.new("cluster1", 'HOOK')
    hook.object = handle
    hook.show_viewport = False
    smooth = ob.modifiers.new("deltaMush1", 'CORRECTIVE_SMOOTH')    # switched off, reads nothing: stays
    smooth.show_viewport = False
    shown = _points(ob)
    copy = _copy(ob)
    assert _names(copy) == ["deltaMush1"], _names(copy)
    assert not copy.modifiers["deltaMush1"].show_viewport
    assert _same(_points(copy), shown)
    assert skin.name in ob.modifiers and hook.name in ob.modifiers, "the original keeps them"
    # a curve's switched-off Hook goes too, a switched-off deformer that reads nothing stays
    cu = bpy.data.curves.new("curveShape1", 'CURVE')
    sp = cu.splines.new('POLY')
    sp.points.add(2)
    for i, p in enumerate(sp.points):
        p.co = (i * 0.1, 0, 0, 1)
    crv = bpy.data.objects.new("curve1", cu)
    bpy.context.collection.objects.link(crv)
    chook = crv.modifiers.new("cluster2", 'HOOK')
    chook.object = handle
    chook.vertex_indices_set([2])
    chook.show_viewport = False
    wave = crv.modifiers.new("wave1", 'WAVE')
    wave.show_viewport = False
    ccopy = _copy(crv)
    assert [m.name for m in ccopy.modifiers] == ["wave1"], [m.name for m in ccopy.modifiers]
    assert not ccopy.modifiers["wave1"].show_viewport


# --- Multires ----------------------------------------------------------------------------------------------

def test_multires_stays_live_with_its_sculpt_detail():
    _fresh()
    ob, md = _sculpted()
    md.render_levels = 2
    shown, detail = _points(ob), _top_level(ob)
    copy = _copy(ob)
    assert _names(copy) == ["Multires"], _names(copy)
    cm = copy.modifiers["Multires"]
    assert (cm.levels, cm.sculpt_levels, cm.render_levels, cm.total_levels) == (1, 2, 2, 2), \
        (cm.levels, cm.sculpt_levels, cm.render_levels, cm.total_levels)
    assert len(copy.data.vertices) == 8, "the base mesh stays the cage of the sculpt"
    assert _same(_points(copy), shown), "the copy shows what the original shows"
    assert _same(_top_level(copy), detail), "the sculpt detail of the top level is on the copy"


def test_multires_bakes_the_shape_key_mix_and_the_deformers_above_it():
    """Shape keys and a deformer above Multires: their result goes into the copy's base mesh (the sculpt stays on
    top of it, unchanged)."""
    _fresh()
    ob, md = _sculpted()
    ob.shape_key_add(name="Basis")
    sk = ob.shape_key_add(name="wide", from_mix=False)
    for v in sk.data:
        v.co.x *= 1.5
    sk.value = 0.5
    bend = ob.modifiers.new("bend1", 'SIMPLE_DEFORM')
    bend.deform_method, bend.angle = 'BEND', math.radians(40)
    ob.modifiers.move(len(ob.modifiers) - 1, 0)
    assert _names(ob) == ["bend1", "Multires"], _names(ob)
    shown, detail = _points(ob), _top_level(ob)
    copy = _copy(ob)
    assert _names(copy) == ["Multires"], _names(copy)
    assert copy.data.shape_keys is None, "no shape keys on the copy"
    assert len(copy.data.vertices) == 8
    assert _same(_points(copy), shown)
    assert _same(_top_level(copy), detail)
    assert ob.data.shape_keys is not None and "bend1" in ob.modifiers, "the original is untouched"


def test_modifiers_after_multires_stay_live_unless_they_read_another_object():
    """Mirror after Multires stays live (baking it would rebuild the base under the sculpt); a skin after Multires
    reads the skeleton, so it goes and the copy doesn't follow the rig."""
    _fresh()
    arm = _skeleton()
    ob, md = _sculpted()
    ob.location.x = 3.0
    mirror = ob.modifiers.new("polyMirror1", 'MIRROR')
    _skin(ob, arm)
    assert _names(ob) == ["Multires", "polyMirror1", "skinCluster1"], _names(ob)
    copy = _copy(ob)
    assert _names(copy) == ["Multires", "polyMirror1"], _names(copy)
    assert copy.modifiers["polyMirror1"].show_viewport and copy.modifiers["polyMirror1"].type == 'MIRROR'
    assert len(copy.data.vertices) == 8
    ob.modifiers["skinCluster1"].show_viewport = False
    rest = _points(ob)
    ob.modifiers["skinCluster1"].show_viewport = True
    assert _same(_points(copy), rest), "the copy is the sculpt without the skin"
    before = _points(copy)
    arm.pose.bones["joint2"].rotation_euler.x = math.radians(70)
    bpy.context.view_layer.update()
    assert not _same(_points(ob), rest), "the original follows its skeleton"
    assert _same(_points(copy), before), "the copy doesn't"
    assert mirror.name in ob.modifiers


def test_switched_off_multires_keeps_its_sculpt_and_what_follows():
    """Multires switched off in the viewport still holds the sculpt: the Mirror after it stays live too."""
    _fresh()
    ob, md = _sculpted()
    ob.modifiers.new("polyMirror1", 'MIRROR')
    md.show_viewport = False
    shown = _points(ob)
    md.show_viewport = True
    detail = _top_level(ob)
    md.show_viewport = False
    copy = _copy(ob)
    assert _names(copy) == ["Multires", "polyMirror1"], _names(copy)
    assert not copy.modifiers["Multires"].show_viewport and copy.modifiers["polyMirror1"].show_viewport
    assert len(copy.data.vertices) == 8
    assert _same(_points(copy), shown)
    copy.modifiers["Multires"].show_viewport = True
    assert _same(_top_level(copy), detail)


# --- Subdiv Proxy ------------------------------------------------------------------------------------------

def test_subdiv_proxy_copy_is_the_cage():
    _fresh()
    ob = _cube()
    _only(ob)
    assert bpy.ops.allset.smooth_proxy(action='CREATE') == {'FINISHED'}
    assert gk.subdiv_proxy(ob) is not None
    copy = _copy(ob)
    assert not [m for m in copy.modifiers if m.type == 'SUBSURF'], _names(copy)
    assert len(copy.data.vertices) == 8, "the cage, not the smooth mesh"
    assert gk.subdiv_proxy(copy) is None and gk.PROXY_KEY not in copy
    assert gk.subdiv_proxy(ob) is not None, "the original keeps its proxy"
    # "both" display: the copy has no cage wire of its own either
    _only(ob)
    assert bpy.ops.allset.smooth_proxy(action='BOTH') == {'FINISHED'}
    assert ob.show_wire
    copy2 = _copy(ob)
    assert not copy2.show_wire and not [m for m in copy2.modifiers if m.type == 'SUBSURF']
    # the cage shown alone (proxy switched off): still the cage only, not a switched-off Subdivision
    _only(ob)
    assert bpy.ops.allset.smooth_proxy(action='TOGGLE') == {'FINISHED'}
    assert not gk.subdiv_proxy(ob).show_viewport
    copy3 = _copy(ob)
    assert not [m for m in copy3.modifiers if m.type == 'SUBSURF'], _names(copy3)


def test_subdiv_proxy_menu_item_makes_the_same_proxy():
    _fresh()
    assert menu_map.MAP["Mesh/Smooth Proxy/Subdiv Proxy"] == ("allset.smooth_proxy", {"action": 'CREATE'})
    ob = _cube()
    display.set_smooth_preview(ob, 3)
    _only(ob)
    assert bpy.ops.allset.menu_item(item="Mesh/Smooth Proxy/Subdiv Proxy") == {'FINISHED'}
    proxy = gk.subdiv_proxy(ob)
    assert proxy is not None
    assert [m.name for m in ob.modifiers][-1] in display.PREVIEW_NAMES, "the smooth preview stays last"
    copy = _copy(ob)
    assert not [m for m in copy.modifiers if m.type == 'SUBSURF' and not display.is_preview(m)], _names(copy)
    assert len(copy.data.vertices) == 8


def test_input_graph_copy_keeps_the_proxy():
    _fresh()
    ob = _cube()
    _only(ob)
    assert bpy.ops.allset.smooth_proxy(action='CREATE') == {'FINISHED'}
    assert bpy.ops.allset.duplicate_special(input_graph=True) == {'FINISHED'}
    copy = bpy.context.active_object
    assert copy is not ob and gk.subdiv_proxy(copy) is not None


# --- still baked (unchanged) -------------------------------------------------------------------------------

def test_modelling_modifiers_shown_in_the_viewport_still_bake():
    _fresh()
    ob = _cube()
    for v in ob.data.vertices:
        v.co.x += 2.0
    ob.modifiers.new("polyMirror1", 'MIRROR')
    arr = ob.modifiers.new("array1", 'ARRAY')
    arr.count = 3
    shown = _points(ob)
    copy = _copy(ob)
    assert not _names(copy), _names(copy)
    assert len(copy.data.vertices) == len(shown) == 48, len(copy.data.vertices)
    assert _same(_points(copy), shown)


def test_boolean_with_its_cutter_still_bakes():
    _fresh()
    ob = _cube()
    cutter = _cube("pCube2", location=(1, 1, 1))
    cutter.display_type = 'WIRE'
    boo = ob.modifiers.new("polyCBoolOp1", 'BOOLEAN')
    boo.operation, boo.object = 'DIFFERENCE', cutter
    shown = _points(ob)
    copy = _copy(ob)
    assert not _names(copy), _names(copy)
    assert _same(_points(copy), shown) and len(copy.data.vertices) != 8
    assert cutter.name in bpy.data.objects, "the original's cutter stays"
    cutter.location.x = 5.0
    bpy.context.view_layer.update()
    assert _same(_points(copy), shown), "the copy doesn't follow the cutter"


def test_subdivision_render_above_viewport_bakes_at_the_viewport_level():
    """A Subdivision added by hand (not Subdiv Proxy) is modelling history: baked at the level the view shows."""
    _fresh()
    ob = _cube()
    sub = ob.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels, sub.render_levels = 1, 3
    shown = _points(ob)
    copy = _copy(ob)
    assert not _names(copy), _names(copy)
    assert len(copy.data.vertices) == 26, len(copy.data.vertices)
    assert _same(_points(copy), shown)
