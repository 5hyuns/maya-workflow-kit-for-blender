"""Maya menu items added for the menu coverage roadmap (#108): Select > Components > Control Vertex (curves and
surfaces), Select > Surface Border / CV Selection Boundary, Edit > Delete All by Type > Sounds, Windows > Home,
Visualize > Create Turntable and the Shape Editor's Shapes > Rebuild Target."""

import math
from importlib import import_module

import bpy
from mathutils import Vector

import kit

menu_map = import_module(kit.MODULE + ".ui.menu_map")
editor_menu_map = import_module(kit.MODULE + ".ui.editor_menu_map")
notices = import_module(kit.MODULE + ".ui.notices")
nurbs_select = import_module(kit.MODULE + ".operators.nurbs_select")
turntable = import_module(kit.MODULE + ".operators.turntable")
shape_editor = import_module(kit.MODULE + ".ui.shape_editor")
startup_cameras = import_module(kit.MODULE + ".operators.startup_cameras")
compat = import_module(kit.MODULE + ".compat")

MAPPED = {
    "Select/Components#2/Control Vertex": "allset.nurbs_component",
    "Select/Components#3/Control Vertex": "allset.nurbs_component",
    "Select/Surface Border": "allset.select_surface_border",
    "Select/CV Selection Boundary": "allset.select_cv_boundary",
    "Edit/Delete All by Type/Sounds": "allset.delete_sounds",
    "Windows/Home": "wm.splash",
    "Visualize/Create Turntable...": "allset.create_turntable",
}


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _cv(nu, i, j):
    return j * nu + i


def test_menu_rows_mapped_and_no_stale_notice():
    for path, op in MAPPED.items():
        assert menu_map.spec(path)[1] == op, (path, menu_map.spec(path))
        mod, name = op.split(".")
        assert compat.has_op(getattr(bpy.ops, mod), name), op
    assert editor_menu_map.MAP["Shape Editor/Shapes/Rebuild Target"] == "allset.shape_rebuild"
    # rows that stay greyed keep their notice; the mapped ones lost theirs
    assert notices.greyed_notice("Select/Components#2/Hull")
    assert notices.greyed_notice("Windows/Minimize Application")
    assert "Shape Editor/Shapes/Rebuild Target" not in notices.NOTICES


# --- Surface Border / CV Selection Boundary rules --------------------------------------------------------------

def test_border_of_a_grid():
    nu, nv = 7, 6          # a 4 x 3 span cubic plane
    got = nurbs_select.border(nu, nv)
    want = {_cv(nu, i, j) for i in range(nu) for j in range(nv) if i in (0, nu - 1) or j in (0, nv - 1)}
    assert got == want and len(got) == 22, len(got)
    # a closed direction has no edge: only the open direction's two rows
    got = nurbs_select.border(8, 5, cyclic_u=True)
    assert got == {_cv(8, i, j) for i in range(8) for j in (0, 4)}, sorted(got)


def test_boundary_keeps_the_outline():
    nu, nv = 7, 6
    region = {_cv(nu, i, j) for i in range(1, 5) for j in range(1, 4)}
    inner = {_cv(nu, 2, 2), _cv(nu, 3, 2)}
    assert nurbs_select.boundary(region, nu, nv) == region - inner
    # the grid's edge counts as outside: a corner block keeps all but its inner CV
    corner = {_cv(nu, i, j) for i in range(3) for j in range(3)}
    assert nurbs_select.boundary(corner, nu, nv) == corner - {_cv(nu, 1, 1)}
    # everything selected = the border
    every = set(range(nu * nv))
    assert nurbs_select.boundary(every, nu, nv) == nurbs_select.border(nu, nv)
    # a lone CV, a single row and two diagonal CVs stay as they are
    for sel in ({_cv(nu, 2, 2)}, {_cv(nu, i, 2) for i in range(nu)}, {_cv(nu, 2, 2), _cv(nu, 3, 3)}):
        assert nurbs_select.boundary(sel, nu, nv) == sel, sorted(sel)
    # an L: the inner corner CV has an unselected diagonal neighbour, so the whole L stays
    nu, nv = 7, 7
    ell = {_cv(nu, i, j) for i in range(5) for j in range(2)} | {_cv(nu, i, j) for i in range(2) for j in range(2, 5)}
    assert nurbs_select.boundary(ell, nu, nv) == ell


def _surface(name="pl"):
    bpy.ops.surface.primitive_nurbs_surface_surface_add()
    ob = bpy.context.active_object
    ob.name = name
    return ob


def _selected_points(ob):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    sp = ob.data.splines[0]
    return {k for k, p in enumerate(sp.points) if p.select}


def test_surface_border_operator_on_two_surfaces_and_a_curve():
    _clear()
    a = _surface("a")
    b = _surface("b")
    bpy.ops.curve.primitive_nurbs_curve_add()
    crv = bpy.context.active_object
    for ob in (a, b, crv):
        ob.select_set(True)
    bpy.context.view_layer.objects.active = a
    assert bpy.ops.allset.select_surface_border() == {'FINISHED'}
    assert bpy.context.mode == 'EDIT_SURFACE'
    assert not crv.select_get()                  # a curve has no border: nothing of it stays selected
    sp = a.data.splines[0]
    want = nurbs_select.border(sp.point_count_u, sp.point_count_v, sp.use_cyclic_u, sp.use_cyclic_v)
    assert _selected_points(a) == want and _selected_points(b) == want, (_selected_points(a), want)
    assert len(want) == 12                       # 4 x 4 CVs


def test_cv_boundary_operator_from_edit_mode():
    _clear()
    ob = _surface()
    bpy.ops.object.mode_set(mode='OBJECT')
    sp = ob.data.splines[0]
    nu, nv = sp.point_count_u, sp.point_count_v   # read now: a mode change frees the spline
    for k, p in enumerate(sp.points):
        p.select = True                          # every CV: the boundary is the border
    bpy.ops.object.mode_set(mode='EDIT')
    assert bpy.ops.allset.select_cv_boundary() == {'FINISHED'}
    assert bpy.context.mode == 'EDIT_SURFACE'
    got = _selected_points(ob)
    assert got == nurbs_select.border(nu, nv) and _cv(nu, 1, 1) not in got, sorted(got)


def test_control_vertex_enters_cv_editing():
    _clear()
    bpy.ops.curve.primitive_nurbs_curve_add()
    crv = bpy.context.active_object
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    crv.select_set(True)
    bpy.context.view_layer.objects.active = crv
    assert bpy.ops.allset.nurbs_component() == {'FINISHED'}
    assert bpy.context.mode == 'EDIT_CURVE' and not cube.select_get()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = cube
    assert not bpy.ops.allset.nurbs_component.poll()     # a mesh: the menu row warns like other wrong selections


# --- Create Turntable ---------------------------------------------------------------------------------------------

def _view():
    area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return area, region


def _turntable_scene():
    _clear()
    for data in list(bpy.data.cameras):
        bpy.data.cameras.remove(data)
    startup_cameras.ensure(bpy.context.scene)
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(3.0, -1.0, 2.0))
    box = bpy.context.active_object
    area, region = _view()
    space = area.spaces.active
    space.use_local_camera, space.camera = False, None
    bpy.context.scene.camera = None
    space.region_3d.view_perspective = 'PERSP'
    bpy.context.scene.frame_set(1)
    return area, region, box


def _turn(area, region, **kw):
    with bpy.context.temp_override(area=area, region=region):
        return bpy.ops.allset.create_turntable(**kw)


def test_turn_keys():
    assert turntable.turn_keys(24, 'COUNTERCLOCKWISE') == [(1.0, 0.0), (24.0, 360.0)]
    assert turntable.turn_keys(48, 'CLOCKWISE') == [(1.0, 0.0), (48.0, -360.0)]


def test_turntable_group_camera_keys_and_view():
    area, region, box = _turntable_scene()
    space = area.spaces.active
    rv3d = space.region_3d
    view_before = rv3d.view_matrix.inverted().translation.copy()
    names = {o.name for o in bpy.data.objects}
    end_before = bpy.context.scene.frame_end
    assert _turn(area, region) == {'FINISHED'}
    new = [o for o in bpy.data.objects if o.name not in names]
    grp = next(o for o in new if o.type == 'EMPTY')
    cam = next(o for o in new if o.type == 'CAMERA')
    assert grp.name.startswith("group") and cam.name == "turnTableCamera1", (grp.name, cam.name)
    assert cam.parent == grp and grp.parent is None
    # translate 0, pivot at the box's centre
    assert Vector(grp.location).length < 1e-6
    assert (grp.matrix_world.translation - Vector((3.0, -1.0, 2.0))).length < 1e-5, grp.matrix_world.translation
    # one turn about the world up axis: 0 at frame 1, 360 at frame 24, constant after
    fcs = [fc for fc in kit.fcurves(grp) if fc.data_path == "rotation_euler"]
    assert [fc.array_index for fc in fcs] == [2], [(fc.data_path, fc.array_index) for fc in fcs]
    keys = [(round(k.co.x, 4), round(math.degrees(k.co.y), 4)) for k in fcs[0].keyframe_points]
    assert keys == [(1.0, 0.0), (24.0, 360.0)], keys
    assert fcs[0].extrapolation == 'CONSTANT'
    # the camera starts where the view looked from and comes back there
    bpy.context.scene.frame_set(1)
    assert (cam.matrix_world.translation - view_before).length < 1e-3, (cam.matrix_world.translation, view_before)
    bpy.context.scene.frame_set(12)
    half = cam.matrix_world.translation
    assert (half - view_before).length > 1.0
    centre = Vector((3.0, -1.0, 2.0))
    assert abs((half - centre).xy.length - (view_before - centre).xy.length) < 1e-3   # on a circle around the box
    bpy.context.scene.frame_set(30)
    assert (cam.matrix_world.translation - view_before).length < 1e-3
    # the view looks through it; the selection and the time range stay
    assert rv3d.view_perspective == 'CAMERA' and space.camera == cam
    assert box.select_get() and not cam.select_get() and not grp.select_get()
    assert bpy.context.view_layer.objects.active == box
    assert bpy.context.scene.frame_end == end_before


def test_turntable_clockwise_and_frames_and_two_objects():
    area, region, box = _turntable_scene()
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(-3.0, 5.0, 6.0))
    other = bpy.context.active_object
    box.select_set(True)
    assert _turn(area, region, frames=48, direction='CLOCKWISE') == {'FINISHED'}
    grp = next(o for o in bpy.data.objects if o.type == 'EMPTY' and o.name.startswith("group"))
    # pivot at the centre of the two boxes' bounding box
    assert (grp.matrix_world.translation - Vector((0.0, 2.0, 4.0))).length < 1e-5, grp.matrix_world.translation
    fc = next(fc for fc in kit.fcurves(grp) if fc.data_path == "rotation_euler")
    keys = [(round(k.co.x, 4), round(math.degrees(k.co.y), 4)) for k in fc.keyframe_points]
    assert keys == [(1.0, 0.0), (48.0, -360.0)], keys
    assert other.select_get() and box.select_get()


def test_turntable_needs_a_selection():
    area, region, box = _turntable_scene()
    box.select_set(False)
    names = {o.name for o in bpy.data.objects}
    try:
        _turn(area, region)
    except RuntimeError as ex:
        assert "select one or more objects first" in str(ex), ex
    else:
        raise AssertionError("no error without a selection")
    assert {o.name for o in bpy.data.objects} == names


# --- Shape Editor > Shapes > Rebuild Target -----------------------------------------------------------------------

def test_rebuild_target_makes_the_target_mesh_once():
    _clear()
    bpy.ops.mesh.primitive_plane_add(size=2.0, location=(5.0, 0.0, 0.0), rotation=(0.0, 0.0, math.pi / 2))
    base = bpy.context.active_object
    base.name = "face"
    base.shape_key_add(name="Basis")
    kb = base.shape_key_add(name="smile")
    kb.data[0].co.z += 1.0
    kb.value = 0.3
    bpy.data.objects.new("smile", bpy.data.meshes.new("taken"))       # the name is taken
    key = base.data.shape_keys
    new = shape_editor.rebuild_target(bpy.context, key, 1)
    assert new is not None and new.name == "smile1", new and new.name
    assert new.data.shape_keys is None and new.parent is None
    assert all(abs(a - b) < 1e-6 for ra, rb in zip(new.matrix_world, base.matrix_world) for a, b in zip(ra, rb))
    # the target at full weight, not at its current 0.3
    assert abs(new.data.vertices[0].co.z - 1.0) < 1e-6 and abs(new.data.vertices[1].co.z) < 1e-6
    assert abs(kb.value - 0.3) < 1e-6                                    # the base keeps its weight
    assert bpy.context.active_object == base and not new.select_get()     # the selection stays
    # the rebuilt mesh still exists: no second one
    assert shape_editor.rebuild_target(bpy.context, key, 1) is None
    bpy.data.objects.remove(new)
    again = shape_editor.rebuild_target(bpy.context, key, 1)
    assert again is not None and again.name == "smile1", again and again.name
