"""#347: a plain copy (Edit > Duplicate, Ctrl+D) and Geometry Nodes.

- A Geometry Nodes modifier the user set up stays live on the copy with its inputs (values, attribute inputs and
  the objects it reads); the modifiers after it stay live too. What comes before it (modifiers, the shape-key mix,
  a skin) is baked into the copy's mesh, so the node tree gets the same geometry and the copy shows what the
  original shows without following the original's rig or animation.
- The kit's own Geometry Nodes modifiers (Maya deformers such as the wire) are baked like Maya history.
"""

import math
from importlib import import_module

import bpy
from mathutils import Vector

import kit

duplicate = import_module(kit.MODULE + ".operators.duplicate")
display = import_module(kit.MODULE + ".operators.display")
wire = import_module(kit.MODULE + ".operators.wire_deformer")
compat = import_module(kit.MODULE + ".compat")


def _fresh():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.armatures, bpy.data.curves, bpy.data.actions,
                 bpy.data.node_groups):
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
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return sorted((tuple(round(c, 4) for c in ev.matrix_world @ v.co) for v in ev.data.vertices))


def _same(a, b, eps=2e-4):
    return len(a) == len(b) and all((Vector(p) - Vector(q)).length < eps for p, q in zip(a, b))


def _copy(ob):
    _only(ob)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    copy = bpy.context.active_object
    assert copy is not ob and copy.data is not ob.data
    return copy


def _names(ob):
    return [m.name for m in ob.modifiers if not display.is_preview(m)]


def _offset_group(name="offsetNodes"):
    """A user node group: Set Position by the Offset input on the Selection, joined with the Target object's
    geometry."""
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Offset", in_out='INPUT', socket_type='NodeSocketVector')
    sel = ng.interface.new_socket("Selection", in_out='INPUT', socket_type='NodeSocketBool')
    sel.default_value = True
    ng.interface.new_socket("Target", in_out='INPUT', socket_type='NodeSocketObject')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi, go = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
    setpos = ng.nodes.new("GeometryNodeSetPosition")
    info = ng.nodes.new("GeometryNodeObjectInfo")
    info.transform_space = 'RELATIVE'
    join = ng.nodes.new("GeometryNodeJoinGeometry")
    ng.links.new(gi.outputs["Geometry"], setpos.inputs["Geometry"])
    ng.links.new(gi.outputs["Offset"], setpos.inputs["Offset"])
    ng.links.new(gi.outputs["Selection"], setpos.inputs["Selection"])
    ng.links.new(gi.outputs["Target"], info.inputs["Object"])
    ng.links.new(setpos.outputs["Geometry"], join.inputs["Geometry"])
    ng.links.new(info.outputs["Geometry"], join.inputs["Geometry"])
    ng.links.new(join.outputs["Geometry"], go.inputs["Geometry"])
    return ng


def _key(md, name):
    return md.node_group.interface.items_tree[name].identifier


def _get(md, name):
    return compat.gn_input_get(md, _key(md, name))


def _set(md, name, value):
    compat.gn_input_set(md, _key(md, name), value)
    md.id_data.update_tag()


def _user_nodes(ob, name="offsetNodes", offset=(0.0, 0.0, 0.5), target=None, group=None):
    md = ob.modifiers.new(name, 'NODES')
    md.node_group = group or _offset_group()
    _set(md, "Offset", offset)
    if target is not None:
        _set(md, "Target", target)
    return md


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


def _wire_curve(name="curve1", z=1.0):
    cu = bpy.data.curves.new(name + "Shape", 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('NURBS')
    sp.points.add(3)
    for p, x in zip(sp.points, (-3, -1, 1, 3)):
        p.co = (x, 0, z, 1)
    sp.order_u = 4
    sp.use_endpoint_u = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    return ob


# --- a user Geometry Nodes modifier ------------------------------------------------------------------------

def test_user_geometry_nodes_stay_live_with_their_inputs():
    """Bevel before the node tree is baked (the tree gets the same geometry); the node modifier stays with the same
    node group, values and attribute input, and still works on the copy."""
    _fresh()
    ob = _cube()
    top = ob.vertex_groups.new(name="top")
    top.add([v.index for v in ob.data.vertices if v.co.z > 0], 1.0, 'REPLACE')
    bevel = ob.modifiers.new("polyBevel1", 'BEVEL')
    bevel.width = 0.1
    md = _user_nodes(ob)
    compat.gn_input_attribute(md, _key(md, "Selection"), "top")
    shown = _points(ob)
    copy = _copy(ob)
    assert _names(copy) == ["offsetNodes"], _names(copy)
    cm = copy.modifiers["offsetNodes"]
    assert cm.type == 'NODES' and cm.show_viewport and cm.node_group is md.node_group
    assert tuple(_get(cm, "Offset")) == (0.0, 0.0, 0.5), tuple(_get(cm, "Offset"))
    if compat.GN_INPUT_STRUCT:
        item = getattr(cm.properties.inputs, _key(cm, "Selection"))
        assert (item.type, item.attribute_name) == ('ATTRIBUTE', "top"), (item.type, item.attribute_name)
    assert "top" in copy.vertex_groups, "the vertex group the node tree reads is on the copy"
    assert len(copy.data.vertices) == 24, "the bevel is baked into the copy's mesh"
    assert _same(_points(copy), shown), "the copy shows what the original shows"
    bevel.width = 0.3                              # the original's bevel no longer shapes the copy
    _set(cm, "Offset", (0.0, 0.0, 2.0))            # the copy's node tree is live
    zs = [p[2] for p in _points(copy)]
    assert abs(max(zs) - 3.0) < 1e-3, max(zs)
    assert abs(max(p[2] for p in _points(ob)) - 1.5) < 1e-3, "the original keeps its own input value"
    assert "polyBevel1" in ob.modifiers and "offsetNodes" in ob.modifiers


def test_modifiers_after_user_geometry_nodes_stay_live():
    """Mirror before the tree is baked; the Subdivision after it stays live (it works on the tree's result)."""
    _fresh()
    ob = _cube(location=(2, 0, 0))
    ob.modifiers.new("polyMirror1", 'MIRROR')
    _user_nodes(ob)
    sub = ob.modifiers.new("polySmoothFace1", 'SUBSURF')
    sub.levels = 1
    shown = _points(ob)
    copy = _copy(ob)
    assert _names(copy) == ["offsetNodes", "polySmoothFace1"], _names(copy)
    assert copy.modifiers["polySmoothFace1"].type == 'SUBSURF' and copy.modifiers["polySmoothFace1"].levels == 1
    assert len(copy.data.vertices) == 16, "the mirror is baked into the copy's mesh"
    assert _same(_points(copy), shown)


def test_geometry_nodes_object_input_still_points_at_that_object():
    _fresh()
    ob = _cube()
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.3, location=(3, 0, 0))
    target = bpy.context.active_object
    target.name = "pSphere1"
    _user_nodes(ob, target=target)
    shown = _points(ob)
    assert len(shown) == 8 + 12, len(shown)
    copy = _copy(ob)
    cm = copy.modifiers["offsetNodes"]
    assert _get(cm, "Target") == target, _get(cm, "Target")
    assert _same(_points(copy), shown)
    target.location.y = 4.0                        # the copy's tree still reads that object
    assert max(p[1] for p in _points(copy)) > 3.5


def test_skin_and_shape_keys_before_geometry_nodes_are_baked():
    """The #347 case with a node tree on top: the shape-key mix and the skin go into the copy's mesh (its pose
    kept), the node modifier stays, and the copy doesn't follow the original's skeleton or keys."""
    _fresh()
    arm = _skeleton()
    ob = _cube()
    ob.shape_key_add(name="Basis")
    sk = ob.shape_key_add(name="wide", from_mix=False)
    for v in sk.data:
        v.co.x *= 1.5
    sk.value = 0.5
    g1, g2 = ob.vertex_groups.new(name="joint1"), ob.vertex_groups.new(name="joint2")
    for v in ob.data.vertices:
        (g2 if v.co.z > 0 else g1).add([v.index], 1.0, 'REPLACE')
    skin = ob.modifiers.new("skinCluster1", 'ARMATURE')
    skin.object = arm
    _user_nodes(ob)
    arm.pose.bones["joint2"].rotation_euler.x = math.radians(40)
    shown = _points(ob)
    copy = _copy(ob)
    assert _names(copy) == ["offsetNodes"], _names(copy)
    assert copy.data.shape_keys is None, "no shape keys on the copy"
    assert _same(_points(copy), shown), "the copy keeps the pose it shows"
    arm.pose.bones["joint2"].rotation_euler.x = math.radians(80)
    sk.value = 1.0
    assert not _same(_points(ob), shown), "the original follows its skeleton and keys"
    assert _same(_points(copy), shown), "the copy doesn't"


def test_switched_off_user_geometry_nodes_stay_with_their_object_input():
    _fresh()
    ob = _cube()
    target = _cube("pCube9", location=(4, 0, 0))
    md = _user_nodes(ob, target=target)
    md.show_viewport = False
    shown = _points(ob)
    copy = _copy(ob)
    assert _names(copy) == ["offsetNodes"], _names(copy)
    cm = copy.modifiers["offsetNodes"]
    assert not cm.show_viewport and _get(cm, "Target") == target
    assert _same(_points(copy), shown)


def test_user_geometry_nodes_after_multires_stay_with_their_object_input():
    """Multires stays live with its levels; a node modifier after it keeps the object it reads."""
    _fresh()
    ob = _cube()
    mr = ob.modifiers.new("Multires", 'MULTIRES')
    with bpy.context.temp_override(object=ob, active_object=ob):
        assert bpy.ops.object.multires_subdivide(modifier=mr.name, mode='CATMULL_CLARK') == {'FINISHED'}
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.3, location=(3, 0, 0))
    target = bpy.context.active_object
    _user_nodes(ob, target=target)
    shown = _points(ob)
    copy = _copy(ob)
    assert _names(copy) == ["Multires", "offsetNodes"], _names(copy)
    assert _get(copy.modifiers["offsetNodes"], "Target") == target
    assert len(copy.data.vertices) == 8
    assert _same(_points(copy), shown)


def test_mesh_to_points_tree_stays_live():
    """A tree that turns the mesh into points: the copy keeps it and shows the same points."""
    _fresh()
    ng = bpy.data.node_groups.new("toPoints", 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi, go = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
    pts = ng.nodes.new("GeometryNodeMeshToPoints")
    ng.links.new(gi.outputs["Geometry"], pts.inputs["Mesh"])
    ng.links.new(pts.outputs["Points"], go.inputs["Geometry"])
    ob = _cube()
    ob.modifiers.new("polyBevel1", 'BEVEL').width = 0.1
    md = ob.modifiers.new("toPoints", 'NODES')
    md.node_group = ng
    copy = _copy(ob)
    assert _names(copy) == ["toPoints"], _names(copy)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    for o in (ob, copy):
        geo = o.evaluated_get(dg).evaluated_geometry()
        assert geo.pointcloud is not None and len(geo.pointcloud.points) == 24, o.name


# --- the kit's own Geometry Nodes modifiers ----------------------------------------------------------------

def _wired_grid():
    _fresh()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=12, y_subdivisions=4, size=6)
    ob = bpy.context.active_object
    ob.name = "pPlane1"
    curve = _wire_curve()
    bpy.context.view_layer.update()
    _only(ob, curve)
    assert bpy.ops.allset.deformer(kind='WIRE') == {'FINISHED'}
    md = ob.modifiers["wire1"]
    assert wire.is_wire(md)
    wire.set_(md, "Dropoff Distance", 10.0)
    curve.location.z += 1.0
    return ob, curve, md


def test_kit_geometry_nodes_deformer_is_baked():
    """The kit's wire (Maya wire deformer) is history: the copy has its result and no wire."""
    ob, curve, _md = _wired_grid()
    shown = _points(ob)
    assert max(p[2] for p in shown) > 0.1, "the wire moves the grid"
    copy = _copy(ob)
    assert _names(copy) == [], _names(copy)
    assert _same(_points(copy), shown)
    curve.location.z += 1.0
    assert _same(_points(copy), shown), "the copy doesn't follow the wire curve"


def test_switched_off_kit_geometry_nodes_that_read_another_object_are_left_out():
    """A switched-off wire reads its curve: a plain copy has no connections, so it goes (no error)."""
    ob, _curve, md = _wired_grid()
    md.show_viewport = False
    shown = _points(ob)
    copy = _copy(ob)
    assert _names(copy) == [], _names(copy)
    assert _same(_points(copy), shown)
