"""Step 208: maya.cmds look-alike 2 (Issue #115) — the same scripts run in mayapy (tests/maya201_cmds_data.py) and
through the kit's Command Line runner (command_line/runner.py -> cmds_shim / cmds_dag / cmds_anim / cmds_file):
returned values, names, channels, world positions, keys, time and playback range are compared. Each case starts with
``cmds.file(new=True, force=True)`` like the mayapy harness. Kit differences that can't follow Maya are listed in
DEVIATIONS with their reason (research/maya/re/cmds_201.md §6)."""

import math
import os
from importlib import import_module
from pathlib import Path

import bpy

import kit
import maya201_cmds_data as truth

runner = import_module(kit.MODULE + ".command_line.runner")
cmds = import_module(kit.MODULE + ".command_line.cmds_shim")
cb = import_module(kit.MODULE + ".ui.channel_box")
naming = import_module(kit.MODULE + ".operators.naming")
prim_history = import_module(kit.MODULE + ".operators.prim_history")

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "tmp" / os.environ.get("ALLSET_SANDBOX", "test_env") / "cmds208"
TOL = 1e-4
ATTRS = (("translateX", "tx"), ("translateY", "ty"), ("translateZ", "tz"), ("rotateX", "rx"), ("rotateY", "ry"),
         ("rotateZ", "rz"), ("scaleX", "sx"), ("scaleY", "sy"), ("scaleZ", "sz"), ("visibility", "v"))

# Where the kit can't give Maya's answer (each with its reason), as {case: {"R<i>": kit value, "rename": {maya long
# name: kit long name}, "skip": [paths not compared]}}.
def _kit_path(value):
    """A Maya scene path of the file case -> the kit's: the test folder, ``.ma`` -> ``.blend`` (cmds_file.py)."""
    if isinstance(value, str) and ("/cmds201_" in value or value.endswith(".ma")):
        name = value.rsplit("/", 1)[-1].replace(".ma", ".blend")
        return name if "/" not in value else f"{TMP.as_posix()}/{name}"
    return value


DEVIATIONS = {
    # Maya allows the same name under two parents; Blender names are unique, so copied children (and their shapes)
    # get new numbers.
    "duplicate_hierarchy": {"R0": ["rig1", "pCube2", "pSphere2"], "R1": ["rig2"], "R2": ["pCube2", "pSphere2"],
                            "rename": {"|rig1|pCube1": "|rig1|pCube2", "|rig1|pSphere1": "|rig1|pSphere2",
                                       "|rig2|pCube1": "|rig2|pCube3", "|rig2|pSphere1": "|rig2|pSphere3"},
                            "node_skip": ["shapes"]},
    # The kit can't write Maya files: .ma paths become .blend (and the test writes into tmp/).
    "file_new_save_open": {"map": _kit_path},
    # A rotated child of a non-uniformly scaled parent: Maya keeps a shear attribute, Blender channels can't, so the
    # kit's closest rotate / scale differ (the world matrix is kept, the residual is in the parent inverse; decision 2).
    "xform_more": {"node_fields": {"|pCube1|pSphere1": ["r", "s"]}},
    # After cutKey -clear Maya's compound getAttr(".rotate") reads 0 while getAttr(".rz") reads 10 (probe 3 G in
    # cmds_201.md §4); the kit keeps 10 like the scalar read and Maya's Channel Box.
    "cut_key": {"node_fields": {"|pCube1": ["r"]}},
    # ls order: Maya's node order vs Blender's object order (compared as sets).
    "space_locator": {"unordered": [6]},
    # Maya leaves an attribute at its value when a key at another time goes onto an existing curve, until the time
    # changes (probe 3 B); Blender's depsgraph writes every animated property from its curve at the next update.
    "set_keyframe": {"node_fields": {"|pCube1": ["t", "r", "s", "wt"]}},
    # In background mode Blender reports a just-loaded home file as modified (measured: read_homefile() -> is_dirty
    # True in -b); the GUI check is in tests/gui/gui_step208_script_editor.py.
    "new_scene_unsaved": {"skip": ["R4"]},
}


def _setup():
    TMP.mkdir(parents=True, exist_ok=True)
    runner.reset()


def _close(a, b, path, out):
    if isinstance(a, bool) or isinstance(b, bool):
        if bool(a) != bool(b) or (a is None) != (b is None):
            out.append(f"{path}: maya {a!r} kit {b!r}")
        return
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if abs(a - b) > TOL * max(1.0, abs(a)):
            out.append(f"{path}: maya {a!r} kit {b!r}")
        return
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            out.append(f"{path}: maya {a!r} kit {b!r}")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            _close(x, y, f"{path}[{i}]", out)
        return
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}.{k}: maya {a.get(k)!r} kit {b.get(k)!r}")
            else:
                _close(a[k], b[k], f"{path}.{k}", out)
        return
    if a != b:
        out.append(f"{path}: maya {a!r} kit {b!r}")


def _plain(v):
    if isinstance(v, tuple):
        return [_plain(x) for x in v]
    if isinstance(v, list):
        return [_plain(x) for x in v]
    return v


def snapshot():
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    nodes = {}
    for ob in sc.objects:
        keys = {}
        for attr, key in ATTRS:
            fc = cb.fcurve(ob, key)
            if fc is not None and len(fc.keyframe_points):
                keys[attr] = [[kp.co.x, float(cmds.from_internal(key, kp.co.y))] for kp in fc.keyframe_points]
        nodes[cmds._long_name(ob)] = {
            "shapes": [cmds.shape_of(ob)] if cmds.shape_of(ob) else [],
            "t": [cmds._from_bu(x) for x in ob.location],
            "r": [math.degrees(x) for x in ob.rotation_euler],
            "s": list(ob.scale),
            "wt": [cmds._from_bu(x) for x in cmds.maya_world(ob).translation],
            "v": not ob.hide_viewport,
            "ro": cmds.ROTATE_ORDERS.index(ob.rotation_mode) if ob.rotation_mode in cmds.ROTATE_ORDERS else 0,
            "keys": keys}
    history = sorted(prim_history.node_dict(o)["name"] for o in
                     {prim_history.owner_of(ob) for ob in sc.objects} - {None})
    return {"nodes": nodes, "time": float(sc.frame_current) + sc.frame_subframe,
            "playback": [cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True),
                         cmds.playbackOptions(q=True, ast=True), cmds.playbackOptions(q=True, aet=True)],
            "history": history}


def run_case(name):
    """(R, scene snapshot, error text) of one case run through the Command Line runner."""
    runner.reset()
    ns = runner.namespace()
    ns["TMP"] = TMP.as_posix()
    r = runner.run("cmds.file(new=True, force=True)", remember=False)
    assert not r.error, r
    ns = runner.namespace()
    ns["TMP"] = TMP.as_posix()
    ns.pop("R", None)
    res = runner.run(truth.CASES[name], remember=False)
    return _plain(runner.namespace().get("R")), snapshot(), (res.text if res.error else "")


def compare(name):
    R, scene, error = run_case(name)
    maya = truth.MAYA[name]
    dev = DEVIATIONS.get(name, {})
    out = []
    if error:
        out.append(f"error: {error}")
    expected = list(maya["R"] or [])
    for i, value in enumerate(expected):
        if f"R{i}" in dev:
            expected[i] = dev[f"R{i}"]
    skip = set(dev.get("skip", ()))
    fix = dev.get("map", lambda v: v)
    for i, (a, b) in enumerate(zip(expected, R or [])):
        if f"R{i}" in skip:
            continue
        a = [fix(x) for x in a] if isinstance(a, list) else fix(a)
        if i in dev.get("unordered", ()):
            a, b = sorted(a), sorted(b)
        _close(a, b, f"R{i}", out)
    if len(expected) != len(R or []):
        out.append(f"R: maya {len(expected)} values, kit {len(R or [])}")
    rename = dev.get("rename", {})
    mnodes = {rename.get(k, k): v for k, v in maya["scene"]["nodes"].items()}
    if "nodes" not in skip:
        if sorted(mnodes) != sorted(scene["nodes"]):
            out.append(f"nodes: maya {sorted(mnodes)} kit {sorted(scene['nodes'])}")
        for k in sorted(set(mnodes) & set(scene["nodes"])):
            a, b = dict(mnodes[k]), dict(scene["nodes"][k])
            for field in list(dev.get("node_skip", ())) + list(dev.get("node_fields", {}).get(k, ())):
                a.pop(field, None)
                b.pop(field, None)
            _close(a, b, f"node {k}", out)
    for field in ("time", "history"):
        if field not in skip:
            _close(maya["scene"][field], scene[field], field, out)
    if "playback" not in skip:
        _close(maya["scene"]["playback"], scene["playback"], "playback", out)
    return out


def test_every_case_matches_mayapy():
    _setup()
    problems = {}
    for name in truth.CASES:
        out = compare(name)
        if out:
            problems[name] = out
    report = "\n".join(f"{n}:\n  " + "\n  ".join(p[:12]) for n, p in problems.items())
    assert not problems, f"{len(problems)} / {len(truth.CASES)} cases differ from mayapy:\n{report}"


# --- rules measured with mayapy (research/maya/re/cmds_201.md §2) ---------------------------------------------------

def test_maya_number_rule():
    nn = naming.next_number
    assert nn("pCube", {"pCube2", "pCube3"}) == 4, "Maya doesn't fill gaps"
    assert nn("pCube", {"pCube1", "pCube2"}) == 3
    assert nn("pCube", {"pCube10"}) == 11
    assert nn("pCube", {"pCube1x"}) == 2, "a name that starts with pCube1 counts"
    assert nn("pCube", {"pCube1"}, {"pCubeShape2"}) == 3, "a taken shape number is skipped"
    assert nn("pCube", {"pCube1", "pCubeShape6"}) == 2, "shapes don't raise the number"
    assert nn("box", {"box"}) == 1 and nn("null", set()) == 1


def test_names_and_shapes():
    _setup()
    runner.run("cmds.file(new=True, force=True)", remember=False)
    assert cmds.shape_name_for("box10") == "boxShape10" and cmds.shape_name_for("hero") == "heroShape"
    assert cmds.renamed_shape("ctrl", "ctrlShape", "ctrl2") == "ctrl2Shape"
    assert cmds.renamed_shape("pCube1", "pCubeShape1", "pCube1x") == "pCube1xShape"
    assert cmds.group(em=True, n="top") == "top1", "Maya's default camera names are taken"
    assert cmds.ls("null*") == [] and cmds.ls("top*") == ["top1"]
    a = cmds.polyCube()[0]
    assert cmds.ls("pCube*") == ["pCube1", "pCubeShape1"], cmds.ls("pCube*")
    assert cmds.ls(a, type="transform") == [a] and cmds.ls(a, type="mesh") == []
    loc = cmds.spaceLocator()[0]
    assert cmds.ls(type="locator") == ["locatorShape1"] and cmds.objExists("locatorShape1")
    assert cmds.rename(loc, "ctrl") == "ctrl" and cmds.listRelatives("ctrl", s=True) == ["ctrlShape"]
    assert cmds.rename("ctrl", "ctrl2") == "ctrl2" and cmds.listRelatives("ctrl2", s=True) == ["ctrl2Shape"]
    assert cmds.listRelatives("ctrl2Shape", p=True) == ["ctrl2"]
    assert cmds.objExists("polyCube1") and cmds.objExists(a + ".tx") and not cmds.objExists(a + ".nope")
    cmds.delete("polyCube1")
    assert not cmds.objExists("polyCube1") and cmds.objExists(a), "deleting the creation node keeps the shape"


def test_errors_like_maya():
    _setup()
    runner.run("cmds.file(new=True, force=True)", remember=False)
    a, b = cmds.polyCube()[0], cmds.polyCube()[0]
    cmds.parent(b, a)
    for call, kind, text in (
            (lambda: cmds.parent(a, b), RuntimeError, "underworld"),
            (lambda: cmds.parent(a), RuntimeError, "Not enough"),
            (lambda: cmds.group(a, bogus=1), TypeError, "Invalid flag"),
            (lambda: cmds.file("nope.ma", open=True, force=True), RuntimeError, "not found"),
            (lambda: cmds.file(new=True), RuntimeError, "Unsaved changes"),
            (lambda: cmds.playbackOptions(q=True), TypeError, "needs"),
            (lambda: cmds.addAttr(a, ln="w", at="matrix"), RuntimeError, "not supported")):
        try:
            call()
        except kind as ex:
            assert text in str(ex), (text, ex)
        else:
            raise AssertionError(f"no {kind.__name__}: {text}")
    cmds.addAttr(a, ln="w", at="double", max=1, k=True)
    try:
        cmds.setAttr(a + ".w", 2)
        raise AssertionError("past the maximum")
    except RuntimeError as ex:
        assert "past its maximum value of 1" in str(ex), ex
    assert cmds.getAttr(a + ".w", k=True) and cmds.getAttr(a + ".w", type=True) == "double"


def test_keys_values_and_refresh():
    _setup()
    runner.run("cmds.file(new=True, force=True)", remember=False)
    a = cmds.polyCube()[0]
    ob = bpy.data.objects[a]
    assert cmds.setKeyframe(a, at="tx", t=1, v=0) == 1 and cmds.setKeyframe(a, at="tx", t=11, v=10) == 1
    got = cmds.keyframe(a, at="tx", q=True, tc=True, vc=True)
    assert all(abs(x - y) < 1e-6 for x, y in zip(got, [1.0, 0.0, 11.0, 10.0])) and len(got) == 4, got
    assert abs(ob.location.x) < 1e-9, "time 1: the first key's value"
    cmds.currentTime(11)
    assert abs(cmds.getAttr(a + ".tx") - 10) < 1e-6 and abs(ob.location.x - 0.1) < 1e-6, "cm -> m"
    assert abs(cmds.getAttr(a + ".tx", time=6) - 5) < 0.6
    cmds.setKeyframe(a, at="v", t=1, v=0)
    assert cmds.keyframe(a, at="v", q=True, vc=True) == [0.0]
    cmds.setKeyframe(a, at="rz", t=1, v=90)
    fc = cb.fcurve(ob, "rz")
    assert abs(fc.keyframe_points[0].co.y - math.pi / 2) < 1e-6, "degrees -> radians"
    assert cmds.keyframe(a, at="tx", e=True, r=True, vc=1) == 1
    assert abs(cmds.getAttr(a + ".tx") - 11) < 1e-6, "keyframe -e re-evaluates the attribute"
    assert cmds.cutKey(a, at="tx") == 1 and cb.fcurve(ob, "tx") is None
    assert abs(cmds.getAttr(a + ".tx") - 11) < 1e-6, "a cut curve leaves the value"
    cmds.setAttr(a + ".tx", lock=True)
    assert cmds.setKeyframe(a, at="tx") == 0, "Maya skips locked attributes"


def test_playback_maps_to_preview_and_scene_range():
    _setup()
    runner.run("cmds.file(new=True, force=True)", remember=False)
    sc = bpy.context.scene
    cmds.playbackOptions(min=10, max=50, ast=1, aet=80)
    assert sc.use_preview_range and (sc.frame_preview_start, sc.frame_preview_end) == (10, 50)
    assert (sc.frame_start, sc.frame_end) == (1, 80)
    cmds.playbackOptions(max=5)
    assert (sc.frame_preview_start, sc.frame_preview_end) == (4, 5), "a max under the min pulls the min"


def test_file_keeps_script_editor_tabs():
    _setup()
    se = import_module(kit.MODULE + ".ui.script_editor")
    t = se.ensure_texts()
    t.clear()
    t.write("cmds.polyCube()\n")
    runner.run("cmds.file(new=True, force=True)", remember=False)
    t2 = bpy.data.texts.get("Python")
    assert t2 is not None and t2.as_string().startswith("cmds.polyCube()") and t2.get(se.LANG_PROP) == "Python"
    assert not any(tx.name.startswith(runner.TEXT_NAME) for tx in bpy.data.texts), "the runner's Text is gone"
