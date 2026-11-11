"""#347: a plain copy (Edit > Duplicate, Ctrl+D) of a group whose child is hidden gets the same child copy as when the
child is shown, like Maya: the geometry its inputs make (modifiers and the shape-key mix baked in; Multires, the
user's Geometry Nodes and switched-off modifiers as on a shown child), and it stays hidden like the original. Hidden
here = hidden with the kit's Hide (h, Ctrl+H), in a collection switched off in the viewport, hidden in the view layer
or excluded from it, or hidden with Blender's own H. Shift+D, Duplicate Special, Smart Duplicate and
``cmds.duplicate`` make the same copy; Ctrl+D stays one undo step. Maya mode off leaves duplicating to Blender."""

from importlib import import_module

import bpy

import kit

duplicate = import_module(kit.MODULE + ".operators.duplicate")
display = import_module(kit.MODULE + ".operators.display")
gk = import_module(kit.MODULE + ".operators.global_keys4")
manip = import_module(kit.MODULE + ".operators.manip")
cmds = import_module(kit.MODULE + ".command_line.cmds_shim")
switch = import_module(kit.MODULE + ".switch")

HOWS = ("hide", "collection", "excluded", "layer_hidden", "eye")


def _fresh():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.curves, bpy.data.armatures, bpy.data.node_groups,
                 bpy.data.collections):
        for idb in list(coll):
            coll.remove(idb)
    duplicate.PAIRS.clear()
    bpy.context.scene.frame_set(1)


def _only(*obs):
    for o in bpy.context.view_layer.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = obs[-1]


def _cube(name="pCube1", coll=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(2.0, 0.0, 0.0))
    ob = bpy.context.active_object
    ob.name = name
    if coll is not None:
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        coll.objects.link(ob)
    return ob


def _mirrored(name="pCube1", coll=None):
    ob = _cube(name, coll)
    ob.modifiers.new("mirror1", 'MIRROR').use_axis[0] = True
    return ob


def _group(*children):
    root = bpy.data.objects.new("group1", None)
    bpy.context.scene.collection.objects.link(root)
    for ob in children:
        ob.parent = root
    return root


def _collection(how):
    """A collection for the child when ``how`` hides it through its collection."""
    if how not in ("collection", "excluded", "layer_hidden"):
        return None
    coll = bpy.data.collections.new("hiddenSet")
    bpy.context.scene.collection.children.link(coll)
    return coll


def _hide(ob, how, coll):
    vl = bpy.context.view_layer
    if how == "hide":                        # the kit's Maya Hide (Ctrl+H)
        _only(ob)
        assert bpy.ops.allset.visibility(action='HIDE') == {'FINISHED'}
        assert ob.hide_viewport
    elif how == "collection":
        coll.hide_viewport = True
    elif how == "excluded":
        vl.layer_collection.children[coll.name].exclude = True
    elif how == "layer_hidden":
        vl.layer_collection.children[coll.name].hide_viewport = True
    elif how == "eye":
        ob.hide_set(True)
    vl.update()


def _local(ob):
    """What ``ob`` shows now in its own space (sorted points)."""
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return sorted(tuple(round(c, 4) for c in v.co) for v in ev.data.vertices)


def _data(ob):
    """The points of ``ob``'s own mesh (no modifiers)."""
    return sorted(tuple(round(c, 4) for c in v.co) for v in ob.data.vertices)


def _names(ob):
    return [m.name for m in ob.modifiers if not display.is_preview(m)]


def _dup(root):
    _only(root)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    new_root = bpy.context.active_object
    assert new_root is not root
    return new_root


def _child_copy(new_root, kind='MESH'):
    kids = [k for k in new_root.children if k.type == kind]
    assert len(kids) == 1, [k.name for k in new_root.children]
    return kids[0]


def _hidden_like(copy, ob, how, coll):
    """The copy is hidden the way the original is."""
    vl = bpy.context.view_layer
    assert set(copy.users_collection) == set(ob.users_collection), \
        (how, [c.name for c in copy.users_collection], [c.name for c in ob.users_collection])
    assert copy.hide_viewport == ob.hide_viewport, (how, copy.hide_viewport)
    if how == "hide":
        assert copy.hide_viewport, "the copy of a hidden child stays hidden"
    if how == "excluded":
        assert copy.name not in vl.objects, "the copy stays out of the view layer like the original"
    if how in ("collection", "layer_hidden"):
        assert not copy.visible_get(), (how, "the copy stays hidden with its collection")
    if coll is not None:
        assert copy.name not in bpy.context.scene.collection.objects, "the copy stays in the original's collection"
    assert not set(copy.keys()) - set(ob.keys()), (how, sorted(set(copy.keys()) - set(ob.keys())))


def _shown_then_hidden(how, make):
    """``make(coll)`` builds the child; returns (child, group, what the child shows while shown, collection)."""
    _fresh()
    coll = _collection(how)
    ob = make(coll)
    root = _group(ob)
    bpy.context.view_layer.update()
    shown = _local(ob)
    _hide(ob, how, coll)
    return ob, root, shown, coll


# --- the report: Ctrl+D of a group with a hidden child ----------------------------------------------------------

def test_hidden_child_copy_is_baked_like_a_shown_one():
    for how in HOWS:
        ob, root, shown, coll = _shown_then_hidden(how, lambda c: _mirrored(coll=c))
        assert len(shown) == 16, (how, len(shown))
        copy = _child_copy(_dup(root))
        assert _names(copy) == [], (how, _names(copy), "the mirror is baked into the copy like a shown child's")
        assert _data(copy) == shown, (how, len(copy.data.vertices), "the copy keeps the geometry the mirror makes")
        if how != "eye":
            _hidden_like(copy, ob, how, coll)
        assert _names(ob) == ["mirror1"] and len(ob.data.vertices) == 8, (how, "the original is untouched")


def test_hidden_child_shape_key_mix_is_baked():
    for how in ("hide", "excluded"):
        def make(coll):
            ob = _cube(coll=coll)
            ob.shape_key_add(name="Basis")
            sk = ob.shape_key_add(name="tall", from_mix=False)
            for v in sk.data:
                v.co.z *= 3.0
            sk.value = 0.5
            return ob
        ob, root, shown, coll = _shown_then_hidden(how, make)
        copy = _child_copy(_dup(root))
        assert copy.data.shape_keys is None, how
        assert _data(copy) == shown, (how, "the copy keeps the shape-key mix it shows")
        _hidden_like(copy, ob, how, coll)


def test_hidden_child_with_a_switched_off_modifier():
    """The mirror shown in the viewport bakes; the switched-off bevel stays on the copy, not applied."""
    for how in ("hide", "collection"):
        def make(coll):
            ob = _mirrored(coll=coll)
            ob.modifiers.new("bevel1", 'BEVEL').show_viewport = False
            return ob
        ob, root, shown, coll = _shown_then_hidden(how, make)
        copy = _child_copy(_dup(root))
        assert _names(copy) == ["bevel1"] and not copy.modifiers["bevel1"].show_viewport, (how, _names(copy))
        assert _data(copy) == shown, (how, len(copy.data.vertices))
        _hidden_like(copy, ob, how, coll)


def test_hidden_child_with_multires_keeps_it_on_the_mixed_base():
    """Multires stays live; the shape-key mix under it goes into the base mesh like on a shown child."""
    for how in ("hide", "excluded"):
        def make(coll):
            ob = _cube(coll=coll)
            ob.shape_key_add(name="Basis")
            sk = ob.shape_key_add(name="wide", from_mix=False)
            for v in sk.data:
                v.co.x *= 1.5
            sk.value = 0.5
            md = ob.modifiers.new("Multires", 'MULTIRES')
            with bpy.context.temp_override(object=ob, active_object=ob):
                assert bpy.ops.object.multires_subdivide(modifier=md.name, mode='CATMULL_CLARK') == {'FINISHED'}
            return ob
        _fresh()
        coll = _collection(how)
        ob = make(coll)
        root = _group(ob)
        bpy.context.view_layer.update()
        ob.modifiers["Multires"].show_viewport = False
        mixed = _local(ob)                       # the base under Multires: the shape-key mix
        ob.modifiers["Multires"].show_viewport = True
        _hide(ob, how, coll)
        copy = _child_copy(_dup(root))
        assert _names(copy) == ["Multires"], (how, _names(copy))
        assert copy.data.shape_keys is None, how
        assert _data(copy) == mixed, (how, "the copy's base mesh holds the shape-key mix")
        _hidden_like(copy, ob, how, coll)


def test_hidden_child_with_user_geometry_nodes():
    """The user's node modifier stays live; the mirror before it bakes, so the node tree gets the same geometry."""
    for how in ("hide", "collection"):
        def make(coll):
            ob = _mirrored(coll=coll)
            ng = bpy.data.node_groups.new("passNodes", 'GeometryNodeTree')
            ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
            ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
            gin, gout = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
            ng.links.new(gin.outputs[0], gout.inputs[0])
            ob.modifiers.new("passNodes", 'NODES').node_group = ng
            return ob
        ob, root, shown, coll = _shown_then_hidden(how, make)
        copy = _child_copy(_dup(root))
        assert _names(copy) == ["passNodes"], (how, _names(copy))
        assert copy.modifiers["passNodes"].node_group is ob.modifiers["passNodes"].node_group
        assert _data(copy) == shown, (how, len(copy.data.vertices), "the mirror before the nodes is baked")
        _hidden_like(copy, ob, how, coll)


def test_a_child_under_the_hidden_copy_stays_hidden_by_it():
    """Maya: a node under a hidden node isn't drawn; the copy of the hidden child hides its own child the same way."""
    dag = import_module(kit.MODULE + ".operators.dag")
    _fresh()
    ob = _mirrored()
    leaf = _cube("leaf1")
    leaf.parent = ob
    root = _group(ob)
    _hide(ob, "hide", None)
    assert leaf.hide_get() and dag.MARK in leaf, "the kit's Hide hides the child under it"
    copy = _child_copy(_dup(root))
    leaf_copy = next(iter(copy.children))
    assert copy.hide_viewport and not leaf_copy.hide_viewport
    assert leaf_copy.hide_get() and dag.MARK in leaf_copy, "hidden by the hidden copy above it"
    assert len(copy.data.vertices) == 16 and len(leaf_copy.data.vertices) == 8
    assert leaf.hide_get() and dag.MARK in leaf, "the original's child stays hidden"


def test_hidden_subdiv_proxy_copy_is_the_cage():
    _fresh()
    ob = _cube()
    _only(ob)
    assert bpy.ops.allset.smooth_proxy(action='CREATE') == {'FINISHED'}
    root = _group(ob)
    _hide(ob, "hide", None)
    copy = _child_copy(_dup(root))
    assert not [m for m in copy.modifiers if m.type == 'SUBSURF'], _names(copy)
    assert len(copy.data.vertices) == 8 and gk.subdiv_proxy(copy) is None
    assert copy.hide_viewport


def test_hidden_curve_child_gets_its_deformer_baked():
    def make(coll):
        cu = bpy.data.curves.new("curveShape1", 'CURVE')
        sp = cu.splines.new('POLY')
        sp.points.add(2)
        for i, p in enumerate(sp.points):
            p.co = (i * 0.5, 0.0, 0.0, 1.0)
        crv = bpy.data.objects.new("curve1", cu)
        (coll or bpy.context.scene.collection).objects.link(crv)
        bend = crv.modifiers.new("bend1", 'SIMPLE_DEFORM')
        bend.deform_method, bend.deform_axis, bend.angle = 'BEND', 'Z', 1.0
        return crv

    def points(ob):
        return [tuple(round(c, 4) for c in p.co[:3]) for p in ob.data.splines[0].points]

    for how in ("hide", "excluded"):
        _fresh()
        coll = _collection(how)
        crv = make(coll)
        root = _group(crv)
        bpy.context.view_layer.update()
        _only(root)
        assert bpy.ops.allset.duplicate() == {'FINISHED'}
        shown = points(_child_copy(bpy.context.active_object, 'CURVE'))     # a shown curve's copy
        _hide(crv, how, coll)
        copy = _child_copy(_dup(root), 'CURVE')
        assert [m.name for m in copy.modifiers] == [], (how, [m.name for m in copy.modifiers])
        assert points(copy) == shown, (how, points(copy), shown)
        _hidden_like(copy, crv, how, coll)


def test_hidden_constrained_child_copy_stays_where_the_constraint_puts_it():
    _fresh()
    target = bpy.data.objects.new("locator1", None)
    bpy.context.scene.collection.objects.link(target)
    ob = _cube()
    con = ob.constraints.new('COPY_LOCATION')
    con.target = target
    root = _group(ob)
    bpy.context.view_layer.update()
    _hide(ob, "hide", None)
    target.location = (0.0, 3.0, 0.0)         # moved while the child is hidden
    bpy.context.view_layer.update()
    copy = _child_copy(_dup(root))
    assert not copy.constraints
    assert (copy.matrix_world.translation - target.location).length < 1e-4, copy.matrix_world.translation
    assert copy.hide_viewport


# --- the other plain copies ------------------------------------------------------------------------------------

def test_shift_d_special_smart_and_cmds_copies_of_a_hidden_child():
    def check(copy, tag):
        assert _names(copy) == [] and len(copy.data.vertices) == 16, (tag, _names(copy), len(copy.data.vertices))
        assert copy.hide_viewport, tag

    ob, root, shown, _coll = _shown_then_hidden("hide", lambda c: _mirrored(coll=c))
    _only(root)
    assert bpy.ops.allset.duplicate_with_transform() == {'FINISHED'}
    check(_child_copy(bpy.context.active_object), "Shift+D")
    _only(root)
    assert bpy.ops.allset.duplicate_special(copies=2) == {'FINISHED'}
    roots = [o for o in bpy.context.selected_objects if o.type == 'EMPTY']
    assert len(roots) == 2, [o.name for o in bpy.context.selected_objects]
    for r in roots:
        check(_child_copy(r), "Duplicate Special")
    _only(root)
    manip.start_duplicate(bpy.context)
    check(_child_copy(bpy.context.active_object), "Smart Duplicate")
    check(_child_copy(bpy.data.objects[cmds.duplicate(root.name)[0]]), "cmds.duplicate of the group")
    copy = bpy.data.objects[cmds.duplicate(ob.name)[0]]           # the hidden object itself
    check(copy, "cmds.duplicate of the hidden object")
    assert _data(copy) == shown


def test_maya_mode_off_leaves_duplicate_to_blender():
    """Plain Blender (Maya mode off) has none of the kit's duplicates: Blender's own duplicate keeps the modifiers."""
    switch.set_mode(False, layout=False)
    try:
        assert not hasattr(bpy.types, "ALLSET_OT_duplicate")
        _fresh()
        ob = _mirrored()
        bpy.context.view_layer.update()
        _only(ob)
        assert bpy.ops.object.duplicate() == {'FINISHED'}
        copy = bpy.context.active_object
        assert copy is not ob and [m.name for m in copy.modifiers] == ["mirror1"]
    finally:
        switch.set_mode(True, layout=False)


def test_ctrl_d_of_a_hidden_child_is_one_undo_step():
    for how in ("hide", "excluded"):
        ob, root, shown, coll = _shown_then_hidden(how, lambda c: _mirrored(coll=c))
        before = sorted(o.name for o in bpy.data.objects)
        bpy.ops.ed.undo_push(message="before")
        _only(root)
        assert bpy.ops.allset.duplicate('EXEC_DEFAULT', True) == {'FINISHED'}
        assert len(bpy.data.objects) == len(before) + 2, how
        bpy.ops.ed.undo()
        assert sorted(o.name for o in bpy.data.objects) == before, (how, "one undo takes both copies back")
        ob = bpy.data.objects["pCube1"]
        assert _names(ob) == ["mirror1"], how
        if how == "hide":
            assert ob.hide_viewport
        else:
            assert bpy.context.view_layer.layer_collection.children["hiddenSet"].exclude
            assert ob.name not in bpy.context.scene.collection.objects
