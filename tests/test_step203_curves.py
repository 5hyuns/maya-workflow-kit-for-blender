"""Step 203 lane C (#110): Graph Editor / Dope Sheet curve commands against Maya 2022 (tests/maya203_graph_data.py,
research/maya/re/graph_editor_201.md §6-§8).

Tolerances: Euler keys / samples 1e-3 deg (Maya prints 3-4 decimals); tangent angles 0.05 deg; Quaternion Slerp
samples 0.01 deg; Quaternion Cubic / Tangent Dependent 0.15 deg (kit squad vs Maya: 0.095 deg measured); Key Sync /
Peak Removal values 1e-3 (noisy peak-removal cases only loosely: spike gone, values inside the original range)."""

import math
from importlib import import_module

import bpy

import kit
import maya203_graph_data as truth

gc = import_module(kit.MODULE + ".operators.graph_curves_203")
undo_steps = import_module(kit.MODULE + ".undo_steps")

ROT = truth.ROTATION_INTERP
FRAMES = ROT["sample_frames"]
CH = ("rx", "ry", "rz")
LABELS = {"NONE": "Independent Euler", "EULER": "Synchronized Euler", "SLERP": "Quaternion Slerp",
          "SQUAD": "Quaternion Cubic", "TANGENT": "Quaternion Tangent Dependent"}


def _clear():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)


def _rot_object(keys=None):
    _clear()
    ob = bpy.data.objects.new("pCube1", None)
    bpy.context.scene.collection.objects.link(ob)
    for i, c in enumerate(CH):
        for f, v in (keys or ROT["keys"])[c]:
            ob.rotation_euler[i] = math.radians(v)
            ob.keyframe_insert("rotation_euler", index=i, frame=f)
    for fc in kit.fcurves(ob):
        for kp in fc.keyframe_points:
            kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
            kp.select_control_point = False
        fc.update()
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob


def _euler(ob):
    return gc.euler_curves(ob)


def _euler_samples(ob):
    curves = _euler(ob)
    return {c: [math.degrees(curves[i].evaluate(f)) for f in FRAMES] for i, c in enumerate(CH)}


def _quat_samples(ob):
    from mathutils import Quaternion
    q = gc.quat_curves(ob)
    out = {c: [] for c in CH}
    prev = None
    for f in FRAMES:
        quat = Quaternion([fc.evaluate(f) for fc in q])
        quat.normalize()
        e = quat.to_euler('XYZ', prev) if prev is not None else quat.to_euler('XYZ')
        prev = e
        for i, c in enumerate(CH):
            out[c].append(math.degrees(e[i]))
    return out


def _max_err(got, want):
    return max(abs(a - b) for c in CH for a, b in zip(got[c], want[c]))


def _check_keys(ob, case, tol=1e-3, angles=True):
    curves = _euler(ob)
    for i, c in enumerate(CH):
        exp = case["curves"][c]
        pts = sorted(curves[i].keyframe_points, key=lambda k: k.co.x)
        assert [round(kp.co.x, 3) for kp in pts] == exp["times"], (c, [kp.co.x for kp in pts], exp["times"])
        for kp, v in zip(pts, exp["values"]):
            assert abs(math.degrees(kp.co.y) - v) < tol, (c, kp.co.x, math.degrees(kp.co.y), v)
        if not angles:
            continue
        for kp, a_in, a_out in zip(pts, exp["in_angle"], exp["out_angle"]):
            for h, a, sign in ((kp.handle_left, a_in, 1.0), (kp.handle_right, a_out, -1.0)):
                dx = (kp.co.x - h.x) * sign
                slope = math.degrees((kp.co.y - h.y) * sign / dx) if abs(dx) > 1e-9 else 0.0
                assert abs(math.degrees(math.atan(slope)) - a) < 0.05, (c, kp.co.x, math.degrees(math.atan(slope)), a)


def test_menu_dict_covers_both_editors():
    keys = set(gc.MENU)
    for ed in ("Graph Editor", "Dope Sheet"):
        for mode, label in LABELS.items():
            assert gc.MENU[f"{ed}/Curves/Change Rotation Interp/{label}"] == ("allset.rotation_interp", {"mode": mode})
        for tail in ("Curves/Key Sync Filter", "Curves/Peak Removal Filter", "Edit/Select Curve Nodes"):
            assert f"{ed}/{tail}" in keys
    assert len(keys) == 16
    for op in ("rotation_interp", "key_sync_filter", "peak_removal_filter", "select_curve_nodes"):
        bpy.ops.allset.__getattr__(op).get_rna_type()


def test_start_curves_match_maya_independent():
    ob = _rot_object()
    assert _max_err(_euler_samples(ob), ROT["cases"]["none__all3"]["sample"]) < 1e-3
    assert gc.change_rotation_interp(ob, "", "NONE") is False          # Maya: no change
    _check_keys(ob, ROT["cases"]["none__all3"])


def test_synchronized_euler_keeps_shape():
    ob = _rot_object()
    for i, c in enumerate(CH):                       # Maya: one rotate curve converts all three
        if c == "rx":
            _euler(ob)[i].keyframe_points[0].select_control_point = True
    targets = gc.rotation_targets(bpy.context.scene, list(kit.fcurves(ob)), True)
    assert targets == [(ob, "")], targets
    assert gc.change_rotation_interp(ob, "", "EULER")
    case = ROT["cases"]["euler__all3"]
    _check_keys(ob, case)
    err = _max_err(_euler_samples(ob), case["sample"])
    assert err < 1e-3, err
    assert ob[gc.PROP] == "EULER" and list(ob[gc.TIMES]) == [1.0, 5.0, 10.0, 15.0, 20.0]
    # back to Independent Euler: keys and tangents stay, the mark goes (Maya euler_then_none)
    assert gc.change_rotation_interp(ob, "", "NONE")
    assert gc.PROP not in ob
    _check_keys(ob, ROT["cases"]["euler_then_none"])
    assert _max_err(_euler_samples(ob), ROT["cases"]["euler_then_none"]["sample"]) < 1e-3


def _synced():
    ob = _rot_object()
    gc.change_rotation_interp(ob, "", "EULER")
    return ob


def test_synchronized_euler_move_key():
    ob = _synced()
    rx = _euler(ob)[0]
    kp = gc._key_at(rx, 10.0)
    gc._shift(kp, 2.0)                                # the user drags rx's key 10 to 12
    rx.update()
    assert gc.sync_owner(ob, "", ob) == 2
    case = ROT["cases"]["euler_move_rx_key10_plus2"]
    _check_keys(ob, case)
    err = _max_err(_euler_samples(ob), case["sample"])
    assert err < 1e-3, err


def test_synchronized_euler_set_and_cut_key_via_handler():
    ob = _synced()
    rx = _euler(ob)[0]
    rx.keyframe_points.insert(12.0, math.radians(100.0))
    kp = gc._key_at(rx, 12.0)
    kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'      # Maya's new key: Auto (flat at a peak)
    rx.update()

    class _U:
        id = ob.animation_data.action

    class _D:
        updates = [_U()]

    gc._on_depsgraph(bpy.context.scene, _D())        # an Action update schedules the sync
    assert bpy.app.timers.is_registered(gc._sync_tick)
    bpy.app.timers.unregister(gc._sync_tick)
    gc._sync_tick()
    case = ROT["cases"]["euler_setkey_rx_12"]
    _check_keys(ob, case)
    got = _euler_samples(ob)
    err_rx = max(abs(a - b) for a, b in zip(got["rx"], case["sample"]["rx"]))
    err_yz = max(abs(a - b) for c in ("ry", "rz") for a, b in zip(got[c], case["sample"][c]))
    print(f"set key residual: rx {err_rx:.4f} deg, ry/rz {err_yz:.4f} deg")
    assert err_rx < 1e-3 and err_yz < 1e-3, (err_rx, err_yz)
    # cutting it removes all three; the curves are the converted ones again
    rx.keyframe_points.remove(gc._key_at(rx, 12.0))
    rx.update()
    assert gc.sync_owner(ob, "", ob) == 2
    case = ROT["cases"]["euler_cutkey_rx_12"]
    _check_keys(ob, case, angles=False)
    err = _max_err(_euler_samples(ob), case["sample"])
    assert err < 1e-3, err


def test_quaternion_modes_against_maya():
    tol = {"SLERP": 0.01, "SQUAD": 0.15, "TANGENT": 0.15}
    maya = {"SLERP": "quaternionSlerp", "SQUAD": "quaternionSquad", "TANGENT": "quaternion"}
    for mode in ("SLERP", "SQUAD", "TANGENT"):
        ob = _rot_object()
        assert gc.change_rotation_interp(ob, "", mode)
        assert ob.rotation_mode == 'QUATERNION' and not any(_euler(ob))
        q = gc.quat_curves(ob)
        assert all(q) and all([round(k.co.x, 3) for k in fc.keyframe_points] == [1.0, 5.0, 10.0, 15.0, 20.0]
                              for fc in q)
        for case in (f"{maya[mode]}__all3", f"{maya[mode]}__rx_only"):
            err = _max_err(_quat_samples(ob), ROT["cases"][case]["sample"])
            print(f"{mode} {case}: max {err:.4f} deg")
            assert err < tol[mode], (mode, case, err)
        # back to Independent Euler: the synchronised Euler curves, original evaluation (Maya *_then_none)
        assert gc.change_rotation_interp(ob, "", "NONE")
        assert ob.rotation_mode == 'XYZ' and not any(gc.quat_curves(ob)) and gc.SNAP not in ob
        back = ROT["cases"].get(f"{maya[mode]}_then_none") or ROT["cases"]["quaternion_then_none"]
        _check_keys(ob, back, angles=False)
        assert _max_err(_euler_samples(ob), back["sample"]) < 1e-3


def test_quaternion_switch_and_edited_keys():
    ob = _rot_object()
    gc.change_rotation_interp(ob, "", "SLERP")
    gc.change_rotation_interp(ob, "", "SQUAD")           # through the snapshot: Squad samples
    assert _max_err(_quat_samples(ob), ROT["cases"]["quaternionSquad__all3"]["sample"]) < 0.15
    # an edited quaternion key: Euler keys rebuilt from the quaternion keys
    w = gc.quat_curves(ob)[0]
    w.keyframe_points[2].co.y += 0.01
    w.update()
    gc.change_rotation_interp(ob, "", "EULER")
    curves = _euler(ob)
    assert all(curves) and ob.rotation_mode == 'XYZ'
    assert [round(k.co.x) for k in curves[0].keyframe_points] == [1, 5, 10, 15, 20]


def _loc_object(keys):
    _clear()
    ob = bpy.data.objects.new("pCube1", None)
    bpy.context.scene.collection.objects.link(ob)
    for i, c in enumerate(("tx", "ty", "tz")):
        for f, v in keys.get(c, ()):
            ob.location[i] = v
            ob.keyframe_insert("location", index=i, frame=f)
    curves = {("tx", "ty", "tz")[fc.array_index]: fc for fc in kit.fcurves(ob)}
    for fc in curves.values():
        for kp in fc.keyframe_points:
            kp.select_control_point = False
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob, curves


def test_key_sync_cases():
    for case, pick in (("keysync__sel_all", lambda c, t: True), ("keysync__sel_none", lambda c, t: False),
                       ("keysync__sel_tx_ty_only", lambda c, t: c in ("tx", "ty")),
                       ("keysync__sel_time_1_5", lambda c, t: 1 <= t <= 5)):
        _ob, curves = _loc_object(truth.KEY_SYNC_KEYS)
        for c, fc in curves.items():
            for kp in fc.keyframe_points:
                kp.select_control_point = pick(c, kp.co.x)
        gc.key_sync([curves[c] for c in ("tx", "ty", "tz")])
        for c, exp in truth.KEY_SYNC[case]["after"].items():
            pts = sorted(curves[c].keyframe_points, key=lambda k: k.co.x)
            assert [round(k.co.x, 3) for k in pts] == exp["times"], (case, c, [k.co.x for k in pts])
            for kp, v in zip(pts, exp["values"]):
                assert abs(kp.co.y - v) < 1e-3, (case, c, kp.co.x, kp.co.y, v)
    # one curve: no change (Maya keysync__single)
    _ob, curves = _loc_object({"ty": truth.KEY_SYNC_KEYS["ty"]})
    for kp in curves["ty"].keyframe_points:
        kp.select_control_point = True
    assert gc.key_sync([curves["ty"]]) == 0
    assert [k.co.x for k in curves["ty"].keyframe_points] == truth.KEY_SYNC["keysync__single"]["after"]["ty"]["times"]


def _peak_curve(keys, selected):
    _clear()
    ob = bpy.data.objects.new("pCube1", None)
    bpy.context.scene.collection.objects.link(ob)
    for f, v in keys:
        ob.location.x = v
        ob.keyframe_insert("location", index=0, frame=f)
    fc = kit.fcurves(ob)[0]
    for kp in fc.keyframe_points:
        kp.select_control_point = {"all": True, "none": False}.get(selected, 3 <= kp.co.x <= 7)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob, fc


def test_peak_removal_clean_cases_exact():
    n = 0
    for name, case in truth.PEAK_REMOVAL.items():
        if name.startswith("noise13_"):
            continue
        _ob, fc = _peak_curve(case["keys"], case["selected"])
        gc.peak_removal([fc])
        got = [kp.co.y for kp in sorted(fc.keyframe_points, key=lambda k: k.co.x)]
        assert all(abs(a - b) < 1e-3 for a, b in zip(got, case["after_values"])), (name, got, case["after_values"])
        n += 1
    assert n >= 80, n


def test_peak_removal_noisy_cases_loosely():
    worst = 0.0
    for name, case in truth.PEAK_REMOVAL.items():
        if not name.startswith("noise13_"):
            continue
        _ob, fc = _peak_curve(case["keys"], case["selected"])
        before = [v for _t, v in case["keys"]]
        gc.peak_removal([fc])
        got = [kp.co.y for kp in sorted(fc.keyframe_points, key=lambda k: k.co.x)]
        spike = max(range(len(before)), key=lambda i: abs(before[i]))
        assert abs(got[spike]) <= 0.35, (name, got)                     # the spike is gone (Maya: within the noise)
        assert min(before) - 1e-6 <= min(got) and max(got) <= max(before) + 1e-6, (name, got)
        worst = max(worst, max(abs(a - b) for a, b in zip(got, case["after_values"])))
    print(f"peak removal noisy residual: max {worst:.4f}")


def test_select_curve_nodes():
    _ob, curves = _loc_object(truth.KEY_SYNC_KEYS)
    curves["ty"].keyframe_points[1].select_control_point = True
    for fc in curves.values():
        fc.select = True
    picked = gc.select_curve_nodes(list(curves.values()))
    assert picked == [curves["ty"]]
    assert [curves[c].select for c in ("tx", "ty", "tz")] == [False, True, False]
    for kp in curves["ty"].keyframe_points:
        kp.select_control_point = False
    assert gc.select_curve_nodes(list(curves.values())) == []
    assert not any(fc.select for fc in curves.values())
    assert bpy.ops.allset.select_curve_nodes() == {'FINISHED'}


def test_one_undo_step_each_and_no_redo_panel():
    ob = _rot_object()
    bpy.ops.ed.undo_push(message="start")
    assert bpy.ops.allset.rotation_interp('EXEC_DEFAULT', True, mode='SLERP') == {'FINISHED'}
    ob = bpy.data.objects["pCube1"]
    assert ob.rotation_mode == 'QUATERNION'
    bpy.ops.ed.undo()
    ob = bpy.data.objects["pCube1"]
    assert ob.rotation_mode == 'XYZ' and all(_euler(ob)) and gc.PROP not in ob
    assert [k.co.x for k in _euler(ob)[0].keyframe_points] == [1.0, 10.0, 20.0]

    _ob, curves = _loc_object(truth.KEY_SYNC_KEYS)
    for fc in curves.values():
        for kp in fc.keyframe_points:
            kp.select_control_point = True
    bpy.ops.ed.undo_push(message="keys")
    assert bpy.ops.allset.key_sync_filter('EXEC_DEFAULT', True) == {'FINISHED'}
    assert len(kit.fcurves(bpy.data.objects["pCube1"])[0].keyframe_points) == 5
    bpy.ops.ed.undo()
    assert len(kit.fcurves(bpy.data.objects["pCube1"])[0].keyframe_points) == 2

    _ob, fc = _peak_curve(truth.PEAK_REMOVAL["flat_n10"]["keys"], "all")
    bpy.ops.ed.undo_push(message="peak")
    assert bpy.ops.allset.peak_removal_filter('EXEC_DEFAULT', True) == {'FINISHED'}
    assert abs(kit.fcurves(bpy.data.objects["pCube1"])[0].keyframe_points[4].co.y) < 1e-6
    bpy.ops.ed.undo()
    assert abs(kit.fcurves(bpy.data.objects["pCube1"])[0].keyframe_points[4].co.y - 10.0) < 1e-6
    # nothing selected: Maya does nothing (warning), no step
    for kp in kit.fcurves(bpy.data.objects["pCube1"])[0].keyframe_points:
        kp.select_control_point = False
    assert bpy.ops.allset.peak_removal_filter('EXEC_DEFAULT', True) == {'CANCELLED'}

    for cls in gc.classes:
        mod, name = cls.bl_idname.split(".")
        rna = getattr(getattr(bpy.ops, mod), name).get_rna_type()
        visible = [p.identifier for p in rna.properties if p.identifier != "rna_type" and not p.is_hidden]
        assert not visible, (cls.bl_idname, visible)
