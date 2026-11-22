"""Issue #443: option windows and tool options read X / Y / Z as the scene's axes, the ones the Channel Box shows.

Duplicate Special, Constraint axes, Scale Constraint Offset, Mesh > Mirror, Mirror Joints, Mirror Skin Weights,
Multi-Cut slice planes, ShrinkWrap Along X / Y / Z, the Create windows' Axis, Revolve / Extrude axes, Orient Joint and
Joint Tool world orientation. Defaults keep their result: a primitive stands upright with Axis Z, Mirror Joints flips
front and back across XZ. Option values saved while the windows read X / Y / Z the Y-up way keep their result too.
"""

import json
import math
import os
import tempfile
from importlib import import_module

import bpy
from mathutils import Vector

import kit

ow = import_module(kit.MODULE + ".operators.option_windows")
joints = import_module(kit.MODULE + ".operators.joints")
skin = import_module(kit.MODULE + ".operators.skin_copy_mirror")
mc = import_module(kit.MODULE + ".operators.multi_cut")
preferences = import_module(kit.MODULE + ".preferences")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    us = bpy.context.scene.unit_settings
    us.system, us.length_unit, us.scale_length = 'METRIC', 'CENTIMETERS', 1.0
    preferences.get().option_settings = ""


def _select(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _run(key, values):
    res = ow.run(ow._BY_KEY[key], bpy.context, values)
    assert not isinstance(res, str), (key, res)
    return res


def _extent(ob):
    bpy.context.view_layer.update()
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return Vector([max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)])


def _empty(name, loc=(0.0, 0.0, 0.0)):
    ob = bpy.data.objects.new(name, None)
    ob.location = loc
    bpy.context.scene.collection.objects.link(ob)
    return ob


def test_duplicate_special_offsets_go_to_the_channels_of_the_same_name():
    _clear()
    bpy.ops.mesh.primitive_cube_add()
    src = bpy.context.active_object
    k = 0.01                                     # 1 Maya unit = 1 cm in the kit's template units
    _run("duplicate_special_maya", {"translate": (0.0, 1.0, 0.0), "rotate": (0.0, 30.0, 0.0),
                                    "scale": (1.0, 2.0, 1.0)})
    copy = bpy.context.active_object
    assert copy is not src
    assert (copy.location - Vector((0.0, k, 0.0))).length < 1e-6, tuple(copy.location)
    assert (Vector(copy.rotation_euler) - Vector((0.0, math.radians(30), 0.0))).length < 1e-6, \
        tuple(copy.rotation_euler)
    assert (copy.scale - Vector((1.0, 2.0, 1.0))).length < 1e-6, tuple(copy.scale)


def test_constraint_axes_and_scale_offset():
    _clear()
    tgt, drv = _empty("locator1", (1.0, 2.0, 3.0)), _empty("locator2")
    _select(tgt, drv)
    _run("point_constraint", {"all": False, "y": True})
    con = drv.constraints[-1]
    assert (con.use_x, con.use_y, con.use_z) == (False, True, False)
    _select(tgt, drv)
    _run("parent_constraint", {"all_t": False, "tz": True, "all_r": False, "ry": True})
    con = drv.constraints[-1]
    assert (con.use_location_x, con.use_location_y, con.use_location_z) == (False, False, True)
    assert (con.use_rotation_x, con.use_rotation_y, con.use_rotation_z) == (False, True, False)
    drv.constraints.clear()
    tgt.scale = (2.0, 3.0, 4.0)
    _select(tgt, drv)
    _run("scale_constraint", {"offset": (1.0, 1.0, 0.5), "all": False, "x": True, "z": True})
    bpy.context.view_layer.update()
    # x 2 x 1, y not constrained (own 1), z 4 x 0.5
    assert (drv.matrix_world.to_scale() - Vector((2.0, 1.0, 2.0))).length < 1e-5, tuple(drv.matrix_world.to_scale())


def test_create_axis_default_stands_upright_and_names_the_scene_axis():
    _clear()
    window = ow._BY_KEY["poly_cylinder"]
    assert window.defaults()["axis"] == "Z"
    _run("poly_cylinder", {"height": 6.0})
    e = _extent(bpy.context.active_object) / 0.01
    assert abs(e.z - 6.0) < 1e-3 and e.x < 5 and e.y < 5, tuple(e)
    _clear()
    _run("poly_cylinder", {"height": 6.0, "axis": "Y"})
    e = _extent(bpy.context.active_object) / 0.01
    assert abs(e.y - 6.0) < 1e-3 and e.z < 5, tuple(e)
    # NURBS: Axis Z upright too, Pivot point in scene axes
    _clear()
    assert ow._BY_KEY["nurbs_cylinder"].defaults()["axis"] == "Z"
    _run("nurbs_cylinder", {"height": 6.0, "radius": 1.0, "pivot": "User defined", "pivot_point": (0.0, 5.0, 0.0)})
    ob = bpy.context.active_object
    e = _extent(ob) / 0.01
    assert abs(e.z - 6.0) < 0.05 and e.x < 2.5, tuple(e)
    bpy.context.view_layer.update()
    centre = sum((ob.matrix_world @ Vector(c) for c in ob.bound_box), Vector()) / 8 / 0.01
    assert abs(centre.y - 5.0) < 0.05 and abs(centre.z) < 0.05, tuple(centre)


def test_mesh_mirror_axis_is_the_scene_axis():
    _clear()
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 3.0, 0.0))
    cube = bpy.context.active_object
    bpy.ops.allset.mirror(axis='Y', cut=False, combine=False, position='WORLD')
    copy = next(o for o in bpy.context.scene.objects if o.type == 'MESH' and o is not cube)
    ys = [(copy.matrix_world @ v.co).y for v in copy.data.vertices]
    zs = [(copy.matrix_world @ v.co).z for v in copy.data.vertices]
    assert abs(min(ys) + 3.5) < 1e-4 and abs(max(ys) + 2.5) < 1e-4, (min(ys), max(ys))
    assert abs(min(zs) + 0.5) < 1e-4 and abs(max(zs) - 0.5) < 1e-4, (min(zs), max(zs))


def test_mirror_planes_are_scene_planes():
    assert joints.PLANES["XY"] == (1.0, 1.0, -1.0) and joints.PLANES["XZ"] == (1.0, -1.0, 1.0)
    assert bpy.ops.allset.mirror_joints.get_rna_type().properties["plane"].default == "XZ"   # front / back, like Maya
    assert (skin.PLANE_AXIS["XY"], skin.PLANE_AXIS["XZ"], skin.PLANE_AXIS["YZ"]) == (2, 1, 0)
    _clear()
    ob = joints.new_skeleton(bpy.context)
    parent = None
    for p in (Vector((1.0, 2.0, 3.0)), Vector((1.0, 2.0, 5.0))):
        parent = joints.add_joint(ob, p, parent, up=Vector((0, 0, 1)), length=0.5)
    bpy.ops.object.mode_set(mode='OBJECT')
    new = joints.mirror(ob, ["joint1"], "XY")
    head = ob.data.bones[new[0]].head_local
    assert (head - Vector((1.0, 2.0, -3.0))).length < 1e-5, tuple(head)
    new = joints.mirror(ob, ["joint1"])                       # default XZ
    head = ob.data.bones[new[0]].head_local
    assert (head - Vector((1.0, -2.0, 3.0))).length < 1e-5, tuple(head)


def test_multi_cut_slice_planes_are_scene_planes():
    assert mc.PLANE_NORMALS["XY"] == Vector((0, 0, 1)) and mc.PLANE_NORMALS["ZX"] == Vector((0, 1, 0))
    items = bpy.context.scene.allset_mesh_tools.bl_rna.properties["slice_plane"].enum_items
    # a scene saved with the Y-up reading stored the ground as 2 and the front plane as 3: they keep their plane
    assert (items["XY"].value, items["ZX"].value, items["YZ"].value, items["NONE"].value) == (2, 3, 1, 0)


def test_shrink_wrap_along_y_is_the_scene_y():
    _clear()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=3.0)
    drv = bpy.context.active_object
    _select(cube, drv)
    _run("deform_shrink_wrap", {"projection": "Parallel To Axes", "along_y": True})
    md = [m for m in cube.modifiers if m.type == 'SHRINKWRAP'][-1]
    assert md.use_project_y and not md.use_project_z and not md.use_project_x


def test_orient_joint_and_joint_tool_world_orientation():
    assert bpy.ops.allset.orient_joint.get_rna_type().properties["world"].default == "Z+"
    assert bpy.ops.allset.joint_tool.get_rna_type().properties["secondary_world"].default == "Z"
    assert ow._BY_KEY["joint_tool"].defaults()["secondary_world"] == "Z"
    _clear()
    ob = joints.new_skeleton(bpy.context)
    parent = None
    for p in (Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((2, 0, 0))):
        parent = joints.add_joint(ob, p, parent, up=Vector((0, 0, 1)), length=0.5)
    with joints._InEditMode(ob) as ebs:
        for eb in ebs:
            eb.roll = 1.0
    z = lambda b: b.matrix_local.to_3x3().col[2]               # noqa: E731  (the bone's Z = the joint's Y)
    joints.orient(ob, ["joint1"], "Y+", True)
    assert all(z(b).dot(Vector((0, 1, 0))) > 0.999 for b in ob.data.bones), [tuple(z(b)) for b in ob.data.bones]
    joints.orient(ob, ["joint1"], "Z+", True)
    assert all(z(b).dot(Vector((0, 0, 1))) > 0.999 for b in ob.data.bones), [tuple(z(b)) for b in ob.data.bones]


def test_revolve_axis_default_is_the_scene_up():
    _clear()
    assert ow._BY_KEY["revolve"].defaults()["axis"] == "Z"
    cu = bpy.data.curves.new("profile", 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('POLY')
    sp.points.add(1)
    sp.points[0].co = (1.0, 0.0, 0.0, 1.0)
    sp.points[1].co = (1.0, 0.0, 2.0, 1.0)
    prof = bpy.data.objects.new("curve1", cu)
    bpy.context.scene.collection.objects.link(prof)
    _select(prof)
    assert bpy.ops.allset.revolve('EXEC_DEFAULT') == {'FINISHED'}
    surf = bpy.context.active_object
    assert surf is not prof and surf.type == 'SURFACE'
    e = _extent(surf)
    # turned about the scene's Z: a tube 2 wide in X and Y, 2 high
    assert abs(e.x - 2.0) < 0.05 and abs(e.y - 2.0) < 0.05 and abs(e.z - 2.0) < 0.05, tuple(e)


def test_world_up_vector_is_a_scene_direction():
    assert ow._BY_KEY["aim_constraint"].defaults()["world_up_vector"] == (0.0, 0.0, 1.0)
    assert ow._BY_KEY["normal_constraint"].defaults()["world_up_vector"] == (0.0, 0.0, 1.0)
    _clear()
    tgt, drv = _empty("locator1", (3.0, 2.0, 1.0)), _empty("locator2")
    _select(tgt, drv)
    _run("aim_constraint", {})
    con = drv.constraints[-1]
    # default: the scene's up, no helper
    assert con.type == 'TRACK_TO' and not con.use_target_z and con.target is tgt
    drv.constraints.clear()
    _select(tgt, drv)
    _run("aim_constraint", {"world_up_vector": (0.0, 1.0, 0.0)})
    con = drv.constraints[-1]
    assert con.type == 'TRACK_TO' and con.use_target_z and con.target is not tgt   # a helper whose Z = scene +Y
    bpy.context.view_layer.update()
    assert (con.target.matrix_world.to_3x3().col[2] - Vector((0.0, 1.0, 0.0))).length < 1e-5
    # Normal / Tangent constraints turn towards the scene's up only: 0 0 1
    res = ow.run(ow._BY_KEY["normal_constraint"], bpy.context, {"world_up_vector": (0.0, 1.0, 0.0)})
    assert isinstance(res, str) and "0 0 1" in res, res


# --- option values saved with the Y-up reading -----------------------------------------------------------------------

OLD = {
    "poly_cylinder": {"axis": "Y", "height": 6.0},
    "nurbs_circle": {"axis": "Free", "axis_definition": [0.0, 1.0, 0.0], "pivot_point": [1.0, 2.0, 3.0]},
    "nurbs_square": {"center": [1.0, 2.0, 3.0]},
    "duplicate_special_maya": {"translate": [0.0, 1.0, 0.0], "rotate": [0.0, 0.0, 30.0], "scale": [1.0, 2.0, 3.0]},
    "point_constraint": {"all": False, "x": False, "y": True, "z": False},
    "scale_constraint": {"offset": [1.0, 2.0, 3.0], "all": False, "x": False, "y": False, "z": True},
    "deform_shrink_wrap": {"along_y": True, "along_z": False},
    "mirror_skin_weights": {"mirror_across": "XZ"},
    "revolve": {"axis": "Z", "pivot_point": [0.0, 0.0, 4.0]},
    "surface_extrude": {"direction_vector": "Y axis"},
    "joint_tool": {"secondary_world": "Z", "secondary_sign": "+"},
    "op_orient_joint": {"world": "Y+", "children": True},
    "op_mirror_joints": {"plane": "XY"},
    "aim_constraint": {"world_up_vector": [0.0, 1.0, 0.0]},
    "normal_constraint": {"world_up_vector": [0.0, 1.0, 0.0]},
}
NEW = {
    "poly_cylinder": {"axis": "Z", "height": 6.0},
    "nurbs_circle": {"axis": "Free", "axis_definition": (0.0, 0.0, 1.0), "pivot_point": (1.0, -3.0, 2.0)},
    "nurbs_square": {"center": (1.0, -3.0, 2.0)},
    "duplicate_special_maya": {"translate": (0.0, 0.0, 1.0), "rotate": (0.0, -30.0, 0.0), "scale": (1.0, 3.0, 2.0)},
    "point_constraint": {"all": False, "x": False, "y": False, "z": True},
    "scale_constraint": {"offset": (1.0, 3.0, 2.0), "all": False, "x": False, "y": True, "z": False},
    "deform_shrink_wrap": {"along_y": False, "along_z": True},
    "mirror_skin_weights": {"mirror_across": "XY"},
    "revolve": {"axis": "Y", "pivot_point": (0.0, -4.0, 0.0)},
    "surface_extrude": {"direction_vector": "Z axis"},
    "joint_tool": {"secondary_world": "Y", "secondary_sign": "-"},
    "op_orient_joint": {"world": "Z+", "children": True},
    "op_mirror_joints": {"plane": "XZ"},
    "aim_constraint": {"world_up_vector": (0.0, 0.0, 1.0)},
    "normal_constraint": {"world_up_vector": (0.0, 0.0, 1.0)},
}


def _same(a, b):
    for k, v in b.items():
        got = a.get(k)
        if isinstance(v, tuple):
            assert got is not None and all(abs(x - y) < 1e-9 for x, y in zip(got, v)), (k, got, v)
        else:
            assert got == v, (k, got, v)


def test_old_saved_values_keep_their_result():
    _clear()
    prefs = preferences.get()
    prefs.option_settings = json.dumps(OLD)                  # no axes marker: written by an older kit
    for key, want in NEW.items():
        _same(ow.saved(key), want)
    # the next save writes the converted values with the marker; reading again doesn't convert twice
    ow.store("poly_cube", {"width": 2.0})
    data = json.loads(prefs.option_settings)
    assert data[ow.AXES_KEY] == 3
    for key, want in NEW.items():
        _same(data[key], want)
        _same(ow.saved(key), want)
    # an old "upright" Axis Y still makes an upright cylinder
    _run("poly_cylinder", ow.saved("poly_cylinder"))
    e = _extent(bpy.context.active_object) / 0.01
    assert abs(e.z - 6.0) < 1e-3, tuple(e)
    # an old Orient Joint world +Y (up) still orients towards the scene's up
    op = type("Op", (), {"world": "X+", "children": False})()
    joints._load_options(op, "orient_joint", ("world", "children"))
    assert (op.world, op.children) == ("Z+", True)


def test_old_settings_file_imported_keeps_its_result():
    _clear()
    prefs = preferences.get()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "kit.json")
        assert bpy.ops.allset.settings_export(filepath=path) == {'FINISHED'}
        data = json.load(open(path, encoding="utf-8"))
        data["preferences"]["option_settings"] = json.dumps(OLD)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        prefs.option_settings = ""
        assert bpy.ops.allset.settings_import(filepath=path) == {'FINISHED'}
    for key, want in NEW.items():
        _same(ow.saved(key), want)


def test_new_saved_values_are_read_as_they_are():
    _clear()
    prefs = preferences.get()
    prefs.option_settings = json.dumps({ow.AXES_KEY: 2, **NEW})
    for key, want in NEW.items():
        _same(ow.saved(key), want)
