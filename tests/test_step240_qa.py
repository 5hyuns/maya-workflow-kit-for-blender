"""Step 240 (release QA, activity J): tests for mutants that survived the mutation sample (tools/qa/qa_mutants.py).

- status_line.snap_on must read Blender's use_snap: an element left in snap_elements while snapping is off is not "on"
  (the Status Line icon would show on while Move doesn't snap, #139 class).
- Animation layer weights (Maya: additive = base + w·x, override = lerp, scale layers multiply by x^w; quaternion
  additive = lower @ q^w) — layer weights other than 1 were not exercised.
- Outliner rows (QA G): the parent → children map keeps Maya DAG order.
"""

import math
from importlib import import_module

import bpy

import kit

anim_layers = import_module(kit.MODULE + ".operators.anim_layers")
status_line = import_module(kit.MODULE + ".ui.status_line")
outliner = import_module(kit.MODULE + ".ui.outliner")


def test_snap_icon_off_when_snapping_is_off():
    ts = bpy.context.scene.tool_settings
    ts.snap_elements = {'GRID'}
    ts.use_snap = False
    assert not status_line.snap_on(ts, "GRID"), "grid icon shows on while Blender snapping is off"
    ts.use_snap = True
    assert status_line.snap_on(ts, "GRID")
    ts.use_snap = False


def test_layer_weights_compose_like_maya():
    c = anim_layers.compose
    assert math.isclose(c([('ADD', 0.5, 10.0)], 2.0), 7.0)              # additive: base + w * x
    assert math.isclose(c([('REPLACE', 0.25, 10.0)], 2.0), 4.0)         # override: lerp
    assert math.isclose(c([('MUL', 0.5, 4.0)], 3.0), 6.0)               # scale: base * x ** w
    assert math.isclose(c([('ADD', 1.0, 1.0), ('REPLACE', 0.5, 0.0), ('ADD', 0.5, 2.0)], 1.0), 2.0)


def test_quaternion_layer_weight():
    from mathutils import Quaternion
    q90 = Quaternion((0, 0, 1), math.radians(90))
    out = anim_layers.compose_quaternion([("L", 'COMBINE', 0.5, q90)], (1, 0, 0, 0))
    assert math.isclose(math.degrees(out.angle), 45.0, abs_tol=1e-4), math.degrees(out.angle)
    out = anim_layers.compose_quaternion([("L", 'REPLACE', 0.5, q90)], (1, 0, 0, 0))
    assert math.isclose(out.normalized().angle, math.radians(45), abs_tol=1e-4)


def test_outliner_rows_keep_dag_order():
    scene = bpy.context.scene
    obs = []
    for name in ("qaA", "qaB", "qaC", "qaD"):
        ob = bpy.data.objects.new(name, None)
        scene.collection.objects.link(ob)
        obs.append(ob)
    a, b, c, d = obs
    c.parent = a
    d.parent = a
    for ob in obs:
        ob.allset_expanded = True
    rows = [r[1] for r in outliner.dag_rows(scene, False) if r[1].startswith("qa")]
    assert rows == ["qaA", "qaC", "qaD", "qaB"], rows
    bpy.data.batch_remove(obs)
