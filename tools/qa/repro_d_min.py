"""QA 240 D: hand-minimised repros of the monkey findings whose automatic shrink stayed long (seed 2 #200, #338) plus
one-action repros of the others. Each test raises while the kit bug is there.

Run: ALLSET_SANDBOX=qa_d python tests/run.py --no-build -k __none__ --extra tools/qa/repro_d_min.py
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import bpy

_spec = spec_from_file_location("qa_d_core", Path(__file__).resolve().parent / "qa_d_core.py")
core = module_from_spec(_spec)
_spec.loader.exec_module(core)


def ctx(sel, active, mode='OBJECT'):
    return {"kind": "ctx", "spec": {"sel": sel, "active": active, "mode": mode}}


def _check(actions, setup=None):
    mk = core.Monkey()
    mk.run(actions, setup=setup)
    assert not mk.failures, mk.failures[0][1] + "\n" + mk.failures[0][2][-1200:]


def test_uv_pin_surface_in_edit_mode():
    """Seed 2 #200: UV Pin on meshes with a UV map, then the pin surface in edit mode -> pins_205 depsgraph
    handler TypeError (foreach_get on the original mesh's UV data, empty while in edit mode)."""
    def setup():
        for ob in bpy.context.scene.objects:
            if ob.type == 'MESH' and not ob.data.uv_layers:
                ob.data.uv_layers.new(name="map1")
    _check([ctx(["pCylinder1", "pSphere1"], "pCylinder1"), {"kind": "menu", "path": "Constrain/UV Pin"},
            ctx(["pCube1", "pSphere1"], "pSphere1", 'EDIT'), ctx(["pCylinder1"], "pCylinder1", 'EDIT')], setup)


def test_cluster_on_zero_scale_object():
    """Seed 2 #338 (hypothesis): Deform > Cluster on an object with a singular matrix -> rig_maya ValueError."""
    def setup():
        bpy.context.scene.objects["pCube1"].scale = (1, 0, 1)
    _check([ctx(["pCube1"], "pCube1"), {"kind": "menu", "path": "Deform/Cluster"}], setup)


def test_circularize_from_object_mode():
    _check([ctx(["pCube1"], "pCube1"), {"kind": "menu", "path": "Edit Mesh/Circularize"}])


def test_remesh_with_joint_active():
    _check([ctx(["joint1"], "joint1"), {"kind": "menu", "path": "Mesh/Remesh"}])


def test_paint_hair_follicles_with_mesh():
    _check([ctx(["pCube1"], "pCube1"), {"kind": "menu", "path": "nHair/Paint Hair Follicles"}])


def test_bifrost_graph_editor():
    _check([{"kind": "menu", "path": "Windows/Bifrost Graph Editor"}])
