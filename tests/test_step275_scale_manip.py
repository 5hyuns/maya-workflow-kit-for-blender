"""Step 275 (#200): the Scale manipulator's centre and axis handles drag Maya's way.

Centre: f = 1 + dx * wpp / R (horizontal px since the press, world length of a px at the pivot depth, pivot to the
farthest corner of the lead's world box); axis: f = 1 + d / L along the handle. Numbers below are Maya's results
for the same drags. The real drag: tests/gui/gui_step275_scale_manip.py."""

import math
from importlib import import_module
from types import SimpleNamespace

import bmesh
import bpy

import kit

ms = import_module(kit.MODULE + ".operators.manip_scale")
manip = import_module(kit.MODULE + ".operators.manip")
manipulator = import_module(kit.MODULE + ".ui.manipulator")

WPP = 0.010511716        # unit cube 20 units from a 35 mm persp camera, 1957 px wide view


def close(a, b, tol=1e-5):
    return abs(a - b) <= tol


def test_uniform_factor_numbers():
    r = math.sqrt(3) / 2
    for dx, want in ((50, 1.606894), (-50, 0.393106), (-100, -0.213788), (-400, -3.855154), (10, 1.121379)):
        got = ms.uniform_factor(dx, WPP, r)
        assert close(got, want), (dx, got, want)
    # through 0 with no clamp: dx = -R_px gives exactly 0
    assert close(ms.uniform_factor(-r / WPP, WPP, r), 0.0, 1e-9)


def test_farthest_corner_numbers():
    r = ms.farthest_corner((0, 0, 0), (-.5, -.5, -2), (.5, .5, 2))
    assert close(r, 2.1213203), r
    assert close(ms.uniform_factor(50, WPP, r), 1.247764)
    r = ms.farthest_corner((.5, .5, .5), (-.5, -.5, -.5), (.5, .5, .5))
    assert close(r, 1.7320508), r
    assert close(ms.uniform_factor(50, 0.010248923, r), 1.295861)
    r = ms.farthest_corner((0, 0, 0), (2.5, -.5, -.5), (3.5, .5, .5))     # geometry moved +3 x, pivot at origin
    assert close(r, 3.570714), r
    assert close(ms.uniform_factor(50, WPP, r), 1.147193)
    assert close(ms.uniform_factor(50, 30 / 1957, math.sqrt(3) / 2), 1.885054)     # front ortho, width 30
    r = ms.farthest_corner((0, 1, 0), (-1, 1, -1), (1, 1, 1))      # top-face vertices of a 2-unit cube
    assert close(r, math.sqrt(2))
    assert close(ms.uniform_factor(50, WPP, r), 1.371645) and close(ms.uniform_factor(-50, WPP, r), 0.628355)


def test_axis_factor_numbers():
    assert close(ms.axis_factor(50, 90), 1.555556)
    assert close(2 * ms.axis_factor(50, 90), 3.111111)
    assert close(ms.axis_factor(50, 180), 1.277778)
    assert close(ms.axis_factor(-200, 90), -1.222222)
    assert close(ms.axis_length_px(1.0, 75), 90) and close(ms.axis_length_px(1.25, 75), 112.5)
    assert close(ms.axis_length_px(1.0, 150, 0.5), 90)


def test_handle_depth_plane_and_mmb_numbers():
    # an axis handle at an angle: the drag along its screen direction, with the tip's depth term
    u = (0.894427, 0.447214)                       # X handle in a persp view turned (-30, 45, 0)
    d = ms.along((50, 0), u)
    assert close(ms.depth_axis_factor(d, 90, 1.0, 90 / 92.685), 1.48251), d
    assert close(ms.depth_axis_factor(ms.along((-50, 0), u), 90, 1.0, 90 / 92.685), 0.51749)
    assert close(ms.depth_axis_factor(50, 90, 20.0, 20.0), 1.555556)          # front view: no depth term
    # plane handle (front view): along the diagonal, 0.44 handle lengths
    w = (1.0, 1.0)
    plane_len = 90 * ms.PLANE_REACH
    for drag, want in (((50, 0), 1.892812), ((0, 50), 1.892812), ((50, 50), 2.785623), ((-50, 0), 0.107188),
                       ((25, 0), 1.446406), ((30, -40), 0.821438), ((-50, -50), -0.785623)):
        got = ms.depth_axis_factor(ms.along(drag, w), plane_len, 1.0, 1.0)
        assert close(got, want), (drag, got, want)
    # MMB anywhere: axis and plane at half speed
    assert close(ms.depth_axis_factor(50, 90 * ms.MMB_SLOWER, 1.0, 1.0), 1.277778)
    assert close(ms.depth_axis_factor(ms.along((50, 0), w), plane_len * ms.MMB_SLOWER, 1.0, 1.0), 1.446406)
    # a factor within the zero band is skipped, just outside it is written
    assert ms.skip_factor(8e-6) and ms.skip_factor(-5e-6) and ms.skip_factor(0.0)
    assert not ms.skip_factor(1.2e-5) and not ms.skip_factor(-1.2e-5)


def test_own_pivots_children_and_zero_scale():
    a = _cube("p_a", size=1.0, location=(-3, 0, 0))
    b = _cube("p_b", size=1.0, location=(3, 0, 0))
    a.select_set(True)
    bpy.context.view_layer.objects.active = b
    ts = bpy.context.scene.tool_settings
    ts.transform_pivot_point = 'MEDIAN_POINT'
    ms.apply(bpy.context, 1.606894, final=True)
    assert a.location.x == -3 and b.location.x == 3, (tuple(a.location), tuple(b.location))     # own pivots
    assert close(a.scale.x, 1.606894) and close(b.scale.x, 1.606894)
    assert ts.transform_pivot_point == 'MEDIAN_POINT'                    # Blender's setting is left alone
    # the lead's children enter R
    for o in (a, b):
        bpy.data.objects.remove(o)
    parent = _cube("p_parent", size=1.0)
    child = _cube("p_child", size=1.0, location=(3, 0, 0))
    child.parent = parent
    for o in bpy.context.scene.objects:
        o.select_set(o == parent)
    bpy.context.view_layer.objects.active = parent
    bpy.context.view_layer.update()
    assert close(ms.radius(bpy.context, parent.location), 3.570714)
    # a scale channel that is 0 becomes 1e-12 when dragged
    parent.scale = (0.0, 1.0, 1.0)
    zeros = ms.zero_channels(bpy.context)
    assert zeros == {"p_parent": (0,)}
    ms.apply(bpy.context, 2.0)
    ms.fix_zero(zeros, (True, True, True))
    assert abs(parent.scale.x - ms.ZERO_SCALE) < 1e-16 and close(parent.scale.y, 2.0), tuple(parent.scale)
    for o in (child, parent):
        bpy.data.objects.remove(o)


def test_drag_rules():
    assert ms.along((50, 30), (10, 0)) == 50 and close(ms.along((30, 40), (0, -2)), -40)
    assert ms.along((7, 3), (0, 0)) == 7 and ms.along((7, 3), None) == 7     # axis toward the viewer: horizontal
    op = SimpleNamespace(_press=(100, 100), _mode='CENTER', _wpp=WPP, _radius=math.sqrt(3) / 2, _snap=False,
                         _dir=None, _len=90.0, _depth0=1.0, _depth_tip=1.0)
    assert close(ms.drag_factor(op, 150, 100), 1.606894)
    assert ms.drag_factor(op, 100, 300) == 1.0 and ms.drag_factor(op, 100, -100) == 1.0     # vertical ignored
    assert close(ms.drag_factor(op, 150, 50), 1.606894)
    op._mode, op._dir = 'AXIS', (1.0, 0.0)
    assert close(ms.drag_factor(op, 150, 40), 1.555556)
    op._snap = True
    assert close(ms.drag_factor(op, 150, 40), 1.6)
    y = ms.channels('AXIS', 'Y')
    assert ms.value_of(y, 2.0) == (1.0, 2.0, 1.0) and ms.value_of(ms.channels('CENTER'), 0.5) == (0.5,) * 3
    assert ms.constraint_of(ms.channels('AXIS', 'Z')) == (False, False, True)
    assert not any(ms.constraint_of(ms.channels('CENTER')))
    assert ms.channels('AXIS', 'X', others=True) == (False, True, True)      # Ctrl on the X handle
    assert ms.channels('PLANE', plane='XZ') == (True, False, True)


def _cube(name, size=2.0, location=(0, 0, 0)):
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    ob = bpy.context.object
    ob.name = name
    for o in bpy.context.scene.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    return ob


def test_radius_object_mode():
    ob = _cube("r_cube", size=1.0)
    ob.scale = (1, 1, 4)
    bpy.context.view_layer.update()
    assert close(ms.radius(bpy.context, ob.location), 2.1213203)
    ob.scale = (4, 1, 1)
    ob.rotation_euler = (0, 0, math.pi / 2)        # world box of the geometry: 1 x 4 x 1
    bpy.context.view_layer.update()
    assert close(ms.radius(bpy.context, ob.location), 2.1213203)
    other = _cube("r_lead", size=4.0)              # lead = the active object only
    ob.select_set(True)
    assert close(ms.radius(bpy.context, other.location), math.sqrt(12))
    bpy.ops.object.empty_add(location=(0, 0, 0))
    emp = bpy.context.object
    emp.empty_display_size = 1.0
    assert close(ms.radius(bpy.context, emp.location), math.sqrt(3))
    for o in (ob, other, emp):
        bpy.data.objects.remove(o)


def test_object_scale_to_a_tenth_is_one_undo_step():
    ob = _cube("u_cube")
    bpy.ops.ed.undo_push(message="test start")
    state = ms.save_state(bpy.context)
    for f in (0.8, 0.0, -0.4, 0.1):               # previews: put back, then scale from the press state
        ms.restore(state)
        assert ms.apply(bpy.context, f) == {'FINISHED'}
        assert close(ob.scale.x, f), (f, tuple(ob.scale))
    ms.restore(state)
    assert ms.apply(bpy.context, 0.1, final=True) == {'FINISHED'}
    assert all(close(s, 0.1) for s in ob.scale), tuple(ob.scale)
    last = bpy.context.window_manager.operators[-1]
    assert last.bl_idname == "TRANSFORM_OT_resize" and not any(last.properties.constraint_axis), \
        tuple(last.properties.constraint_axis)
    assert manip.handle_from_op(last.bl_idname, last.properties) == ('RESIZE', None)    # centre = active handle
    bpy.ops.ed.undo()
    ob = bpy.data.objects["u_cube"]
    assert all(close(s, 1.0) for s in ob.scale), ("one undo goes back to the press", tuple(ob.scale))


def test_axis_scale_registers_its_axis():
    ob = _cube("a_cube")
    ob.scale = (2, 3, 4)
    state = ms.save_state(bpy.context)
    ms.apply(bpy.context, 2.5, ms.channels('AXIS', 'X'), 'GLOBAL')
    ms.restore(state)
    ms.apply(bpy.context, 1.555556, ms.channels('AXIS', 'X'), 'GLOBAL', final=True)
    assert close(ob.scale.x, 3.111112) and ob.scale.y == 3 and ob.scale.z == 4, tuple(ob.scale)
    last = bpy.context.window_manager.operators[-1]
    got = manip.handle_from_op(last.bl_idname, last.properties)
    assert got == ('RESIZE', {"constraint_axis": (True, False, False), "orient_type": 'GLOBAL'}), got
    bpy.data.objects.remove(ob)


def test_cancel_restores_exactly():
    ob = _cube("c_cube")
    ob.location = (1, 2, 3)
    ob.rotation_euler = (0.3, 0.2, 0.1)
    before = ob.matrix_basis.copy()
    state = ms.save_state(bpy.context)
    ms.apply(bpy.context, -2.0)
    ms.restore(state)
    assert all(abs(a - b) < 1e-6 for ra, rb in zip(ob.matrix_basis, before) for a, b in zip(ra, rb)),         (ob.matrix_basis, before)
    bpy.data.objects.remove(ob)


def test_edit_mesh_selected_vertices():
    ob = _cube("e_cube")
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.select_set(v.co.z > 0)
    bm.select_flush(True)
    bmesh.update_edit_mesh(ob.data)
    bpy.context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
    center, _frame, _otype = manipulator.pivot_frame(bpy.context, 'RESIZE')
    assert (center - ob.matrix_world.translation).to_tuple(5) == (0, 0, 1)
    r = ms.radius(bpy.context, center)
    assert close(r, math.sqrt(2)), r
    f = ms.uniform_factor(-50, WPP, r)
    state = ms.save_state(bpy.context)
    ms.apply(bpy.context, 3.0)
    ms.restore(state)
    ms.apply(bpy.context, f, final=True)
    bm = bmesh.from_edit_mesh(ob.data)
    top = sorted(round(abs(v.co.x), 5) for v in bm.verts if v.co.z > 0)
    bottom = sorted(round(abs(v.co.x), 5) for v in bm.verts if v.co.z < 0)
    assert top == [round(0.628355, 5)] * 4 and bottom == [1.0] * 4, (top, bottom)
    ms.restore(state)
    bm = bmesh.from_edit_mesh(ob.data)
    assert sorted(round(abs(v.co.x), 5) for v in bm.verts) == [1.0] * 8
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects.remove(ob)


def test_unsupported_modes_keep_blender_resize():
    ob = _cube("s_cube")
    assert ms.supported(bpy.context)
    ts = bpy.context.scene.tool_settings
    ts.use_transform_data_origin = True             # D / Insert pivot edit: Blender's resize as before
    assert not ms.supported(bpy.context)
    ts.use_transform_data_origin = False
    bpy.data.objects.remove(ob)


class _Gizmo:
    def __init__(self):
        self.calls = []

    def target_set_operator(self, idname):
        props = SimpleNamespace()
        self.calls.append((idname, props))
        return props


def test_handles_bound_to_the_kit_scale():
    group = SimpleNamespace(handles=[], _ops_for=None)
    for ax in 'XYZ':
        group.handles.append((_Gizmo(), 'AXIS', ax))
    for pl in manipulator.PLANES:
        group.handles.append((_Gizmo(), 'PLANE', pl))
    group.handles.append((_Gizmo(), 'CENTER', None))
    manipulator.ALLSET_GGT_xform._bind_ops(group, 'RESIZE', 'LOCAL')
    by_role = {}
    for gz, role, data in group.handles:
        (idname, props), = gz.calls
        by_role[(role, data)] = (idname, props)
    assert by_role[('CENTER', None)][0] == "allset.manip_scale" and by_role[('CENTER', None)][1].mode == 'CENTER'
    for ax in 'XYZ':
        idname, props = by_role[('AXIS', ax)]
        assert idname == "allset.manip_scale" and props.mode == 'AXIS' and props.axis == ax
        assert props.orient_type == 'LOCAL'
    for pl in manipulator.PLANES:
        idname, props = by_role[('PLANE', pl)]
        assert idname == "allset.manip_scale" and props.mode == 'PLANE' and props.plane == pl
    group = SimpleNamespace(handles=[(_Gizmo(), 'CENTER', None), (_Gizmo(), 'AXIS', 'X')], _ops_for=None)
    manipulator.ALLSET_GGT_xform._bind_ops(group, 'TRANSLATE', 'GLOBAL')
    assert all(gz.calls[0][0] == "transform.translate" for gz, _r, _d in group.handles)


def test_registered_and_waited_for():
    assert hasattr(bpy.types, "ALLSET_OT_manip_scale")
    cls = bpy.types.ALLSET_OT_manip_scale
    assert 'REGISTER' not in cls.bl_options and 'UNDO' not in cls.bl_options     # the final resize is the step
    assert "ALLSET_OT_manip_scale".startswith(ms.TRANSFORM_MODALS)


def test_disable_removes_it():
    kit.disable()
    assert not hasattr(bpy.types, "ALLSET_OT_manip_scale")
    kit.enable()
    assert hasattr(bpy.types, "ALLSET_OT_manip_scale")
