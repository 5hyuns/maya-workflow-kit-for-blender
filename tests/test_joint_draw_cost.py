"""Maya joints stay light when nothing about a rig changed: a view keeps every skeleton's lines until something that
can change them reaches that skeleton.

- moving another object, a material or a key on another object builds no joint lines (no new joined lines either);
- a joint selection recolours the skeleton it changed and keeps its geometry; the other skeletons stay as they were;
- an edit (a hidden joint, a custom shape's geometry) builds the touched skeleton again; a new frame builds only the
  skeletons whose pose changed;
- a skeleton in Edit Mode is built again only when its edit bones read differently, and the others stay;
- a redraw doesn't walk every object of the scene to find the skeletons; Draw Label joints of one skeleton are kept
  when another is selected;
- repeated clicks in the same view project the drawn lines once.
In every case the lines and colours equal a build from scratch."""

import math
import time
from importlib import import_module
from types import SimpleNamespace

import bpy
import numpy as np
from mathutils import Vector

import kit

mj = import_module(kit.MODULE + ".ui.maya_joints")
joints = import_module(kit.MODULE + ".operators.joints")
labels = import_module(kit.MODULE + ".operators.joint_labels")
preselect = import_module(kit.MODULE + ".operators.preselect")
lj = import_module(kit.MODULE + ".ui.layer_joints")


class _Count:
    """Counts calls of ``owner.name`` (several names: one count each)."""

    def __init__(self, owner, *names):
        self.owner, self.names = owner, names
        self.calls = dict.fromkeys(names, 0)
        self.real = {n: getattr(owner, n) for n in names}

    def __enter__(self):
        for n in self.names:
            def counted(*a, _n=n, **k):
                self.calls[_n] += 1
                return self.real[_n](*a, **k)
            setattr(self.owner, n, counted)
        return self

    def __exit__(self, *exc):
        for n in self.names:
            setattr(self.owner, n, self.real[n])

    def __getitem__(self, name):
        return self.calls[name]


BUILD = ("_parts", "_joint_list", "_spheres", "_bone_array", "_control_lines", "_read_widget", "_joint_parts")


def _object_mode():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _clear():
    _object_mode()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for data in (bpy.data.armatures, bpy.data.meshes, bpy.data.materials, bpy.data.actions):
        for d in list(data):
            data.remove(d)
    mj._forget()


def _circle(name, n=12, r=0.15):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), 0.0) for i in range(n)],
                   [(i, (i + 1) % n) for i in range(n)], [])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _rig(x, count=14, ctrl=None):
    """A kit skeleton with branches; every third joint draws ``ctrl`` as its custom shape."""
    arm = joints.new_skeleton(bpy.context)
    made = [joints.add_joint(arm, Vector((x, 0, 0)), None, length=0.5)]
    for i in range(1, count):
        parent = made[(i - 1) // 2 if i % 5 == 0 else i - 1]
        made.append(joints.add_joint(arm, Vector((x + 0.3 * math.sin(i), 0.2 * (i % 3), 0.15 * i)), parent,
                                     length=0.1))
    joints.finish(bpy.context, arm, made)
    _object_mode()
    if ctrl is not None:
        for i, pb in enumerate(arm.pose.bones):
            if i % 3 == 1:
                pb.custom_shape = ctrl
    return arm


def _scene():
    _clear()
    ctrl = _circle("ctrl")
    a, b = _rig(0.0, ctrl=ctrl), _rig(2.0, ctrl=ctrl)
    bpy.ops.mesh.primitive_cube_add(location=(5.0, 0.0, 0.0))
    cube = bpy.context.object
    cube.name = "plain"
    for ob in bpy.data.objects:
        ob.select_set(False)
    bpy.context.view_layer.objects.active = None
    bpy.context.view_layer.update()
    return a, b, cube, ctrl


def _space():
    return next(ar.spaces.active for s in bpy.data.screens for ar in s.areas if ar.type == 'VIEW_3D')


def _view(objects, mode='OBJECT'):
    return SimpleNamespace(space_data=_space(), region_data=SimpleNamespace(is_perspective=True),
                           scene=bpy.context.scene, view_layer=bpy.context.view_layer, visible_objects=objects,
                           mode=mode, screen=None)


def _fresh(view):
    """The view's lines built from scratch (nothing kept)."""
    mj._forget()
    got = mj._joined(view)
    return np.array(got[0]), np.array(got[1])


def _same(got, want, what):
    pts, cols = np.array(got[0]), np.array(got[1])
    assert pts.shape == want[0].shape and np.array_equal(pts, want[0]), f"{what}: points"
    assert np.array_equal(cols, want[1]), f"{what}: colours"


def test_another_objects_move_selection_or_material_builds_no_joint_lines():
    """A mesh dragged, selected or given a material, a key on it: no skeleton is built again and the views keep
    their joined lines (no new GPU lines)."""
    a, b, cube, _ctrl = _scene()
    view = _view([a, b])
    real = mj.transforming
    try:
        first = mj._joined(view)
        mj.transforming = lambda: True            # a move runs in Object Mode
        with _Count(mj, *BUILD) as n:
            for step in range(3):
                cube.location.x += 0.2
                bpy.context.view_layer.update()
                assert mj._joined(view) is first, f"drag step {step}: the joined lines are kept"
        mj.transforming = real
        with _Count(mj, *BUILD) as m:
            cube.select_set(True)                 # a Scene update
            bpy.context.view_layer.objects.active = cube
            bpy.context.view_layer.update()
            assert mj._joined(view) is first, "selecting a mesh keeps the joint lines"
            mat = bpy.data.materials.new("m")
            cube.data.materials.append(mat)
            bpy.context.view_layer.update()
            mat.diffuse_color = (1.0, 0.0, 0.0, 1.0)
            bpy.context.view_layer.update()
            cube.keyframe_insert("location", frame=1)
            bpy.context.view_layer.update()
            got = mj._joined(view)
        assert not any(n[f] for f in BUILD if f != "_parts") and not n["_parts"], n.calls
        assert not any(m[f] for f in BUILD if f != "_parts"), f"nothing is read or built again: {m.calls}"
        _same(got, _fresh(view), "after the mesh edits")
    finally:
        mj.transforming = real


def test_a_joint_selection_recolours_its_skeleton_only():
    """Selecting joints in Pose Mode: the touched skeleton keeps its joint list and geometry (only its colours and
    axes change), the other skeleton is not looked at; the lines equal a build from scratch."""
    a, b, _cube, _ctrl = _scene()
    bpy.context.view_layer.objects.active = a
    a.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    view = _view([a, b], 'POSE')
    try:
        mj._joined(view)
        kept_b = mj._PARTS[b.as_pointer()]
        for picks in (["j3"], ["j3", "j7"], []):
            names = [pb.name for pb in a.pose.bones]
            chosen = [names[int(p[1:])] for p in picks]
            for pb in a.pose.bones:
                pb.select = pb.name in chosen
            a.data.bones.active = a.data.bones[chosen[-1]] if chosen else None
            bpy.context.view_layer.update()
            with _Count(mj, *BUILD) as n:
                got = mj._joined(view)
            assert n["_parts"] == 1 and not n["_joint_list"], \
                f"{picks}: only the touched skeleton is looked at, its joint list kept ({n.calls})"
            assert not (n["_spheres"] or n["_bone_array"] or n["_control_lines"] or n["_read_widget"]), \
                f"{picks}: the geometry is kept ({n.calls})"
            assert mj._PARTS[b.as_pointer()] is kept_b, f"{picks}: the other skeleton's lines are kept"
            _same(got, _fresh(view), f"selection {picks}")
            kept_b = mj._PARTS[b.as_pointer()]
    finally:
        _object_mode()


def test_edits_and_frames_build_only_what_changed():
    """A control's shape scaled reads its skeleton again (and only it); a custom shape's geometry edited builds the
    skeletons that draw it; a new frame (playing) builds the lines of the animated skeleton only. The lines equal a
    build from scratch each time."""
    a, b, _cube, ctrl = _scene()
    for k in (1, 10):
        for i, pb in enumerate(a.pose.bones):
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler = (0.1 * k, 0.02 * i, 0.0)
            pb.keyframe_insert("rotation_euler", frame=k)
    bpy.context.scene.frame_set(1)
    view = _view([a, b])
    real = mj.transforming
    try:
        mj._joined(view)
        a.pose.bones[4].custom_shape_scale_xyz = (2.0, 2.0, 2.0)
        bpy.context.view_layer.update()
        with _Count(mj, *BUILD) as n:
            got = mj._joined(view)
        assert n["_parts"] == 1 and n["_joint_list"] == 1 and n["_control_lines"] == 1, \
            f"a scaled control shape: its skeleton only ({n.calls})"
        _same(got, _fresh(view), "a scaled control shape")
        ctrl.data.vertices[0].co.x += 0.05
        ctrl.data.update()
        bpy.context.view_layer.update()
        with _Count(mj, *BUILD) as n:
            got = mj._joined(view)
        assert n["_parts"] == 2 and n["_read_widget"] == 1, f"an edited control shape: both, read once ({n.calls})"
        _same(got, _fresh(view), "an edited control shape")
        mj.transforming = lambda: True            # what is kept while playing is kept
        kept_b = mj._PARTS[b.as_pointer()]
        for frame in (4, 7):
            bpy.context.scene.frame_set(frame)
            with _Count(mj, *BUILD) as n:
                got = mj._joined(view)
            assert n["_spheres"] == 1 and n["_joint_list"] == 0, f"frame {frame}: the animated skeleton ({n.calls})"
            assert mj._PARTS[b.as_pointer()] is kept_b, f"frame {frame}: the still skeleton keeps its lines"
            want = _fresh(view)
            _same(got, want, f"frame {frame}")
            kept_b = mj._PARTS[b.as_pointer()]
    finally:
        mj.transforming = real
        bpy.context.scene.frame_set(1)


def test_edit_mode_builds_the_edited_skeleton_when_it_changes():
    """A skeleton in Edit Mode: redraws without a change build nothing; an edit bone moved, a Maya frame written or a
    bone put in a hidden bone collection (neither sends an update) builds it again; the skeleton in Object Mode keeps
    its geometry. The lines equal the view's own lines."""
    a, b, _cube, _ctrl = _scene()
    hidden = a.data.collections.new("hidden")
    hidden.is_visible = False
    bpy.context.view_layer.objects.active = a
    a.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    view = _view([a, b], 'EDIT_ARMATURE')
    try:
        mj._joined(view)
        with _Count(mj, *BUILD) as n:
            for _redraw in range(3):
                mj._joined(view)
        assert not any(n.calls.values()), f"no change: nothing built ({n.calls})"
        eb = a.data.edit_bones[3]
        for step, edit in enumerate((lambda: setattr(eb, "head", eb.head + Vector((0.05, 0.0, 0.0))),
                                     lambda: eb.__setitem__(joints.MAYA_FRAME, [0.9238795, 0.0, 0.3826834, 0.0]),
                                     lambda: setattr(eb, "select", True),
                                     lambda: hidden.assign(a.data.edit_bones[5]))):
            edit()
            if step in (0, 2):
                bpy.context.view_layer.update()
            with _Count(mj, *BUILD) as n:
                got = mj._joined(view)
            # (an Edit Mode update makes display layers read every skeleton's joint list again: the other one
            # keeps its geometry)
            assert n["_joint_parts"] == 1 and n["_spheres"] == 1 and not n["_bone_array"] and \
                not n["_control_lines"], f"edit {step}: the edited skeleton is built ({n.calls})"
            pts, cols = mj.view_lines(view)
            assert np.array_equal(got[0], pts) and np.array_equal(got[1], cols), f"edit {step}: the view's lines"
    finally:
        _object_mode()


def test_views_find_their_skeletons_without_walking_every_object():
    """A redraw lists the view layer's skeletons from a list read once per update that can add or remove objects:
    the same skeletons in the same order as the visible objects, also after one is hidden or added; the time
    doesn't grow with thousands of other objects."""
    a, b, _cube, _ctrl = _scene()
    space = _space()
    ctx = bpy.context

    def want():
        return [ob for ob in ctx.visible_objects if ob.type == 'ARMATURE' and ob.visible_in_viewport_get(space)]

    assert mj._view_skeletons(ctx, space) == want() == [a, b]
    assert mj.armatures(ctx.view_layer) is mj.armatures(ctx.view_layer), "read once"
    b.hide_set(True)
    bpy.context.view_layer.update()
    assert mj._view_skeletons(ctx, space) == want() == [a]
    b.hide_set(False)
    c = _rig(4.0)
    bpy.context.view_layer.update()
    assert mj._view_skeletons(ctx, space) == want() == [a, b, c], "a new skeleton"

    def per_call():
        best = float("inf")
        for _rep in range(5):
            t = time.perf_counter()
            for _ in range(200):
                mj._view_skeletons(ctx, space)
            best = min(best, (time.perf_counter() - t) / 200)
        return best

    small = per_call()
    me = bpy.data.meshes.new("many")
    coll = bpy.data.collections.new("many")
    bpy.context.scene.collection.children.link(coll)
    for i in range(4000):
        coll.objects.link(bpy.data.objects.new(f"many_{i}", me))
    bpy.context.view_layer.update()
    mj._view_skeletons(ctx, space)
    big = per_call()
    assert big < 3 * small + 2e-5, f"4000 more objects: {1e6 * big:.1f} us vs {1e6 * small:.1f} us per redraw"
    assert mj._view_skeletons(ctx, space) == want()


def test_draw_label_joints_of_other_skeletons_stay_found():
    """Selecting a joint of one skeleton keeps the Draw Label joints found for another skeleton."""
    a, b, _cube, _ctrl = _scene()
    for ob in (a, b):
        labels.set_label(ob.data.bones[2], side=labels.LEFT, type=labels.T_KNEE, draw=True)
    ctx = SimpleNamespace(screen=None, view_layer=bpy.context.view_layer)
    labels._labelled.clear()
    try:
        first = labels.label_points(ctx)
        kept = labels._labelled[b.as_pointer()][1]
        a.pose.bones[1].select = True
        bpy.context.view_layer.update()
        assert labels.label_points(ctx) == first
        assert labels._labelled[b.as_pointer()][1] is kept, "the other skeleton's labels are kept"
    finally:
        labels._labelled.clear()


def _front_view():
    """Front orthographic region 200 x 100: world (x, z) -> (100 + 20 x, 50 + 20 z) px."""
    from mathutils import Matrix
    view = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, -10), (0, 0, 0, 1)))
    proj = Matrix(((0.2, 0, 0, 0), (0, 0.4, 0, 0), (0, 0, -0.01, 0), (0, 0, 0, 1)))
    return SimpleNamespace(region_data=SimpleNamespace(perspective_matrix=proj @ view, is_perspective=False),
                           region=SimpleNamespace(width=200, height=100, as_pointer=lambda: 1),
                           space_data=_space(), window=None, scene=bpy.context.scene,
                           view_layer=bpy.context.view_layer, mode='OBJECT', screen=None,
                           evaluated_depsgraph_get=bpy.context.evaluated_depsgraph_get)


def test_clicks_in_one_view_project_the_drawn_lines_once():
    """After a draw, clicks in the same view project the skeleton's drawn lines once (a selection redraw keeps
    them); the distances are the joint-by-joint ones; another view projects them again."""
    a, b, _cube, _ctrl = _scene()
    ctx = _front_view()
    ctx.visible_objects = [a, b]
    mice = ((100.0, 52.0), (108.0, 60.0), (140.0, 55.0))
    want = {m: mj._screen_distance(ctx, a, m) for m in mice}     # read joint by joint (nothing drawn yet)
    mj._joined(ctx)
    with _Count(preselect, "project") as n:
        for m in mice:
            got = mj.screen_distance(ctx, a, m)
            assert set(got) == set(want[m]) and all(abs(got[k] - want[m][k]) < 1e-3 for k in got), m
        a.select_set(True)                        # a selection and its redraw keep the drawn lines
        bpy.context.view_layer.update()
        mj._joined(ctx)
        for m in mice:
            assert mj.screen_distance(ctx, a, m).keys() == want[m].keys()
    assert n["project"] == 1, f"the drawn lines are projected once, got {n['project']}"
    other = _front_view()
    other.region.width = 300
    with _Count(preselect, "project") as n:
        mj.screen_distance(other, a, mice[0])
    assert n["project"] == 1, "another view projects them again"


def test_joint_colours_are_the_per_joint_colours():
    """The colours of all joints at once equal the joint-by-joint colours: own selection, the lead, a Template /
    Reference layer, else the nearest selected joint above."""
    a, _b, _cube, _ctrl = _scene()
    jl = mj._joint_list(a)
    names = jl.names
    real = lj.state
    lj.state = lambda ob: {names[5]: lj.TEMPLATE, names[6]: lj.TEMPLATE, names[9]: lj.REFERENCE}
    try:
        jl = mj._joint_list(a)
        for sel, lead in (({names[0]}, names[0]), ({names[2], names[5]}, names[5]), ({names[1]}, None),
                          (set(names[3:8]), names[4]), (set(), None)):
            col = mj.colours(jl.js, sel, lead)
            want = np.array([(*col[nm], 1.0) for nm in names], np.float32) if sel else None
            got = mj._joint_rgba(jl, sel, lead)
            if want is not None:
                assert np.array_equal(got, want), (sel, lead)
    finally:
        lj.state = real
