"""Step 226 lane D (Issue #136, ATTACH_PLAN L5): Set Driven Key like Maya 2026 (operators/driven_key.py).

Maya truth (mayapy 2026, research/scripts/maya_controls226/measure.py -> research/maya/re/controls_226.json): curve shapes
of 2 / 3 / 4 keys (29 samples each, auto tangents, infinity Constant), two drivers on one channel = blendWeighted sum
(20 pairs), rotate 10 / 10 -> 60, a third driver (0, 0) (1, 5) -> 65. Spec research/maya/re/maya2026_controls.md §L5."""

import math
from importlib import import_module

import bpy
from mathutils import Vector

import kit

sdk = import_module(kit.MODULE + ".operators.driven_key")
cb = import_module(kit.MODULE + ".ui.channel_box")
joints = import_module(kit.MODULE + ".operators.joints")

TOL = 1e-4

# copy of controls_226.json (research/ is not in git)
MAYA = {"sdk_two_keys": {"keys": [[0, 0], [10, 90]], "xs": [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0], "ty": [0.0, 0.0, 0.0, 0.0, 0.0, 0.6525, 2.52, 5.4675, 9.36, 14.0625, 19.44, 25.3575, 31.68, 38.2725, 45.0, 51.7275, 58.32, 64.6425, 70.56, 75.9375, 80.64, 84.5325, 87.48, 89.3475, 90.0, 90.0, 90.0, 90.0, 90.0]},  # noqa: E501
        "sdk_three_keys": {"keys": [[0, 0], [3, 20], [10, 90]], "xs": [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0], "ty": [0.0, 0.0, 0.0, 0.0, 0.0, 0.856481, 3.185185, 6.625, 10.814815, 15.393519, 20.0, 24.90051, 30.489796, 36.59949, 43.061224, 49.706633, 56.367347, 62.875, 69.061224, 74.757653, 79.795918, 84.007653, 87.22449, 89.278061, 90.0, 90.0, 90.0, 90.0, 90.0]},  # noqa: E501
        "sdk_four_keys_overshoot": {"keys": [[0, 0], [2, 50], [6, 40], [10, 90]], "xs": [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0], "ty": [0.0, 0.0, 0.0, 0.0, 0.0, 7.8125, 25.0, 42.1875, 50.0, 49.570312, 48.4375, 46.835938, 45.0, 43.164062, 41.5625, 40.429688, 40.0, 42.148438, 47.8125, 55.820312, 65.0, 74.179688, 82.1875, 87.851562, 90.0, 90.0, 90.0, 90.0, 90.0]},  # noqa: E501
        "sdk_two_drivers": {"curl": [[0, 0], [10, 90]], "spread": [[0, 0], [4, -10], [10, -30]], "pairs": [[0, 0], [0, 3], [0, 7], [0, 10], [2.5, 0], [2.5, 3], [2.5, 7], [2.5, 10], [5, 0], [5, 3], [5, 7], [5, 10], [10, 0], [10, 3], [10, 7], [10, 10], [12, 0], [12, 3], [12, 7], [12, 10]], "ty": [0.0, -6.75, -22.25, -30.0, 14.0625, 7.3125, -8.1875, -15.9375, 45.0, 38.25, 22.75, 15.0, 90.0, 83.25, 67.75, 60.0, 90.0, 83.25, 67.75, 60.0]},  # noqa: E501
        "sdk_two_drivers_rotate": {"rz_10_10": 60.0}, "sdk_three_drivers_rotate": {"rz": 65.0}}


def _clear():
    st = bpy.context.window_manager.allset_sdk
    st.open = False
    st.driven.clear()
    st.driver.object = None
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for coll in (bpy.data.objects, bpy.data.armatures, bpy.data.meshes):
        for idb in list(coll):
            coll.remove(idb)


def _empty(name, **props):
    ob = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ob)
    for k, v in props.items():
        ob[k] = float(v)
    return ob


def _select(*obs, active=None):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or obs[-1]


def _set(node, key, value):
    sdk.set_raw_value(node, key, value)
    node.id_data.update_tag()
    bpy.context.view_layer.update()


def _key(drv, dattr, dv, tgt, attr, v):
    """Maya setDrivenKeyframe -cd drv.dattr -dv dv -v v (the other drivers sit at 0 = their keys at 0)."""
    _set(drv, dattr, dv)
    fc = sdk.sdk_fcurve(tgt, attr)
    if fc is not None:
        fc.mute = True                   # what the window does while posing (hold_driven)
    sdk.set_raw_value(tgt, attr, v)
    sdk.set_key(tgt, attr, drv, dattr)
    _set(drv, dattr, 0.0)


def _read(node, key):
    bpy.context.view_layer.update()
    return sdk.raw_value(node, key)


def _cases():
    return [n for n in ("sdk_two_keys", "sdk_three_keys", "sdk_four_keys_overshoot")]


def test_curve_shapes_match_mayapy():
    """Maya auto tangents (flat ends, chord slope, flat extremes), infinity Constant: every sample within 1e-4."""
    for name in _cases():
        _clear()
        case = MAYA[name]
        drv = _empty("drv", curl=0)
        tgt = _empty("tgt", ty=0)
        for dv, v in case["keys"]:
            _key(drv, "cp:curl", dv, tgt, "cp:ty", v)
        fc = sdk.sdk_fcurve(tgt, "cp:ty")
        assert fc is not None and not sdk.is_blend(fc) and fc.extrapolation == 'CONSTANT'
        assert len(fc.keyframe_points) == len(case["keys"])
        worst = 0.0
        for x, y in zip(case["xs"], case["ty"]):
            _set(drv, "cp:curl", x)
            worst = max(worst, abs(_read(tgt, "cp:ty") - y))
        print(f"MAYA226 {name} max deviation {worst:.2e}")
        assert worst < TOL, (name, worst)


def test_maya_slopes_rule():
    pts = [(0, 0), (3, 20), (10, 90)]
    assert sdk.maya_slopes(pts) == [0.0, 9.0, 0.0]
    assert sdk.maya_slopes([(0, 0), (2, 50), (6, 40), (10, 90)]) == [0.0, 0.0, 0.0, 0.0]


def test_two_drivers_add_like_blend_weighted():
    _clear()
    case = MAYA["sdk_two_drivers"]
    drv = _empty("drv", curl=0, spread=0)
    tgt = _empty("tgt", ty=0)
    for dv, v in case["curl"]:
        _key(drv, "cp:curl", dv, tgt, "cp:ty", v)
    assert not sdk.is_blend(sdk.sdk_fcurve(tgt, "cp:ty"))
    for dv, v in case["spread"]:
        _key(drv, "cp:spread", dv, tgt, "cp:ty", v)
    blend = sdk.sdk_fcurve(tgt, "cp:ty")
    assert sdk.is_blend(blend) and blend.driver.type == 'SUM' and len(blend.driver.variables) == 2
    assert [v.targets[0].data_path for v in blend.driver.variables] == ['["allset_sdk_0"]', '["allset_sdk_1"]']
    assert not blend.keyframe_points and not blend.modifiers
    assert cb.custom_keys(tgt) == ["ty"], "hidden inputs are not Channel Box attributes"
    curl = sdk.driver_curve(tgt, "cp:ty", drv, "cp:curl")
    spread = sdk.driver_curve(tgt, "cp:ty", drv, "cp:spread")
    assert curl is not None and spread is not None and curl != spread
    assert len(curl.keyframe_points) == 2 and len(spread.keyframe_points) == 3
    worst = 0.0
    for (c, s), y in zip(case["pairs"], case["ty"]):
        drv["curl"], drv["spread"] = float(c), float(s)
        drv.update_tag()
        worst = max(worst, abs(_read(tgt, "cp:ty") - y))
    print(f"MAYA226 sdk_two_drivers max deviation {worst:.2e}")
    assert worst < TOL, worst
    # Key again for an existing driver goes into its own curve (no third input); the other input's current value
    # (spread 10 -> -30) stays added, so the curl key = posed 80 - (-30)
    _key(drv, "cp:curl", 10, tgt, "cp:ty", 80)
    assert len(blend.driver.variables) == 2 and len(curl.keyframe_points) == 2
    assert abs(curl.keyframe_points[1].co[1] - 110) < 1e-6, [tuple(k.co) for k in curl.keyframe_points]
    drv["curl"], drv["spread"] = 10.0, 10.0
    drv.update_tag()
    assert abs(_read(tgt, "cp:ty") - 80) < TOL


def _rz(ob):
    bpy.context.view_layer.update()
    return math.degrees(ob.rotation_euler[2])


def _load_driver(drv, attr):
    _select(drv)
    cb.set_selected_channels([attr])
    assert bpy.ops.allset.sdk_load(which='DRIVER') == {'FINISHED'}


def test_rotate_two_and_three_drivers_through_the_window():
    """measure.py: curl (0,0)(10,90) + spread (0,0)(10,-30) on rz -> 60; fist (0,0)(1,5) -> 65. Window flow: Key /
    pose held while open / Go to Previous / Next / Close."""
    _clear()
    drv = _empty("drv", curl=0, spread=0, fist=0)
    tgt = _empty("tgt")
    st = bpy.context.window_manager.allset_sdk
    bpy.ops.allset.sdk_window()
    _load_driver(drv, "cp:curl")
    _select(tgt)
    cb.set_selected_channels(["rz"])
    assert bpy.ops.allset.sdk_load(which='DRIVEN') == {'FINISHED'}

    def pose(driver_values, rz=None):
        for k, v in driver_values.items():
            cb.set_value(drv, "cp:" + k, float(v))
        bpy.context.view_layer.update()
        if rz is not None:
            _select(tgt)
            cb.apply_entry("rz", str(rz))        # Channel Box edit: held by the muted driver

    pose({"curl": 0})
    assert bpy.ops.allset.sdk_key() == {'FINISHED'}
    pose({"curl": 10}, 90)
    bpy.ops.allset.sdk_key()
    pose({"curl": 0})
    _load_driver(drv, "cp:spread")
    pose({"spread": 0})
    bpy.ops.allset.sdk_key()
    pose({"spread": 10}, -30)
    bpy.ops.allset.sdk_key()
    pose({"curl": 10, "spread": 10})
    print(f"MAYA226 sdk_two_drivers_rotate {_rz(tgt) - MAYA['sdk_two_drivers_rotate']['rz_10_10']:.2e}")
    assert abs(_rz(tgt) - 60.0) < TOL, _rz(tgt)
    assert sdk.is_blend(sdk.sdk_fcurve(tgt, "rz"))
    # third driver: keyed while curl / spread give 60 -> its input keeps only its own part
    _load_driver(drv, "cp:fist")
    pose({"fist": 0})
    bpy.ops.allset.sdk_key()
    pose({"fist": 1}, 65)
    bpy.ops.allset.sdk_key()
    blend = sdk.sdk_fcurve(tgt, "rz")
    assert len(blend.driver.variables) == 3 and not blend.mute
    print(f"MAYA226 sdk_three_drivers_rotate {_rz(tgt) - MAYA['sdk_three_drivers_rotate']['rz']:.2e}")
    assert abs(_rz(tgt) - 65.0) < TOL, _rz(tgt)
    pose({"curl": 0, "spread": 0})
    assert abs(_rz(tgt) - 5.0) < TOL, ("Maya: fist alone gives its own curve", _rz(tgt))
    pose({"curl": 10, "spread": 10})
    # Go to Previous / Next walk the loaded driver's keys (fist 0 / 1)
    assert bpy.ops.allset.sdk_go(direction='PREVIOUS') == {'FINISHED'}
    assert abs(drv["fist"]) < 1e-6 and abs(_rz(tgt) - 60.0) < TOL
    assert bpy.ops.allset.sdk_go(direction='NEXT') == {'FINISHED'}
    assert abs(drv["fist"] - 1) < 1e-6 and abs(_rz(tgt) - 65.0) < TOL
    assert bpy.ops.allset.sdk_go(direction='NEXT') == {'CANCELLED'}
    # posing the summed channel holds the typed value while the window is open; Close drops it
    pose({}, 30)
    assert blend.mute and abs(_rz(tgt) - 30.0) < 1e-3, _rz(tgt)
    bpy.ops.allset.sdk_close()
    assert not st.open and not blend.mute and abs(_rz(tgt) - 65.0) < TOL
    # release_all after a load-like reset unmutes summed channels too
    blend.mute = True
    assert sdk.release_all() >= 1 and not blend.mute


def test_blend_shape_weight_is_a_driven_node():
    _clear()
    me = bpy.data.meshes.new("pSphere1")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    head = bpy.data.objects.new("pSphere1", me)
    bpy.context.scene.collection.objects.link(head)
    head.shape_key_add(name="Basis")
    head.shape_key_add(name="smile")
    key = me.shape_keys
    key.name = "blendShape1"
    drv = _empty("ctrl", curl=0, spread=0)
    bpy.ops.allset.sdk_window()
    _load_driver(drv, "cp:curl")
    _select(head)
    cb.set_selected_channels([])
    bpy.ops.allset.sdk_load(which='DRIVEN')
    st = bpy.context.window_manager.allset_sdk
    nodes = sdk.driven_nodes(st)
    assert nodes[0] == head and nodes[1] == key, nodes
    assert sdk.node_label(nodes[1]) == "blendShape1" and sdk.channels(key) == ["bs:smile"]
    bpy.ops.allset.sdk_pick(which='NODE', index=1)
    assert [i.label for i in st.driven_items] == ["smile"]
    bpy.ops.allset.sdk_pick(which='DRIVEN', key="bs:smile")
    bpy.ops.allset.sdk_key()
    fc = sdk.sdk_fcurve(key, "bs:smile")
    assert fc is not None and fc.id_data == key and fc.data_path == 'key_blocks["smile"].value'
    cb.set_value(drv, "cp:curl", 10.0)
    bpy.context.view_layer.update()
    key.key_blocks["smile"].value = 1.0
    sdk._on_posed(key.name, 'KEY', fc.data_path, -1)     # = the msgbus notification of that edit
    assert fc.mute
    bpy.ops.allset.sdk_key()
    assert not fc.mute
    cb.set_value(drv, "cp:curl", 5.0)
    assert abs(_read(key, "bs:smile") - 0.5) < TOL, _read(key, "bs:smile")
    # a second driver on the target weight: inputs on the shape Key ID
    cb.set_value(drv, "cp:curl", 0.0)
    _load_driver(drv, "cp:spread")
    bpy.ops.allset.sdk_key()
    blend = sdk.sdk_fcurve(key, "bs:smile")
    assert sdk.is_blend(blend) and "allset_sdk_0" in key.keys() and "allset_sdk_1" in key.keys()
    cb.set_value(drv, "cp:curl", 5.0)
    assert abs(_read(key, "bs:smile") - 0.5) < TOL
    bpy.ops.allset.sdk_close()


def test_constraint_weight_is_a_driven_node():
    _clear()
    loc = _empty("locator1")
    tgt = _empty("pCube1")
    con = tgt.constraints.new('COPY_LOCATION')
    con.target = loc
    drv = _empty("ctrl", curl=0)
    bpy.ops.allset.sdk_window()
    _load_driver(drv, "cp:curl")
    _select(tgt)
    bpy.ops.allset.sdk_load(which='DRIVEN')
    st = bpy.context.window_manager.allset_sdk
    nodes = sdk.driven_nodes(st)
    assert nodes[1] == con and sdk.node_label(con) == "pCube1_pointConstraint1", sdk.node_label(con)
    assert sdk.channels(con) == ["cw"] and sdk.attr_label(con, "cw") == "locator1W0"
    st.driven_index = 1
    st.driven_attrs = "cw"
    bpy.ops.allset.sdk_key()                     # curl 0 -> influence 1
    fc = sdk.sdk_fcurve(con, "cw")
    assert fc.data_path == 'constraints["Copy Location"].influence'
    cb.set_value(drv, "cp:curl", 10.0)
    con.influence = 0.0
    sdk._on_posed(tgt.name, 'OBJECT', fc.data_path, -1)
    bpy.ops.allset.sdk_key()
    cb.set_value(drv, "cp:curl", 5.0)
    assert abs(_read(con, "cw") - 0.5) < TOL
    # a multi-target group's Maya weight property (lane C) is driven instead of the influence
    tgt["allset_w_Copy Location"] = 1.0
    c = sdk.chan(con, "cw")
    assert c.path == '["allset_w_Copy Location"]' and c.struct == tgt
    bpy.ops.allset.sdk_close()


def test_ik_blend_and_hidden_inputs_on_a_joint():
    """ikBlend is the handle's custom attribute (step 223): it lists like any custom channel. Two drivers on a joint
    channel put the hidden inputs on the pose bone."""
    _clear()
    handle = _empty("ikHandle1", ikBlend=1)
    assert "cp:ikBlend" in sdk.channels(handle)
    drv = _empty("ctrl", curl=0, spread=0)
    arm = joints.new_skeleton(bpy.context)
    parent = None
    for p in ((0, 0, 0), (0, 0, 1), (0, 0, 2)):
        parent = joints.add_joint(arm, Vector(p), parent, length=0.5)
    joints.finish(bpy.context, arm, ["joint1", "joint2", "joint3"])
    bpy.ops.object.mode_set(mode='OBJECT')
    pb = arm.pose.bones["joint2"]
    _key(drv, "cp:curl", 0, pb, "rz", 0)
    _key(drv, "cp:curl", 10, pb, "rz", math.radians(90))
    _key(drv, "cp:spread", 0, pb, "rz", 0)
    _key(drv, "cp:spread", 10, pb, "rz", math.radians(-30))
    blend = sdk.sdk_fcurve(pb, "rz")
    assert sdk.is_blend(blend) and blend.data_path == 'pose.bones["joint2"].rotation_euler'
    assert blend.driver.variables[0].targets[0].data_path == 'pose.bones["joint2"]["allset_sdk_0"]'
    assert "allset_sdk_1" in pb.keys() and cb.custom_keys(pb) == []
    drv["curl"] = drv["spread"] = 10.0
    drv.update_tag()
    bpy.context.view_layer.update()
    assert abs(math.degrees(pb.rotation_euler[2]) - 60.0) < TOL, math.degrees(pb.rotation_euler[2])
